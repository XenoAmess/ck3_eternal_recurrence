"""Fail-closed structural fixtures for the offline character-status reader."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from e2_05_a03_character_status import (  # noqa: E402
    CK3_SHA256, StatusUnknown, parse_melted, verify_checkpoint_receipt,
)


DATE = "1066.12.29"


def save(*entries: str, date: str = DATE) -> bytes:
    return (f"date={date}\nliving={{\n" + "\n".join(entries) + "\n}\n").encode("utf-8")


def character(body: str, character_id: int = 33437) -> str:
    return f"\t{character_id}={{\n{body}\n\t}}"


class CharacterStatusTest(unittest.TestCase):
    def assert_unknown(self, data: bytes) -> None:
        with self.assertRaises(StatusUnknown):
            parse_melted(data, 33437, DATE)

    def test_alive_exact_direct_scope(self) -> None:
        data = save(character('\t\talive_data={\n\t\t\thealth=4.2\n\t\t}'))
        result = parse_melted(data, 33437, DATE)
        self.assertEqual(result["life_status"], "alive")
        self.assertIsNone(result["death"])

    def test_alive_focus_date_is_not_a_death_field(self) -> None:
        data = save(character('\t\talive_data={\n\t\t\tfocus={\n'
                              '\t\t\t\ttype=martial\n\t\t\t\tdate=1066.9.15\n'
                              '\t\t\t}\n\t\t}'))
        result = parse_melted(data, 33437, DATE)
        self.assertEqual(result["life_status"], "alive")
        self.assertIsNone(result["death"])

    def test_alive_direct_death_field_remains_unknown(self) -> None:
        self.assert_unknown(save(character('reason="death_battle"\n'
                                           'alive_data={ focus={ date=1066.9.15 } }')))

    def test_dead_exact_direct_fields(self) -> None:
        data = save(character('\t\tdead_data={\n\t\t\tdate=1066.12.29\n'
                              '\t\t\treason="death_battle"\n\t\t\tkiller=34120\n\t\t}'))
        result = parse_melted(data, 33437, DATE)
        self.assertEqual(result["life_status"], "dead")
        self.assertEqual(result["death"], {"date": DATE, "reason": "death_battle",
                                           "killer_character_id": 34120})

    def test_duplicate_life_blocks_and_both_kinds_are_unknown(self) -> None:
        for body in ("alive_data={} alive_data={}", "dead_data={} dead_data={}",
                     "alive_data={} dead_data={}"):
            with self.subTest(body=body):
                self.assert_unknown(save(character(body)))

    def test_nested_life_shadow_is_unknown(self) -> None:
        self.assert_unknown(save(character("alive_data={}\nother={ dead_data={} }")))
        self.assert_unknown(save(character("other={ alive_data={} }")))

    def test_dead_fields_outside_scope_or_nested_shadow_are_unknown(self) -> None:
        fields = 'date=1066.12.29 reason="death_battle" killer=34120'
        self.assert_unknown(save(character(f"other={{ {fields} }}\n"
                                           f"dead_data={{ {fields} }}")))
        self.assert_unknown(save(character(f"dead_data={{ inner={{ {fields} }} }}")))

    def test_missing_or_duplicate_dead_fields_are_unknown(self) -> None:
        complete = 'date=1066.12.29 reason="death_battle" killer=34120'
        for body in ('date=1066.12.29 reason="death_battle"',
                     'date=1066.12.29 killer=34120',
                     'reason="death_battle" killer=34120',
                     complete + ' killer=34120',
                     complete + ' date={}',
                     'date=nope reason="death_battle" killer=34120',
                     'date=1066.12.29 reason="death_battle" killer=0'):
            with self.subTest(body=body):
                self.assert_unknown(save(character(f"dead_data={{ {body} }}")))

    def test_duplicate_target_database_and_date_are_unknown(self) -> None:
        target = character("alive_data={}")
        self.assert_unknown(save(target, target))
        self.assert_unknown(save(target) + save(target))
        self.assert_unknown(b"date=1066.12.29\n" + save(target))
        self.assert_unknown(save(target, date="1066.12.30"))
        self.assert_unknown(b"living=no\n" + save(target))
        self.assert_unknown(b"date={}\n" + save(target))
        self.assert_unknown(save("33437=no", target))

    def test_malformed_structure_is_unknown(self) -> None:
        data = save(character("alive_data={}"))
        self.assert_unknown(data[:-2])
        self.assert_unknown(data.replace(b"alive_data={}", b'alive_data={"unterminated}'))
        self.assert_unknown(save(character("alive_data=yes")))

    def test_unrelated_same_id_is_not_character_database_entry(self) -> None:
        data = b"other={ 33437={ dead_data={} } }\n" + save(character("alive_data={}"))
        self.assertEqual(parse_melted(data, 33437, DATE)["life_status"], "alive")

    def test_receipt_self_reported_hash_cannot_override_caller_pin(self) -> None:
        fake_sha = "A" * 64
        body = {
            "result": "CALL_COMPLETED",
            "body": {"step": "save-checkpoint", "accepted": True,
                     "submission": {"date_raw": 53146848},
                     "checkpoint": {"status": "saved", "name": "xar_checkpoint.ck3",
                                    "sha256": fake_sha, "size": 5, "date_raw": 53146848,
                                    "episode_character_id": 29829, "path": "fake"}},
            "driver_state": {"hello": {"expected_ck3_sha256": CK3_SHA256,
                                        "ck3_build_match": True,
                                        "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                                        "bridge_version": "0.1.0"}},
        }
        with self.assertRaises(StatusUnknown):
            verify_checkpoint_receipt(json.dumps(body).encode(), expected_sha="B" * 64,
                                      expected_date_raw=53146848, actor_id=29829)

    def test_receipt_missing_or_wrong_type_return_fields_are_unknown(self) -> None:
        base = {
            "result": "CALL_COMPLETED",
            "body": {"step": "save-checkpoint", "accepted": True,
                     "submission": {"date_raw": 53146848},
                     "checkpoint": {"status": "saved", "name": "xar_checkpoint.ck3",
                                    "sha256": "A" * 64, "size": 5, "date_raw": 53146848,
                                    "episode_character_id": 29829, "path": "save.ck3"}},
            "driver_state": {"hello": {"expected_ck3_sha256": CK3_SHA256,
                                        "ck3_build_match": True,
                                        "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                                        "bridge_version": "0.1.0"}},
        }
        for field, value in (("size", None), ("size", True), ("size", 0),
                             ("path", None), ("path", ""), ("bridge_version", None),
                             ("bridge_version", "wrong")):
            with self.subTest(field=field, value=value):
                payload = json.loads(json.dumps(base))
                branch = (payload["driver_state"]["hello"] if field == "bridge_version"
                          else payload["body"]["checkpoint"])
                if value is None:
                    branch.pop(field)
                else:
                    branch[field] = value
                with self.assertRaises(StatusUnknown):
                    verify_checkpoint_receipt(json.dumps(payload).encode(),
                                              expected_sha="A" * 64,
                                              expected_date_raw=53146848, actor_id=29829)


if __name__ == "__main__":
    unittest.main()
