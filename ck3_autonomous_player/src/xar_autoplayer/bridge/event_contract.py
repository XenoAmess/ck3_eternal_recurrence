"""Backend-neutral contract for one currently actionable CK3 event."""

from __future__ import annotations

from collections.abc import Iterable


EVENT_OPTION_STEP_PREFIX = "select-event-option-"


def event_option_step(option_number: int) -> str:
    """Return the semantic step for a 1-based rendered option number."""
    _positive_integer(option_number, "option_number")
    return f"{EVENT_OPTION_STEP_PREFIX}{option_number}"


def parse_event_option_step(step: object) -> int | None:
    """Parse a select-event step, returning its 1-based option number."""
    if not isinstance(step, str) or not step.startswith(EVENT_OPTION_STEP_PREFIX):
        return None
    suffix = step.removeprefix(EVENT_OPTION_STEP_PREFIX)
    if not suffix.isascii() or not suffix.isdigit():
        return None
    option_number = int(suffix)
    return option_number if option_number > 0 else None


def normalize_active_event(
    value: object,
    *,
    default_source: str,
) -> dict[str, object] | None:
    """Normalize native and OCR event shapes into one planner-facing object.

    ``option_number`` is deliberately 1-based because it is also the suffix in
    ``select-event-option-N`` and the existing OCR shortcut number.  ``index``
    remains the zero-based value consumed by ``CSelectEventOptionCommand``.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("active_event must be an object or null")

    instance_id = value.get("instance_id")
    if instance_id is not None:
        _non_negative_integer(instance_id, "active_event instance_id")

    title = value.get("title")
    if title is not None and (not isinstance(title, str) or not title.strip()):
        raise ValueError("active_event title must be a non-empty string or null")

    source = value.get("source", default_source)
    if not isinstance(source, str) or not source:
        raise ValueError("active_event source must be a non-empty string")

    raw_options = value.get("options")
    if raw_options is not None and not isinstance(raw_options, list):
        raise ValueError("active_event options must be a list")
    normalized_by_number: dict[int, dict[str, object]] = {}
    for fallback_number, raw_option in enumerate(raw_options or (), start=1):
        if not isinstance(raw_option, dict):
            raise ValueError("active_event option must be an object")
        option_number = raw_option.get("option_number")
        if option_number is None:
            raw_index = raw_option.get("index")
            if raw_index is None:
                option_number = fallback_number
            else:
                _non_negative_integer(raw_index, "active_event option index")
                option_number = int(raw_index) + 1
        _positive_integer(option_number, "active_event option_number")
        option_number = int(option_number)
        raw_index = raw_option.get("index", option_number - 1)
        _non_negative_integer(raw_index, "active_event option index")
        if int(raw_index) != option_number - 1:
            raise ValueError("active_event option index and option_number disagree")
        if option_number in normalized_by_number:
            raise ValueError("active_event option numbers must be unique")

        label = raw_option.get("label", raw_option.get("visible_text"))
        if label is not None and not isinstance(label, str):
            raise ValueError("active_event option label must be a string or null")
        enabled = raw_option.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError("active_event option enabled must be boolean")
        option: dict[str, object] = {
            "index": option_number - 1,
            "option_number": option_number,
            "label": label,
            "enabled": enabled,
        }
        score = raw_option.get("strategy_score")
        if score is not None:
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError(
                    "active_event option strategy_score must be numeric or null"
                )
            option["strategy_score"] = score
        reasons = raw_option.get("strategy_reasons")
        if isinstance(reasons, list):
            option["strategy_reasons"] = [
                reason for reason in reasons if isinstance(reason, str)
            ]
        normalized_by_number[option_number] = option

    option_count = value.get("option_count")
    if option_count is None and raw_options is not None:
        option_count = len(normalized_by_number)
    if option_count is not None:
        _non_negative_integer(option_count, "active_event option_count")
        option_count = int(option_count)
        if normalized_by_number and max(normalized_by_number) > option_count:
            raise ValueError("active_event option exceeds option_count")
        for option_number in range(1, option_count + 1):
            normalized_by_number.setdefault(
                option_number,
                {
                    "index": option_number - 1,
                    "option_number": option_number,
                    "label": None,
                    "enabled": True,
                },
            )

    return {
        "source": source,
        "instance_id": instance_id,
        "option_count": option_count,
        "title": title,
        "options": [normalized_by_number[key] for key in sorted(normalized_by_number)],
    }


def choose_event_option_number(active_event: object) -> int | None:
    """Choose the best enabled option, preferring score then visual order."""
    if not isinstance(active_event, dict):
        return None
    options = active_event.get("options")
    if not isinstance(options, list):
        return None
    ranked: list[tuple[float, int]] = []
    for option in options:
        if not isinstance(option, dict) or option.get("enabled") is not True:
            continue
        option_number = option.get("option_number")
        if (
            isinstance(option_number, bool)
            or not isinstance(option_number, int)
            or option_number <= 0
        ):
            continue
        score = option.get("strategy_score", 0)
        numeric_score = (
            float(score)
            if not isinstance(score, bool) and isinstance(score, (int, float))
            else 0.0
        )
        ranked.append((numeric_score, option_number))
    if not ranked:
        return None
    _score, option_number = max(ranked, key=lambda row: (row[0], -row[1]))
    return option_number


def action_step_set(capabilities: object) -> set[str]:
    """Extract exact semantic action names from a driver capability object."""
    raw_steps = (
        capabilities.get("action_steps") if isinstance(capabilities, dict) else None
    )
    if not isinstance(raw_steps, Iterable) or isinstance(raw_steps, (str, bytes)):
        return set()
    return {step for step in raw_steps if isinstance(step, str) and step}


def _positive_integer(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _non_negative_integer(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
