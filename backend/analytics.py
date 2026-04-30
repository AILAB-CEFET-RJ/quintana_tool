from statistics import median
from bson import ObjectId
import database


COMPETENCIES = [
    {"code": "C1", "title": "Norma escrita", "field": "nota_competencia_1_model"},
    {"code": "C2", "title": "Proposta e repertório", "field": "nota_competencia_2_model"},
    {"code": "C3", "title": "Argumentação", "field": "nota_competencia_3_model"},
    {"code": "C4", "title": "Coesão", "field": "nota_competencia_4_model"},
    {"code": "C5", "title": "Intervenção", "field": "nota_competencia_5_model"},
]


def score(redacao, field):
    try:
        return float(redacao.get(field, 0) or 0)
    except (TypeError, ValueError):
        return 0


def object_id_time(redacao):
    value = redacao.get("created_at") or redacao.get("submitted_at")
    if value:
        return value
    return str(redacao.get("_id", ""))


def serialize_id(value):
    if isinstance(value, ObjectId):
        return str(value)
    return value


def theme_map_for_professor(professor_name):
    temas = list(database.db.temas.find({"nome_professor": professor_name}))
    return {
        str(tema["_id"]): {
            "_id": str(tema["_id"]),
            "tema": tema.get("tema", "Tema sem título"),
            "nome_professor": tema.get("nome_professor"),
        }
        for tema in temas
    }


def teacher_essays(professor_name, class_id=None, activity_id=None):
    temas = theme_map_for_professor(professor_name)
    query = {"id_tema": {"$in": list(temas.keys())}}

    if class_id:
        query["class_id"] = class_id

    if activity_id:
        query["activity_id"] = activity_id

    redacoes = list(database.db.redacoes.find(query))
    return redacoes, temas


def latest_versions(redacoes):
    grouped = {}

    for redacao in redacoes:
        group_id = redacao.get("version_group_id") or str(redacao.get("_id"))
        current = grouped.get(group_id)
        current_version = int(current.get("version_number", 1)) if current else -1
        candidate_version = int(redacao.get("version_number", 1))

        if (
            current is None
            or candidate_version > current_version
            or (
                candidate_version == current_version
                and object_id_time(redacao) > object_id_time(current)
            )
        ):
            grouped[group_id] = redacao

    return list(grouped.values())


def averages_for(redacoes):
    if not redacoes:
        return {item["code"]: 0 for item in COMPETENCIES}

    return {
        item["code"]: round(
            sum(score(redacao, item["field"]) for redacao in redacoes) / len(redacoes),
            1
        )
        for item in COMPETENCIES
    }


def build_distribution(redacoes):
    distribution = []

    for item in COMPETENCIES:
        values = [score(redacao, item["field"]) for redacao in redacoes]
        values = [value for value in values if value >= 0]

        distribution.append({
            "competency": item["code"],
            "title": item["title"],
            "average": round(sum(values) / len(values), 1) if values else 0,
            "median": round(median(values), 1) if values else 0,
            "min": round(min(values), 1) if values else 0,
            "max": round(max(values), 1) if values else 0,
            "count": len(values),
            "below_120_count": len([value for value in values if value < 120]),
            "below_120_percent": round((len([value for value in values if value < 120]) / len(values)) * 100, 1) if values else 0,
        })

    return distribution


def build_ranking(distribution):
    return [
        {
            "rank": index + 1,
            "competency": item["competency"],
            "title": item["title"],
            "average": item["average"],
            "below_120_percent": item["below_120_percent"],
        }
        for index, item in enumerate(sorted(distribution, key=lambda row: row["average"]))
    ]


def build_heatmap(redacoes):
    by_student = {}

    for redacao in redacoes:
        student = redacao.get("aluno") or "Aluno sem nome"
        current = by_student.get(student)

        if current is None or object_id_time(redacao) > object_id_time(current):
            by_student[student] = redacao

    rows = []
    for student, redacao in sorted(by_student.items()):
        rows.append({
            "student": student,
            "scores": {
                item["code"]: score(redacao, item["field"])
                for item in COMPETENCIES
            },
            "total": score(redacao, "nota_total"),
            "essay_count": len([item for item in redacoes if item.get("aluno") == student]),
            "redacao_id": str(redacao.get("_id")),
        })

    return rows


def build_groups(heatmap):
    groups = {
        item["code"]: {
            "competency": item["code"],
            "title": item["title"],
            "students": [],
            "recommended_activity": recommended_activity(item["code"])
        }
        for item in COMPETENCIES
    }

    for row in heatmap:
        lowest_code = min(row["scores"], key=lambda code: row["scores"][code])
        groups[lowest_code]["students"].append(row["student"])

    return [group for group in groups.values() if group["students"]]


def recommended_activity(code):
    return {
        "C1": "Revisão orientada de norma escrita e clareza frasal.",
        "C2": "Oficina de leitura da proposta e repertório sociocultural.",
        "C3": "Oficina de desenvolvimento argumentativo.",
        "C4": "Atividade de coesão e progressão textual.",
        "C5": "Oficina de proposta de intervenção completa.",
    }.get(code, "Atividade de reescrita orientada.")


def build_evolution(redacoes, temas):
    by_theme = {}

    for redacao in redacoes:
        theme_id = redacao.get("id_tema")
        by_theme.setdefault(theme_id, []).append(redacao)

    evolution = []
    for theme_id, items in by_theme.items():
        theme = temas.get(theme_id, {})
        averages = averages_for(items)
        evolution.append({
            "theme_id": theme_id,
            "label": theme.get("tema", "Tema não encontrado"),
            "submitted_at": min([object_id_time(item) for item in items]) if items else "",
            "averages": averages,
            "total_average": round(sum(score(item, "nota_total") for item in items) / len(items), 1) if items else 0,
            "submission_count": len(items),
        })

    return sorted(evolution, key=lambda item: item["submitted_at"])


def build_theme_performance(evolution):
    return [
        {
            "theme_id": item["theme_id"],
            "theme": item["label"],
            "total_average": item["total_average"],
            "submission_count": item["submission_count"],
            **item["averages"],
        }
        for item in sorted(evolution, key=lambda row: row["total_average"])
    ]


def build_alerts(redacoes, distribution, heatmap, class_id=None, activity_id=None):
    alerts = []

    for item in distribution:
        if item["count"] and item["below_120_percent"] >= 50:
            alerts.append({
                "type": "competency_low",
                "severity": "high" if item["below_120_percent"] >= 65 else "medium",
                "message": f"{item['below_120_percent']}% da turma ficou abaixo de 120 em {item['competency']}.",
                "competency": item["competency"],
            })

    by_student = {}
    for redacao in sorted(redacoes, key=object_id_time):
        by_student.setdefault(redacao.get("aluno") or "Aluno sem nome", []).append(redacao)

    drops = []
    for student, items in by_student.items():
        if len(items) < 2:
            continue

        previous = items[-2]
        latest = items[-1]
        for item in COMPETENCIES:
            if score(latest, item["field"]) < score(previous, item["field"]):
                drops.append({"student": student, "competency": item["code"]})

    if drops:
        c3_drops = [item for item in drops if item["competency"] == "C3"]
        if c3_drops:
            alerts.append({
                "type": "competency_drop",
                "severity": "medium",
                "message": f"{len(c3_drops)} alunos tiveram queda em C3 nas duas últimas redações.",
                "competency": "C3",
                "students": [item["student"] for item in c3_drops],
            })

    if class_id and activity_id:
        class_doc = database.db.classes.find_one({"_id": ObjectId(class_id)}) if ObjectId.is_valid(class_id) else None
        if class_doc:
            expected_students = set(class_doc.get("students", []))
            submitted_students = set(redacao.get("aluno") for redacao in redacoes if redacao.get("activity_id") == activity_id)
            missing = sorted(expected_students - submitted_students)
            if missing:
                alerts.append({
                    "type": "missing_submission",
                    "severity": "medium",
                    "message": f"{len(missing)} alunos não submeteram a atividade selecionada.",
                    "students": missing,
                })

    return alerts


def build_teacher_analytics(professor_name, class_id=None, activity_id=None):
    redacoes, temas = teacher_essays(professor_name, class_id, activity_id)
    latest_redacoes = latest_versions(redacoes)
    distribution = build_distribution(latest_redacoes)
    ranking = build_ranking(distribution)
    heatmap = build_heatmap(latest_redacoes)
    groups = build_groups(heatmap)
    evolution = build_evolution(latest_redacoes, temas)
    theme_performance = build_theme_performance(evolution)
    alerts = build_alerts(latest_redacoes, distribution, heatmap, class_id, activity_id)

    return {
        "scope": {
            "teacher": professor_name,
            "class_id": class_id,
            "activity_id": activity_id,
            "essay_count": len(latest_redacoes),
            "student_count": len(heatmap),
        },
        "distribution": distribution,
        "ranking": ranking,
        "heatmap": heatmap,
        "groups": groups,
        "evolution": evolution,
        "theme_performance": theme_performance,
        "alerts": alerts,
    }
