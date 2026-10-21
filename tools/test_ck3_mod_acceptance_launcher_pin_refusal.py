"""Portable refusal metadata regressions; no Steam, game or screen actions."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from ck3_mod_acceptance_background_types import JsonObject, json_object
from ck3_mod_acceptance_fresh_machine_bootstrap import exact_pin
from ck3_mod_acceptance_launcher_pin_refusal import (
    COOPERATIVE_STOP, PIN_ERROR, create_launcher_pin_refusal, public_operation_argv, validate_launcher_pin_refusal,
)


class LauncherPinRefusalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.machine = 'synthetic-pin-refusal-machine'
        self.live = self.root/'live'
        self.keeper = self.root/'keeper'
        self.source = self.root/'source'
        for directory in (self.live,self.keeper,self.source):
            directory.mkdir()
        self.launcher = self.source/'ck3_mod_acceptance_launcher.py'
        tools = Path(__file__).resolve().parent
        self.launcher.write_bytes((tools/self.launcher.name).read_bytes())
        helper = self.source/'ck3_mod_acceptance_fresh_machine_bootstrap.py'
        helper.write_bytes((tools/helper.name).read_bytes())
        self.producer = self.root/helper.name
        self.producer.write_bytes(helper.read_bytes())
        self.frozen = json_object({'run_id': 'synthetic-R0001', 'files': {
            str(self.launcher): {key:value for key,value in exact_pin(self.launcher).items() if key!='path'},
            str(self.producer): {key:value for key,value in exact_pin(self.producer).items() if key!='path'}}})
        self.context = self.live/'run-context.json'
        self.save(self.context, {'run_id':'synthetic-R0001','run_dir':str(self.live)})
        self.command = self.root/'command.json'
        stamp = datetime.now(timezone.utc).isoformat()
        self.save(self.command, {'machine_id':self.machine,'observed_at_utc':stamp,
            'argv':['python','ck3_mod_acceptance.py','run','--run-context',str(self.context)]})
        self.completion = self.root/'completion.json'
        self.terminal: JsonObject = {'machine_id':self.machine,'observed_at_utc':stamp,'exit_code':2,
            'command':str(self.command),'original_subprocess_wait_observed':True}
        self.save(self.completion,self.terminal)
        self.stdout = self.root/'stdout.json'
        self.save(self.stdout, {'run_id':'synthetic-R0001','runtime_status':'LAUNCH_FAILED',
            'business_acceptance':'NOT_ASSESSED','launcher_exit_code':2,'launcher_argv':['python',str(self.launcher)]})
        self.stderr = self.root/'stderr.json'
        self.save(self.stderr, {'status':'BLOCKED','error':PIN_ERROR,'business_pass':False})
        (self.keeper/'STOP').write_text(COOPERATIVE_STOP,encoding='utf-8')
        self.request = self.root/'request.json'
        self.refresh()

    def save(self, path: Path, value: object) -> None:
        path.write_text(json.dumps(value),encoding='utf-8')

    def refresh(self) -> None:
        self.save(self.request,create_launcher_pin_refusal(machine_id=self.machine,command=exact_pin(self.command),
            completion=exact_pin(self.completion),stdout=exact_pin(self.stdout),stderr=exact_pin(self.stderr),
            keeper_stop=exact_pin(self.keeper/'STOP')))

    def check(self) -> None:
        validate_launcher_pin_refusal(exact_pin(self.request),frozen=self.frozen,live=self.live,
                                     keeper=self.keeper,machine_id=self.machine)

    def test_typed_producer_consumer_json_round_trip_and_exact_terminal(self) -> None:
        self.check()
        request = json.loads(self.request.read_text())
        self.save(self.request,json.loads(json.dumps(request)))
        self.check()
        self.save(self.stderr,{'status':'BLOCKED','error':'another guard','business_pass':False})
        self.refresh()
        with self.assertRaisesRegex(ValueError,'Exact before-launch'):
            self.check()

    def test_wrong_machine_bool_exit_missing_wait_and_changed_original_rejected(self) -> None:
        for field,bad in (('machine_id','another-machine'),('exit_code',True),('original_subprocess_wait_observed',False)):
            self.save(self.completion,{**self.terminal,field:bad})
            self.refresh()
            with self.assertRaisesRegex(ValueError,'public command/completion'):
                self.check()
        self.save(self.completion,self.terminal)
        self.refresh()
        self.stderr.write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'original'):
            self.check()

    def test_missing_consumer_pin_is_required_and_other_live_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError,'another allocation'):
            validate_launcher_pin_refusal(exact_pin(self.request),frozen=self.frozen,live=self.root/'other',
                                         keeper=self.keeper,machine_id=self.machine)
        files = json_object(self.frozen['files'])
        consumer = self.source/self.producer.name
        files[str(consumer)] = json_object({key:value for key,value in exact_pin(consumer).items() if key!='path'})
        self.frozen['files'] = files
        with self.assertRaisesRegex(ValueError,'missing consumer-source pin'):
            self.check()

    def test_root_wait_observation_has_no_handle_or_game_exit_credit(self) -> None:
        argv,finished=public_operation_argv(exact_pin(self.command),exact_pin(self.completion),
            machine_id=self.machine,mode='run',exit_code=2)
        self.assertIn('run',argv)
        self.assertIsNotNone(finished.tzinfo)
        self.assertNotIn('actual_original_popen_wait',self.terminal)
        self.save(self.completion,{**self.terminal,'actual_original_popen_wait':True})
        with self.assertRaisesRegex(ValueError,'public command/completion'):
            public_operation_argv(exact_pin(self.command),exact_pin(self.completion),
                machine_id=self.machine,mode='run',exit_code=2)


if __name__ == '__main__':
    unittest.main()
