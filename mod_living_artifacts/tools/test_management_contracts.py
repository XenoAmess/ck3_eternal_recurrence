"""Authored native rows exercise real event contracts; no CK3 qualification."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

SHARED = Path(__file__).resolve().parents[2] / "tools"
if str(SHARED) not in sys.path:
    sys.path.append(str(SHARED))

from acceptance_contract import Frame, Object, field, json_value, mapping, object_value
from management_event_contract import management_choice, source_option_index


def replace_field(value: Object, path: tuple[str, ...], replacement: object) -> Object:
    """Produce a changed JSON row without mutating a shared fixture."""
    if not path:
        raise ValueError("At least one field is required")
    result = dict(value)
    result[path[0]] = json_value(replacement) if len(path) == 1 else replace_field(
        object_value(field(value, path[0])), path[1:], replacement)
    return result


def displayed_option(native: int, rendered: int, *, enabled: bool = True) -> Object:
    return {"native_option_index": native, "rendered_index": rendered,
        "shown": True, "enabled": enabled, "resolved_name": f"构造的显示项 {native}"}


def event_fixture(*, event: str = "xalw.10", instance: int = 87,
                  options: list[Object] | None = None, frame: Frame | None = None) -> tuple[Object, Frame]:
    frame = Frame(3, 2, 123456, 91, 124, "9") if frame is None else frame
    selected = [displayed_option(4, 0), displayed_option(9, 1)] if options is None else options
    query: Object = {
        "current_event_window_context": {
            "schema": "current-event-window-context-v1", "schema_version": 1,
            "status": "available", "event_definition_key": event,
            "current_event_instance_id": instance, "date_raw": frame.date_raw,
            "snapshot_revision": frame.native_revision, "window_match_count": 1,
            "readiness": {"option_presentation_ready": True},
            "root_scope": {"status": "available", "type_key": "character",
                "typed_identity": {"status": "available", "kind": "character",
                    "character_id": frame.player_id}},
            "options": json_value(selected),
        },
        "source": {"paused": True, "date_raw": frame.date_raw,
            "native_revision": frame.native_revision},
    }
    return query, frame


class ManagementEventTests(unittest.TestCase):
    def test_source_option_indices_are_derived_from_actual_generated_definitions(self) -> None:
        expected = (
            ("xalw.10", ("feed", "feed_common", "feed_masterwork", "feed_famed", "feed_illustrious",
                "train", "suppress", "renew", "appease", "close")),
            ("xalw.11", ("confirm", "cancel")),
            ("xalw.12", ("open", "close")),
        )
        for event, suffixes in expected:
            for index, suffix in enumerate(suffixes):
                # Guidance reuses the existing general close localization key.
                key = "xalw.10.close" if event == "xalw.12" and suffix == "close" else event + "." + suffix
                with self.subTest(event=event, key=key):
                    self.assertEqual(source_option_index(event, key), index)
        for event, option in (("xalw.99", "xalw.10.close"), ("xalw.10", "xalw.11.confirm"),
                ("xalw.10", "missing")):
            with self.subTest(event=event, option=option), self.assertRaises(ValueError):
                source_option_index(event, option)

    def test_hidden_options_keep_native_index_and_real_displayed_label(self) -> None:
        query, frame = event_fixture()
        actual = management_choice(query, frame=frame, instance_id=87,
            event_key="xalw.10", option_key="xalw.10.feed_illustrious")
        self.assertEqual(actual.native_option_index, 4)
        self.assertEqual(actual.rendered_index, 0)
        self.assertEqual(actual.resolved_name, "构造的显示项 4")
        self.assertEqual(actual.arguments(), {"event_instance_id": 87, "option_number": 5})
        self.assertNotEqual(actual.arguments()["option_number"], actual.rendered_index + 1)

    def test_guidance_and_confirmation_use_their_source_defined_choices(self) -> None:
        for event, key in (("xalw.12", "xalw.12.open"), ("xalw.11", "xalw.11.confirm")):
            with self.subTest(event=event):
                query, frame = event_fixture(event=event, options=[displayed_option(0, 0)])
                actual = management_choice(query, frame=frame, instance_id=87,
                    event_key=event, option_key=key)
                self.assertEqual(actual.arguments(), {"event_instance_id": 87, "option_number": 1})

    def test_request_instance_requires_exact_integer_not_false_equal_bool_or_float(self) -> None:
        query, frame = event_fixture(instance=1)
        for identity in (True, 1.0, 0, -1, 2**31):
            with self.subTest(identity=identity):
                # unittest's dynamic invocation deliberately supplies invalid API inputs.
                self.assertRaises(ValueError, management_choice, query, frame=frame,
                    instance_id=identity, event_key="xalw.10", option_key="xalw.10.feed_illustrious")

    def test_wrong_identity_pause_readiness_and_false_equal_json_numbers_are_rejected(self) -> None:
        query, frame = event_fixture()
        context = ("current_event_window_context",)
        changes: tuple[tuple[tuple[str, ...], object], ...] = (
            (context + ("schema",), "other"), (context + ("schema_version",), True),
            (context + ("schema_version",), 1.0), (context + ("status",), "unavailable"),
            (context + ("event_definition_key",), "xalw.11"),
            (context + ("current_event_instance_id",), True), (context + ("current_event_instance_id",), 87.0),
            (context + ("current_event_instance_id",), 88), (context + ("date_raw",), 123457),
            (context + ("date_raw",), 123456.0), (context + ("snapshot_revision",), 2.0),
            (context + ("snapshot_revision",), 3), (context + ("window_match_count",), True),
            (context + ("window_match_count",), 1.0), (context + ("window_match_count",), 2),
            (context + ("readiness", "option_presentation_ready"), 1),
            (context + ("root_scope", "status"), "unavailable"),
            (context + ("root_scope", "type_key"), "title"),
            (context + ("root_scope", "typed_identity", "kind"), "title"),
            (context + ("root_scope", "typed_identity", "character_id"), 92),
            (context + ("root_scope", "typed_identity", "character_id"), 91.0),
            (("source", "paused"), False), (("source", "paused"), 1),
            (("source", "date_raw"), 123456.0), (("source", "native_revision"), 3),
        )
        for path, value in changes:
            with self.subTest(path=path, value=value), self.assertRaises(ValueError):
                management_choice(replace_field(query, path, value), frame=frame, instance_id=87,
                    event_key="xalw.10", option_key="xalw.10.feed_illustrious")

    def test_missing_required_context_and_root_fields_are_rejected(self) -> None:
        query, frame = event_fixture()
        parents = ((), ("source",), ("current_event_window_context",),
            ("current_event_window_context", "readiness"),
            ("current_event_window_context", "root_scope"),
            ("current_event_window_context", "root_scope", "typed_identity"))
        for path in parents:
            nested = query
            for name in path:
                nested = object_value(field(nested, name))
            for missing in nested:
                reduced = {key: value for key, value in nested.items() if key != missing}
                changed = replace_field(query, path, reduced) if path else reduced
                with self.subTest(parent=path, missing=missing), self.assertRaises(ValueError):
                    management_choice(changed, frame=frame, instance_id=87,
                        event_key="xalw.10", option_key="xalw.10.feed_illustrious")

    def test_disabled_hidden_duplicate_reordered_and_wrong_type_options_are_rejected(self) -> None:
        query, frame = event_fixture()
        desired = displayed_option(4, 0)
        changes: tuple[tuple[str, object], ...] = (
            ("native_option_index", True), ("native_option_index", 4.0),
            ("rendered_index", True), ("rendered_index", 0.0), ("rendered_index", 1),
            ("shown", 1), ("shown", False), ("enabled", 1), ("enabled", False),
            ("resolved_name", ""), ("resolved_name", None),
        )
        candidates: list[tuple[str, object]] = [
            ("empty", []), ("not-list", (desired,)),
            ("not-displayed", [displayed_option(9, 0)]),
            ("duplicate", [desired, displayed_option(4, 1)]),
            ("too-many", [displayed_option(index, index) for index in range(65)]),
        ]
        candidates.extend((name, [{**desired, name: value}]) for name, value in changes)
        candidates.extend(("missing-" + name, [{key: value for key, value in desired.items() if key != name}])
            for name in desired)
        for name, options in candidates:
            # Keep tuple as a wrong runtime shape; JSON encoding would normalize it.
            changed = mapping(field(query, "current_event_window_context"), "authored native context")
            changed["options"] = options
            invalid: dict[str, object] = {**query, "current_event_window_context": changed}
            with self.subTest(case=name), self.assertRaises(ValueError):
                management_choice(invalid, frame=frame, instance_id=87,
                    event_key="xalw.10", option_key="xalw.10.feed_illustrious")


if __name__ == "__main__":
    unittest.main()
