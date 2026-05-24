from datetime import datetime, timezone
import math
import re


VALID_ENEM_SCORES = {0, 40, 80, 120, 160, 200}


def _score(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _word_count(text):
    return len(re.findall(r"\w+", text or "", flags=re.UNICODE))


def _flag(code, message, severity="medium"):
    return {
        "code": code,
        "message": message,
        "severity": severity,
    }


def validate_ai_evaluation(text, scores, model_info=None, checked_at=None):
    """
    Apply deterministic sanity checks to an automatic essay evaluation.

    This layer does not correct model outputs. It only marks potentially
    inconsistent evaluations so teachers can prioritize human review.
    """
    checked_at = checked_at or datetime.now(timezone.utc).isoformat()
    model_info = model_info or {}
    numeric_scores = [_score(value) for value in scores]
    flags = []

    if any(value is None for value in numeric_scores):
        flags.append(_flag(
            "invalid_score",
            "Uma ou mais competências receberam nota inválida.",
            "high",
        ))

    valid_scores = [value for value in numeric_scores if value is not None]
    for index, value in enumerate(numeric_scores, start=1):
        if value is None:
            continue
        if value < 0 or value > 200:
            flags.append(_flag(
                "score_out_of_range",
                f"C{index} recebeu {value:g}, fora da faixa esperada de 0 a 200.",
                "high",
            ))
        if round(value) not in VALID_ENEM_SCORES:
            flags.append(_flag(
                "non_standard_score_step",
                f"C{index} recebeu {value:g}, valor fora dos níveis usuais do ENEM.",
                "low",
            ))

    if valid_scores:
        maximum = max(valid_scores)
        minimum = min(valid_scores)
        total = sum(valid_scores)
        zero_indexes = [index + 1 for index, value in enumerate(numeric_scores) if value == 0]
        high_scores = [value for value in valid_scores if value >= 160]

        if zero_indexes and high_scores:
            flags.append(_flag(
                "isolated_zero",
                f"{', '.join(f'C{index}' for index in zero_indexes)} recebeu 0 enquanto outra competência ficou em 160 ou mais.",
                "high",
            ))

        if maximum - minimum >= 160:
            flags.append(_flag(
                "high_dispersion",
                "Há dispersão muito alta entre as notas por competência.",
                "medium",
            ))

        words = _word_count(text)
        if words < 80 and total >= 700:
            flags.append(_flag(
                "short_text_high_score",
                "Texto muito curto recebeu nota total alta.",
                "high",
            ))
        if words >= 250 and total <= 200:
            flags.append(_flag(
                "long_text_low_score",
                "Texto longo recebeu nota total muito baixa.",
                "medium",
            ))
    else:
        words = _word_count(text)

    stripped_text = (text or "").strip()
    if not stripped_text or stripped_text.lower() == "erro" or words < 20:
        flags.append(_flag(
            "insufficient_text",
            "Texto ausente, muito curto ou possivelmente inválido para avaliação automática.",
            "high",
        ))

    model_type = str(model_info.get("model_type") or model_info.get("type") or "").lower()
    model_name = str(model_info.get("model_name") or model_info.get("name") or "").lower()
    if model_type in {"pkl", "seed"} or "checkpoint" in model_name:
        flags.append(_flag(
            "model_review_recommended",
            "Avaliação gerada por modelo leve, legado ou por dados sintéticos; recomenda-se revisão humana.",
            "low",
        ))

    high_or_medium = any(flag["severity"] in {"high", "medium"} for flag in flags)
    if high_or_medium:
        status = "requires_review"
    elif flags:
        status = "review_recommended"
    else:
        status = "ok"

    return {
        "status": status,
        "requires_review": high_or_medium,
        "flags": flags,
        "checked_at": checked_at,
    }
