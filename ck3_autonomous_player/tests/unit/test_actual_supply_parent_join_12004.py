"""New pure fixtures plus preserved compiled-wire consumption; never game evidence."""
from copy import deepcopy
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

BRIDGE=Path(__file__).parents[2]/'src/xar_autoplayer/bridge'
package=types.ModuleType('supply_parent_fixture_bridge')
package.__path__=[str(BRIDGE)]
sys.modules[package.__name__]=package
def load(name):return importlib.import_module(package.__name__+'.'+name)
cb_contract=load('army_actual_supply_callback_observations_contract')
wr_contract=load('army_actual_loss_writer_observations_contract')
parent_contract=load('army_actual_supply_parent_join_contract')
summary=load('army_actual_supply_parent_join_summary')
old_test_path=Path(__file__).with_name('test_episode04_starvation_loss_12004.py')
spec=importlib.util.spec_from_file_location('old_packet_factory',old_test_path)
factory=importlib.util.module_from_spec(spec);spec.loader.exec_module(factory)


def joined_packet():
    army,window=factory.packet()
    army.update(army_id=window['army_id'],native_carmy_id=window['native_carmy_id'])
    invocation=dict(invocation_token=7,native_thread_id=101,nesting_depth=1,
        parent_invocation_token=None,callback_caller_return_rva=0x2A9AB4B,
        callback_entry_rva=0x24E3410,receiver_basis='actual_24E3410_rcx_carmy')
    callback=army['actual_supply_callback_observations_v1']['events'][0]
    callback['supply_parent_invocation_v1']=deepcopy(invocation)
    # Deliberately disagree with both callback endpoints: writer stock is its
    # own real operand, not a before/after proxy chosen to make S<10 true.
    callback['before']['supply_raw']=2000000
    callback['after']['supply_raw']=5000000
    army['actual_loss_writer_observations_v1']['events'][0]['supply_parent_context_v1']=dict(
        invocation=deepcopy(invocation),army_id=0,native_carmy_id=16777216,
        passed_date_raw64=124,stock_at_writer_entry_raw=999999,stock_scale=100000,
        receiver_identity_matches=True,capture_failure_flags=0)
    return army


def normalize(army):
    result=deepcopy(army)
    result['actual_supply_callback_observations_v1']=cb_contract.normalize_actual_supply_callback_observations_v1(
        army['actual_supply_callback_observations_v1'],current_army_id=army['army_id'],current_native_carmy_id=army['native_carmy_id'])
    result['actual_loss_writer_observations_v1']=wr_contract.normalize_actual_loss_writer_observations_v1(
        army['actual_loss_writer_observations_v1'],current_regiment_ids=[0])
    return result


def join(army):return summary.join_actual_supply_parent_writer_observations_v1(army,
    game_version='1.20.0.4',executable_sha256=factory.api.EXE_SHA256,callback_after_sequence=0,loss_after_sequence=0)


class ParentJoinTests(unittest.TestCase):
    def test_real_operand_at_writer_and_exact_ten_negative_boundaries(self):
        for stock,expected in [(999999,5),(0,5),(1000000,None),(1000001,None),(-1,None)]:
            army=joined_packet()
            army['actual_loss_writer_observations_v1']['events'][0]['supply_parent_context_v1']['stock_at_writer_entry_raw']=stock
            actual=join(normalize(army))
            self.assertEqual(actual['strict_below_ten_supply_physical_debit_soldiers'],expected)
            self.assertEqual(actual['events'][0]['stock_at_writer_entry_raw'],stock)
            self.assertFalse(actual['callback_entry_stock_used'])
            self.assertFalse(actual['callback_return_stock_used'])
        self.assertEqual(join(normalize(army))['joined_writer_count'],1)

    def test_cross_thread_parent_receiver_generation_and_null_stock_are_unknown(self):
        for mutate in [lambda p:p['invocation'].update(native_thread_id=102),
                lambda p:p.update(native_carmy_id=33554432),
                lambda p:p.update(receiver_identity_matches=False,capture_failure_flags=8),
                lambda p:p.update(stock_at_writer_entry_raw=None,capture_failure_flags=4)]:
            army=joined_packet();mutate(army['actual_loss_writer_observations_v1']['events'][0]['supply_parent_context_v1'])
            result=join(normalize(army));self.assertEqual(result['joined_writer_count'],0)
            self.assertIsNone(result['strict_below_ten_supply_physical_debit_soldiers'])

    def test_nested_token_pairs_ignore_completion_sequence_order(self):
        army=joined_packet()
        callbacks=army['actual_supply_callback_observations_v1']
        outer=callbacks['events'][0];outer['sequence']=2
        inner=deepcopy(outer);inner['sequence']=1
        inner['supply_parent_invocation_v1'].update(invocation_token=8,nesting_depth=2,parent_invocation_token=7)
        callbacks.update(events=[inner,outer],event_count=2,latest_sequence=2)
        result=join(normalize(army))
        self.assertEqual(result['events'][0]['callback_sequence'],2)
        self.assertEqual(result['strict_below_ten_supply_physical_debit_soldiers'],5)

    def test_default_off_old_wire_is_identical_and_optional_malformed_rejected(self):
        army=joined_packet()
        del army['actual_supply_callback_observations_v1']['events'][0]['supply_parent_invocation_v1']
        del army['actual_loss_writer_observations_v1']['events'][0]['supply_parent_context_v1']
        normalized=normalize(army)
        self.assertEqual(normalized,army)
        self.assertEqual(join(normalized)['events'][0]['reason'],'parent_context_absent')
        for mutate in [lambda p:p.update(stock_scale=1),lambda p:p['invocation'].update(invocation_token=0),
                lambda p:p['invocation'].update(nesting_depth=2),lambda p:p['invocation'].update(native_thread_id=True)]:
            army=joined_packet();mutate(army['actual_loss_writer_observations_v1']['events'][0]['supply_parent_context_v1'])
            with self.assertRaises(ValueError):normalize(army)

    def test_non_supply_stage_bad_physical_sum_and_journal_gap_do_not_qualify_r05(self):
        for kind,rva in [('residual_allocator',0x2A958E8),('siege_or_raid_preferred',0x24E377C),('other_writer_caller',1)]:
            army=joined_packet();army['actual_loss_writer_observations_v1']['events'][0].update(caller_kind=kind,caller_return_rva=rva)
            result=join(normalize(army));self.assertEqual(result['joined_writer_count'],1)
            self.assertIsNone(result['strict_below_ten_supply_physical_debit_soldiers'])
        army=joined_packet();army['actual_loss_writer_observations_v1']['events'][0]['actual_physical_soldier_debit']=500
        self.assertIsNone(join(normalize(army))['strict_below_ten_supply_physical_debit_soldiers'])
        army=joined_packet();army['actual_loss_writer_observations_v1'].update(oldest_available_sequence=3,latest_sequence=3)
        self.assertIsNone(join(normalize(army))['strict_below_ten_supply_physical_debit_soldiers'])

    def test_duplicate_parent_token_never_selects_a_convenient_callback(self):
        army=joined_packet();family=army['actual_supply_callback_observations_v1']
        duplicate=deepcopy(family['events'][0]);duplicate['sequence']=2
        family.update(events=family['events']+[duplicate],event_count=2,latest_sequence=2)
        result=join(normalize(army))
        self.assertEqual(result['joined_writer_count'],0)
        self.assertIn('duplicate_callback_invocation_token',result['unknown_reasons'])

    def test_duplicate_writer_sequence_blocks_double_sum_and_input_is_unchanged(self):
        army=joined_packet();original=deepcopy(army)
        self.assertEqual(join(normalize(army))['strict_below_ten_supply_physical_debit_soldiers'],5)
        self.assertEqual(army,original)
        writers=army['actual_loss_writer_observations_v1']
        writers.update(events=writers['events']+[deepcopy(writers['events'][0])],event_count=2)
        actual=join(normalize(army))
        self.assertIsNone(actual['strict_below_ten_supply_physical_debit_soldiers'])
        self.assertIn('writer_event_sequences_repeated_or_unordered',actual['unknown_reasons'])


def consume_compiled_wire(path):
    wire=json.loads(Path(path).read_text(encoding='utf-8'))
    if wire['native_EXE_invoked'] is not False or wire['original_callback_calls']!=4 or wire['original_writer_calls']!=10:
        raise ValueError('wrong typed-local wire provenance/counts')
    outcomes=[]
    for label in ['a','b']:
        army=dict(army_id=wire['army_'+label+'_id'],native_carmy_id=wire['native_carmy_'+label+'_id'])
        army['actual_supply_callback_observations_v1']=cb_contract.normalize_actual_supply_callback_observations_v1(
            wire['callback_'+label],current_army_id=army['army_id'],current_native_carmy_id=army['native_carmy_id'])
        army['actual_loss_writer_observations_v1']=wr_contract.normalize_actual_loss_writer_observations_v1(
            wire['writers'],current_regiment_ids=[0x03000001])
        result=join(army)
        # A has six scoped calls: four complete, one unreadable stock, one
        # changed-generation capture. The latter two retain unknown status.
        expected=(4 if label=='a' else 1) if wire['parent_join_enabled'] else 0
        if result['joined_writer_count']!=expected:
            raise ValueError(f'{label}: expected {expected} joined writer contexts, got {result["joined_writer_count"]}')
        if result['strict_below_ten_supply_physical_debit_soldiers'] is not None:
            raise ValueError('fixture caller outside actual4 source must not be presented as actual supply-stage loss')
        outcomes.append(result)
    print(json.dumps(dict(status='GREEN',scope='compiled-typed-local-wire-through-production-optional-contracts-and-keyed-consumer',
        native_EXE_invoked=False,parent_join_enabled=wire['parent_join_enabled'],rows=outcomes),ensure_ascii=False,indent=2))


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--native-wire':consume_compiled_wire(sys.argv[2])
    else:unittest.main(verbosity=2)
