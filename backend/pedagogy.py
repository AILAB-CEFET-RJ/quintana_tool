COMPETENCY_DETAILS = [
    {
        "code": "C1",
        "title": "Norma escrita",
        "field": "nota_competencia_1_model",
        "description": "Domínio da modalidade escrita formal",
        "low": "Há indícios de desvios ou escolhas linguísticas que podem prejudicar a precisão do texto.",
        "mid": "A escrita está compreensível, mas ainda pode ganhar mais regularidade formal.",
        "high": "A escrita formal está bem controlada e sustenta a leitura do texto.",
        "suggestion": "Revise concordância, pontuação, ortografia e escolhas vocabulares antes de reenviar.",
        "practice_action": "Faça uma leitura final procurando uma correção por vez: pontuação, concordância e repetição de palavras.",
        "checklist": "Revisei desvios de gramática, pontuação e ortografia?"
    },
    {
        "code": "C2",
        "title": "Proposta e repertório",
        "field": "nota_competencia_2_model",
        "description": "Compreensão da proposta e uso de repertório sociocultural",
        "low": "O texto precisa se conectar melhor ao tema e usar repertório de forma mais produtiva.",
        "mid": "O texto atende ao tema, mas pode articular melhor repertório e tese.",
        "high": "O texto demonstra boa compreensão da proposta e repertório pertinente.",
        "suggestion": "Garanta que tese, repertório e argumentos respondam diretamente ao recorte temático.",
        "practice_action": "Sublinhe a tese e verifique se cada repertório explica o problema discutido.",
        "checklist": "Minha tese responde diretamente ao tema proposto?"
    },
    {
        "code": "C3",
        "title": "Argumentação",
        "field": "nota_competencia_3_model",
        "description": "Seleção, organização e desenvolvimento de argumentos",
        "low": "A argumentação ainda precisa de desenvolvimento, organização e defesa mais clara do ponto de vista.",
        "mid": "Os argumentos existem, mas podem ser explicados com mais profundidade e encadeamento.",
        "high": "A argumentação está bem organizada e sustenta o ponto de vista.",
        "suggestion": "Desenvolva cada argumento com explicação, evidência e relação explícita com a tese.",
        "practice_action": "Em cada parágrafo argumentativo, escreva uma frase de ideia central e uma frase de consequência.",
        "checklist": "Cada parágrafo desenvolve um argumento completo?"
    },
    {
        "code": "C4",
        "title": "Coesão",
        "field": "nota_competencia_4_model",
        "description": "Mecanismos linguísticos para construção da argumentação",
        "low": "A progressão entre ideias precisa de conectores e retomadas mais claros.",
        "mid": "A coesão funciona em parte, mas pode variar conectivos e melhorar transições.",
        "high": "A coesão está bem construída e facilita a progressão argumentativa.",
        "suggestion": "Use conectivos para explicitar causa, oposição, consequência, exemplificação e conclusão.",
        "practice_action": "Revise o início dos parágrafos e troque conectivos repetidos por relações mais precisas.",
        "checklist": "Usei conectivos adequados entre ideias e parágrafos?"
    },
    {
        "code": "C5",
        "title": "Intervenção",
        "field": "nota_competencia_5_model",
        "description": "Proposta de intervenção",
        "low": "A proposta de intervenção está ausente, incompleta ou genérica.",
        "mid": "A proposta existe, mas pode detalhar melhor os elementos exigidos.",
        "high": "A proposta de intervenção está clara e bem relacionada ao problema.",
        "suggestion": "Explicite agente, ação, meio, finalidade e detalhamento na conclusão.",
        "practice_action": "Reescreva a conclusão conferindo os cinco elementos da intervenção.",
        "checklist": "Minha proposta tem agente, ação, meio, finalidade e detalhamento?"
    }
]


def level_for_score(score):
    if score < 120:
        return "low"
    if score < 160:
        return "mid"
    return "high"


def score_for_competency(grades, index):
    try:
        return float(list(grades.values())[index])
    except (IndexError, TypeError, ValueError):
        return 0


def build_structured_feedback(grades):
    competencies = []

    for index, item in enumerate(COMPETENCY_DETAILS):
        score = score_for_competency(grades, index)
        level = level_for_score(score)
        competencies.append({
            "code": item["code"],
            "title": item["title"],
            "description": item["description"],
            "score": score,
            "diagnosis": item[level],
            "suggestion": item["suggestion"],
            "practice_action": item["practice_action"],
        })

    priorities = [
        {
            "rank": rank + 1,
            "competency": item["code"],
            "title": item["title"],
            "score": item["score"],
            "reason": "Menor nota entre as competências avaliadas.",
            "next_action": next(
                detail["suggestion"]
                for detail in COMPETENCY_DETAILS
                if detail["code"] == item["code"]
            )
        }
        for rank, item in enumerate(sorted(competencies, key=lambda comp: comp["score"])[:3])
    ]

    rewrite_checklist = [
        {
            "id": item["code"].lower(),
            "competency": item["code"],
            "label": item["checklist"]
        }
        for item in COMPETENCY_DETAILS
    ]

    return {
        "competencies": competencies,
        "priorities": priorities,
        "rewrite_checklist": rewrite_checklist
    }


def build_textual_feedback_from_structured(structured_feedback):
    competencies = structured_feedback.get("competencies", [])
    priorities = structured_feedback.get("priorities", [])

    lines = [
        "## Feedback por competência",
        "",
        "A avaliação automática textual detalhada não está disponível no momento. "
        "Abaixo está uma devolutiva formativa gerada a partir das notas por competência.",
        "",
    ]

    for item in competencies:
        lines.extend([
            f"### {item.get('code')} — {item.get('title')}",
            f"**Nota:** {int(float(item.get('score', 0) or 0))}/200",
            "",
            f"**Diagnóstico:** {item.get('diagnosis', '')}",
            "",
            f"**Sugestão:** {item.get('suggestion', '')}",
            "",
            f"**Ação prática:** {item.get('practice_action', '')}",
            "",
        ])

    if priorities:
        lines.extend([
            "## Prioridades de estudo",
            "",
        ])
        for item in priorities:
            lines.append(
                f"{item.get('rank')}. {item.get('competency')} — {item.get('title')}: "
                f"{item.get('next_action')}"
            )

    return "\n".join(lines).strip()
