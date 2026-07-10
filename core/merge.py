"""Детерминированное слияние profile_patch → Profile."""
from copy import deepcopy

SCALAR_LISTS = {"skills", "achievements", "languages"}
KEYED_LISTS = {
    "experience": ("org", "role"),
    "projects": ("name",),
    "education": ("institution",),
}


def _key(item: dict, fields: tuple) -> tuple:
    """ Ключ для сравнения элементов списка по заданным полям. """
    return tuple((item or {}).get(f) for f in fields)


def merge_profile(profile: dict, patch: dict) -> dict:
    """Применяет patch к profile детерминированно. Модель НЕ перезаписывает profile целиком."""

    result = deepcopy(profile)
    for k, v in (patch or {}).items():
        if k in SCALAR_LISTS and isinstance(v, list):
            cur = result.get(k) or []
            result[k] = cur + [x for x in v if x not in cur]
        elif k in KEYED_LISTS and isinstance(v, list):
            cur = result.get(k) or []
            idx = {_key(it, KEYED_LISTS[k]): i for i, it in enumerate(cur)}
            for item in v:
                kk = _key(item, KEYED_LISTS[k])
                if kk in idx:
                    cur[idx[kk]] = {**cur[idx[kk]], **item}
                else:
                    idx[kk] = len(cur)
                    cur.append(item)
            result[k] = cur
        elif isinstance(v, dict):
            base = result.get(k) or {}
            base.update(v)
            result[k] = base
        elif v not in (None, "", []):
            result[k] = v
    return result
