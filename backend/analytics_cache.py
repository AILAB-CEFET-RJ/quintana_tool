from datetime import datetime, timezone
from time import time

from config import ANALYTICS_CACHE_TTL_SECONDS

_cache = {}


def make_key(teacher, class_id=None, activity_id=None, group_by="activity"):
    return "|".join([
        teacher or "",
        f"class={class_id or ''}",
        f"activity={activity_id or ''}",
        f"group_by={group_by or 'activity'}",
    ])


def get_cached_analytics(teacher, class_id=None, activity_id=None, group_by="activity"):
    if ANALYTICS_CACHE_TTL_SECONDS <= 0:
        return None

    key = make_key(teacher, class_id, activity_id, group_by)
    entry = _cache.get(key)
    if not entry:
        return None

    if time() - entry["created_monotonic"] > ANALYTICS_CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None

    payload = dict(entry["payload"])
    payload["cache"] = {
        "cached": True,
        "generated_at": entry["generated_at"],
        "ttl_seconds": ANALYTICS_CACHE_TTL_SECONDS,
    }
    return payload


def set_cached_analytics(teacher, class_id, activity_id, group_by, payload):
    if ANALYTICS_CACHE_TTL_SECONDS <= 0:
        return payload

    key = make_key(teacher, class_id, activity_id, group_by)
    generated_at = datetime.now(timezone.utc).isoformat()
    cached_payload = dict(payload)
    cached_payload["cache"] = {
        "cached": False,
        "generated_at": generated_at,
        "ttl_seconds": ANALYTICS_CACHE_TTL_SECONDS,
    }
    _cache[key] = {
        "created_monotonic": time(),
        "generated_at": generated_at,
        "payload": cached_payload,
    }
    return cached_payload


def invalidate_teacher_analytics(teacher=None):
    if teacher is None:
        _cache.clear()
        return

    prefix = f"{teacher}|"
    for key in list(_cache.keys()):
        if key.startswith(prefix):
            _cache.pop(key, None)
