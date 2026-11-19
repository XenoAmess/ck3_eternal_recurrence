from __future__ import annotations

from pathlib import Path
from decimal import Decimal
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import inspect_ck3_save_player_topology as topology


MELTED = """SAV0100
meta_data={
\tversion="1.19.0.6"
\tmeta_player_tier=3
\tmeta_main_portrait={
\t\tid=20
\t}
\tmeta_number_of_players=1
}
\t\t100={
\t\t\tkey="d_manager"
\t\t\tholder=20
\t\t}
\t\t101={
\t\t\tkey="k_owner"
\t\t\tholder=10
\t\t}
\t\t102={
\t\t\tkey="c_subject"
\t\t\tholder=30
\t\t}
\t20={
\t\tfirst_name="Manager"
\t\talive_data={ }
\t\tlanded_data={
\t\t\tgovernment="celestial_government"
\t\t}
\t}
\t10={
\t\tfirst_name="Owner"
\t\talive_data={ }
\t\tlanded_data={
\t\t\tgovernment="celestial_government"
\t\t}
\t}
\t30={
\t\tfirst_name="Subject"
\t\talive_data={ }
\t\tlanded_data={
\t\t\tgovernment="celestial_government"
\t\t}
\t}
\t\t200={
\t\t\tvassal=20
\t\t\tliege=10
\t\t\tcontract_group="celestial_vassal"
\t\t}
\t\t201={
\t\t\tvassal=30
\t\t\tliege=20
\t\t\tcontract_group="celestial_vassal"
\t\t}
played_character={
\tcharacter=20
\tplayer=1
}
currently_played_characters={
\t20
}
"""


class SaveTopologyTests(unittest.TestCase):
    def test_single_player_manager_topology(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_text(MELTED, encoding="utf-8")
            report = topology.inspect_melted(path)

        self.assertEqual(report["result"], "GREEN")
        self.assertTrue(report["offline_single_player_ready"])
        self.assertEqual(report["celestial_manager_candidate_count"], 1)
        self.assertEqual(
            report["player_manager_candidates"],
            [
                {
                    "contract_id": 200,
                    "player_manager_character_id": 20,
                    "immediate_liege_character_id": 10,
                    "player_primary_title_tier": 3,
                    "player_primary_title_key": "d_manager",
                    "player_government": "celestial_government",
                    "liege_primary_title_tier": 4,
                    "liege_primary_title_key": "k_owner",
                    "liege_government": "celestial_government",
                    "direct_landed_vassal_count": 1,
                    "direct_landed_vassal_character_ids": [30],
                }
            ],
        )

    def test_multiplayer_shape_is_not_single_player_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "melted.ck3"
            path.write_text(
                MELTED.replace("meta_number_of_players=1", "meta_number_of_players=5")
                + "played_character={\n\tcharacter=30\n\tplayer=2\n}\n",
                encoding="utf-8",
            )
            report = topology.inspect_melted(path)

        self.assertFalse(report["offline_single_player_ready"])
        self.assertEqual(report["played_character_records"],
                         [{"character_id": 20, "player_id": 1}, {"character_id": 30, "player_id": 2}])


class NativeSaveStreamTests(unittest.TestCase):
    @staticmethod
    def archive(path: Path, body: bytes, names: tuple[str, ...] = ("gamestate",)) -> None:
        path.write_bytes(b"SAV0102")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
                for name in names:
                    archive.writestr(name, body)

    def test_native_topology_cli_matches_plaintext_without_extracting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            body = MELTED.encode("utf-8")
            plain = root / "source.txt"
            plain.write_bytes(body)
            zipped = root / "native.ck3"
            self.archive(zipped, body)
            plain_out, zip_out = root / "plain.json", root / "zip.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(topology.main(["--melted", str(plain), "--output", str(plain_out)]), 0)
                self.assertEqual(topology.main(["--native-save", str(zipped), "--output", str(zip_out)]), 0)
            p = json.loads(plain_out.read_text(encoding="utf-8"))
            z = json.loads(zip_out.read_text(encoding="utf-8"))
            source = z.pop("source")
            self.assertIsNone(p.pop("source"))
            self.assertEqual(p, z)
            self.assertEqual(source["format"], "native_zip_plaintext")
            self.assertEqual(source["content_sha256"], hashlib.sha256(body).hexdigest())
            self.assertEqual(source["sha256"], hashlib.sha256(zipped.read_bytes()).hexdigest())
            self.assertEqual(source["member"]["name"], "gamestate")
            self.assertEqual(source["content_bytes"], len(body))
            self.assertEqual({x.name for x in root.iterdir()}, {"source.txt", "native.ck3", "plain.json", "zip.json"})
            with self.assertRaisesRegex(ValueError, "cannot use"):
                topology.main(["--native-save", str(zipped), "--keep-melted", str(root / "forbidden.txt")])

    def test_invalid_native_members_encoding_and_crc_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            body = MELTED.encode("utf-8")
            variants = (
                ("missing", ("meta",), body),
                ("extra", ("gamestate", "meta"), body),
                ("duplicate", ("gamestate", "gamestate"), body),
                ("traversal", ("../gamestate",), body),
                ("binary", ("gamestate",), b"binary-not-plaintext"),
                ("utf8", ("gamestate",), body + b"\xff"),
                ("nul", ("gamestate",), body + b"\x00"),
            )
            for name, members, content in variants:
                with self.subTest(name=name):
                    path = root / (name + ".ck3")
                    self.archive(path, content, members)
                    with self.assertRaises((ValueError, UnicodeDecodeError, zipfile.BadZipFile)):
                        topology._save_input_identity(path, native_zip=True)
            for name in ("crc", "encrypted"):
                with self.subTest(name=name):
                    path = root / (name + ".ck3")
                    self.archive(path, body)
                    raw = bytearray(path.read_bytes())
                    central = raw.index(b"PK\x01\x02")
                    if name == "crc":
                        raw[central + 16] ^= 1
                    else:
                        raw[central + 8] |= 1
                    path.write_bytes(raw)
                    with self.assertRaises((ValueError, zipfile.BadZipFile)):
                        topology._save_input_identity(path, native_zip=True)

    def test_container_change_during_member_validation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "changing.ck3"
            self.archive(path, MELTED.encode("utf-8"))
            original = topology._gamestate_member
            def mutate(archive: zipfile.ZipFile) -> zipfile.ZipInfo:
                member = original(archive)
                with path.open("ab") as stream:
                    stream.write(b"changed during validation")
                return member
            with patch.object(topology, "_gamestate_member", side_effect=mutate):
                with self.assertRaisesRegex(ValueError, "changed while validating"):
                    topology._save_input_identity(path, native_zip=True)

    def test_original_twenty_case_health_cli_and_verifier_plain_zip_parity(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        mod_tools = repo / "mod_superman_qiang/tools"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def cli(script: Path, arguments: list[str]) -> None:
                result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(script), *arguments],
                                        capture_output=True, text=True, encoding="utf-8", check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            cli(mod_tools / "prepare_health_fixture.py", ["--output", str(root / "fixture")])
            manifest_bytes = (root / "fixture.fixture.json").read_bytes()
            manifest = json.loads(manifest_bytes)
            self.assertEqual(manifest["case_count"], 20)
            run = root / "run"
            run.mkdir()
            (run / "fixture.json").write_bytes(manifest_bytes)
            spec = importlib.util.spec_from_file_location("synthetic_health_case_data", mod_tools / "health_fixture_data.py")
            self.assertIsNotNone(spec)
            assert spec is not None and spec.loader is not None
            data = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(data)
            data.cases[5]["donor_target"] = "10"
            def q(value: object) -> int:
                return int(Decimal(str(value)) * 100000)
            def variable(name: str, kind: str, identity: int) -> str:
                return f'\t\t\t{{\n\t\t\t\tflag="{name}"\n\t\t\t\ttype={kind}\n\t\t\t\tidentity={identity % (1 << 64)}\n\t\t\t}}\n'
            def body(after: bool) -> bytes:
                text = 'meta_data={\n\tversion="1.21.0"\n\tmeta_player_tier=3\n\tmeta_number_of_players=1\n\tmeta_main_portrait={\n\t\tid=100\n\t}\n}\n'
                # Exercise an actual split UTF-8 codepoint across hash chunks.
                text += '#' + 'x' * (65790 - len(text.encode("utf-8"))) + '\u6d4b\u8bd5\n'
                for index, contract in enumerate(manifest["base_skill_contract"]):
                    original = data.cases[index]
                    for role_index, role in enumerate(("receiver", "donor")):
                        cid = 100 + 2 * index + role_index
                        ledger = q(contract["expected_health_balances"][role_index]) if after else q(original[role + "_initial_balance"])
                        text += f'\t{cid}={{\n\t\tfirst_name="Synthetic_{cid}"\n\t\talive_data={{\n\t\t\thealth=5.00000\n\t\t}}\n\t\tskills={{ 10 10 10 10 10 10 }}\n\t\tvariables={{\n'
                        if cid == 100:
                            for j, row in enumerate(manifest["base_skill_contract"]):
                                for k, name in enumerate(("receiver", "donor")):
                                    text += variable(row[name + "_root_reference"], "char", 100 + 2 * j + k)
                            text += variable("sxat_health_baseline_ready", "value", 100000)
                            if after:
                                text += variable("sxat_health_matrix_done", "value", 100000)
                                for row in manifest["base_skill_contract"]:
                                    text += variable("sxat_case_" + row["case"].replace("-", "_"), "value", 100000)
                        if ledger or (after and contract["case"] == "health-ledger-to-zero"):
                            text += variable("sxad_health_balance", "value", ledger)
                        if after:
                            target = original[role + "_target"]
                            before = 500000 if target is None else q(target)
                            delta = q(contract["expected_health_delta"][role_index])
                            next_day = 500000 + delta if role == "receiver" and contract["receiver_dangerous_fixture_penalty_removed_after_immediate_sampling"] else before + delta
                            for name, value in (("sxat_before_health", before), ("sxat_immediate_after_health", before + delta), ("sxat_after_health", next_day)):
                                text += variable(name, "value", value)
                        text += '\t\t}\n'
                        if ledger:
                            sign = "gain" if ledger > 0 else "loss"
                            scale = format(Decimal(abs(ledger)) / 100000, "f")
                            text += f'\t\tmodifier={{ modifier="sxad_health_{sign}_modifier" scale={scale} }}\n'
                        text += '\t}\n'
                text += 'played_character={\n\tcharacter=100\n\tplayer=1\n}\ncurrently_played_characters={\n\t100\n}\n'
                return text.encode("utf-8")
            reports = {}
            for phase in ("before", "after"):
                plaintext = body(phase == "after")
                savedir = root / (phase + "-source")
                savedir.mkdir()
                (savedir / "melted.ck3").write_bytes(plaintext)
                zipped = root / (phase + ".ck3")
                self.archive(zipped, plaintext)
                for mode in ("plain", "zip"):
                    output = root / (phase + "-" + mode)
                    source_args = ["--save-dir", str(savedir)] if mode == "plain" else ["--native-save", str(zipped)]
                    cli(mod_tools / "inspect_health_save_readback.py", ["--run", str(run), *source_args, "--sdk", str(repo), "--player-id", "100", "--output-dir", str(output)])
                    report = json.loads((output / "health-readback.json").read_text(encoding="utf-8"))
                    self.assertEqual(len(report["root_references"]), 40)
                    self.assertEqual(len(report["characters"]), 40)
                    self.assertEqual([report[k] for k in ("pass_count", "fail_count", "missing_count")], [20, 0, 0] if phase == "after" else [0, 0, 20])
                    self.assertEqual(report["melted_sha256"], hashlib.sha256(plaintext).hexdigest())
                    identity = report.pop("save_input")
                    self.assertEqual(identity["content_bytes"], len(plaintext))
                    self.assertEqual(identity["sha256"], hashlib.sha256((zipped if mode == "zip" else savedir / "melted.ck3").read_bytes()).hexdigest())
                    self.assertFalse(list(output.rglob("melted.ck3")))
                    self.assertFalse(list(output.rglob("gamestate")))
                    reports[phase, mode] = report
                self.assertEqual(reports[phase, "plain"], reports[phase, "zip"])
            gates = []
            for mode in ("plain", "zip"):
                gate = root / (mode + "-gate.json")
                cli(mod_tools / "verify_health_readback.py", ["--before", str(root / ("before-" + mode) / "health-readback.json"), "--after", str(root / ("after-" + mode) / "health-readback.json"), "--fixture", str(run / "fixture.json"), "--output", str(gate)])
                result = json.loads(gate.read_text(encoding="utf-8"))
                self.assertIs(result["ok"], True)
                self.assertEqual(result["case_count"], 20)
                self.assertEqual(result["errors"], [])
                gates.append(result["cases"])
            self.assertEqual(gates[0], gates[1])


if __name__ == "__main__":
    unittest.main()
