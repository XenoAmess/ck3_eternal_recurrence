"""Pure model/source regressions. None starts a native executable or debugger."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from parent_postload_contract import MODE, PREFIX_SHA, SCHEMA, normalize_rows
from postload_wire import wire_json


def fixture() -> tuple[dict[str, object], list[dict[str, object]]]:
    expected: dict[str, object] = dict(
        machine_id='synthetic-model-only', synthetic=True, pid=7,
        created=134370171141306732, entry=0x100000, post_pc=0x10001a,
        subject_field_address=0x2001c0, character=0x200000, full_id=33388,
        context=0, local_player_id=1, game_state=0x300000,
        date_raw=53149056, absolute_day=389544, foreign_limit=512,
        capture_ms=15000, admission_id='synthetic-cold', owner_binding=None)
    start: dict[str, object] = dict(expected, kind='start', schema=SCHEMA,
        mode=MODE, breakpoint_kind='execution', observation_kind='parent_postload_execution',
        entryExact=False, target_record_limit=1, prefix_sha256=PREFIX_SHA)
    arm: dict[str, object] = dict(kind='arm', thread_id=12, thread_generation=1,
        thread_created=134370171141306733, success=True, readback=True,
        saved_debug=[0, 0, 0, 0, 0, 0], armed_debug=[0x10001a, 0, 0, 0, 0, 1])
    capture: dict[str, object] = dict(kind='parent_postload_execution', thread_id=12,
        thread_generation=1, thread_created=134370171141306733,
        RIP=0x10001a, exception_address=0x10001a, RBP=0x200000,
        subject_field_address=0x2001c0, entryExact=False, RSP=0x400000,
        RAX=0x4000a8, RDX=0, loaded_context=0, RCX=0x500000, R8=2, R9=0,
        DR6=1, eflags=514, qpc=99,
        arguments_basis='preserved_after_load_before_mov_r14_rcx',
        first_read_complete=True, second_read_complete=True,
        full_id_before=33388, full_id_after=33388,
        magic_before=0x43686172, magic_after=0x43686172,
        death_before=0, death_after=0, context_before=0, context_after=0,
        admitted_context_unchanged=True, loaded_equals_post_samples=True,
        return_before=0x600000, return_after=0x600000,
        state_before=0x300000, state_after=0x300000,
        date_before=53149056, date_after=53149056,
        day_before=389544, day_after=389544,
        source_anchor_matches=True, postload_owner_clock_qualified=True,
        parent_return_observed=False, paid_maintenance_raw=None, payer=None, cadence=None)
    restore: dict[str, object] = dict(kind='restore', thread_id=12, thread_generation=1,
        thread_created=134370171141306733, readback=True,
        equal_original=True, debug=[0, 0, 0, 0, 0, 0])
    terminal: dict[str, object] = dict(kind='terminal', reason='target_captured',
        capture_count=1, foreign_count=0, restored=True, detached=True,
        pending_event=False, cleanup_complete=True, process_exited=False,
        observation_thread_admission_complete=True, window_complete=False, full_R08=False)
    return expected, [start, arm, dict(kind='ready', census_complete=True), capture, restore, terminal]


class ContractTests(unittest.TestCase):
    def normalize(self, expected: dict[str, object], rows: list[dict[str, object]]) -> dict[str, object]:
        return dict(normalize_rows(wire_json(rows), wire_json(expected)))

    def test_new_postload_null_secondary_positive(self) -> None:
        expected, rows = fixture()
        out = self.normalize(expected, rows)
        self.assertTrue(out['target_postload_qualified'])
        self.assertFalse(out['entryExact'])
        self.assertIsNone(out['paid_maintenance_raw'])

    def test_reject_old_data_mode_and_data_DR(self) -> None:
        for key in ('schema', 'dr'):
            with self.subTest(key=key):
                expected, rows = fixture()
                if key == 'schema':
                    rows[0]['schema'] = 'xar.maintenance.parent_pointer_read.raw.v2'
                else:
                    rows[1]['armed_debug'] = [0x2001c0, 0, 0, 0, 0, 0xb0001]
                with self.assertRaises(ValueError):
                    self.normalize(expected, rows)

    def test_postload_requires_exact_PC_RBP_and_stack(self) -> None:
        for field, wrong in [('RIP', 0x28c2e2e), ('RBP', 0x700000), ('RAX', 0x400000)]:
            with self.subTest(field=field):
                expected, rows = fixture()
                rows[3][field] = wrong
                with self.assertRaises(ValueError):
                    self.normalize(expected, rows)

    def test_full6_generation_and_unknown_cleanup_rejected(self) -> None:
        for field in ('DR7', 'birth', 'missing', 'unknown'):
            with self.subTest(field=field):
                expected, rows = fixture()
                if field == 'DR7':
                    rows[4]['debug'] = [0, 0, 0, 0, 0, 1024]
                elif field == 'birth':
                    rows[4]['thread_created'] = 134370171141306734
                elif field == 'missing':
                    rows.pop(4)
                else:
                    rows[-1]['pending_event'] = True
                with self.assertRaises(ValueError):
                    self.normalize(expected, rows)

    def test_foreign_execution_RF_required_and_flags_preserved(self) -> None:
        expected, rows = fixture()
        marker: dict[str, object] = dict(kind='foreign_resume', count=1, thread_id=12,
            thread_generation=1, thread_created=134370171141306733,
            RIP=0x10001a, exception_address=0x10001a, RBP=0x700000,
            RCX=0x500000, RDX=0, R8=0, R9=0,
            flags_before=514, flags_after=66050,
            RIP_unchanged=True, DR0_retained=True, RF_once=True, TF=False)
        rows.insert(3, marker)
        rows[-1]['foreign_count'] = 257
        self.assertTrue(self.normalize(expected, rows)['target_postload_qualified'])
        for field, bad in [('RF_once', False), ('TF', True), ('flags_after', 514)]:
            with self.subTest(field=field):
                variant = deepcopy(rows)
                variant[3][field] = bad
                with self.assertRaises(ValueError):
                    self.normalize(expected, variant)

    def test_context_drift_remains_diagnostic(self) -> None:
        expected, rows = fixture()
        rows[3].update(RDX=0x800000, loaded_context=0x800000,
            context_before=0x800000, context_after=0x800000,
            admitted_context_unchanged=False)
        out = self.normalize(expected, rows)
        self.assertTrue(out['target_postload_qualified'])
        self.assertFalse(out['admitted_context_unchanged'])

    def test_u64_wire_cannot_be_unsafe_number_or_leading_zero(self) -> None:
        expected, rows = fixture()
        encoded = wire_json(rows)
        if not isinstance(encoded, list) or not isinstance(encoded[0], dict):
            raise ValueError('fixture encoder shape')
        encoded[0]['created'] = 134370171141306732
        with self.assertRaises(ValueError):
            normalize_rows(encoded, wire_json(expected))
        encoded[0]['created'] = '0134370171141306732'
        with self.assertRaises(ValueError):
            normalize_rows(encoded, wire_json(expected))

    def test_late_owned_execution_requires_same_site_birth_and_full6(self) -> None:
        expected, rows = fixture()
        late: dict[str, object] = dict(kind='cleanup_owned_execution',
            owned_late_event=True, thread_id=12, thread_generation=1,
            thread_created=134370171141306733, RIP=0x10001a,
            exception_address=0x10001a, eflags=514,
            restored_generation=True, debug=[0, 0, 0, 0, 0, 0])
        rows.insert(-1, late)
        self.assertTrue(self.normalize(expected, rows)['cleanup_complete'])
        for field, bad in [('exception_address', 0x100000),
                           ('thread_created', 134370171141306734), ('eflags', 770)]:
            with self.subTest(field=field):
                variant = deepcopy(rows)
                variant[-2][field] = bad
                with self.assertRaises(ValueError):
                    self.normalize(expected, variant)

    def test_old_pointer_owner_schema_is_not_postload_admission(self) -> None:
        from postload_owner_binding import validate
        owner: dict[str, object] = dict(schema='xar.maintenance.parent_postload.owner-binding.v1',
            mode='native_campaign_character_postload_v1', episode_projection='native_campaign',
            episode_run_id=None, original_episode_key_present=False,
            pid=7, process_create_time_100ns=134370171141306732,
            connection_generation=1, player_character_full_id=33388,
            local_player_id=1, game_state_identity_witness=0x300000,
            character=0x200000, context=0, controlled_window_id=1,
            payment_epoch=1, native_revision=2, date_raw=53149056,
            absolute_day_raw=389544, callsite_anchor_rva=0x28f785a)
        self.assertEqual(validate(owner)['local_player_id'], 1)
        owner['schema'] = 'xar.maintenance.parent_pointer_read.owner-binding.v2'
        with self.assertRaises(ValueError):
            validate(owner)

    def test_native_source_site_and_default_off_are_explicit(self) -> None:
        root = Path(__file__).resolve().parent
        core = (root/'parent_postload_execution_once.inc').read_text()
        capture = (root/'parent_postload_capture.inc').read_text()
        cmake = (root/'CMakeLists.txt').read_text()
        self.assertIn('PostloadArm(h,o.post_pc)', core)
        self.assertIn('c.Rbp==x.character', core)
        self.assertIn('c.Rip!=o.post_pc', core)
        self.assertIn('c.Dr7|=1;', core)
        self.assertNotIn('0xb0001', core)
        self.assertIn('--explicit-postload-execution-breakpoint-v1', core)
        self.assertIn('"postload_mode_qualified"', core)
        self.assertNotIn('"parent_mode_qualified"', core)
        self.assertIn('std::array<std::uint8_t,29>', core)
        self.assertIn('preserved_after_load_before_mov_r14_rcx', capture)
        self.assertIn('Independent post-load execution observer" OFF)', cmake)

    def test_postload_only_macro_reaches_include_without_entry_mode(self) -> None:
        source = (Path(__file__).resolve().parent/'cold_observer.cpp').read_text()
        stack: list[bool] = [True]
        visible: list[str] = []
        definitions = {'XAR_PARENT_POSTLOAD_EXECUTION_OBSERVER'}
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith('#ifdef '):
                stack.append(stack[-1] and stripped.split()[1] in definitions)
            elif stripped == '#endif':
                if len(stack) == 1:
                    raise ValueError('unexpected preprocessor endif')
                stack.pop()
            elif stack[-1]:
                visible.append(stripped)
        self.assertEqual(len(stack), 1)
        self.assertIn('#include "parent_postload_execution_once.inc"', visible)
        self.assertNotIn('#include "parent_entry_execution_once.inc"', visible)
        self.assertIn('return PostloadEntryMain(argc,argv);', visible)

    def test_cpp_start_entry_is_new_decimal_string_wire(self) -> None:
        core = (Path(__file__).resolve().parent/'parent_postload_execution_once.inc').read_text()
        self.assertNotIn('<<o.entry', core)
        self.assertIn('<<PointerU64Json(o.entry)', core)

    def test_arm_requires_producer_exact_DR7_and_clear_low_DR6(self) -> None:
        for vector in ([0x10001a, 0, 0, 0, 0, 1025], [0x10001a, 0, 0, 0, 1, 1]):
            expected, rows = fixture()
            rows[1]['armed_debug'] = vector
            with self.assertRaises(ValueError):
                self.normalize(expected, rows)
        expected, rows = fixture()
        rows[1]['saved_debug'] = [0, 0, 0, 0, 0, 1024]
        rows[1]['armed_debug'] = [0x10001a, 0, 0, 0, 0xffff0ff0, 1025]
        rows[4]['debug'] = [0, 0, 0, 0, 0, 1024]
        self.assertTrue(self.normalize(expected, rows)['cleanup_complete'])

    def test_capture_cannot_wash_TF_or_nonowned_DR6_status(self) -> None:
        for field, bad in [('eflags', 770), ('DR6', 16385)]:
            expected, rows = fixture()
            rows[3][field] = bad
            with self.assertRaises(ValueError):
                self.normalize(expected, rows)

    def test_late_restored_DR6_is_exact_saved_or_saved_B0(self) -> None:
        expected, rows = fixture()
        late: dict[str, object] = dict(kind='cleanup_owned_execution',
            owned_late_event=True, thread_id=12, thread_generation=1,
            thread_created=134370171141306733, RIP=0x10001a,
            exception_address=0x10001a, eflags=514, restored_generation=True,
            debug=[0, 0, 0, 0, 0x4001, 0])
        rows.insert(-1, late)
        with self.assertRaises(ValueError):
            self.normalize(expected, rows)
        late['debug'] = [0, 0, 0, 0, 1, 0]
        self.assertTrue(self.normalize(expected, rows)['cleanup_complete'])

    def test_qualify_never_washes_float_or_bool_revision_and_date(self) -> None:
        from postload_owner_binding import ORDINARY, qualify
        snapshot: dict[str, object] = dict(episode_projection='native_campaign',
            paused=True, map_ready=True, played_character=dict(alive=True, character_id=33388),
            local_player_id=1, native_revision=2, date_raw=53149056,
            diagnostics=dict(bridge_pid=7, connection_generation=1,
                last_heartbeat=dict(main_thread_query_mailbox_v1=dict(game_state=0x300000))))
        session: dict[str, object] = dict(game_state_identity_witness=0x300000,
            same_owned_process_no_load_window=True, loaded_game_epoch=None,
            pid=7, connection_generation=1, player_character_full_id=33388,
            snapshot_revision=2, native_date_raw=53149056,
            process_create_time_100ns=134370171141306732,
            controlled_window_id=1, absolute_day_raw=389544)
        journal: dict[str, object] = dict(current_session=session,
            controlled_window_admitted=True, sampling=dict(capture_enabled=True, epoch=1))
        leaf: dict[str, object] = dict(snapshot_revision=2, date_raw=53149056,
            character=0x200000, values=dict(context_identity_before=0))
        self.assertEqual(qualify(ORDINARY, None, snapshot, journal, leaf,
            expected_game_state=0x300000, expected_local_player_id=1)['local_player_id'], 1)
        for key, value in [('native_revision', 2.0), ('native_revision', True),
                           ('date_raw', 53149056.0), ('date_raw', False)]:
            with self.subTest(key=key, value=value):
                variant = deepcopy(snapshot)
                variant[key] = value
                with self.assertRaises(ValueError):
                    qualify(ORDINARY, None, variant, journal, leaf,
                        expected_game_state=0x300000, expected_local_player_id=1)


if __name__ == '__main__':
    unittest.main()
