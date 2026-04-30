import ollama
import json
from openai import OpenAI

#ollama_client = ollama.Client(host='http://ollama:11434')
client = OpenAI()

def get_system_prompt(competencias_str):
    return (
        "Você é um avaliador pedagógico especialista em produção textual no contexto do ENEM. "
        "Sua tarefa é analisar uma redação escrita por um estudante, considerando as notas atribuídas "
        "a cada uma das cinco competências avaliativas do exame e também o tema (i.e., a proposta) da redação correspondente.\n\n"
        "Você deve gerar sugestões específicas de melhoria para o texto, sempre levando em conta:\n"
        "- O conteúdo integral da redação produzida.\n"
        "- As notas atribuídas em cada uma das cinco competências (0–200).\n"
        "- O tema da redação (proposta e/ou texto motivador).\n\n"
        f"**Competências Avaliadas:**\n{competencias_str}\n\n"
        "Apresente sua resposta no seguinte formato:\n\n"
        "**Sugestões de Melhoria (uma por competência):**\n"
        "1. **Competência [V]** (Nota: [nota]): [Sugestão concisa]\n"
        "2. **Competência [W]** (Nota: [nota]): [Sugestão concisa]\n"
        "3. **Competência [XX]** (Nota: [nota]): [Sugestão concisa]\n"
        "4. **Competência [Y]** (Nota: [nota]): [Sugestão concisa]\n"
        "5. **Competência [Z]** (Nota: [nota]): [Sugestão concisa]\n\n"
        "Guie-se pelas notas fornecidas e pelo conteúdo do texto para cada sugestão."
        "[Para cada competência, gere até 3 sugestões focadas nessa competência, levando em conta o conteúdo da redação, o escopo do tema e a nota recebida]\n"
        "---\n\n"
        "Importante: Use o tema da redação para avaliar a pertinência temática e o foco argumentativo do estudante. "
        "Se a proposta de intervenção for vaga, sugira maneiras de conectá-la melhor ao problema central. "
        "Não reescreva a redação nem emita julgamentos genéricos; concentre-se em orientar melhorias concretas."
    )

def get_user_prompt(tema, texto, competencias_str_user):
    return (
        f"Tema da redação:\n{tema}\n\n"
        f"Texto da redação:\n{texto}\n\n"
        f"Notas por competência:\n{competencias_str_user}"
    )

def get_llm_feedback(essay, grades, theme) -> str:
    competencias_str = "\n".join([
        f"- **{k}**: Nota {v}"
        for k, v in grades.items()
    ])

    system_prompt = get_system_prompt(competencias_str)

    competencias_str_user = "\n".join([
        f"Competência: Nota {v} | {k}"
        for k, v in grades.items()
    ])

    user_prompt = get_user_prompt(theme, essay, competencias_str_user)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


def get_structured_llm_feedback(essay, grades, theme) -> dict:
    competencies = "\n".join([
        f"- {index + 1}: {name} | Nota {score}"
        for index, (name, score) in enumerate(grades.items())
    ])

    system_prompt = (
        "Você é um avaliador pedagógico especialista em redação do ENEM. "
        "Retorne apenas JSON válido, sem markdown. "
        "O JSON deve conter as chaves: competencies, priorities e rewrite_checklist. "
        "competencies deve ser uma lista com 5 objetos contendo: code, title, description, score, diagnosis, suggestion, practice_action. "
        "priorities deve conter 3 objetos ordenados por urgência contendo: rank, competency, title, score, reason, next_action. "
        "rewrite_checklist deve conter itens com: id, competency, label. "
        "Use códigos C1, C2, C3, C4 e C5. Não invente nota; use as notas fornecidas."
    )

    user_prompt = (
        f"Tema:\n{theme}\n\n"
        f"Redação:\n{essay}\n\n"
        f"Competências e notas:\n{competencies}"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    return json.loads(resp.choices[0].message.content)
