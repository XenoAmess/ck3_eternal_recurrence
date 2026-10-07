"""Synthetic version joins for the stock grant and ordinary routes only."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import test_lyd_private_build_12004 as builds
sys.path.insert(0, str(Path(__file__).resolve().parent / 'unit'))
import test_ordinary_interaction as old
from xar_autoplayer.bridge import grant_title_picker_v1 as grant
from xar_autoplayer.bridge import ordinary_interaction_contract as ordinary
from xar_autoplayer.bridge import confucian_readonly_private_v1 as query


def actual4_ordinary(raw):
    raw = copy.deepcopy(raw)
    if 'exact_build' in raw:
        raw['exact_build'] = query.CK3_12004.game_version
        raw['executable_sha256'] = query.CK3_12004.executable_sha256
        raw['source'] = raw['source'].replace('1.20.0.3', '1.20.0.4')
    for key in (ordinary.QUERY_PAYLOAD, ordinary.INITIATE_PAYLOAD, 'preflight_context'):
        if key in raw:
            raw[key] = actual4_ordinary(raw[key])
    return raw


class GrantOrdinaryBuildTests(unittest.TestCase):
    def test_ordinary_source_image_connected_and_preflight_builds_correlate(self):
        frame = builds.upgraded_frame()
        binding = ordinary.interaction_binding(frame, 3)
        raw = actual4_ordinary(old.envelope(old.context(frame)))
        result = ordinary.project_query(raw, binding, old.KEY, old.RECIPIENT)
        self.assertEqual(result[ordinary.QUERY_PAYLOAD]['recipient_id'], old.RECIPIENT)
        self.assertFalse(result[ordinary.QUERY_PAYLOAD]['business_postcondition_verified'])
        ordinary.require_result_build(raw, frame, ordinary.QUERY_PAYLOAD)
        for mutate in (
                lambda r:r[ordinary.QUERY_PAYLOAD].update(executable_sha256=query.CK3_12003.executable_sha256),
                lambda r:r[ordinary.QUERY_PAYLOAD].update(source='native_current_ordinary_interaction_context_1.20.0.3'),
                lambda r:r[ordinary.QUERY_PAYLOAD].update(actor_binding_verified=False)):
            changed = copy.deepcopy(raw)
            mutate(changed)
            with self.assertRaises(ValueError):
                ordinary.project_query(changed, binding, old.KEY, old.RECIPIENT)
        with self.assertRaises(ValueError):
            ordinary.require_result_build(raw, builds.base.frame(), ordinary.QUERY_PAYLOAD)
        ack = actual4_ordinary(old.native_ack(frame))
        ordinary.normalize_native_initiation(ack, binding, old.KEY, old.RECIPIENT)
        ack[ordinary.INITIATE_PAYLOAD]['preflight_context'] = old.context(frame)
        with self.assertRaises(ValueError):
            ordinary.normalize_native_initiation(ack, binding, old.KEY, old.RECIPIENT)

    def test_grant_result_uses_original_connected_image_without_credit(self):
        for build, frame in ((query.CK3_12003, builds.base.frame()),
                             (query.CK3_12004, builds.upgraded_frame())):
            for mixed in (False, True):
                with self.subTest(build=build.game_version, mixed=mixed):
                    observation = dict(available=False, window_visible=False,
                        window_binding_verified=False, rows_complete=False, native_can_send=None,
                        warning_confirmation_required=None, rows=[], selected_title_full_ids=[], requested_title_holders=[])
                    raw = dict(schema=grant.SCHEMA, operation='query', exact_build=build.game_version,
                        executable_sha256=(query.CK3_12003 if build==query.CK3_12004 else query.CK3_12004).executable_sha256 if mixed else build.executable_sha256,
                        owner_thread_verified=False, frame_verified=False, source_abi_pins_verified=False,
                        dispatch_invoked=False, native_call_completed=False, selection_verified=False,
                        transfer_verified=False, business_full_credit=False, recipient_character_full_id=65865,
                        before=observation, after=observation, status='unavailable', unavailable_reason='synthetic_unknown')
                    calls=[]
                    driver=SimpleNamespace(take_snapshot=lambda:copy.deepcopy(frame),
                        capabilities=lambda:{'bridge_capabilities':['game.command.query-grant-title-picker-v1']})
                    setattr(driver, grant.PERMISSION, True)
                    def execute(*args, **kwargs):
                        calls.append((args, kwargs))
                        return raw
                    driver._execute_primitive_step=execute
                    if mixed:
                        with self.assertRaises(ValueError):
                            grant.execute(driver,'query',65865,expected_revision=3,
                                requested_title_full_ids=[],expected_selected_title_full_ids=[])
                    else:
                        result=grant.execute(driver,'query',65865,expected_revision=3,
                            requested_title_full_ids=[],expected_selected_title_full_ids=[])
                        self.assertFalse(result['business_full_credit'])
                    self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
