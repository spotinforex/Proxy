import time

_seen_ids: dict[str, float] = {}
DEDUP_TTL = 60


def is_duplicate(message_id: str) -> bool:
    now = time.time()
    expired = [k for k, v in _seen_ids.items() if now - v > DEDUP_TTL]
    for k in expired:
        del _seen_ids[k]
    if message_id in _seen_ids:
        return True
    _seen_ids[message_id] = now
    return False
