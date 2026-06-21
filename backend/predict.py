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
import json
import os
import sys
import torch
import torch.nn as nn
import numpy as np
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer
from peft import PeftModel

def apply_head_tail_token_ids(token_ids, payload_max_length):
    if payload_max_length <= 0:
        raise ValueError("payload_max_length must be > 0")

    if len(token_ids) <= payload_max_length:
        return token_ids
    head_len = payload_max_length // 2
    tail_len = payload_max_length - head_len
    return token_ids[:head_len] + token_ids[-tail_len:]


def create_sliding_window_token_ids(token_ids, payload_max_length, stride, min_payload_length=32):
    if payload_max_length <= 0:
        raise ValueError("payload_max_length must be > 0")
    if stride <= 0:
        raise ValueError("stride must be > 0")
    if min_payload_length <= 0:
        raise ValueError("min_payload_length must be > 0")

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
_TOKENIZER_CACHE = {}
_MODEL_CACHE = {}

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


class SingleOutputClassifier(nn.Module):
    def __init__(self, base_model_name, num_classes=6, dropout_rate=0.3):
        super().__init__()
        self.base = AutoModel.from_pretrained(base_model_name)
        hidden_size = self.base.config.hidden_size
        self.dropout = nn.Dropout(dropout_rate)
        self.head = nn.Linear(hidden_size, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.base(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]
        pooled = self.dropout(pooled)
        return {"logits": self.head(pooled)}


def _resolve_base_model_name(base_model_name=None):
    return base_model_name or BASE_MODEL_NAME


def load_tokenizer(base_model_name: str = BASE_MODEL_NAME):
    base_model_name = _resolve_base_model_name(base_model_name)
    if base_model_name not in _TOKENIZER_CACHE:
        _TOKENIZER_CACHE[base_model_name] = AutoTokenizer.from_pretrained(base_model_name)
    return _TOKENIZER_CACHE[base_model_name]


def _read_adapter_config(adapter_path):
    config_path = os.path.join(adapter_path, "adapter_config.json")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r") as f:
        return json.load(f)


def load_model(adapter_path: str, base_model_name: str = BASE_MODEL_NAME, device=None, output_mode="multi_output"):
    base_model_name = _resolve_base_model_name(base_model_name)
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    cache_key = (output_mode, adapter_path, base_model_name, str(device))
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    print(f"[INFO] Carregando modelo base: {base_model_name}")
    if output_mode == "single_output":
        adapter_config = _read_adapter_config(adapter_path)
        if adapter_config.get("task_type") == "SEQ_CLS":
            base = AutoModelForSequenceClassification.from_pretrained(base_model_name, num_labels=6)
        else:
            base = SingleOutputClassifier(base_model_name, num_classes=6)
    else:
        base = MultiOutputClassifier(base_model_name, num_classes_per_label=[6, 6, 6, 6, 6])

    print(f"[INFO] Carregando adapters LoRA de: {adapter_path}")
    model = PeftModel.from_pretrained(base, adapter_path)
    model.eval()
    model.to(device)
    _MODEL_CACHE[cache_key] = model
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

        if strategy in {"truncate_512", "full_context"}:
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
            merged = _build_input_ids_with_special_tokens(tokenizer, window_token_ids)
            all_input_ids.append(merged)
            all_attention_masks.append([1] * len(merged))
            all_essay_ids.append(essay_idx)

    return all_input_ids, all_attention_masks, all_essay_ids


def _build_input_ids_with_special_tokens(tokenizer, token_ids):
    cls_token_id = getattr(tokenizer, "cls_token_id", None)
    sep_token_id = getattr(tokenizer, "sep_token_id", None)
    bos_token_id = getattr(tokenizer, "bos_token_id", None)
    eos_token_id = getattr(tokenizer, "eos_token_id", None)

    start_token_id = cls_token_id if cls_token_id is not None else bos_token_id
    end_token_id = sep_token_id if sep_token_id is not None else eos_token_id

    if start_token_id is None or end_token_id is None:
        raise ValueError(
            "Tokenizer sem tokens especiais de início/fim conhecidos. "
            "Configure tokenizer com cls/sep ou bos/eos."
        )

    return [start_token_id] + token_ids + [end_token_id]


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
    max_length: int = 512,
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
        strategy: estratégia de tokenização ('truncate_512', 'head_tail_512', 'sliding_window_512' ou 'full_context').
        max_length: comprimento máximo da sequência após special tokens.
        stride: stride para sliding_window_512 (padrão: 256).
        min_tokens: mínimo de tokens por janela para sliding_window_512 (padrão: 32).
        batch_size: tamanho do batch na inferência.
        conjunto: conjunto de dados (1, 2 ou 3) — usado para nomear as competências.
        as_scores: se True, converte classes (0-5) para notas (0-200); se False, retorna classes.

    Returns:
        lista de dicts com as predições por competência para cada texto.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base_model_name = _resolve_base_model_name(base_model_name)
    print(f"[INFO] Device: {device} | Estratégia: {strategy}")

    tokenizer = load_tokenizer(base_model_name)
    model = load_model(adapter_path, base_model_name, device, output_mode="multi_output")

    all_input_ids, all_attention_masks, all_essay_ids = _tokenize_texts(
        texts, tokenizer, strategy, max_length=max_length, stride=stride, min_tokens=min_tokens
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


def predict_single_output(
    texts: list,
    adapter_path: str,
    base_model_name: str = BASE_MODEL_NAME,
    strategy: str = "truncate_512",
    max_length: int = 512,
    stride: int = 256,
    min_tokens: int = 32,
    batch_size: int = 8,
    as_scores: bool = True,
):
    """
    Faz inferência com um adapter LoRA treinado para uma única competência.

    Retorna uma lista de dicts no formato {"score": valor}, em que valor é nota
    0-200 quando as_scores=True ou classe 0-5 quando as_scores=False.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base_model_name = _resolve_base_model_name(base_model_name)
    print(f"[INFO] Device: {device} | Estratégia: {strategy} | single_output")

    tokenizer = load_tokenizer(base_model_name)
    model = load_model(adapter_path, base_model_name, device, output_mode="single_output")

    all_input_ids, all_attention_masks, all_essay_ids = _tokenize_texts(
        texts, tokenizer, strategy, max_length=max_length, stride=stride, min_tokens=min_tokens
    )

    accumulator = {i: [] for i in range(len(texts))}
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

        logits = out["logits"] if isinstance(out, dict) else out.logits
        for row_idx, essay_id in enumerate(batch_essay_ids):
            accumulator[essay_id].append(logits[row_idx].detach().cpu())

    results = []
    for essay_id in range(len(texts)):
        mean_logits = torch.stack(accumulator[essay_id]).mean(dim=0)
        cls = int(mean_logits.argmax().item())
        results.append({"score": CLASS_TO_SCORE[cls] if as_scores else cls})

    return results


def main():
    parser = argparse.ArgumentParser(description="Inferência multioutput")
    parser.add_argument("--adapter_path", required=True, help="Caminho para a pasta com os adapters LoRA")
    parser.add_argument("--texts", nargs="+", required=True, help="Textos das redações")
    parser.add_argument("--base_model", default=BASE_MODEL_NAME, help="Modelo base HuggingFace")
    parser.add_argument("--strategy", default="truncate_512",
                        choices=["truncate_512", "head_tail_512", "sliding_window_512", "full_context"])
    parser.add_argument("--max_length", type=int, default=512)
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
        max_length=args.max_length,
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
