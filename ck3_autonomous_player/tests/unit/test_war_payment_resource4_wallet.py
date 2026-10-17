"""Full producer-shaped journal checks; synthetic wire, no native/live qualification."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO), str(REPO/'ck3_autonomous_player/src')]
from xar_autoplayer.bridge import war_payment_observations_v1 as payment
from xar_autoplayer.bridge import war_payment_resource4_wallet_v1 as wallet
from xar_autoplayer.bridge.version_identity import CK3_12004

FIXTURE = Path(__file__).with_name('fixtures')/'war_payment_generic_context_12004_a04.json'
CASES = json.loads(FIXTURE.read_bytes())
BASE = next(x['value'].get(payment.JOURNAL_KEY, x['value']) for x in CASES if x['case'] == 'positive')


def producer_shaped_journal():
    # Reuse the complete compiled-producer envelope, not a fabricated normalized DTO.
    # Only the new, not-yet-compiled child and its gateway callback are synthetic.
    j = deepcopy(BASE)
    r = j['records'][0]
    r.pop(payment.GENERIC_CONTEXT_KEY)
    r.update(kind=1, receiver=r['before']['character'], second_pointer=0,
             resource_kind_raw=4, component_raw=3, amount_raw=23,
             caller_return_rva=0x28f7c94, same_wrapper_after=False,
             personal_wrapper_matches_character=False, source_boarding_call_chain_matches=False)
    for phase in ('before', 'after'):
        r[phase].update(wrapper=0, wrapper_balance_bits=None)
    f = dict(character_full_id=j['current_session']['player_character_full_id'],
             character_magic=0x43686172, extension=r['before']['character_extension'],
             context=0x60000, physical_4a0_bits=payment.U64-6, failed_reads=0)
    r[wallet.KEY] = dict(schema_version=1, source_entry_rva=wallet.ENTRY,
        resource_name='unknown', maintenance_attribution='unclosed',
        balance_boundary='whole_original_callback_entry_return', before=f, after=deepcopy(f))
    r[wallet.KEY]['after']['physical_4a0_bits'] = (f['physical_4a0_bits']-r['amount_raw']) & payment.U64
    # Deliberately unrelated personal-gold movement must not supply resource4 evidence.
    r['after']['personal_gold_bits'] = 1
    return j, r


def snapshot(j):
    s = j['current_session'];date = s['native_date_raw'] & 0xffffffff
    if date >= 1 << 31:
        date -= 1 << 32
    return dict(paused=True, map_ready=True, revision=s['snapshot_revision']+1,
        native_revision=s['snapshot_revision'], date_raw=date,
        played_character=dict(character_id=s['player_character_full_id']),
        diagnostics=dict(bridge_pid=s['pid'], connection_generation=s['connection_generation'],
            hello=dict(expected_ck3_version=CK3_12004.game_version,
                       expected_ck3_sha256=CK3_12004.executable_sha256)))


def consume(j):
    return wallet.consume_resource4_wallet_contexts(j, snapshot=snapshot(j), machine_id=j['machine_id'])


class Resource4WalletTests(unittest.TestCase):
    def test_full_normalizer_and_consumer_preserve_actual_callback_identity(self):
        j, r = producer_shaped_journal();original = deepcopy(j)
        result = consume(j)
        self.assertEqual(result['journal'], j)
        self.assertIsNot(result['journal'], j)
        self.assertEqual(j, original)
        self.assertNotEqual(snapshot(j)['revision'], snapshot(j)['native_revision'])
        q, = result['qualified_resource4_boundaries']
        self.assertEqual(q['before_balance_bits'], r[wallet.KEY]['before']['physical_4a0_bits'])
        self.assertEqual(q['after_balance_bits'], r[wallet.KEY]['after']['physical_4a0_bits'])
        self.assertEqual(q['slot_address'], 0x604a0)
        self.assertEqual(q['caller_return_rva'], r['caller_return_rva'])
        self.assertEqual(q['journal_sequence'], r['journal_sequence'])
        self.assertEqual(q['entry_event'], r['entry_event'])
        self.assertEqual(q['returned_event'], r['returned_event'])
        self.assertEqual(q['session_entry'], r['session_entry'])
        self.assertTrue(q['boundary_matches_requested_sub_mod64'])
        self.assertEqual(q['resource_name'], 'unknown')
        for name in ('military_paid_raw', 'payer', 'cadence', 'settlement_token'):
            self.assertIsNone(q[name])

    def test_owner_context_and_read_failures_remain_literal_without_qualification(self):
        for variant in ('owner', 'context', 'read', 'null_context', 'session'):
            with self.subTest(variant=variant):
                j, r = producer_shaped_journal();v = r[wallet.KEY]
                if variant == 'owner':
                    for phase in ('before', 'after'):
                        v[phase]['character_full_id'] += 1
                        r[phase]['character_id'] += 1
                if variant == 'context':
                    v['after']['context'] += 8
                if variant == 'read':
                    v['before'].update(physical_4a0_bits=None, failed_reads=1)
                if variant == 'null_context':
                    for phase in ('before', 'after'):
                        v[phase].update(context=0, physical_4a0_bits=None)
                if variant == 'session':
                    r['session_return']['connection_generation'] += 1
                result = consume(j)
                self.assertEqual(result['journal'], j)
                self.assertEqual(result['qualified_resource4_boundaries'], [])

    def test_personal_gold_cannot_replace_missing_resource4_values(self):
        j, r = producer_shaped_journal()
        r['after']['personal_gold_bits'] = r['before']['personal_gold_bits']-r['amount_raw']
        for phase in ('before', 'after'):
            r[wallet.KEY][phase].update(physical_4a0_bits=None, failed_reads=1)
        self.assertEqual(consume(j)['qualified_resource4_boundaries'], [])
        r.pop(wallet.KEY)
        self.assertEqual(consume(j)['qualified_resource4_boundaries'], [])
        self.assertEqual(payment.normalize_journal(BASE, snapshot=snapshot(BASE), machine_id=BASE['machine_id']), BASE)

    def test_physical_zero_is_retained_and_request_mismatch_is_not_paid(self):
        j, r = producer_shaped_journal()
        for phase in ('before', 'after'):
            r[wallet.KEY][phase]['physical_4a0_bits'] = 0
        q, = consume(j)['qualified_resource4_boundaries']
        self.assertEqual((q['before_balance_bits'], q['after_balance_bits']), (0, 0))
        self.assertFalse(q['boundary_matches_requested_sub_mod64'])
        self.assertIsNone(q['military_paid_raw'])

    def test_wrong_kind_resource_and_attribution_are_rejected_by_production_normalizer(self):
        for variant in ('kind', 'resource', 'currency', 'paid'):
            with self.subTest(variant=variant):
                j, r = producer_shaped_journal()
                if variant == 'kind':r['kind'] = 3
                if variant == 'resource':r['resource_kind_raw'] = 0
                if variant == 'currency':r[wallet.KEY]['resource_name'] = 'gold'
                if variant == 'paid':r[wallet.KEY]['paid'] = True
                with self.assertRaises(ValueError):consume(j)


if __name__ == '__main__':
    unittest.main()
