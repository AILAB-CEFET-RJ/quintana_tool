import re
from collections import Counter


MIN_NON_EMPTY_LINES = 7
MIN_WORDS = 30
MIN_ALPHA_CHARS = 100
APPROX_CHARS_PER_LINE = 55
MIN_UNIQUE_WORDS = 12
MAX_REPEATED_WORD_RATIO = 0.55


def _non_empty_lines(text):
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _words(text):
    return re.findall(r"\b[\wÀ-ÿ]+\b", (text or "").lower(), flags=re.UNICODE)


def _alpha_count(text):
    return len(re.findall(r"[A-Za-zÀ-ÿ]", text or "", flags=re.UNICODE))


def _estimated_written_lines(text, non_empty_line_count):
    alpha_chars = _alpha_count(text)
    estimated_by_length = alpha_chars // APPROX_CHARS_PER_LINE
    return max(non_empty_line_count, estimated_by_length)


def classify_essay_submission(text):
    stripped = (text or "").strip()
    lines = _non_empty_lines(stripped)
    word_list = _words(stripped)
    words = len(word_list)
    word_counts = Counter(word_list)
    unique_words = len(word_counts)
    most_common_word_count = word_counts.most_common(1)[0][1] if word_counts else 0
    repeated_word_ratio = most_common_word_count / words if words else 0
    alpha_chars = _alpha_count(stripped)
    written_lines = _estimated_written_lines(stripped, len(lines))

    if not stripped:
        return {
            "is_valid_for_model": False,
            "zero_grade": True,
            "code": "empty_submission",
            "message": "A redação recebeu nota zero porque o texto enviado está vazio.",
            "metrics": {
                "non_empty_lines": 0,
                "estimated_written_lines": 0,
                "words": 0,
                "unique_words": 0,
                "repeated_word_ratio": 0,
                "alpha_chars": 0,
            },
        }

    if written_lines < MIN_NON_EMPTY_LINES:
        return {
            "is_valid_for_model": False,
            "zero_grade": True,
            "code": "below_minimum_lines",
            "message": "A redação recebeu nota zero porque tem menos de 7 linhas escritas.",
            "metrics": {
                "non_empty_lines": len(lines),
                "estimated_written_lines": written_lines,
                "words": words,
                "unique_words": unique_words,
                "repeated_word_ratio": repeated_word_ratio,
                "alpha_chars": alpha_chars,
            },
        }

    if words < MIN_WORDS or alpha_chars < MIN_ALPHA_CHARS:
        return {
            "is_valid_for_model": False,
            "zero_grade": True,
            "code": "insufficient_written_text",
            "message": (
                "A redação recebeu nota zero porque não apresenta texto escrito suficiente "
                "para avaliação."
            ),
            "metrics": {
                "non_empty_lines": len(lines),
                "estimated_written_lines": written_lines,
                "words": words,
                "unique_words": unique_words,
                "repeated_word_ratio": repeated_word_ratio,
                "alpha_chars": alpha_chars,
            },
        }

    if unique_words < MIN_UNIQUE_WORDS or repeated_word_ratio > MAX_REPEATED_WORD_RATIO:
        return {
            "is_valid_for_model": False,
            "zero_grade": True,
            "code": "low_textual_diversity",
            "message": (
                "A redação recebeu nota zero porque o texto apresenta repetição excessiva "
                "ou baixa diversidade de palavras."
            ),
            "metrics": {
                "non_empty_lines": len(lines),
                "estimated_written_lines": written_lines,
                "words": words,
                "unique_words": unique_words,
                "repeated_word_ratio": repeated_word_ratio,
                "alpha_chars": alpha_chars,
            },
        }

    return {
        "is_valid_for_model": True,
        "zero_grade": False,
        "code": "valid",
        "message": "",
        "metrics": {
            "non_empty_lines": len(lines),
            "estimated_written_lines": written_lines,
            "words": words,
            "unique_words": unique_words,
            "repeated_word_ratio": repeated_word_ratio,
            "alpha_chars": alpha_chars,
        },
    }


def build_invalid_submission_quality(validity, checked_at):
    return {
        "status": "invalid_submission",
        "requires_review": False,
        "flags": [
            {
                "code": validity.get("code", "invalid_submission"),
                "message": validity.get("message", "Redação não avaliável."),
                "severity": "high",
            }
        ],
        "checked_at": checked_at,
        "metrics": validity.get("metrics", {}),
    }
