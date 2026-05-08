"""
Inferência com modelos multioutput (MULTIPLE_OUTPUT_CLASSIFICATION).

Uso:
    python predict.py \
        --adapter_path ../../artifacts/results/MULTIPLE_OUTPUT_CLASSIFICATION/.../general/<date>-c1-/ \
        --texts "Texto da redação aqui..." \
        --strategy truncate_512 \
        --conjunto 1
"""

import argparse
import sys
import torch
import torch.nn as nn
import numpy as np
from transformers import AutoModel, AutoTokenizer
from peft import PeftModel

def apply_head_tail_token_ids(token_ids, payload_max_length):
    if len(token_ids) <= payload_max_length:
        return token_ids
    head_len = payload_max_length // 2
    tail_len = payload_max_length - head_len
    return token_ids[:head_len] + token_ids[-tail_len:]


def create_sliding_window_token_ids(token_ids, payload_max_length, stride, min_payload_length=32):
    if len(token_ids) <= payload_max_length:
        return [token_ids]
    windows = []
    start = 0
    while start < len(token_ids):
        window = token_ids[start : start + payload_max_length]
        if len(window) < min_payload_length:
            break
        windows.append(window)
        if start + payload_max_length >= len(token_ids):
            break
        start += stride
    return windows or [token_ids[:payload_max_length]]


BASE_MODEL_NAME = "FacebookAI/xlm-roberta-large"

COMPETENCIES = {
    1: [
        "dominio_da_modalidade_escrita_formal",
        "compreender_a_proposta_e_aplicar_conceitos_das_varias_areas_de_conhecimento_para_desenvolver_o_texto_dissertativoargumentativo_em_prosa",
        "selecionar_relacionar_organizar_e_interpretar_informacoes_em_defesa_de_um_ponto_de_vista",
        "conhecimento_dos_mecanismos_linguisticos_necessarios_para_a_construcao_da_argumentacao",
        "proposta_de_intervencao_com_respeito_aos_direitos_humanos",
    ],
    2: [
        "adequacao_ao_tema",
        "adequacao_e_leitura_critica_da_coletanea",
        "adequacao_ao_genero_textual",
        "adequacao_a_modalidade_padrao_da_lingua",
        "coesao_e_coerencia",
    ],
    3: [
        "conteudo",
        "estrutura_do_texto",
        "estrutura_de_ideias",
        "vocabulario",
        "gramatica_e_ortografia",
    ],
}

# Converte classe (0-5) para nota (0-200, passo de 40)
CLASS_TO_SCORE = {i: i * 40 for i in range(6)}


class MultiOutputClassifier(nn.Module):
    def __init__(self, base_model_name, num_classes_per_label, dropout_rate=0.3):
        super().__init__()
        self.base = AutoModel.from_pretrained(base_model_name)
        hidden_size = self.base.config.hidden_size
        self.dropout = nn.Dropout(dropout_rate)
        self.heads = nn.ModuleList([
            nn.Linear(hidden_size, num_classes)
            for num_classes in num_classes_per_label
        ])
        self.num_classes = num_classes_per_label[0]

    def forward(self, input_ids, attention_mask):
        outputs = self.base(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]
        pooled = self.dropout(pooled)
        logits = [head(pooled) for head in self.heads]
        return {"logits": logits}


def load_model(adapter_path: str, base_model_name: str = BASE_MODEL_NAME, device=None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"[INFO] Carregando modelo base: {base_model_name}")
    base = MultiOutputClassifier(base_model_name, num_classes_per_label=[6, 6, 6, 6, 6])

    print(f"[INFO] Carregando adapters LoRA de: {adapter_path}")
    model = PeftModel.from_pretrained(base, adapter_path)
    model.eval()
    model.to(device)
    return model


def _tokenize_texts(texts, tokenizer, strategy, max_length=512, stride=256, min_tokens=32):
    """Tokeniza uma lista de textos usando a mesma estratégia do treino."""
    special_tokens = tokenizer.num_special_tokens_to_add(pair=False)
    payload_max = max(1, max_length - special_tokens)

    all_input_ids = []
    all_attention_masks = []
    all_essay_ids = []

    for essay_idx, text in enumerate(texts):
        token_ids = tokenizer.encode(text, add_special_tokens=False)

        if strategy == "truncate_512":
            windows = [token_ids[:payload_max]]
        elif strategy == "head_tail_512":
            windows = [apply_head_tail_token_ids(token_ids, payload_max_length=payload_max)]
        elif strategy == "sliding_window_512":
            windows = create_sliding_window_token_ids(
                token_ids,
                payload_max_length=payload_max,
                stride=stride,
                min_payload_length=min_tokens,
            )
        else:
            raise ValueError(f"strategy inválida: '{strategy}'")

        for window_token_ids in windows:
            merged = tokenizer.build_inputs_with_special_tokens(window_token_ids)
            all_input_ids.append(merged)
            all_attention_masks.append([1] * len(merged))
            all_essay_ids.append(essay_idx)

    return all_input_ids, all_attention_masks, all_essay_ids


def _pad_batch(input_ids_list, attention_masks_list, tokenizer):
    max_len = max(len(ids) for ids in input_ids_list)
    pad_id = tokenizer.pad_token_id

    padded_ids = []
    padded_masks = []
    for ids, mask in zip(input_ids_list, attention_masks_list):
        pad_len = max_len - len(ids)
        padded_ids.append(ids + [pad_id] * pad_len)
        padded_masks.append(mask + [0] * pad_len)

    return (
        torch.tensor(padded_ids, dtype=torch.long),
        torch.tensor(padded_masks, dtype=torch.long),
    )


def predict(
    texts: list,
    adapter_path: str,
    base_model_name: str = BASE_MODEL_NAME,
    strategy: str = "truncate_512",
    stride: int = 256,
    min_tokens: int = 32,
    batch_size: int = 8,
    conjunto: int = 1,
    as_scores: bool = True,
):
    """
    Faz inferência sobre uma lista de textos.

    Args:
        texts: lista de strings com as redações.
        adapter_path: caminho para a pasta com adapter_config.json e adapter_model.safetensors.
        base_model_name: nome do modelo base no HuggingFace Hub.
        strategy: estratégia de tokenização ('truncate_512', 'head_tail_512', 'sliding_window_512').
        stride: stride para sliding_window_512 (padrão: 256).
        min_tokens: mínimo de tokens por janela para sliding_window_512 (padrão: 32).
        batch_size: tamanho do batch na inferência.
        conjunto: conjunto de dados (1, 2 ou 3) — usado para nomear as competências.
        as_scores: se True, converte classes (0-5) para notas (0-200); se False, retorna classes.

    Returns:
        lista de dicts com as predições por competência para cada texto.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Device: {device} | Estratégia: {strategy}")

    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    model = load_model(adapter_path, base_model_name, device)

    all_input_ids, all_attention_masks, all_essay_ids = _tokenize_texts(
        texts, tokenizer, strategy, stride=stride, min_tokens=min_tokens
    )

    # Acumulador para sliding window: essay_id → lista de logits por head
    n_heads = 5
    accumulator = {i: [[] for _ in range(n_heads)] for i in range(len(texts))}

    n_windows = len(all_input_ids)
    for start in range(0, n_windows, batch_size):
        batch_ids_list = all_input_ids[start : start + batch_size]
        batch_mask_list = all_attention_masks[start : start + batch_size]
        batch_essay_ids = all_essay_ids[start : start + batch_size]

        input_ids, attention_mask = _pad_batch(batch_ids_list, batch_mask_list, tokenizer)
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)

        with torch.no_grad():
            out = model(input_ids=input_ids, attention_mask=attention_mask)

        logits = out["logits"]  # lista de n_heads tensores [batch, 6]

        for row_idx, essay_id in enumerate(batch_essay_ids):
            for head_idx in range(n_heads):
                accumulator[essay_id][head_idx].append(
                    logits[head_idx][row_idx].detach().cpu()
                )

    # Agrega logits das janelas (média) e obtém predições finais
    competencies = COMPETENCIES.get(conjunto, COMPETENCIES[1])
    results = []
    for essay_id in range(len(texts)):
        mean_logits = [
            torch.stack(accumulator[essay_id][h]).mean(dim=0)
            for h in range(n_heads)
        ]
        classes = [int(lgt.argmax().item()) for lgt in mean_logits]

        entry = {}
        for i, comp in enumerate(competencies):
            short_name = f"c{i+1}"
            cls = classes[i]
            entry[short_name] = CLASS_TO_SCORE[cls] if as_scores else cls
            entry[f"{short_name}_nome"] = comp
        results.append(entry)

    return results


def main():
    parser = argparse.ArgumentParser(description="Inferência multioutput textgrader")
    parser.add_argument("--adapter_path", required=True, help="Caminho para a pasta com os adapters LoRA")
    parser.add_argument("--texts", nargs="+", required=True, help="Textos das redações")
    parser.add_argument("--base_model", default=BASE_MODEL_NAME, help="Modelo base HuggingFace")
    parser.add_argument("--strategy", default="truncate_512",
                        choices=["truncate_512", "head_tail_512", "sliding_window_512"])
    parser.add_argument("--stride", type=int, default=256)
    parser.add_argument("--min_tokens", type=int, default=32)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--conjunto", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--raw_classes", action="store_true",
                        help="Retorna classes (0-5) em vez de notas (0-200)")
    args = parser.parse_args()

    results = predict(
        texts=args.texts,
        adapter_path=args.adapter_path,
        base_model_name=args.base_model,
        strategy=args.strategy,
        stride=args.stride,
        min_tokens=args.min_tokens,
        batch_size=args.batch_size,
        conjunto=args.conjunto,
        as_scores=not args.raw_classes,
    )

    print("\n=== Predições ===")
    for i, res in enumerate(results):
        print(f"\nRedação {i+1}:")
        for j in range(1, 6):
            key = f"c{j}"
            nome = res[f"{key}_nome"]
            valor = res[key]
            print(f"  {key} | {nome}: {valor}")


if __name__ == "__main__":
    main()
