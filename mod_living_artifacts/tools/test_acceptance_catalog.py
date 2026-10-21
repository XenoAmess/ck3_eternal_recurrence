"""Exercise the real catalog producer/consumer boundary without game execution."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from living_artifacts_acceptance_model import (
    AcceptanceCatalog, ArtifactSeed, ContentSlot, IndependentAssertion,
    ProductionAction, Requirement, read_catalog,
    verify_catalog_sources,
)

CATALOG = Path(__file__).resolve().parents[1] / "docs/content-acceptance-cells.json"


class CatalogTests(unittest.TestCase):
    def test_actual_catalog_json_roundtrip(self) -> None:
        original = read_catalog(CATALOG)
        value: object = json.loads(json.dumps(original.to_json(), ensure_ascii=False))
        self.assertEqual(AcceptanceCatalog.parse(value), original)
        self.assertEqual(len(original.requirements), 63)
        self.assertEqual(len(original.cells), 63)
        self.assertEqual({cell.status for cell in original.cells}, {"NOT_RUN"})

    def test_top_level_and_status_are_closed(self) -> None:
        source = read_catalog(CATALOG).to_json()
        for field in ("schema", "schema_version", "requirements", "cells"):
            row: dict[str, object] = dict(source)
            row.pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError):
                AcceptanceCatalog.parse(row)
        extra: dict[str, object] = dict(source)
        extra["passed"] = True
        with self.assertRaises(ValueError):
            AcceptanceCatalog.parse(extra)
        changed = deepcopy(source)
        row_cell: dict[str, object] = dict(changed["cells"][0])
        row_cell["status"] = "PASS"
        row_top: dict[str, object] = dict(source)
        row_top["cells"] = [row_cell, *source["cells"][1:]]
        with self.assertRaises(ValueError):
            AcceptanceCatalog.parse(row_top)

    def test_integer_domains_reject_bool_float(self) -> None:
        source = read_catalog(CATALOG).to_json()
        for bad in (True, 1.0):
            row: dict[str, object] = dict(source)
            row["schema_version"] = bad
            with self.subTest(version=bad), self.assertRaises(ValueError):
                AcceptanceCatalog.parse(row)
        actual = next(seed for cell in read_catalog(CATALOG).cells for seed in cell.artifact_seeds)
        for field in ("level", "xp", "resonance"):
            for bad in (True, 1.0):
                row_seed: dict[str, object] = dict(actual.to_json())
                row_seed[field] = bad
                with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                    ArtifactSeed.parse(row_seed)

    def test_slot_registry_and_alias_guards(self) -> None:
        for kind, row in (("affix", {"slot": 1, "id": 13, "rank": 1}),
                          ("curse", {"slot": 3, "id": 1, "rank": 1}),
                          ("affix", {"slot": 1, "id": 1, "rank": 4}),
                          ("affix", {"slot": True, "id": 1, "rank": 1})):
            with self.subTest(row=row), self.assertRaises(ValueError):
                ContentSlot.parse(row, "curse" if kind == "curse" else "affix")
        actual = next(seed for cell in read_catalog(CATALOG).cells for seed in cell.artifact_seeds)
        seed = actual.to_json()
        seed["alias"] = "76561198273714027"
        with self.assertRaises(ValueError):
            ArtifactSeed.parse(seed)
        repeated = actual.to_json()
        repeated["affixes"] = [{"slot": 1, "id": 1, "rank": 1}, {"slot": 2, "id": 1, "rank": 2}]
        with self.assertRaises(ValueError):
            ArtifactSeed.parse(repeated)

    def test_decimal_string_and_null_are_distinct(self) -> None:
        base: dict[str, object] = {"id": "check", "metric": "gold_delta", "expected_decimal": None,
                                  "description": "Identity check", "evidence_required": ["actual_native_state"]}
        self.assertIsNone(IndependentAssertion.parse(base).expected_decimal)
        for good in ("0", "-1.2", "0.25", "1200"):
            self.assertEqual(IndependentAssertion.parse({**base, "expected_decimal": good}).expected_decimal, good)
        for bad in (0, 0.25, True, "-0", "01", "1.0", "1e2", "", "+1"):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                IndependentAssertion.parse({**base, "expected_decimal": bad})

    def test_route_kind_pairs_and_missing_capability(self) -> None:
        base: dict[str, object] = {"id": "action", "kind": "native_feed", "route": "missing",
                                  "description": "No real selector is available", "required_tools": []}
        self.assertEqual(ProductionAction.parse(base).route, "missing")
        for change in ({"route": "existing_mcp"}, {"route": "offline"}, {"kind": "offline_check"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                ProductionAction.parse({**base, **change})
        offline = ProductionAction.parse({**base, "kind": "offline_check", "route": "offline"})
        self.assertEqual(offline.route, "offline")

    def test_requirement_domain_and_reciprocal_references(self) -> None:
        with self.assertRaises(ValueError):
            Requirement.parse({"id": "LW-G01", "domain": "affix", "cell_ids": ["LW-G01"]})
        catalog = read_catalog(CATALOG).to_json()
        catalog["requirements"][0]["cell_ids"] = ["not-an-existing-cell"]
        with self.assertRaises(ValueError):
            AcceptanceCatalog.parse(catalog)

    def test_duplicate_json_keys_rejected(self) -> None:
        raw = CATALOG.read_text(encoding="utf-8")
        raw = raw.replace('"schema_version": 1,', '"schema_version": 1, "schema_version": 1,', 1)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "duplicate.json"
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(ValueError):
                read_catalog(path)

    def test_real_source_bindings_and_changed_hash(self) -> None:
        catalog = read_catalog(CATALOG)
        repository = Path(__file__).resolve().parents[2]
        verify_catalog_sources(catalog, repository)
        first = catalog.cells[0]
        bad_source = replace(first.source_refs[0], sha256="0" * 64)
        bad_cell = replace(first, source_refs=(bad_source, *first.source_refs[1:]))
        bad_catalog = replace(catalog, cells=(bad_cell, *catalog.cells[1:]))
        with self.assertRaises(ValueError):
            verify_catalog_sources(bad_catalog, repository)


if __name__ == "__main__":
    unittest.main()
