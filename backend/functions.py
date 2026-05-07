import pandas as pd
import pickle
from support import use_vectorizer
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

def get_model_config(name):
    models = config['available_models']
    model = next((m for m in models if m['name'] == name), None)
    if not model:
        raise ValueError(f"Modelo '{name}' não encontrado. Disponíveis: {[m['name'] for m in models]}")
    return model

def get_computervision_client():
    subscription_key = os.getenv('SUBSCRIPTION_KEY')
    endpoint = os.getenv('ENDPOINT')

    if not subscription_key or not endpoint:
        raise RuntimeError(
            'SUBSCRIPTION_KEY e ENDPOINT precisam estar configurados para usar OCR.'
        )

    return ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))


def use_vectorizer(df_train):
    vectorizer_vez = pickle.load(open('vectorizer.pkl','rb'))
    ## realiza efetivamente a vetorização, transformando em uma matriz esparsa
    X = vectorizer_vez.transform(df_train['texto'])
    
    # transforma a matriz esparsa em um dataframe organizado com as frequencias TF-IDF das palavras 
    df_vetorizado = pd.DataFrame(X.A, columns=vectorizer_vez.get_feature_names_out())

    return df_vetorizado

def evaluate_redacao(redacao: str, conjunto: int = 1) -> dict:
    model_config = get_model_config(config['model'])
    model_type = model_config.get('type', 'pkl') 
    model_path = model_config['path']

    if model_type == 'lora':
        from predict import predict
        resultados = predict(
            texts=[redacao],
            adapter_path=model_path,
            strategy="truncate_512",
            conjunto=conjunto,
            as_scores=True,
        )
        pred = resultados[0]
        notas = {f"nota_{i}": pred[f"c{i}"] for i in range(1, 6)}

    elif model_type == 'pkl':
        import pickle
        import pandas as pd

        tupla = (redacao,)
        texto_df = pd.DataFrame(tupla, columns=['texto'])
        texto_vetorizado = use_vectorizer(texto_df)
        modelo_salvo = pickle.load(open(model_path, 'rb'))
        result = modelo_salvo.predict(texto_vetorizado)
        notas = {f"nota_{i}": result[0][i - 1] for i in range(1, 6)}

    else:
        raise ValueError(f"Tipo de modelo desconhecido: '{model_type}'")

    return notas


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
