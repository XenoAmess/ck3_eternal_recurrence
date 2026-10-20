"""Focused authored CasePort producers plus retained original-source consumers; no game."""
from __future__ import annotations
import ast
import base64
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import ck3_mod_acceptance_cases
# Explicit authored-caller overlay only; the production SDK/package stays selected from Root.
# No existing package/module bytes are copied or replaced.
ck3_mod_acceptance_cases.__path__.insert(0, str(Path(__file__).resolve().parent / 'ck3_mod_acceptance_cases'))
from faith_e02_artifact_pair_contract import (ARTIFACT, DATE, EXE, PLAYER, RECIPIENTS, SAFE, SITE, Arm, Contract,
    Draft, Frame, Object, Pin, array, digest, encode, field, frame, integer, item, json_value, knight,
    mapping, object_value, parse_contract, parse_pin, pin, read, require, text, write_once)
import faith_e02_artifact_pair_queue as Q
import faith_e02_artifact_pair_join as J
from ck3_mod_acceptance_cases import faith_e02_artifact_pair_adapter as A

ROOT = Path('C:/workspace/ck3_eternal_recurrence')
LANE = Path(__file__).resolve().parents[2]
EP = Path('C:/workspace/ck3-faith-and-power-20261017/episode02')


def own_contract(root: Path, arm: str = 'personal', draft: Draft | None = None) -> Contract:
    # Source pins are real; this synthetic cohort is deliberately not a live qualification.
    source = pin(Path(__file__).resolve())
    pending = EP / 'capture-b14-a01/state-a01/native-session/holy-site-relic-action-intents/02990f36bbe8dd7a1ca527216a08140b565fc1697257128fe1e0c8f9724741c9.pending.json'
    result = EP / 'capture-b14-a01/live/4-8e1c2f1861--faith-engine--R0007/case-output/firstfour-integrated-result.json'
    selected_arm: Arm = 'personal' if arm == 'personal' else 'enshrine'
    return Contract(selected_arm, 'authored-pair', '4-8e1c2f1861', str(root / 'not-a-save.ck3'), root / 'pair',
                    pin(pending), pin(result), source, source, (), draft, 96)


def public_context(c: Contract) -> Object:
    base = Path(__file__).resolve().parent
    deps = [pin(base / 'faith_e02_artifact_pair_contract.py'), pin(base / 'faith_e02_artifact_pair_queue.py'),
            pin(base / 'ck3_mod_acceptance_cases/faith_e02_artifact_pair_adapter.py')]
    saved: Object = {'save': c.save_path, 'bytes': 50210503,
        'sha256': '7bd48c5eb8c51a24badd02ba57cb030dba3526da4483479ae9adc231cea7ea7e', 'player_id': PLAYER, 'date_raw': DATE}
    contract: Object = {'schema': 'faith-e02-artifact-pair-case-v1', 'product': 'faith-engine',
        'case': 'faith-engine-e02-artifact-pair-' + c.arm + '-v1', 'arm': c.arm, 'pair_id': c.pair_id,
        'machine_id': c.machine_id, 'saved_input': saved, 'pair_evidence_root': str(c.pair_root),
        'artifact_id': ARTIFACT, 'holy_site_id': SITE, 'recipient_ids': list(RECIPIENTS),
        'metric': 'knight_effectiveness_raw', 'native_cohort': {'dll': json_value(c.native_dll), 'qualification': json_value(c.native_qualification)},
        'previous_enshrine': {'pending': json_value(c.prior_pending), 'world_result': json_value(c.prior_result)},
        'draft': None, 'dependencies': json_value(deps), 'max_public_calls': 96,
        'profile': {'enabled_mods': [], 'product_files': []}}
    return {'product': 'faith-engine', 'case': contract['case'], 'case_contract': contract,
            'case_spec': {**A.FLAGS, 'required_mcp_tools': json_value(sorted(Q.REQUIRED)),
                'opt_in_read_only_mcp_tools': json_value(sorted(Q.OPTIN_READONLY)),
                'whole_product_acceptance_credit': False, 'business_contract_applicable': False,
                'budgets': {'hold_seconds': 3000, 'timeout': 5400}, 'initial_plan': {'steps': []}}}


class FakePort:
    """Synthetic DTO producer; real CasePort method names/file rows, never a private host."""
    def __init__(self, root: Path, c: Contract, pid: int = 1001) -> None:
        self.output = root / ('output-' + c.arm)
        self.output.mkdir(parents=True)
        self.state = root / ('state-' + c.arm)
        self.operator_reviewer = 'authored-fixture-reviewer'
        self.frozen: object = {'run_id': 'authored-managed-' + c.arm}
        self.manifest: object = {'machine_id': c.machine_id, 'native': {'dll': c.native_dll},
                                'native_input_identity_evidence': c.native_qualification}
        self.c = c
        self.pid = pid
        self.revision = 10
        self.equipped = False
        self.enshrined = False
        self.visible = False
        self.selected = False
        self.slot = 1
        self.world_calls: list[str] = []
        self.tools: list[str] = []
        self.ack_unknown = False
        self.ack_without_sequence = False
        self.pending_post = False
        self.draft_location = 700
        self.draft_artifact = False
        self.draft_type_selected = False
        self.draft_candidates = [700, 701]
        self.sequence = 50
        self.snapshots = 0

    def guard(self, reserve: int = 90) -> object:
        require(reserve >= 90, 'fixture must preserve normal exit reserve')
        return {'owned': True}

    def remaining(self) -> float: return 3000.0

    def snapshot_value(self) -> Object:
        return {'format_version': 1, 'paused': True, 'map_ready': True, 'backend_id': 'native-headless',
            'source': 'injected-dll-named-pipe', 'episode_projection': 'native_campaign', 'episode_run_id': None,
            'revision': self.revision, 'native_revision': self.revision-1, 'date_raw': DATE,
            'active_event': None, 'pending_character_interaction': None,
            'played_character': {'character_id': PLAYER, 'alive': True, 'source': 'native'},
            'played_character_gold': {'raw': 139800000, 'scale': 100000},
            'played_character_prestige': {'raw': 1000000, 'scale': 100000},
            'played_character_piety': {'raw': 2000000, 'scale': 100000},
            'managed_campaign_run_binding': {'run_id': json_value(field(self.frozen, 'run_id')), 'state_dir': str(self.state),
                'bridge_pipe': 'authored-pipe', 'host_path': 'authored-global-host', 'frozen_argv_sha256': 'a'*64},
            'diagnostics': {'connected': True, 'bridge_pid': self.pid, 'connection_generation': 1, 'pipe_name': 'authored-pipe',
                'hello': {'pid': self.pid, 'connection_generation': 1, 'expected_ck3_version': '1.20.0.4',
                    'expected_ck3_sha256': EXE, 'ck3_build_match': True}}}

    def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> object:
        self.snapshots += 1
        value = self.snapshot_value()
        write_once(self.output / ('case-snapshot-' + str(self.snapshots).zfill(4) + '.actual-results.json'), {'rows': [{'result': value}]})
        return value

    def view(self) -> Object:
        return {'available': True, 'root_present': self.visible, 'native_visible': self.visible,
                'effective_visible': self.visible, 'current_player_selected': self.selected}

    def current_inventory(self, desired: bool = False, once: bool = False) -> Object:
        return {'available': True, 'needs_recovery': once and not desired, 'once_intent_consumed': once,
                'intent_sequence': self.sequence if once else 0, 'desired_window_observed': desired, 'current': self.view()}

    def personal(self) -> Object:
        return {'available': True, 'read_only': True, 'loaded_source_pins_verified': True,
                'requested_artifact_id': ARTIFACT, 'played_character_id': PLAYER, 'date_raw': DATE,
                'personally_owned': not self.enshrined, 'inventory_artifact': not self.enshrined,
                'equipped': self.equipped, 'equipped_slot_index': self.slot if self.equipped else None,
                'effective_slot_index': self.slot, 'replacing_artifact_id': None,
                'can_equip_in_effective_slot': not self.equipped, 'can_unequip': self.equipped}

    def knight(self, target: int) -> Object:
        raw = 100000 + (4000 if self.equipped and target == PLAYER else 8000 if self.enshrined else 0)
        return {'schema': 'ck3_12004_character_knight_effectiveness_v1', 'available': True,
            'read_only': True, 'two_pass_stable': True, 'own_actor_context_verified': True,
            'callback_provenance': 'exact4_native', 'game_version': '1.20.0.4', 'executable_sha256': EXE,
            'snapshot_revision': self.revision-1, 'date_raw': DATE, 'played_character_id': PLAYER,
            'character_id': target, 'rite_id': 15 if target == PLAYER else 16, 'faith_id': 50,
            'knight_effectiveness_raw': raw, 'actual_knight_effectiveness_breakdown': 'authored total ' + str(raw),
            'raw_scale': 100000, 'modifier_cache_refreshed': False, 'cache_generation_time_known': False,
            'site_attribution_observed': False, 'gameplay_command_submitted': False,
            'raw_pointer_fields_persisted': False, 'selected_site_contribution_raw': None, 'script_cache_rng_effects': 'unknown'}

    def permissions(self) -> Object:
        return {'available': True, 'read_only': True, 'played_character_id': PLAYER, 'date_raw': DATE,
            'requested_holy_site_id': SITE, 'site_inventory_slots': {'available': True,
                'slots': [{'slot_index': 1, 'artifact_id': ARTIFACT if self.enshrined else None}]},
            'player_inventory': {'available': True, 'owner_matches_player': True,
                'artifact_ids': [] if self.enshrined else [ARTIFACT]},
            'artifact_permissions': {'can_enshrine': {'available': True, 'value': not self.enshrined}},
            'current_buttons': {'can_enshrine': {'available': True, 'value': not self.enshrined}}}

    def action(self) -> Object:
        return {'available': True, 'read_only': True, 'played_character_id': PLAYER, 'date_raw': DATE,
            'requested_holy_site_id': SITE, 'requested_artifact_id': ARTIFACT, 'loaded_source_pins_verified': True,
            'selected_artifact_matches_request': True, 'preview_identity_available': True, 'preview_identity_sha256': 'd'*64,
            'permissions': self.permissions(), 'artifact_ownership': {'available': True, 'object_resolved': True,
                'artifact_id': ARTIFACT, 'character_owner_id': None if self.enshrined else PLAYER,
                'holy_site_owner_id': SITE if self.enshrined else None, 'character_owner_matches_player': not self.enshrined,
                'player_owned_reference_member': not self.enshrined,
                'player_equipped_slot_member': {'available': True, 'value': self.equipped},
                'site_equipped_slot_member': {'available': True, 'value': self.enshrined}},
            'destination': {'available': True, 'original_picker_called': True, 'effective_slot_index': 1, 'replacing_artifact_id': None},
            'selected_action_effect_description': {'available': True, 'text': 'authored original effect'},
            'enshrine_disabled_tooltip': {'available': True, 'text': ''}}

    def site(self) -> Object:
        return {'available': True, 'read_only': True, 'played_character_id': PLAYER, 'date_raw': DATE,
                'requested_holy_site_id': SITE, 'player_rite_id': 15, 'player_faith_id': 50,
                'county_context': {'available': True, 'county_holder_id': RECIPIENTS[1]},
                'cached_world_state': {'available': True, 'is_active': True, 'total_active_artifact_rarity': 8 if self.enshrined else 4},
                'inventory': {'available': True, 'artifact_ids': [60, ARTIFACT] if self.enshrined else [60]}}

    def creation(self) -> Object:
        allowed = self.draft_location == 701
        return {'available': True, 'models_available': True, 'models_complete': True, 'selection_available': True,
                'potential_barony_title_ids': json_value(self.draft_candidates if self.draft_type_selected else [999]), 'enshrinable_artifact_ids': [ARTIFACT],
                'selected_type_key': 'site_of_wisdom', 'selected_barony_title_id': self.draft_location,
                'selected_artifact_ids': [ARTIFACT] if self.draft_artifact else [],
                'normal_requirements_legality_observed': True, 'normal_requirements_can_create': allowed,
                'create_tooltip_available': True, 'create_tooltip': 'authored place allowed' if allowed else 'authored place conflict',
                'bypass_requirements_observed': True, 'bypass_requirements_raw': 0,
                'native_rarity_sum_observed': True, 'native_rarity_sum_raw': 4,
                'native_enabled_observed': True, 'native_create_button_enabled': allowed,
                'cached_resource_quote_available': True, 'cached_resource_vector_raw': [0]*10}

    def execute_plan(self, steps: list[Object], name: str, timeout: int | float | None = None, reserve: int = 90) -> object:
        rows: list[Object] = []
        timeout_after = False
        for step in steps:
            tool = text(field(step, 'tool'), 'tool')
            args = mapping(field(step, 'args'), 'args')
            self.tools.append(tool)
            value: Object = {}
            if tool == Q.KNIGHT: value = self.knight(integer(field(args, 'character_id'), 'target'))
            elif tool == Q.ITEM: value = self.personal()
            elif tool == Q.RELIC: value = self.site()
            elif tool == Q.PERMISSION: value = self.permissions()
            elif tool == Q.ACTION: value = self.action()
            elif tool in {Q.WINDOW, Q.CLOSE_QUERY}:
                value = self.current_inventory() if tool == Q.CLOSE_QUERY or args.get('window_kind') == 'inventory' else {
                    'available': True, 'effective_visible': True, 'current_subject_id': SITE}
            elif tool in {Q.OPEN, Q.CLOSE}:
                self.sequence += 1
                self.visible = tool == Q.OPEN
                self.selected = True
                value = self.current_inventory(once=True)
            elif tool in {Q.OPEN_POST, Q.CLOSE_POST}: value = self.current_inventory(desired=True, once=True)
            elif tool == Q.EQUIP:
                self.world_calls.append(tool)
                self.sequence += 1
                self.equipped = True
                value = {'once_intent_consumed': True, 'intent_sequence': 0 if self.ack_without_sequence else self.sequence}
            elif tool == Q.EQUIP_POST:
                value = {'intent_sequence': self.sequence, 'desired_inventory_state_observed': not self.pending_post}
            elif tool == Q.DONATE:
                self.world_calls.append(tool)
                self.enshrined = True
                value = {'ack_only': True}
                timeout_after = self.ack_unknown
            elif tool == Q.SELECT_ITEM: value = {'selection_only': True}
            elif tool == Q.SITE_OPEN: value = {'presentation_only': True}
            elif tool in Q.DRAFT:
                if tool == 'ck3_select_holy_site_creation_type_v1': self.draft_type_selected = True
                if tool == 'ck3_select_holy_site_creation_barony_v1': self.draft_location = integer(field(args, 'barony_title_id'), 'location')
                if tool == 'ck3_set_holy_site_creation_artifact_selection_v1': self.draft_artifact = True
                value = {'selection_only': True, 'create_dispatched': False}
            elif tool == Q.CREATION: value = self.creation()
            else: raise ValueError('Unimplemented authored producer tool: ' + tool)
            # Real successful CaseClient rows omit optional error, intentionally.
            rows.append({'id': json_value(field(step, 'id')), 'ok': True, 'result': value, 'after_snapshot': self.snapshot_value()})
        write_once(self.output / (name + '.actual-results.json'), {'rows': json_value(rows)})
        if timeout_after: raise subprocess.TimeoutExpired(['authored-original-queue'], 20)
        return rows

    def root_checkpoint(self, name: str, request: Object, reserve: int = 90) -> object:
        image = self.output / 'authored-not-live.png'
        if not image.exists():
            image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jE5cAAAAASUVORK5CYII='))
        approval = text(field(request, 'requested_review'), 'review kind')
        return {'run_id': field(self.frozen, 'run_id'), 'reviewer': self.operator_reviewer, 'status': 'complete',
                approval: True, 'original_image_directly_reviewed': True,
                'reviewed_native_observation_sha256': field(request, 'native_projection_sha256'), 'original_image': pin(image)}


class Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-', dir=LANE)
        self.root = Path(self.temp.name)

    def tearDown(self) -> None: self.temp.cleanup()

    def session(self, arm: str = 'personal', **options: bool) -> tuple[A.Session, FakePort]:
        c = own_contract(self.root, arm)
        port = FakePort(self.root, c, 1001 if arm == 'personal' else 1002)
        for key, value in options.items(): setattr(port, key, value)
        session = A.Session(port, c)
        session.snapshot()
        return session, port

    def test_integer_rejects_bool_float_missing_null(self) -> None:
        for value in (True, False, 1.0, None, '1'):
            with self.subTest(value=value), self.assertRaises(ValueError): integer(value, 'identity', 1)
        with self.assertRaises(ValueError): field({}, 'required_nullable')
        self.assertIsNone(field({'required_nullable': None}, 'required_nullable'))

    def test_json_safe64_roundtrip_and_tuple_rejection(self) -> None:
        value: Object = {'id': 4294967294, 'raw_decimal': str(-(2**63)), 'nullable': None, 'rows': [1, 'x']}
        self.assertEqual(json.loads(encode(value)), value)
        with self.assertRaises(ValueError): encode({'raw': SAFE+1})
        with self.assertRaises(ValueError): encode({'rows': (1, 2)})
        p = self.root / 'duplicate.json';p.write_text('{"id":1,"id":2}', encoding='utf-8')
        with self.assertRaises(ValueError): read(p)

    def test_original_pending_is_known_success_not_unlocked(self) -> None:
        c = own_contract(self.root)
        before = pin(Path(c.prior_pending['path']))
        self.assertEqual(A.check_history(c), '4-8e1c2f1861--faith-engine--R0007')
        self.assertEqual(pin(Path(c.prior_pending['path'])), before)

    def test_queue_world_batch_and_wrong_readback_rejected(self) -> None:
        bad = [Q.step('x', Q.OPEN), Q.step('y', Q.CLOSE)]
        with self.assertRaises(ValueError): Q.validate({'steps': bad})
        bad = [Q.step('x', Q.SITE_OPEN, {'holy_site_id': SITE}), Q.step('y', Q.WINDOW, {'window_kind': 'inventory'})]
        with self.assertRaises(ValueError): Q.validate({'steps': bad})
        bad = [Q.step('x', Q.SELECT_ITEM, {'holy_site_id': SITE, 'artifact_id': ARTIFACT}),
               Q.step('y', Q.ACTION, {'holy_site_id': SITE, 'artifact_id': 268})]
        with self.assertRaises(ValueError): Q.validate({'steps': bad})

    def test_queue_has_no_create_adopt_remove_or_raw_route(self) -> None:
        for tool in ('ck3_create_holy_site_once', 'ck3_adopt_holy_site_v1', 'ck3_remove_holy_site_relic_v1', 'ck3_execute_step'):
            with self.assertRaises(ValueError): Q.validate({'steps': [Q.step('x', tool)]})
        with self.assertRaises(ValueError): Q.validate({'steps': [{'id': 'day', 'kind': 'advance_day', 'days': 1}]})

    def test_actual_registered_signatures_and_declared_flags(self) -> None:
        tree = ast.parse((ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py').read_text(encoding='utf-8-sig'))
        signatures = {n.name: {a.arg for a in n.args.args + n.args.kwonlyargs} for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        for tool in Q.REQUIRED:
            if tool == 'ck3_execute_step': continue
            self.assertIn(tool, signatures)
        public = (ROOT / 'tools/ck3_mod_acceptance.py').read_text(encoding='utf-8-sig')
        for flag in A.FLAGS: self.assertIn(flag, public)
        self.assertFalse(A.FLAGS['opt_in_holy_site_creation_create_once'])

    def test_personal_once_exact_post_and_independent_owner_slot(self) -> None:
        session, port = self.session()
        result = A.perform_personal(session)
        self.assertTrue(result['personal_owner_slot_observed'])
        self.assertEqual(port.world_calls, [Q.EQUIP])
        self.assertTrue(session.world_confirmed)
        self.assertNotIn(Q.DONATE, port.tools)

    def test_personal_unknown_ack_without_sequence_never_borrows_latest(self) -> None:
        session, port = self.session(ack_without_sequence=True)
        with self.assertRaises(ValueError): A.perform_personal(session)
        self.assertEqual(port.world_calls, [Q.EQUIP])
        self.assertNotIn(Q.EQUIP_POST, port.tools)
        self.assertTrue(session.world_claimed)
        self.assertFalse(session.world_confirmed)
        with self.assertRaises(ValueError): A.claim(session)

    def test_personal_three_post_reads_do_not_repeat_submit(self) -> None:
        session, port = self.session(pending_post=True)
        with self.assertRaises(ValueError): A.perform_personal(session)
        self.assertEqual(port.tools.count(Q.EQUIP_POST), 3)
        self.assertEqual(port.world_calls, [Q.EQUIP])

    def test_enshrine_once_independent_three_world_reads(self) -> None:
        session, port = self.session('enshrine')
        result = A.perform_enshrine(session)
        self.assertTrue(result['owner_slot_inventory_observed'])
        self.assertFalse(result['retained_sdk_claim_cleared'])
        self.assertEqual(port.world_calls, [Q.DONATE])
        self.assertTrue(session.world_confirmed)

    def test_enshrine_actual_timeout_class_still_reads_without_replay(self) -> None:
        session, port = self.session('enshrine', ack_unknown=True)
        result = A.perform_enshrine(session)
        self.assertTrue(result['ack_unknown'])
        self.assertEqual(port.world_calls, [Q.DONATE])
        self.assertTrue(session.world_confirmed)

    def test_draft_two_native_candidates_original_text_no_create(self) -> None:
        session, port = self.session()
        session.c = replace(session.c, draft=Draft('site_of_wisdom', ARTIFACT, 700, 701))
        result = A.draft(session)
        self.assertIsNotNone(result)
        self.assertFalse(field(result, 'create_dispatched'))
        self.assertEqual(port.draft_location, 701)
        self.assertEqual(port.world_calls, [])

    def test_pre_native_candidate_is_not_original_refusal(self) -> None:
        session, port = self.session()
        session.c = replace(session.c, draft=Draft('site_of_wisdom', ARTIFACT, 700, 702))
        with self.assertRaisesRegex(ValueError, 'PRE_NATIVE_CANDIDATE_BLOCKED'): A.draft(session)
        self.assertNotIn('ck3_select_holy_site_creation_barony_v1', port.tools)
        self.assertEqual(port.world_calls, [])

    def test_named_metric_real_producer_body_projection(self) -> None:
        index = read(EP / 'production-b16-a01/qualifications/native-a01/KNIGHT-EFFECTIVENESS-WIRE-PACKETS.actual.json')
        packets = array(field(index, 'packets'), 'actual producer packets')
        seen = 0
        for entry in packets:
            actual_pin = parse_pin(entry)
            body = read(Path(actual_pin['path']))
            if field(body, 'available') is not True:
                with self.assertRaises(ValueError): knight(body, Frame(1, 1, 0, 1, 1, 1, 'fixture-only'), 1)
                continue
            native = Frame(1, integer(field(body, 'snapshot_revision'), 'native revision', 1),
                integer(field(body, 'date_raw'), 'date'), integer(field(body, 'played_character_id'), 'player', 1), 1, 1, 'fixture-only')
            target = integer(field(body, 'character_id'), 'actual fixture target')
            projected = knight(body, native, target)
            self.assertEqual(projected['raw_decimal'], str(field(body, 'knight_effectiveness_raw')))
            self.assertFalse(projected['site_attribution_observed'])
            seen += 1
        self.assertEqual(seen, 2)

    def test_two_independent_original_arm_producers_join_same_named_metric(self) -> None:
        session, port = self.session()
        personal = A.run_case(public_context(session.c), port)
        self.assertEqual(personal['status'], 'ARM_OBSERVED_PAIR_PENDING', personal.get('error'))
        # Synthetic control rows are ephemeral test data, not retained scene evidence.
        require(port.output.resolve().is_relative_to(self.root.resolve()), 'Synthetic cleanup target escaped the owned test root')
        shutil.rmtree(port.output)
        other = replace(session.c, arm='enshrine')
        other_port = FakePort(self.root, other, 1002)
        enshrine = A.run_case(public_context(other), other_port)
        self.assertEqual(enshrine['status'], 'ARM_OBSERVED_PAIR_PENDING', enshrine.get('error'))
        joined = J.combine(personal, enshrine)
        self.assertEqual(joined['status'], 'SAME_SOURCE_TWO_ARMS_OBSERVED')
        self.assertFalse(joined['site_attribution_observed'])
        self.assertFalse(joined['total_payment_observed'])
        self.assertEqual(json.loads(encode(joined))['named_metric'], 'knight_effectiveness_raw')
        for key, replacement in [('run_id', field(personal, 'run_id')), ('actual_pid', field(personal, 'actual_pid'))]:
            bad = {**enshrine, key: json_value(replacement)}
            with self.assertRaises(ValueError): J.combine(personal, bad)
        bad = {**enshrine, 'unknown_original_action': True}
        with self.assertRaises(ValueError): J.combine(personal, bad)
        bad = {**enshrine, 'before': {**object_value(field(enshrine, 'before')), 'date_raw': DATE+1}}
        with self.assertRaises(ValueError): J.combine(personal, bad)

    def test_public_contract_roundtrip_and_strict_missing_flags(self) -> None:
        context = public_context(own_contract(self.root))
        c = A.validate_contract(context)
        self.assertEqual(c.arm, 'personal')
        decoded = json.loads(encode(context))
        self.assertEqual(A.validate_contract(decoded), c)
        spec = object_value(field(context, 'case_spec'))
        for value in (None, 1, 1.0):
            bad = {**context, 'case_spec': {**spec, 'opt_in_player_inventory_window_close': value}}
            with self.assertRaises(ValueError): A.validate_contract(bad)
        raw = object_value(field(context, 'case_contract'))
        for value in (True, 267.0):
            with self.assertRaises(ValueError): parse_contract({**raw, 'artifact_id': value})
        missing = {k: v for k, v in raw.items() if k != 'draft'}
        with self.assertRaises(ValueError): parse_contract(missing)
        self.assertEqual(parse_contract({**raw, 'draft': None}).draft, None)

    def test_substituted_history_cannot_rotate_retained_once(self) -> None:
        context = public_context(own_contract(self.root))
        raw = object_value(field(context, 'case_contract'))
        history = object_value(field(raw, 'previous_enshrine'))
        substituted = self.root / 'substituted-pending.json'
        write_once(substituted, {'known': 'authored substitute, never the retained actual SDK claim'})
        bad = {**raw, 'previous_enshrine': {**history, 'pending': json_value(pin(substituted))}}
        with self.assertRaisesRegex(ValueError, 'exact protected original B14'): parse_contract(bad)


if __name__ == '__main__': unittest.main(verbosity=2)
