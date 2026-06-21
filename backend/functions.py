import pandas as pd
import pickle
import os
from datetime import datetime
import json
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import os
import time
load_dotenv()

with open('configModel.json', 'r') as f:
    config = json.load(f)

SUPPORTED_OUTPUT_MODES = {"multi_output", "single_output_bundle"}
SUPPORTED_RUNTIMES = {"lora", "pkl"}
COMPETENCY_KEYS = ("c1", "c2", "c3", "c4", "c5")
_PKL_MODEL_CACHE = {}
_VECTORIZER_CACHE = {}


def _get_output_mode(model_config):
    if "output_mode" in model_config:
        return model_config["output_mode"]
    return "multi_output"


def _get_runtime(model_config):
    if "runtime" in model_config:
        return model_config["runtime"]
    return model_config.get("type", "pkl")


def get_model_config(name):
    models = config['available_models']
    model = next((m for m in models if m['name'] == name), None)
    if not model:
        raise ValueError(f"Modelo '{name}' não encontrado. Disponíveis: {[m['name'] for m in models]}")
    return model

def get_active_model_info():
    model_config = get_model_config(config['model'])
    output_mode = _get_output_mode(model_config)
    runtime = _get_runtime(model_config)
    components = {}
    for competency, component in model_config.get("models", {}).items():
        components[competency] = {
            "name": component.get("name", competency),
            "runtime": _get_runtime(component),
            "path": component.get("path"),
            "base_model": component.get("base_model", model_config.get("base_model")),
        }

    return {
        "name": model_config.get("name", config["model"]),
        "version": model_config.get("version", model_config.get("name", config["model"])),
        "type": runtime,
        "runtime": runtime,
        "output_mode": output_mode,
        "path": model_config.get("path"),
        "base_model": model_config.get("base_model"),
        "components": components,
    }


def validate_model_config(model_config):
    output_mode = _get_output_mode(model_config)
    runtime = _get_runtime(model_config)

    if output_mode not in SUPPORTED_OUTPUT_MODES:
        raise ValueError(
            f"output_mode desconhecido: '{output_mode}'. "
            f"Suportados: {sorted(SUPPORTED_OUTPUT_MODES)}"
        )

    if output_mode == "multi_output":
        if runtime not in SUPPORTED_RUNTIMES:
            raise ValueError(
                f"runtime desconhecido: '{runtime}'. "
                f"Suportados: {sorted(SUPPORTED_RUNTIMES)}"
            )
        if not model_config.get("path"):
            raise ValueError("Modelo multi_output precisa informar 'path'.")
        if not os.path.exists(model_config["path"]):
            raise FileNotFoundError(f"Caminho do modelo não encontrado: {model_config['path']}")
        return

    models = model_config.get("models") or {}
    missing = [key for key in COMPETENCY_KEYS if key not in models]
    if missing:
        raise ValueError(
            "Modelo single_output_bundle precisa informar modelos para "
            f"{', '.join(missing)}."
        )

    for competency in COMPETENCY_KEYS:
        component_config = models[competency]
        component_runtime = _get_runtime(component_config)
        if component_runtime not in SUPPORTED_RUNTIMES:
            raise ValueError(
                f"runtime desconhecido em {competency}: '{component_runtime}'. "
                f"Suportados: {sorted(SUPPORTED_RUNTIMES)}"
            )
        if not component_config.get("path"):
            raise ValueError(f"Modelo {competency} precisa informar 'path'.")
        if not os.path.exists(component_config["path"]):
            raise FileNotFoundError(
                f"Caminho do modelo {competency} não encontrado: {component_config['path']}"
            )

def get_computervision_client():
    subscription_key = os.getenv('SUBSCRIPTION_KEY')
    endpoint = os.getenv('ENDPOINT')

    if not subscription_key or not endpoint:
        raise RuntimeError(
            'SUBSCRIPTION_KEY e ENDPOINT precisam estar configurados para usar OCR.'
        )

    return ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))


def _load_pkl(path):
    if path not in _PKL_MODEL_CACHE:
        with open(path, 'rb') as f:
            _PKL_MODEL_CACHE[path] = pickle.load(f)
    return _PKL_MODEL_CACHE[path]


def _load_vectorizer(path):
    if path not in _VECTORIZER_CACHE:
        with open(path, 'rb') as f:
            _VECTORIZER_CACHE[path] = pickle.load(f)
    return _VECTORIZER_CACHE[path]


def _vectorize_text(redacao, vectorizer_path="vectorizer.pkl"):
    texto_df = pd.DataFrame((redacao,), columns=['texto'])
    vectorizer_vez = _load_vectorizer(vectorizer_path)
    ## realiza efetivamente a vetorização, transformando em uma matriz esparsa
    X = vectorizer_vez.transform(texto_df['texto'])
    
    # transforma a matriz esparsa em um dataframe organizado com as frequencias TF-IDF das palavras 
    df_vetorizado = pd.DataFrame(X.A, columns=vectorizer_vez.get_feature_names_out())

    return df_vetorizado


def _normalize_score(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0

    if 0 <= score <= 5 and score == int(score):
        score = score * 40

    return max(0, min(200, int(round(score))))


def _evaluate_multi_output_lora(redacao, model_config, conjunto):
    from predict import predict
    resultados = predict(
        texts=[redacao],
        adapter_path=model_config["path"],
        base_model_name=model_config.get("base_model"),
        strategy=model_config.get("strategy", "truncate_512"),
        conjunto=conjunto,
        as_scores=True,
    )
    pred = resultados[0]
    return {f"nota_{i}": _normalize_score(pred[f"c{i}"]) for i in range(1, 6)}


def _evaluate_multi_output_pkl(redacao, model_config):
    texto_vetorizado = _vectorize_text(redacao, model_config.get("vectorizer_path", "vectorizer.pkl"))
    modelo_salvo = _load_pkl(model_config["path"])
    result = modelo_salvo.predict(texto_vetorizado)
    return {f"nota_{i}": _normalize_score(result[0][i - 1]) for i in range(1, 6)}


def _evaluate_single_output_pkl(redacao, component_config):
    texto_vetorizado = _vectorize_text(redacao, component_config.get("vectorizer_path", "vectorizer.pkl"))
    model = _load_pkl(component_config["path"])
    result = model.predict(texto_vetorizado)
    return _normalize_score(result[0])


def _evaluate_single_output_lora(redacao, component_config):
    from predict import predict_single_output
    result = predict_single_output(
        texts=[redacao],
        adapter_path=component_config["path"],
        base_model_name=component_config.get("base_model"),
        strategy=component_config.get("strategy", "truncate_512"),
        as_scores=True,
    )
    return _normalize_score(result[0]["score"])


def _evaluate_single_output(redacao, component_config):
    runtime = _get_runtime(component_config)
    if runtime == "pkl":
        return _evaluate_single_output_pkl(redacao, component_config)
    if runtime == "lora":
        return _evaluate_single_output_lora(redacao, component_config)
    raise ValueError(f"runtime desconhecido em single_output_bundle: '{runtime}'")


def _evaluate_single_output_bundle(redacao, model_config):
    models = model_config["models"]
    return {
        f"nota_{index}": _evaluate_single_output(redacao, models[competency])
        for index, competency in enumerate(COMPETENCY_KEYS, start=1)
    }

def evaluate_redacao(redacao: str, conjunto: int = 1) -> dict:
    model_config = get_model_config(config['model'])
    validate_model_config(model_config)
    output_mode = _get_output_mode(model_config)
    runtime = _get_runtime(model_config)

    if output_mode == "single_output_bundle":
        return _evaluate_single_output_bundle(redacao, model_config)

    if runtime == "lora":
        return _evaluate_multi_output_lora(redacao, model_config, conjunto)
    if runtime == "pkl":
        return _evaluate_multi_output_pkl(redacao, model_config)

    raise ValueError(f"runtime desconhecido: '{runtime}'")


def persist_essay(essay, grades):
    if not os.path.exists('essays'):
        os.makedirs('essays')

    now = datetime.now()
    filename = now.strftime("%Y%m%d_%H%M%S")
        
    obj = {"essay": essay, "grades": grades, "date": filename}
    with open (f'essays/{filename}.json', 'w') as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)

def get_text(imagem):
    computervision_client = get_computervision_client()

    # Leia imagem do arquivo
    local_image_handwritten = imagem.stream

    # Chame API com imagem e resposta bruta (permite obter o local da operação)
    recognize_handwriting_results = computervision_client.read_in_stream(local_image_handwritten, raw=True)
    # Obtenha o local da operação (URL com ID como último apêndice)
    operation_location_remote = recognize_handwriting_results.headers["Operation-Location"]
    # Tire o ID e use para obter resultados
    operation_id = operation_location_remote.split("/")[-1]

    # Chame a API "GET" e aguarde a recuperação dos resultados
    while True:
        get_handw_results = computervision_client.get_read_result(operation_id)
        if get_handw_results.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    # salve em uma variável o texto detectado
    if get_handw_results.status == OperationStatusCodes.succeeded:
        text = ""
        for text_result in get_handw_results.analyze_result.read_results:
            for line in text_result.lines:
                text += line.text + " "
        return text.strip()
    else:
        return "Erro"
