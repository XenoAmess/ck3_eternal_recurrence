#!/usr/bin/env python3
"""Static contracts for the AH312-322 / AI323-333 CK3 runtime.

These tests prove generated source semantics only.  They are not CK3, MCP,
fixture-live, production-live, or release evidence.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_361_career_learning_runtime as generator
from zg361_effect_sharding import MAX_EFFECTS_PER_SHARD, top_level_effect_blocks


MOD_ROOT = generator.MOD_ROOT


def read(relative: str) -> str:
    return (MOD_ROOT / relative).read_text(encoding="utf-8-sig")


def read_effect_family(pattern: str) -> str:
    paths = tuple(sorted((MOD_ROOT / "common/scripted_effects").glob(pattern)))
    if not paths:
        raise AssertionError(f"missing effect family: {pattern}")
    return "\n\n".join(path.read_text(encoding="utf-8-sig") for path in paths)


def block(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\{{", text)
    if match is None:
        raise AssertionError(f"missing top-level block {key}")
    opening = text.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise AssertionError(f"unterminated block {key}")


def assert_balanced(test: unittest.TestCase, text: str, label: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for line_number, line in enumerate(text.splitlines(), 1):
        code = line.split("#", 1)[0]
        for char in code:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                test.assertGreaterEqual(depth, 0, f"{label}:{line_number}: extra close")
    test.assertFalse(quoted, f"{label}: unterminated quote")
    test.assertEqual(depth, 0, f"{label}: brace imbalance")


def loc_keys(text: str) -> tuple[str, ...]:
    return tuple(
        match.group(1)
        for match in re.finditer(r'^\s+([^\s:]+):\d+\s+"', text, flags=re.MULTILINE)
    )


class CareerLearningRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read_effect_family(
            "zg361_career_learning_[0-9][0-9][0-9]_*_effects.txt"
        )
        cls.events = read("events/zg361_career_learning_runtime_events.txt")
        cls.career_effects = read_effect_family(
            "zg361_career_hc_[0-9][0-9][0-9]_*_effects.txt"
        )
        cls.case_effects = read_effect_family(
            "zg361_case_kernel_[0-9][0-9][0-9]_*_effects.txt"
        )
        cls.case_triggers = read("common/scripted_triggers/zg361_case_kernel_triggers.txt")
        cls.triggers = read("common/scripted_triggers/zg361_triggers.txt")
        cls.loc_en = read("localization/english/zg361_career_learning_l_english.yml")
        cls.loc_zh = read(
            "localization/simp_chinese/zg361_career_learning_l_simp_chinese.yml"
        )
        cls.spec = read("docs/361-phase2-career-learning-ck3-runtime-spec.md")

    def test_exact_22_id_operation_and_stage_coverage(self) -> None:
        self.assertEqual(generator.EXPECTED_IDS, tuple(range(312, 334)))
        self.assertEqual(len(generator.MECHANISMS), 22)
        self.assertEqual(len({row.operation for row in generator.MECHANISMS}), 22)
        flattened = {
            mechanism_id
            for stages in generator.STAGES.values()
            for ids in stages
            for mechanism_id in ids
        }
        self.assertEqual(flattened, set(range(312, 334)))
        self.assertEqual({row.domain for row in generator.MECHANISMS}, {"ah", "ai"})

    def test_readiness_claim_is_honest(self) -> None:
        self.assertEqual(generator.READINESS, "static-ready")
        self.assertIn("Readiness: `static-ready`", self.spec)
        self.assertIn("MCP evidence: `none`", self.spec)
        self.assertIn("CK3 live evidence: `none`", self.spec)
        boundary = self.spec.split("## 十、后续", 1)[0]
        self.assertNotIn("fixture-live", boundary)
        self.assertNotIn("production-live", boundary)

    def test_outputs_are_current_bom_and_strictly_isolated(self) -> None:
        rendered = generator.outputs()
        self.assertEqual(len(rendered), len(generator.effect_shard_outputs()) + 10)
        for path, payload in rendered.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), payload)
                self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))
                relative = path.relative_to(MOD_ROOT).as_posix()
                self.assertTrue(
                    relative == "events/zg361_career_learning_runtime_events.txt"
                    or relative.startswith("common/scripted_effects/zg361_career_learning_")
                    and relative.endswith("_effects.txt")
                    or relative.startswith("localization/")
                    and "zg361_career_learning_l_" in relative
                )
        for relative in (
            "tools/gen_361_career_learning_runtime.py",
            "tools/test_zg361_career_learning_runtime.py",
            "tools/zg361_career_learning_semantic_model.py",
            "tools/test_zg361_career_learning_semantic_model.py",
            "docs/361-phase2-career-learning-ck3-runtime-spec.md",
        ):
            self.assertTrue((MOD_ROOT / relative).read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_effects_are_purpose_sharded_with_exact_ordered_bodies(self) -> None:
        paths = tuple(generator.effect_shard_outputs())
        self.assertFalse(generator.LEGACY_EFFECTS_PATH.exists())
        actual: list[tuple[str, str]] = []
        for path in paths:
            blocks = top_level_effect_blocks(path.read_bytes(), generated_header=generator.HEADER)
            with self.subTest(path=path.name):
                self.assertGreaterEqual(len(blocks), 1)
                self.assertLessEqual(len(blocks), MAX_EFFECTS_PER_SHARD)
            actual.extend(blocks)
        expected = top_level_effect_blocks(generator.render_effects(), generated_header=generator.HEADER)
        self.assertEqual(tuple(actual), expected)

    def test_ck3_blocks_are_balanced_and_top_level_unique(self) -> None:
        for text, label in ((self.effects, "effects"), (self.events, "events")):
            assert_balanced(self, text, label)
            keys = re.findall(r"(?m)^([A-Za-z0-9_.]+)\s*=\s*\{", text)
            duplicates = sorted({key for key in keys if keys.count(key) > 1})
            self.assertEqual(duplicates, [], label)

    def test_every_mechanism_has_real_write_consumer_and_six_field_receipt(self) -> None:
        for row in generator.MECHANISMS:
            with self.subTest(mechanism=row.mechanism_id):
                core = block(self.effects, f"zg361_cl_m{row.mechanism_id:03d}_core_effect")
                consumer = block(
                    self.effects, f"zg361_cl_m{row.mechanism_id:03d}_consume_effect"
                )
                manager = block(
                    self.effects,
                    f"zg361_cl_m{row.mechanism_id:03d}_manager_apply_effect",
                )
                self.assertEqual(core.count("zg361_case_kernel_record_operation_effect"), 1)
                for suffix in ("owner", "subject", "cycle", "case", "state", "choice"):
                    self.assertIn(
                        f"zg361_cl_m{row.mechanism_id:03d}_receipt_{suffix}", core
                    )
                self.assertIn("zg361_case_kernel_full_guard_trigger", core)
                self.assertIn(
                    f"zg361_cl_m{row.mechanism_id:03d}_consume_effect = yes", core
                )
                self.assertIn(row.consumer, consumer)
                self.assertIn("set_variable", consumer)
                self.assertIn(
                    f"zg361_cl_m{row.mechanism_id:03d}_core_effect", manager
                )
                self.assertIn(row.operation, self.effects)

    def test_duplicate_and_stale_paths_precede_all_domain_mutation(self) -> None:
        for row in generator.MECHANISMS:
            source = block(self.effects, f"zg361_cl_m{row.mechanism_id:03d}_core_effect")
            with self.subTest(mechanism=row.mechanism_id):
                record_at = source.index("zg361_case_kernel_record_operation_effect")
                self.assertLess(source.index(f"CODE = 3 MECHANISM = {row.mechanism_id}"), record_at)
                self.assertLess(source.index(f"CODE = 2 MECHANISM = {row.mechanism_id}"), record_at)
                prefix = source[:record_at]
                self.assertNotIn(
                    f"set_variable = {{ name = zg361_cl_m{row.mechanism_id:03d}_route",
                    prefix,
                )
                self.assertNotIn("remove_treasury", prefix)
                self.assertNotIn("add_gold = { value = 0 subtract", prefix)

    def test_all_callers_use_a_frozen_five_field_ticket(self) -> None:
        ticket_fields = ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE")
        for row in generator.MECHANISMS:
            core = block(self.effects, f"zg361_cl_m{row.mechanism_id:03d}_core_effect")
            manager = block(
                self.effects,
                f"zg361_cl_m{row.mechanism_id:03d}_manager_apply_effect",
            )
            for field in ticket_fields:
                self.assertIn(f"EXPECTED_{field} = $TICKET_{field}$", core)
                self.assertIn(f"TICKET_{field} = $TICKET_{field}$", manager)

        for domain, stages in generator.STAGES.items():
            for state in range(1, len(stages) + 1):
                runner = block(
                    self.effects, f"zg361_cl_run_{domain}_stage_{state:02d}_effect"
                )
                transition_at = runner.index(
                    f"zg361_case_{domain}_advance_{state:02d}_effect"
                )
                transition = runner[transition_at:]
                for field in ("OWNER", "SUBJECT", "CYCLE", "CASE"):
                    self.assertIn(f"TICKET_{field} = $TICKET_{field}$", transition)
                for field in ticket_fields:
                    self.assertIn(f"EXPECTED_{field} = $TICKET_{field}$", runner)

                event_id = 100 + state - 1 if domain == "ah" else 200 + state - 1
                event = block(self.events, f"zg361cl.{event_id}")
                prefix = f"zg361_cl_{domain}_s{state:02d}_deadline_"
                for field in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"TICKET_{field.upper()} = var:{prefix}{field}", event)

    def test_case_kernel_five_field_guards_and_deadline_identity_are_reused(self) -> None:
        self.assertIn("zg361_case_kernel_full_guard_trigger", self.case_triggers)
        self.assertIn("trigger_else = { always = no }", self.case_triggers)
        for domain, stages in generator.STAGES.items():
            for state in range(1, len(stages) + 1):
                with self.subTest(domain=domain, state=state):
                    schedule = block(
                        self.effects,
                        f"zg361_cl_schedule_{domain}_stage_{state:02d}_effect",
                    )
                    self.assertIn("zg361_case_kernel_schedule_deadline_effect", schedule)
                    for token in (
                        "DEADLINE_OWNER_VAR",
                        "DEADLINE_SUBJECT_VAR",
                        "DEADLINE_CYCLE_VAR",
                        "DEADLINE_CASE_VAR",
                        "DEADLINE_STATE_VAR",
                    ):
                        self.assertIn(token, schedule)
                    event_id = 100 + state - 1 if domain == "ah" else 200 + state - 1
                    event = block(self.events, f"zg361cl.{event_id}")
                    self.assertIn("zg361_case_kernel_expire_deadline_effect", event)
                    self.assertIn("stale", event)

    def test_deadline_rechecks_live_authority_before_any_receipt(self) -> None:
        for row in generator.MECHANISMS:
            core = block(self.effects, f"zg361_cl_m{row.mechanism_id:03d}_core_effect")
            record_at = core.index("zg361_case_kernel_record_operation_effect")
            permission = core[:record_at]
            self.assertIn("zg361_is_celestial_liege_trigger = yes", permission)
            self.assertIn("zg361_is_reviewable_vassal_trigger = yes", permission)
            self.assertIn(f"liege = var:zg361_case_{row.domain}_owner", permission)
            self.assertLess(permission.index("CODE = 1"), len(permission))

        # Prewritten receipts are a fast path: the stage runner must still gate
        # them before its first receipt check and before transition.
        for domain, stages in generator.STAGES.items():
            for state in range(1, len(stages) + 1):
                runner = block(
                    self.effects, f"zg361_cl_run_{domain}_stage_{state:02d}_effect"
                )
                guard_at = runner.index("zg361_case_kernel_full_guard_trigger")
                permission_at = runner.index("zg361_is_celestial_liege_trigger = yes")
                receipt_at = runner.index("zg361_case_kernel_receipt_is_current_trigger")
                transition_at = runner.index(
                    f"zg361_case_{domain}_advance_{state:02d}_effect"
                )
                self.assertLess(guard_at, permission_at)
                self.assertLess(permission_at, receipt_at)
                self.assertLess(receipt_at, transition_at)
                self.assertIn("zg361_is_reviewable_vassal_trigger = yes", runner)
                self.assertIn(f"liege = var:zg361_case_{domain}_owner", runner)
                self.assertIn("CODE = 1", runner[:receipt_at])
                self.assertIn(
                    f"zg361_cl_schedule_{domain}_stage_{state:02d}_effect = yes",
                    runner[:receipt_at],
                )

    def test_shared_domain_transitions_match_authoritative_state_machines(self) -> None:
        for domain, stages in generator.STAGES.items():
            for state, ids in enumerate(stages, 1):
                transition = f"zg361_case_{domain}_advance_{state:02d}_effect"
                with self.subTest(domain=domain, state=state):
                    self.assertIn(f"{transition} = {{", self.case_effects)
                    runner = block(
                        self.effects, f"zg361_cl_run_{domain}_stage_{state:02d}_effect"
                    )
                    self.assertEqual(runner.count(f"{transition} ="), 1)
                    for mechanism_id in ids:
                        self.assertIn(
                            f"zg361_cl_m{mechanism_id:03d}_core_effect", runner
                        )
                    self.assertIn(
                        f"zg361_cl_schedule_{domain}_stage_{state:02d}_effect = yes",
                        runner,
                    )
                    self.assertGreaterEqual(
                        runner.count(
                            f"zg361_cl_schedule_{domain}_stage_{state:02d}_effect = yes"
                        ),
                        2,
                    )
                    transition_at = runner.index(f"{transition} =")
                    self.assertIn(
                        "limit = { var:zg361_case_kernel_applied = 1 }",
                        runner[transition_at:],
                    )

    def test_subject_responses_reset_per_case_and_choice_is_frozen_from_command(self) -> None:
        for domain in ("ah", "ai"):
            opened = block(self.effects, f"zg361_cl_open_{domain}_case_effect")
            expected = {
                mechanism_id
                for mechanism_id in generator.SUBJECT_RESPONSE_IDS
                if next(
                    row
                    for row in generator.MECHANISMS
                    if row.mechanism_id == mechanism_id
                ).domain
                == domain
            }
            for mechanism_id in expected:
                self.assertIn(
                    f"remove_variable = zg361_cl_m{mechanism_id:03d}_subject_response",
                    opened,
                )
        for row in generator.MECHANISMS:
            core = block(self.effects, f"zg361_cl_m{row.mechanism_id:03d}_core_effect")
            record_at = core.index("zg361_case_kernel_record_operation_effect")
            receipt_fragment = core[record_at : core.index("OPERATION_ID", record_at)]
            self.assertIn("CHOICE = scope:zg361_cl_route", receipt_fragment)

    def test_portfolio_adapter_is_manager_scope_and_one_digest_per_cycle(self) -> None:
        dispatcher = block(self.effects, "zg361_cl_dispatch_direct_reports_effect")
        queue = block(self.effects, "zg361_cl_queue_owner_digest_effect")
        digest = block(self.events, "zg361cl.390")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", dispatcher)
        self.assertIn("every_vassal", dispatcher)
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", dispatcher)
        self.assertIn("zg361_cl_portfolio_ah_expected", dispatcher)
        self.assertIn("zg361_cl_portfolio_ai_expected", dispatcher)
        self.assertNotIn("zg361_cl_portfolio_expected", dispatcher)
        self.assertGreater(
            dispatcher.index("zg361_cl_open_ah_applied = 1"),
            dispatcher.index("zg361_cl_open_ah_case_effect = yes"),
        )
        self.assertGreater(
            dispatcher.index("zg361_cl_open_ai_applied = 1"),
            dispatcher.index("zg361_cl_open_ai_case_effect = yes"),
        )
        self.assertNotIn("is_ai = no", dispatcher)
        self.assertIn("zg361_cl_portfolio_ah_completed", queue)
        self.assertIn("zg361_cl_portfolio_ai_completed", queue)
        self.assertIn("zg361_cl_portfolio_ah_expected", queue)
        self.assertIn("zg361_cl_portfolio_ai_expected", queue)
        self.assertIn("value = $CASE_CYCLE$", queue)
        self.assertIn("var:zg361_cl_portfolio_cycle = scope:zg361_cl_completion_cycle", queue)
        self.assertIn("zg361_cl_portfolio_digest_shown = 0", queue)
        self.assertIn("zg361_cl_portfolio_digest_shown value = 1", queue)
        self.assertIn("var:$OWNER_VAR$", queue)
        self.assertIn("OWNER_VAR = zg361_case_ah_owner", self.effects)
        self.assertIn("OWNER_VAR = zg361_case_ai_owner", self.effects)
        self.assertEqual(self.effects.count("trigger_event = { id = zg361cl.390"), 1)
        self.assertIn("trigger = { is_ai = no }", digest)
        self.assertIn("eligible AI career/learning portfolio advanced silently", queue)

    def test_six_subject_prompts_and_one_batched_digest_are_visible(self) -> None:
        hidden_expected = sum(len(stages) for stages in generator.STAGES.values()) + len(
            generator.MECHANISMS
        )
        self.assertEqual(self.events.count("hidden = yes"), hidden_expected)
        event_ids = re.findall(r"(?m)^(zg361cl\.\d+)\s*=\s*\{", self.events)
        self.assertEqual(
            len(event_ids), hidden_expected + len(generator.SUBJECT_RESPONSE_IDS) + 1
        )
        self.assertEqual(event_ids.count("zg361cl.390"), 1)
        self.assertEqual(self.events.count("title = "), len(generator.SUBJECT_RESPONSE_IDS) + 1)
        for mechanism_id in generator.SUBJECT_RESPONSE_IDS:
            event = block(self.events, f"zg361cl.{mechanism_id}")
            self.assertIn("is_ai = no", event)
            self.assertIn("zg361_case_kernel_full_guard_trigger", event)
            self.assertNotIn("zg361_is_celestial_liege_trigger", event)
            self.assertIn(
                f"zg361_cl_m{mechanism_id:03d}_subject_response_effect", event
            )
            self.assertEqual(event.count("ROUTE = 1"), 1)
            self.assertEqual(event.count("ROUTE = 2"), 1)
        self.assertIn("Twenty-two popups did not line up", self.loc_en)
        self.assertIn("没有二十二封弹窗排队敲门", self.loc_zh)

    def test_dual_payer_set_is_exact_atomic_and_real(self) -> None:
        self.assertEqual(set(generator.DUAL_COSTS), {314, 321, 323, 326, 330, 333})
        for mechanism_id, (treasury, manager, routes) in generator.DUAL_COSTS.items():
            row = next(row for row in generator.MECHANISMS if row.mechanism_id == mechanism_id)
            source = block(self.effects, f"zg361_cl_m{mechanism_id:03d}_core_effect")
            with self.subTest(mechanism=mechanism_id):
                self.assertEqual(source.count("zg361_case_kernel_reserve_transaction_effect"), 2)
                self.assertEqual(source.count("zg361_case_kernel_settle_transaction_effect"), 2)
                self.assertEqual(source.count("zg361_case_kernel_refund_transaction_effect"), 4)
                self.assertIn(f"treasury >= {treasury}", source)
                self.assertIn(f"gold >= {manager}", source)
                self.assertIn(f"remove_treasury = {treasury}", source)
                self.assertIn(
                    f"add_gold = {{ value = 0 subtract = {manager} }}", source
                )
                self.assertIn("dual_payment_settled value = 1", source)
                for route in routes:
                    self.assertIn(f"scope:zg361_cl_route = {route}", source)
                self.assertIn("CODE = 5", source)
                self.assertEqual(row.domain in {"ah", "ai"}, True)
                reserve_at = source.index("zg361_case_kernel_reserve_transaction_effect")
                settle_at = source.rindex("zg361_case_kernel_settle_transaction_effect")
                record_at = source.index("zg361_case_kernel_record_operation_effect")
                debit_at = source.index(f"remove_treasury = {treasury}")
                consumer_at = source.index(
                    f"zg361_cl_m{mechanism_id:03d}_consume_effect = yes"
                )
                self.assertLess(reserve_at, settle_at)
                self.assertLess(settle_at, record_at)
                self.assertLess(record_at, debit_at)
                self.assertLess(debit_at, consumer_at)
                self.assertNotIn("remove_treasury", source[:record_at])
                failure_tail = source[record_at:]
                self.assertGreaterEqual(
                    failure_tail.count("zg361_case_kernel_refund_transaction_effect"),
                    2,
                )

    def test_declining_relocation_and_contact_never_charge(self) -> None:
        for mechanism_id in (314, 321):
            _treasury, _manager, charged_routes = generator.DUAL_COSTS[mechanism_id]
            self.assertEqual(charged_routes, frozenset({1}))
            charged = generator.charged_route_trigger(charged_routes)
            self.assertIn("scope:zg361_cl_route = 1", charged)
            self.assertNotIn("scope:zg361_cl_route = 2", charged)
        relocation = block(self.effects, "zg361_cl_m314_consume_effect")
        self.assertIn("performance_delta value = 0", relocation)
        self.assertIn("declined value = 1", relocation)

    def test_assessed_subject_responses_do_not_grant_manager_authority(self) -> None:
        found = {
            int(value)
            for value in re.findall(
                r"(?m)^zg361_cl_m(\d{3})_subject_response_effect = \{", self.effects
            )
        }
        self.assertEqual(found, set(generator.SUBJECT_RESPONSE_IDS))
        for mechanism_id in found:
            source = block(
                self.effects, f"zg361_cl_m{mechanism_id:03d}_subject_response_effect"
            )
            self.assertIn("zg361_case_kernel_subject_self_guard_trigger", source)
            self.assertIn("is_ai = no", source)
            self.assertIn("answered", source)
            self.assertNotIn("zg361_is_celestial_liege_trigger", source)
            self.assertNotIn("_open_", source)
            self.assertNotIn("_advance_", source)
            self.assertNotIn("_core_effect", source)

    def test_only_six_legal_response_variables_are_read_and_really_produced(self) -> None:
        reads = {
            int(value)
            for value in re.findall(
                r"has_variable = zg361_cl_m(\d{3})_subject_response", self.effects
            )
        }
        self.assertEqual(reads, set(generator.SUBJECT_RESPONSE_IDS))
        self.assertFalse(reads & (set(generator.EXPECTED_IDS) - set(generator.SUBJECT_RESPONSE_IDS)))
        for mechanism_id in generator.SUBJECT_RESPONSE_IDS:
            event = block(self.events, f"zg361cl.{mechanism_id}")
            response = block(
                self.effects, f"zg361_cl_m{mechanism_id:03d}_subject_response_effect"
            )
            self.assertIn("remove_variable = zg361_cl_subject_response_applied", response)
            self.assertIn("zg361_cl_subject_response_applied value = 1", response)
            self.assertEqual(
                event.count(f"zg361_cl_m{mechanism_id:03d}_subject_response_effect"),
                2,
            )
            other_events = self.events.replace(event, "")
            self.assertNotIn(
                f"zg361_cl_m{mechanism_id:03d}_subject_response_effect", other_events
            )

    def test_player_subject_prompts_are_serial_and_ai_uses_background_default(self) -> None:
        stage2 = block(self.effects, "zg361_cl_run_ah_stage_02_effect")
        self.assertIn("zg361_cl_prompt_gate value = 0", stage2)
        for mechanism_id in (314, 315, 318):
            self.assertIn(f"zg361_cl_m{mechanism_id:03d}_prompt_pending", stage2)
            self.assertIn(f"trigger_event = {{ id = zg361cl.{mechanism_id} days = 1 }}", stage2)
        self.assertLess(
            stage2.index("id = zg361cl.314"),
            stage2.index("id = zg361cl.315"),
        )
        self.assertLess(
            stage2.index("id = zg361cl.315"),
            stage2.index("id = zg361cl.318"),
        )
        self.assertGreaterEqual(stage2.count("limit = { is_ai = yes }"), 3)
        for mechanism_id in generator.SUBJECT_RESPONSE_IDS:
            event = block(self.events, f"zg361cl.{mechanism_id}")
            for suffix in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"var:zg361_cl_m{mechanism_id:03d}_prompt_{suffix}", event)
            self.assertIn("var:zg361_cl_subject_response_applied = 1", event)

    def test_real_internal_transfer_reuses_career_hc_vacancy_and_native_settlement(self) -> None:
        expected_calls = {
            312: "zg361_career_hc_claim_cl_transfer_vacancy_effect",
            314: "zg361_career_hc_accept_cl_transfer_effect",
            315: "zg361_career_hc_start_cl_transfer_trial_effect",
            319: "zg361_career_hc_authorize_cl_transfer_release_effect",
        }
        for mechanism_id, call in expected_calls.items():
            core = block(self.effects, f"zg361_cl_m{mechanism_id:03d}_core_effect")
            self.assertIn(call, core)
            self.assertIn("zg361_transfer_cl_applied", core)
            self.assertIn("zg361_cl_route value = 3", core)
            self.assertIn(f"CODE = 6 MECHANISM = {mechanism_id}", core)

        claim = block(
            self.career_effects,
            "zg361_career_hc_claim_cl_transfer_vacancy_effect",
        )
        for token in (
            "zg361_transfer_vacancy_status = 1",
            "zg361_transfer_vacancy_maturity_cycle <= $TICKET_CYCLE$",
            "zg361_transfer_hc_reserved = 1",
            "zg361_transfer_hc_conserved = 1",
            "zg361_transfer_consumer_kind value = 2",
        ):
            self.assertIn(token, claim)
        self.assertNotIn("zg361_pp_", claim)

        settle = block(
            self.career_effects,
            "zg361_career_hc_settle_cl_transfer_effect",
        )
        for mechanism_id in (312, 314, 315, 319):
            self.assertIn(f"zg361_cl_m{mechanism_id:03d}_receipt_owner", settle)
            self.assertIn(f"zg361_cl_m{mechanism_id:03d}_receipt_choice = 1", settle)
        create_at = settle.index("create_title_and_vassal_change")
        change_at = settle.index("change_liege", create_at)
        resolve_at = settle.index("resolve_title_and_vassal_change", change_at)
        post_at = settle.index("liege = scope:zg361_transfer_cl_settle_receiver", resolve_at)
        self.assertLess(create_at, change_at)
        self.assertLess(change_at, resolve_at)
        self.assertLess(resolve_at, post_at)
        self.assertIn("zg361_transfer_hc_settled add = 1", settle)
        self.assertIn("zg361_career_hc_reclaim_transfer_hc_effect = yes", settle)
        self.assertNotIn("zg361_pp_", settle)

        resolver = block(self.effects, "zg361_cl_m319_resolve_obligation_effect")
        self.assertIn("zg361_career_hc_settle_cl_transfer_effect = yes", resolver)
        self.assertIn("zg361_cl_m312_hire_once_effect = yes", resolver)
        self.assertIn("mobility_settlement_failed", resolver)
        hire = block(self.effects, "zg361_cl_m312_hire_once_effect")
        self.assertIn("EXPECTED_OWNER = var:zg361_cl_m312_object_owner", hire)
        self.assertIn("zg361_transfer_vacancy_status = 3", hire)
        # AH and AI cases are parallel; a real #319 move cannot strand the
        # still-frozen AI stages under their former direct-liege check.
        ai_after_move = block(self.effects, "zg361_cl_m333_core_effect")
        self.assertIn("zg361_transfer_consumer_kind = 2", ai_after_move)
        self.assertIn("zg361_transfer_vacancy_status = 3", ai_after_move)
        self.assertIn("liege = var:zg361_transfer_cl_receiver", ai_after_move)

    def test_count_barons_are_reviewable_but_cannot_manage(self) -> None:
        celestial = block(self.triggers, "zg361_is_celestial_liege_trigger")
        reviewable = block(self.triggers, "zg361_is_reviewable_vassal_trigger")
        self.assertIn("highest_held_title_tier >= tier_duchy", celestial)
        self.assertIn("liege = { zg361_is_celestial_liege_trigger = yes }", reviewable)
        self.assertNotIn("highest_held_title_tier >= tier_duchy", reviewable)
        for row in generator.MECHANISMS:
            manager = block(
                self.effects,
                f"zg361_cl_m{row.mechanism_id:03d}_manager_apply_effect",
            )
            core = block(self.effects, f"zg361_cl_m{row.mechanism_id:03d}_core_effect")
            self.assertIn("zg361_is_celestial_liege_trigger = yes", core)
            self.assertIn("zg361_is_reviewable_vassal_trigger = yes", core)
            self.assertNotIn("is_ai = no", manager)

    def test_real_crisis_and_actual_redundancy_facts_are_required(self) -> None:
        crisis = block(self.effects, "zg361_cl_m331_core_effect")
        stage4 = block(self.effects, "zg361_cl_run_ai_stage_04_effect")
        self.assertIn("is_at_war = yes", crisis)
        self.assertNotIn("\n                    at_war = yes", crisis)
        self.assertIn("ROUTE = 3", stage4)
        self.assertIn("No CK3 war fact", stage4)
        self.assertIn("is_at_war = yes", stage4)

        exemption = block(self.effects, "zg361_cl_m333_layoff_exemption_effect")
        for fact in (
            "has_variable = zg361_b2_m074_actual_exit",
            "var:zg361_b2_m074_actual_exit = 1",
            "var:zg361_b2_m074_reason = 1",
            "var:zg361_b2_m074_subject = this",
            "var:zg361_b2_m074_treasury_paid = 50",
            "var:zg361_b2_m074_personal_received = 50",
            "var:zg361_b2_m074_hc_released = 1",
            "var:zg361_b2_m074_state = 3",
            "var:zg361_b2_m074_state = 4",
        ):
            self.assertIn(fact, exemption)
        stage5 = block(self.effects, "zg361_cl_run_ai_stage_05_effect")
        resolver = block(self.effects, "zg361_cl_m333_resolve_obligation_effect")
        event = block(self.events, f"zg361cl.{generator.obligation_event_id(333)}")
        exemption_at = resolver.index("zg361_cl_m333_layoff_exemption_effect = yes")
        recovery_at = resolver.index("zg361_cl_m333_recover_outstanding_effect = yes")
        self.assertLess(exemption_at, recovery_at)
        self.assertNotIn("zg361_cl_m333_recover_outstanding_effect = yes", stage5)
        self.assertIn("zg361_case_ai_advance_05_effect", stage5)
        self.assertIn("zg361_cl_m333_resolve_obligation_effect = yes", event)

    def test_internal_market_semantics_are_not_generic_reskins(self) -> None:
        assertions = {
            312: ("legal_hc", "vacancy_hire_limit value = 1", "market_trust_delta value = -2"),
            313: ("pip_link_frozen", "whitewash_audit", "anti_retaliation_audit"),
            314: ("lump_sum value = 10", "temporary_allowance value = 6", "family_support value = 4"),
            315: ("trial_days value = 90", "credit_sum value = 100", "failed_is_low_grade value = 0"),
            316: ("professional_base value = 30", "historical_payments_immutable", "step_3 value = 35"),
            317: ("acl_stage", "access_log_rows", "rating_changed_without_evidence"),
            318: ("formal_limit value = 2", "withdrawal_still_consumes", "manager_timeout_refunds"),
            319: ("counteroffer_limit value = 1", "release_deadline_days value = 30", "promise_pending value = 1"),
            320: ("minimum_same_issue_sample value = 2", "anonymous_identity_hidden", "original_reason_preserved"),
            321: ("consent", "maintenance_once_per_cycle", "humiliation_history_immutable"),
            322: ("old_case_links value = 2", "active_flow_limit value = 1", "history_wipe_blocked"),
        }
        for mechanism_id, needles in assertions.items():
            source = block(self.effects, f"zg361_cl_m{mechanism_id:03d}_consume_effect")
            for needle in needles:
                self.assertIn(needle, source, f"{mechanism_id}: {needle}")

    def test_learning_semantics_are_not_generic_reskins(self) -> None:
        assertions = {
            323: ("protected_hours_pool value = 20", "completion_performance_credit value = 0", "hours_conserved"),
            324: ("outcome_requires_application", "observed_delta value = 12", "performance_credit value = 0"),
            325: ("practical_threshold value = 60", "training_owner_audit", "automatic_low_grade value = 0"),
            326: ("delivery_opportunity_cost value = 4", "attrition_risk value = 1", "adopted_value value = 0"),
            327: ("teaching_hours value = 8", "share_sum value = 100", "performance_credit value = 6"),
            328: ("maintainers value = 1", "capacity_conserved", "cross_team_impact"),
            329: ("active_mentor_count value = 1", "rematch_limit value = 1", "deadline_after value = 190"),
            330: ("role_identity_conserved", "failed_is_low_grade value = 0", "fairness_debt value = 1"),
            331: ("protected_hours value = 10", "delivery_hours value = 94", "repaid_hours value = 0"),
            332: ("safe_simulation value = 1", "real_incident value = 0", "development_gap value = 1"),
            333: ("monthly_reduction value = 2", "recovery_cap value = 24", "outstanding value = 18"),
        }
        for mechanism_id, needles in assertions.items():
            source = block(self.effects, f"zg361_cl_m{mechanism_id:03d}_consume_effect")
            for needle in needles:
                self.assertIn(needle, source, f"{mechanism_id}: {needle}")

    def test_high_cost_training_recovery_is_capped_split_and_once_only(self) -> None:
        consumer = block(self.effects, "zg361_cl_m333_consume_effect")
        recovery = block(self.effects, "zg361_cl_m333_recover_outstanding_effect")
        exemption = block(self.effects, "zg361_cl_m333_layoff_exemption_effect")
        self.assertIn("training_cost value = 24", consumer)
        self.assertIn("outstanding value = 18", consumer)
        self.assertIn("application_evidence value = 0", consumer)
        self.assertIn("recovery_settled = 0", recovery)
        self.assertIn("gold >= 18", recovery)
        self.assertIn("subtract = 18", recovery)
        self.assertIn("add_treasury = 13", recovery)
        self.assertIn("add_gold = 5", recovery)
        self.assertIn("recovered value = 18", recovery)
        self.assertIn("organization_layoff_exempt value = 1", exemption)
        self.assertIn("outstanding value = 0", exemption)
        resolver = block(self.effects, "zg361_cl_m333_resolve_obligation_effect")
        event = block(self.events, f"zg361cl.{generator.obligation_event_id(333)}")
        self.assertLess(
            resolver.index("zg361_cl_m333_recover_outstanding_effect = yes"),
            resolver.index("var:zg361_cl_m333_recovery_settled = 1"),
        )
        self.assertIn("days = 30", resolver)
        self.assertIn("zg361_cl_m333_resolve_obligation_effect = yes", event)

    def test_all_22_receipts_own_typed_objects_and_named_consumers(self) -> None:
        self.assertEqual(set(generator.OBJECT_KINDS), set(range(312, 334)))
        self.assertEqual(len(set(generator.OBJECT_KINDS.values())), 22)
        for row in generator.MECHANISMS:
            mechanism_id = row.mechanism_id
            p = f"zg361_cl_m{mechanism_id:03d}"
            with self.subTest(mechanism_id=mechanism_id):
                core = block(self.effects, f"{p}_core_effect")
                consumer = block(self.effects, f"{p}_consume_effect")
                record_at = core.index("zg361_case_kernel_record_operation_effect")
                object_at = core.index(f"{p}_object_kind_id", record_at)
                schedule_at = core.index(f"{p}_obligation_pending value = 1", object_at)
                consumer_at = core.index(f"{p}_consume_effect = yes", schedule_at)
                self.assertLess(record_at, object_at)
                self.assertLess(object_at, schedule_at)
                self.assertLess(schedule_at, consumer_at)
                for suffix in (
                    "object_owner",
                    "object_subject",
                    "object_cycle",
                    "object_case",
                    "object_route",
                    "object_revision",
                    "relation_manager",
                    "relation_official",
                    "acl_class",
                ):
                    self.assertIn(f"{p}_{suffix}", core)
                self.assertIn(f"{p}_object_active value = 1", core)
                self.assertIn(f"{p}_debt_active value = 1", core)
                self.assertIn(f"{p}_object_consumer_revision", consumer)
                self.assertIn(row.consumer, consumer)

    def test_typed_role_offer_mentor_and_succession_relations_are_projected(self) -> None:
        expected_relations = {
            312: ("reporting_manager", "vacancy_candidate"),
            314: ("target_manager", "offered_official"),
            315: ("trial_target_manager", "trial_official"),
            319: ("releasing_manager", "released_official"),
            323: ("budget_owner", "learner"),
            324: ("learning_owner", "learner"),
            327: ("application_owner", "teacher"),
            330: ("target_role_owner", "affected_official"),
            332: ("incumbent", "successor_candidate"),
            333: ("contract_owner", "bound_official"),
        }
        for mechanism_id, suffixes in expected_relations.items():
            core = block(self.effects, f"zg361_cl_m{mechanism_id:03d}_core_effect")
            for suffix in suffixes:
                self.assertIn(f"zg361_cl_m{mechanism_id:03d}_{suffix}", core)

        mentor = block(self.effects, "zg361_cl_m329_core_effect")
        self.assertIn("random_vassal", mentor)
        self.assertIn("NOT = { this = scope:zg361_cl_mentor_subject }", mentor)
        self.assertIn("zg361_cl_m329_mentor_distinct value = 1", mentor)
        self.assertIn("zg361_cl_m329_mentor_missing value = 1", mentor)
        mentor_consumer = block(self.effects, "zg361_cl_m329_consume_effect")
        self.assertIn("var:zg361_cl_m329_mentor_distinct = 0", mentor_consumer)
        self.assertIn("zg361_cl_m329_match_failed value = 1", mentor_consumer)

    def test_business_obligations_are_frozen_scheduled_and_single_use(self) -> None:
        self.assertEqual(set(generator.OBLIGATION_DAYS), set(range(312, 334)))
        for row in generator.MECHANISMS:
            mechanism_id = row.mechanism_id
            p = f"zg361_cl_m{mechanism_id:03d}"
            with self.subTest(mechanism_id=mechanism_id):
                core = block(self.effects, f"{p}_core_effect")
                resolver = block(self.effects, f"{p}_resolve_obligation_effect")
                event_id = generator.obligation_event_id(mechanism_id)
                event = block(self.events, f"zg361cl.{event_id}")
                self.assertIn(f"{p}_resolve_obligation_effect = yes", event)
                for route, days in generator.OBLIGATION_DAYS[mechanism_id].items():
                    self.assertIn(f"scope:zg361_cl_route = {route}", core)
                    self.assertIn(
                        f"trigger_event = {{ id = zg361cl.{event_id} days = {days} }}",
                        core,
                    )
                for suffix in (
                    "obligation_owner",
                    "obligation_subject",
                    "obligation_cycle",
                    "obligation_case",
                    "obligation_route",
                ):
                    self.assertIn(f"{p}_{suffix}", core)
                duplicate_at = resolver.index(f"CODE = 3 MECHANISM = {mechanism_id}")
                stale_at = resolver.index(f"CODE = 2 MECHANISM = {mechanism_id}")
                permission_at = resolver.index(f"CODE = 1 MECHANISM = {mechanism_id}")
                finalize_at = resolver.index(f"{p}_obligation_resolved value = 1")
                self.assertLess(duplicate_at, stale_at)
                self.assertLess(stale_at, permission_at)
                self.assertLess(permission_at, finalize_at)
                self.assertIn(f"var:{p}_object_subject = this", resolver)
                self.assertIn(f"var:{p}_object_owner = var:{p}_receipt_owner", resolver)
                self.assertIn(f"var:{p}_object_cycle = var:{p}_receipt_cycle", resolver)
                self.assertIn(f"var:{p}_object_case = var:{p}_receipt_case", resolver)
                self.assertIn("zg361_is_celestial_liege_trigger = yes", resolver)
                self.assertIn(f"{p}_obligation_orphaned value = 1", resolver)
                self.assertIn(f"{p}_object_state value = 4", resolver)

    def test_unresolved_object_blocks_overwrite_before_receipt_or_payment(self) -> None:
        for row in generator.MECHANISMS:
            mechanism_id = row.mechanism_id
            p = f"zg361_cl_m{mechanism_id:03d}"
            core = block(self.effects, f"{p}_core_effect")
            record_at = core.index("zg361_case_kernel_record_operation_effect")
            prefix = core[:record_at]
            self.assertIn(f"has_variable = {p}_obligation_pending", prefix)
            self.assertIn(f"var:{p}_obligation_pending = 0", prefix)
            self.assertIn(f"CODE = 4 MECHANISM = {mechanism_id}", prefix)
            self.assertNotIn(f"{p}_object_revision value = 1", prefix)

    def test_route_c_is_a_due_debt_not_a_fake_business_consumer(self) -> None:
        for row in generator.MECHANISMS:
            mechanism_id = row.mechanism_id
            p = f"zg361_cl_m{mechanism_id:03d}"
            core = block(self.effects, f"{p}_core_effect")
            debt_at = core.index(f"{p}_debt_active value = 1")
            deferred_at = core.index(f"{p}_deferred value = 1", debt_at)
            consumer_at = core.index(f"{p}_consume_effect = yes", deferred_at)
            self.assertLess(debt_at, deferred_at)
            self.assertLess(deferred_at, consumer_at)
            self.assertIn(f"{p}_debt_due_cycle", core)
            self.assertIn(f"{p}_consumer_value value = 0", core)
        # The high-cost unbound route still pays for the course.
        self.assertIn(3, generator.DUAL_COSTS[333][2])

    def test_relationship_consumers_have_real_opinion_consequences(self) -> None:
        self.assertEqual(
            generator.RELATIONSHIP_IDS,
            frozenset({313, 314, 315, 317, 319, 321, 322, 327, 329, 330, 332, 333}),
        )
        for mechanism_id in generator.RELATIONSHIP_IDS:
            consumer = block(self.effects, f"zg361_cl_m{mechanism_id:03d}_consume_effect")
            resolver = block(self.effects, f"zg361_cl_m{mechanism_id:03d}_resolve_obligation_effect")
            self.assertIn("add_opinion", consumer)
            self.assertIn("friendliness_opinion", consumer)
            self.assertIn("angry_opinion", consumer)
            self.assertIn("opinion = 5", consumer)
            self.assertIn("opinion = -5", consumer)
            self.assertIn("add_opinion", resolver)

    def test_deadline_consumers_apply_domain_results_not_only_markers(self) -> None:
        expected = {
            312: "vacancy_closed",
            314: "allowance_active value = 0",
            315: "trial_resolved",
            317: "acl_review_closed",
            318: "slot_timeout_settled",
            319: "manager_talent_delta value = -20",
            323: "learning_budget_window_closed",
            324: "outcome_window_closed",
            327: "teaching_application_window_closed",
            329: "mentor_credit value = 1",
            330: "reskill_assessment_closed",
            331: "repaid_hours value = 4",
            332: "succession_drill_closed",
            333: "training_service_window_closed",
        }
        for mechanism_id, needle in expected.items():
            resolver = block(self.effects, f"zg361_cl_m{mechanism_id:03d}_resolve_obligation_effect")
            self.assertIn(needle, resolver, mechanism_id)

    def test_localization_has_identical_nine_language_structure(self) -> None:
        expected_keys = loc_keys(self.loc_en)
        self.assertEqual(len(expected_keys), 5 + 22 * 4)
        self.assertEqual(expected_keys, loc_keys(self.loc_zh))
        for folder, _header in generator.LANGUAGES:
            path = (
                MOD_ROOT
                / f"localization/{folder}/zg361_career_learning_l_{folder}.yml"
            )
            text = path.read_text(encoding="utf-8-sig")
            self.assertEqual(loc_keys(text), expected_keys, folder)
        self.assertIn("这岗位真的存在", self.loc_zh)
        self.assertIn("Training Debt Shrinks Monthly", self.loc_en)
        self.assertIn("English structural placeholders", self.spec)

    def test_no_gui_or_central_file_is_generated(self) -> None:
        relative = {path.relative_to(MOD_ROOT).as_posix() for path in generator.outputs()}
        forbidden_fragments = (
            "gui/",
            "zg361_effects.txt",
            "zg361_b1",
            "zg361_b2",
            "zg361_manager_governance",
            "interactions/",
        )
        for path in relative:
            for fragment in forbidden_fragments:
                self.assertNotIn(fragment, path)
        self.assertIn("no top-level GUI", self.spec)


if __name__ == "__main__":
    unittest.main()
