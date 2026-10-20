"""Source routing and exact peers only; no native/business qualification."""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
import hashlib,json,tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
from ck3_mod_acceptance_cases import parent_bundle_loader as loader
from ck3_mod_acceptance_cases import r10_prepare_adapter as adapter
from ck3_mod_acceptance_background_types import file_pin,json_value

ROOT=Path(os.environ.get('XAR_PRODUCTION_SOURCE_TOOLS',str(Path(__file__).resolve().parent)))
ACTOR=Path(os.environ.get('XAR_PARENT_ACTOR_SOURCE',str(ROOT/'ck3_mod_acceptance_cases/r08_parent_entry_one_day.py')))
TOOL_NAMES=('prepare_parent_entry_admission.py','consume_parent_entry_actual.py','parent_entry_execution_contract.py','owner_binding.py','cold_observer.cpp','parent_entry_execution_once.inc')
SCRATCH=Path(tempfile.gettempdir())


def pin(path: Path) -> dict:
    payload=path.read_bytes()
    return dict(path=str(path),bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())


class ParentBundle(unittest.TestCase):
    def setUp(self) -> None:
        self.temp=tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.q=self.root/'q.json';self.q.write_text('{}')
        for name in TOOL_NAMES:(self.root/name).write_text('source-only pinned path fixture '+name)
        sources={name:str(ROOT/'ck3_mod_acceptance_cases'/(name+'.py')) for name in loader.ORDER}
        sources['r08_parent_entry_one_day']=str(ACTOR)
        self.index=self.root/'index.json'
        self.value=dict(schema='xar.e04.parent.public-source-bundle.v1',modules=sources,
                        files=[pin(Path(path)) for path in sources.values()]+[pin(self.root/name) for name in TOOL_NAMES])
        self.index.write_text(json.dumps(self.value))
        self.cfg=dict(bundle_index_pin=pin(self.index),qualification_pin=pin(self.q),observer_pin=pin(self.q),
            root_scope_path=str(self.root/'not-authorized.json'),actor_id=33388,expected_start_date_raw=53149056,
            parent_tools=str(self.root),prefix='r08-parent-source-only',
            deadline_utc=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),
            payment_enable_once_authorized=False,natural_phase_enable_once_authorized=False)
        self.context=dict(case_contract={'schema':'xar.e04.r10-common-preparation.v1'},
                          case_inputs={'r08_parent_entry_one_day':self.cfg})

    def replace_index(self) -> None:
        self.index.write_text(json.dumps(self.value));self.cfg['bundle_index_pin']=pin(self.index)

    def test_actual_pinned_parent_route_same_client_without_r10_queries(self) -> None:
        parent=loader.load(self.context)
        self.assertEqual(Path(parent.__file__).resolve(),ACTOR)
        adapter.validate_contract(self.context)
        client=object()
        with patch.object(parent,'run_case',return_value={'source_route_only':True}) as route, \
             patch.object(adapter,'collect_ready_t0',side_effect=AssertionError('Unexpected R10 query prelude')):
            result=adapter.run_case(self.context,client)
        self.assertTrue(result['source_route_only']);route.assert_called_once_with(self.context,client)

    def test_default_off_and_existing_case_exclusion(self) -> None:
        adapter.validate_contract({'case_contract':self.context['case_contract'],'case_inputs':{}})
        bad={**self.context,'case_inputs':{**self.context['case_inputs'],'r06_refill_one_day':{}}}
        with self.assertRaisesRegex(ValueError,'mutually exclusive'):adapter.validate_contract(bad)

    def test_cached_module_still_checks_source_pins(self) -> None:
        loader.load(self.context)
        self.value['files'][0]['sha256']='0'*64;self.replace_index()
        with self.assertRaisesRegex(ValueError,'peer changed'):loader.load(self.context)

    def test_finite_module_set_and_duplicate_pin_rejected(self) -> None:
        self.value['modules']['foreign_module']=str(self.q);self.replace_index()
        with self.assertRaisesRegex(ValueError,'finite peer'):loader.load(self.context)
        self.value['modules'].pop('foreign_module');self.value['files'].append(self.value['files'][0]);self.replace_index()
        with self.assertRaisesRegex(ValueError,'Duplicate'):loader.load(self.context)

    def test_typed_json_and_pin_boundary_rejects_non_json_and_numeric_aliases(self) -> None:
        for invalid in [True,1.0]:
            with self.subTest(value=invalid),self.assertRaises(ValueError):file_pin({**pin(self.q),'bytes':invalid})
        for invalid in [(1,2),float('nan'),Path('not-json')]:
            with self.subTest(value=repr(invalid)),self.assertRaises(ValueError):json_value(invalid)

    def test_refusal_protocol_is_exact_final_pair(self) -> None:
        import ck3_mod_acceptance_background_refusal as refusal
        self.assertEqual(refusal.GATE_PROTOCOL_SHA256,pin(ROOT/'ck3_mod_acceptance_steam_gate.py')['sha256'])
        self.assertEqual(refusal.LAUNCHER_PROTOCOL_SHA256,pin(ROOT/'ck3_mod_acceptance_launcher.py')['sha256'])
        self.assertNotEqual(refusal.LAUNCHER_PROTOCOL_SHA256,'6ef5b8b0882c56fb3bccff74d9c3e77437663add415b63fda2995cbcba4e1d76')

    def test_each_executed_parent_tool_is_bound_before_any_action(self) -> None:
        from unittest.mock import Mock
        from ck3_mod_acceptance_cases import r08_parent_entry_controller as controller
        import copy
        original=copy.deepcopy(self.value)
        for name in TOOL_NAMES:
            with self.subTest(peer=name):
                self.value=copy.deepcopy(original)
                self.value['files']=[r for r in self.value['files'] if r['path']!=str(self.root/name)]
                self.replace_index();client=Mock()
                with patch.object(controller,'observe') as observer,patch.object(controller.subprocess,'Popen') as popen:
                    with self.assertRaises(ValueError):adapter.run_case(self.context,client)
                self.assertFalse(client.mock_calls);observer.assert_not_called();popen.assert_not_called()

    def test_crossed_parent_tool_directory_refused_before_any_action(self) -> None:
        from unittest.mock import Mock
        self.cfg['parent_tools']=str(self.root/'other-parent-tools');client=Mock()
        with self.assertRaises(ValueError):adapter.run_case(self.context,client)
        self.assertFalse(client.mock_calls)


if __name__=='__main__':unittest.main()
