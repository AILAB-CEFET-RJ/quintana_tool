# Configuração dos modelos de avaliação

O arquivo `backend/configModel.json` define qual modelo avaliativo será usado pelo backend para corrigir redações submetidas por estudantes.

## Conceitos

A configuração separa duas dimensões:

- `output_mode`: descreve o formato da saída do modelo.
- `runtime`: descreve como o modelo é carregado e executado.

Modos de saída suportados:

- `multi_output`: um único modelo retorna as cinco notas, de C1 a C5.
- `single_output_bundle`: cinco modelos single-output são agrupados, cada um responsável por uma competência.

Runtimes suportados:

- `lora`: adapter LoRA/PEFT executado sobre um modelo base HuggingFace.
- `pkl`: modelo serializado em pickle, usado com o vetorizador TF-IDF.

Independentemente da configuração interna, o backend sempre normaliza a saída para:

```python
{
    "nota_1": 120,
    "nota_2": 160,
    "nota_3": 120,
    "nota_4": 160,
    "nota_5": 80
}
```

Assim, o frontend não precisa saber se a correção veio de um modelo multi-output ou de um conjunto de modelos single-output.

## Modelo multi-output com LoRA

```json
{
  "name": "principal",
  "output_mode": "multi_output",
  "runtime": "lora",
  "path": "adapters/principal",
  "base_model": "FacebookAI/xlm-roberta-large",
  "strategy": "truncate_512"
}
```

Esse formato usa um único adapter capaz de produzir as cinco competências simultaneamente.

## Modelo multi-output com pickle

```json
{
  "name": "checkpoint_07_08",
  "output_mode": "multi_output",
  "runtime": "pkl",
  "path": "checkpoint_07_08.pkl",
  "vectorizer_path": "vectorizer.pkl"
}
```

Esse formato espera que o modelo retorne um vetor com cinco posições, uma para cada competência.

## Bundle single-output com LoRA

```json
{
  "name": "single_lora_v1",
  "output_mode": "single_output_bundle",
  "runtime": "lora",
  "models": {
    "c1": {
      "name": "single_lora_v1_c1",
      "runtime": "lora",
      "path": "adapters/single_lora_v1/c1",
      "base_model": "neuralmind/bert-large-portuguese-cased",
      "strategy": "sliding_window_512",
      "tokenizer_max_length": 512,
      "sliding_window_stride": 256,
      "sliding_window_min_tokens": 32,
      "script_type": "ORDINAL_CLASSIFICATION_WITH_WK_LOSS",
      "use_prompt_pair": false
    },
    "c2": {
      "name": "single_lora_v1_c2",
      "runtime": "lora",
      "path": "adapters/single_lora_v1/c2",
      "base_model": "neuralmind/bert-large-portuguese-cased",
      "strategy": "sliding_window_512",
      "tokenizer_max_length": 512,
      "sliding_window_stride": 256,
      "sliding_window_min_tokens": 32,
      "script_type": "ORDINAL_CLASSIFICATION_WITH_WK_LOSS",
      "use_prompt_pair": false
    },
    "c3": {
      "name": "single_lora_v1_c3",
      "runtime": "lora",
      "path": "adapters/single_lora_v1/c3",
      "base_model": "neuralmind/bert-large-portuguese-cased",
      "strategy": "sliding_window_512",
      "tokenizer_max_length": 512,
      "sliding_window_stride": 256,
      "sliding_window_min_tokens": 32,
      "script_type": "ORDINAL_CLASSIFICATION_WITH_WK_LOSS",
      "use_prompt_pair": false
    },
    "c4": {
      "name": "single_lora_v1_c4",
      "runtime": "lora",
      "path": "adapters/single_lora_v1/c4",
      "base_model": "neuralmind/bert-large-portuguese-cased",
      "strategy": "sliding_window_512",
      "tokenizer_max_length": 512,
      "sliding_window_stride": 256,
      "sliding_window_min_tokens": 32,
      "script_type": "ORDINAL_CLASSIFICATION_WITH_WK_LOSS",
      "use_prompt_pair": false
    },
    "c5": {
      "name": "single_lora_v1_c5",
      "runtime": "lora",
      "path": "adapters/single_lora_v1/c5",
      "base_model": "neuralmind/bert-large-portuguese-cased",
      "strategy": "sliding_window_512",
      "tokenizer_max_length": 512,
      "sliding_window_stride": 256,
      "sliding_window_min_tokens": 32,
      "script_type": "ORDINAL_CLASSIFICATION_WITH_WK_LOSS",
      "use_prompt_pair": false
    }
  }
}
```

Nesse formato, o backend executa os cinco modelos e agrega as saídas em uma única avaliação.

Os campos `strategy`, `tokenizer_max_length`, `sliding_window_stride`,
`sliding_window_min_tokens`, `script_type` e `use_prompt_pair` devem refletir os
metadados salvos no `results.json` do treinamento. Para modelos treinados com
`sliding_window_512`, a inferência também divide redações longas em janelas,
executa o modelo em cada janela, calcula a média dos logits e só então escolhe a
classe final.

O bundle `single_lora_v1` atual foi treinado com `use_prompt_pair=false`. Modelos
futuros treinados com prompt-pair exigem suporte adicional para receber tema e
contexto motivador na inferência.

## Seleção do modelo ativo

A chave `model` seleciona qual entrada de `available_models` será usada:

```json
{
  "model": "principal",
  "available_models": []
}
```

Para trocar o modelo ativo, altere o valor de `model` para o `name` desejado e reinicie o backend.

## Observações operacionais

- O backend lê `configModel.json` durante a inicialização.
- Alterações no arquivo exigem reinício do backend.
- O backend mantém cache em memória para modelos pickle, vetorizadores e modelos LoRA já carregados.
- O campo `ai_evaluation` salvo em cada redação registra `model_runtime`, `model_output_mode` e os componentes do bundle, quando houver.
