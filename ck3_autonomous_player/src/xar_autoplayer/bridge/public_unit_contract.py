"""Public CUnit handles are non-negative int32 values, including slot zero.

This contract applies only to public CUnit IDs. Native CArmy, character,
province, war, siege and combat handles keep their own contracts.
"""

from __future__ import annotations


def is_public_cunit_id(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= 2**31 - 1
    )


def public_cunit_id(value: object, name: str) -> int:
    if not is_public_cunit_id(value):
        raise ValueError(f"{name} must be a public CUnit int32 in [0, {2**31 - 1}]")
    return value


def optional_public_cunit_id(value: object, name: str) -> int | None:
    return None if value is None else public_cunit_id(value, name)


def canonical_public_cunit_decimal(value: str) -> bool:
    return (
        value == "0"
        or bool(value and value.isascii() and value.isdigit() and value[0] != "0")
    )


def canonical_public_cunit_token(value: str) -> int | None:
    if not canonical_public_cunit_decimal(value):
        return None
    parsed = int(value)
    return parsed if is_public_cunit_id(parsed) else None


def public_cunit_ids(
    value: object,
    name: str,
    *,
    unique: bool = True,
    strictly_increasing: bool = False,
    nonempty: bool = False,
) -> list[int]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(f"{name} must be a{' nonempty' if nonempty else ''} list")
    result = [public_cunit_id(item, f"{name}[{index}]") for index, item in enumerate(value)]
    if unique and len(result) != len(set(result)):
        raise ValueError(f"{name} contains duplicate public CUnit IDs")
    if strictly_increasing and any(left >= right for left, right in zip(result, result[1:])):
        raise ValueError(f"{name} must be in strict native numeric order")
    return result
