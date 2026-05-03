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

ANALYTICS_PROJECTION = {
    "titulo": 1,
    "nota_total": 1,
    "id_tema": 1,
    "aluno": 1,
    "nota_competencia_1_model": 1,
    "nota_competencia_2_model": 1,
    "nota_competencia_3_model": 1,
    "nota_competencia_4_model": 1,
    "nota_competencia_5_model": 1,
    "created_at": 1,
    "submitted_at": 1,
    "version_group_id": 1,
    "version_number": 1,
    "class_id": 1,
    "activity_id": 1,
    "is_latest_version": 1,
}


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
    temas = list(database.db.temas.find(
        {"nome_professor": professor_name},
        {"tema": 1, "nome_professor": 1}
    ))
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
    class_ids = [str(item["_id"]) for item in database.db.classes.find({"teacher": professor_name}, {"_id": 1})]
    activity_ids = [str(item["_id"]) for item in database.db.activities.find({"teacher": professor_name}, {"_id": 1})]
    query = {"$or": [
        {"id_tema": {"$in": list(temas.keys())}},
        {"class_id": {"$in": class_ids}},
        {"activity_id": {"$in": activity_ids}},
    ]}

    if class_id:
        query = {"$and": [query, {"class_id": class_id}]}

    if activity_id:
        query = {"$and": [query, {"activity_id": activity_id}]}

    redacoes = list(database.db.redacoes.find(query, ANALYTICS_PROJECTION))
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


def percentile(values, percent):
    if not values:
        return 0

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percent
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def boxplot_stats(values):
    if not values:
        return {
            "q1": 0,
            "q3": 0,
            "iqr": 0,
            "lower_whisker": 0,
            "upper_whisker": 0,
            "outliers": [],
        }

    q1 = percentile(values, 0.25)
    q3 = percentile(values, 0.75)
    iqr = q3 - q1
    lower_limit = q1 - 1.5 * iqr
    upper_limit = q3 + 1.5 * iqr
    non_outliers = [value for value in values if lower_limit <= value <= upper_limit]

    return {
        "q1": round(q1, 1),
        "q3": round(q3, 1),
        "iqr": round(iqr, 1),
        "lower_whisker": round(min(non_outliers), 1) if non_outliers else round(min(values), 1),
        "upper_whisker": round(max(non_outliers), 1) if non_outliers else round(max(values), 1),
        "outliers": [round(value, 1) for value in values if value < lower_limit or value > upper_limit],
    }


def build_distribution(redacoes):
    distribution = []

    for item in COMPETENCIES:
        values = [score(redacao, item["field"]) for redacao in redacoes]
        values = [value for value in values if value >= 0]
        boxplot = boxplot_stats(values)

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
            **boxplot,
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
        "reforco_geral": {
            "key": "reforco_geral",
            "title": "Reforço geral",
            "competency": "Geral",
            "students": [],
            "recommended_activity": "Sequência de reescrita guiada com foco em planejamento, argumentação e intervenção.",
            "profile": "Média geral abaixo de 100."
        },
        "intervencao": {
            "key": "intervencao",
            "title": "Proposta de intervenção",
            "competency": "C5",
            "students": [],
            "recommended_activity": recommended_activity("C5"),
            "profile": "C5 abaixo de 120."
        },
        "argumentacao": {
            "key": "argumentacao",
            "title": "Desenvolvimento argumentativo",
            "competency": "C3",
            "students": [],
            "recommended_activity": recommended_activity("C3"),
            "profile": "C3 abaixo de 120."
        },
        "coesao": {
            "key": "coesao",
            "title": "Coesão textual",
            "competency": "C4",
            "students": [],
            "recommended_activity": recommended_activity("C4"),
            "profile": "C4 abaixo de 120."
        },
        "tema_repertorio": {
            "key": "tema_repertorio",
            "title": "Tema e repertório",
            "competency": "C2",
            "students": [],
            "recommended_activity": recommended_activity("C2"),
            "profile": "C2 abaixo de 120."
        },
        "norma": {
            "key": "norma",
            "title": "Norma escrita",
            "competency": "C1",
            "students": [],
            "recommended_activity": recommended_activity("C1"),
            "profile": "C1 abaixo de 120."
        },
        "alta_performance": {
            "key": "alta_performance",
            "title": "Alta performance",
            "competency": "Avançado",
            "students": [],
            "recommended_activity": "Atividade de refinamento: repertório autoral, precisão argumentativa e proposta detalhada.",
            "profile": "Nenhuma competência abaixo de 120."
        },
    }

    for row in heatmap:
        scores = row["scores"]
        average = sum(scores.values()) / len(scores) if scores else 0

        if average < 100:
            group_key = "reforco_geral"
        elif scores.get("C5", 0) < 120:
            group_key = "intervencao"
        elif scores.get("C3", 0) < 120:
            group_key = "argumentacao"
        elif scores.get("C4", 0) < 120:
            group_key = "coesao"
        elif scores.get("C2", 0) < 120:
            group_key = "tema_repertorio"
        elif scores.get("C1", 0) < 120:
            group_key = "norma"
        else:
            group_key = "alta_performance"

        groups[group_key]["students"].append(row["student"])

    return [group for group in groups.values() if group["students"]]


def recommended_activity(code):
    return {
        "C1": "Revisão orientada de norma escrita e clareza frasal.",
        "C2": "Oficina de leitura da proposta e repertório sociocultural.",
        "C3": "Oficina de desenvolvimento argumentativo.",
        "C4": "Atividade de coesão e progressão textual.",
        "C5": "Oficina de proposta de intervenção completa.",
    }.get(code, "Atividade de reescrita orientada.")


def activity_map(activity_ids):
    object_ids = [ObjectId(value) for value in activity_ids if value and ObjectId.is_valid(value)]
    activities = list(database.db.activities.find({"_id": {"$in": object_ids}})) if object_ids else []
    return {str(item["_id"]): item for item in activities}


def week_key(value):
    if not value:
        return "Sem data"
    return str(value)[:10]


def build_evolution(redacoes, temas, group_by="activity"):
    activities = activity_map([item.get("activity_id") for item in redacoes])
    grouped = {}

    for redacao in redacoes:
        if group_by == "week":
            key = week_key(redacao.get("submitted_at") or redacao.get("created_at"))
        elif group_by == "theme":
            key = redacao.get("id_tema")
        else:
            key = redacao.get("activity_id") or redacao.get("id_tema")

        grouped.setdefault(key, []).append(redacao)

    evolution = []
    for key, items in grouped.items():
        first = items[0] if items else {}
        activity = activities.get(key, {})
        theme_id = activity.get("theme_id") or first.get("id_tema")
        theme = temas.get(theme_id, {})
        label = activity.get("title") or theme.get("tema") or key or "Sem agrupamento"
        averages = averages_for(items)
        evolution.append({
            "key": key,
            "group_by": group_by,
            "theme_id": theme_id,
            "activity_id": str(activity.get("_id")) if activity else first.get("activity_id"),
            "label": label,
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


def build_alerts(redacoes, distribution, heatmap, class_id=None, activity_id=None, evolution=None):
    alerts = []

    for item in distribution:
        if item["count"] and item["below_120_percent"] >= 50:
            alerts.append({
                "type": "competency_low",
                "severity": "high" if item["below_120_percent"] >= 65 else "medium",
                "message": f"{item['below_120_percent']}% da turma ficou abaixo de 120 em {item['competency']}.",
                "competency": item["competency"],
                "action": "Planejar uma intervenção coletiva para essa competência.",
            })

        if item.get("iqr", 0) >= 60:
            alerts.append({
                "type": "high_dispersion",
                "severity": "medium",
                "message": f"A turma apresenta alta dispersão em {item['competency']} (IQR {item['iqr']}).",
                "competency": item["competency"],
                "action": "Separar grupos por nível antes da atividade de reescrita.",
            })

    by_student = {}
    for redacao in sorted(redacoes, key=object_id_time):
        by_student.setdefault(redacao.get("aluno") or "Aluno sem nome", []).append(redacao)

    drops = []
    sharp_total_drops = []
    no_progress_students = []
    for student, items in by_student.items():
        if len(items) < 2:
            continue

        previous = items[-2]
        latest = items[-1]
        total_delta = score(latest, "nota_total") - score(previous, "nota_total")
        if total_delta <= -80:
            sharp_total_drops.append(student)

        for item in COMPETENCIES:
            if score(latest, item["field"]) < score(previous, item["field"]):
                drops.append({"student": student, "competency": item["code"]})

        if len(items) >= 3:
            last_three = items[-3:]
            first_total = score(last_three[0], "nota_total")
            last_total = score(last_three[-1], "nota_total")
            if last_total - first_total < 20:
                no_progress_students.append(student)

    if drops:
        c3_drops = [item for item in drops if item["competency"] == "C3"]
        if c3_drops:
            alerts.append({
                "type": "competency_drop",
                "severity": "medium",
                "message": f"{len(c3_drops)} alunos tiveram queda em C3 nas duas últimas redações.",
                "competency": "C3",
                "students": [item["student"] for item in c3_drops],
                "action": "Revisar desenvolvimento argumentativo com esses estudantes.",
            })

    if sharp_total_drops:
        alerts.append({
            "type": "sharp_total_drop",
            "severity": "high",
            "message": f"{len(sharp_total_drops)} alunos tiveram queda brusca na nota total.",
            "students": sharp_total_drops,
            "action": "Verificar se houve mudança de tema, compreensão da proposta ou problemas de escrita.",
        })

    if no_progress_students:
        alerts.append({
            "type": "no_progress",
            "severity": "medium",
            "message": f"{len(no_progress_students)} alunos não apresentaram evolução relevante nas últimas três redações.",
            "students": no_progress_students,
            "action": "Planejar devolutiva individual ou roteiro de reescrita mais dirigido.",
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
                    "action": "Retomar a atividade com a turma ou enviar lembrete aos estudantes.",
                })

            submitted_count = len(submitted_students)
            expected_count = len(expected_students)
            if expected_count and submitted_count / expected_count < 0.7:
                alerts.append({
                    "type": "low_submission_rate",
                    "severity": "high",
                    "message": f"A atividade selecionada tem baixa taxa de submissão ({submitted_count}/{expected_count}).",
                    "action": "Avaliar prorrogação de prazo ou reforço de comunicação da atividade.",
                })

    if evolution:
        totals = [item.get("total_average", 0) for item in evolution if item.get("submission_count", 0) > 0]
        if totals:
            average_total = sum(totals) / len(totals)
            low_items = [item for item in evolution if item.get("submission_count", 0) > 0 and item.get("total_average", 0) <= average_total - 80]
            for item in low_items:
                alerts.append({
                    "type": "low_theme_performance",
                    "severity": "medium",
                    "message": f"'{item['label']}' teve desempenho abaixo do padrão da turma.",
                    "action": "Verificar se o tema exigia repertório específico ou se a proposta gerou dificuldade de compreensão.",
                })

    return alerts


def build_teacher_analytics(professor_name, class_id=None, activity_id=None, group_by="activity"):
    redacoes, temas = teacher_essays(professor_name, class_id, activity_id)
    latest_redacoes = latest_versions(redacoes)
    distribution = build_distribution(latest_redacoes)
    ranking = build_ranking(distribution)
    heatmap = build_heatmap(latest_redacoes)
    groups = build_groups(heatmap)
    evolution = build_evolution(latest_redacoes, temas, group_by)
    theme_evolution = evolution if group_by == "theme" else build_evolution(latest_redacoes, temas, "theme")
    theme_performance = build_theme_performance(theme_evolution)
    alerts = build_alerts(latest_redacoes, distribution, heatmap, class_id, activity_id, evolution)

    return {
        "scope": {
            "teacher": professor_name,
            "class_id": class_id,
            "activity_id": activity_id,
            "group_by": group_by,
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
