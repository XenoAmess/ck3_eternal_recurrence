"""Focused regressions for the newly observed shared meter/prepared gaps."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime,timezone
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
TOOLS=HERE.parent

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

r=load_module(TOOLS/'comparison/r10_compare.py','shared_hot_reader')
relay=load_module(TOOLS/'split_merge/root_relay.py','shared_hot_root_relay')

class PreparedAndMeter(unittest.TestCase):
    def io(self,scene):
        run=scene/'synthetic--vanilla--R0999';run.mkdir()
        (run/'requests').mkdir();(run/'responses').mkdir()
        state=scene/'state-a02';native=state/'native-session';native.mkdir(parents=True)
        case=scene/'cases/case1';case.mkdir(parents=True)
        seen=[]
        def request(name,tool,args):
            seen.append((name,tool,args));return {'body':{},'is_error':False}
        io=SimpleNamespace(assets=scene,run=run,state_dir=state,native_session=native,
            case=case,ledger=case.parent,meta={'machine_id':'synthetic','source_head':'a'*40},
            binding={'pid':1,'process_create_time_100ns':2,'generation':3,'actor':4,'episode':'synthetic'},
            request=request)
        return io,seen

    def budget(self,scene):
        return r.RuntimeTotalBudget(2*r.MAX_FILE+65536+32768,scene_root=scene,
            source_head='a'*40,machine_id='synthetic',deadline_utc='2030-01-01T00:00:00+00:00',
            clock=lambda:datetime(2026,10,17,tzinfo=timezone.utc))

    def test_live_meter_counts_exact_prepared_session_and_whole_run_once(self):
        with tempfile.TemporaryDirectory()as temp:
            scene=Path(temp);io,seen=self.io(scene)
            (io.run/'mcp-calls.jsonl').write_bytes(b'm'*77)
            (io.native_session/'driver-state.json').write_bytes(b'd'*101)
            stale=scene/'state-a01/native-session';stale.mkdir(parents=True)
            (stale/'stale.json').write_bytes(b'x'*1003)
            (io.state_dir/'profile').mkdir();(io.state_dir/'profile/profile-metadata').write_bytes(b'p'*499)
            (io.ledger/'ledger.json').write_bytes(b'l'*23)
            budget=self.budget(scene);budget.bind_live(io)
            binding=(io.case/'runtime-total-budget.binding.actual.json').stat().st_size
            self.assertEqual(io.used_bytes(),77+101+23+binding)
            self.assertEqual(budget.used_bytes((io.run,io.native_session,io.ledger,io.case)),io.used_bytes())
            self.assertEqual(seen,[])

    def test_actual_session_or_root_payload_stops_before_full_query_transport(self):
        for location in ('run','native_session'):
            with self.subTest(location=location),tempfile.TemporaryDirectory()as temp:
                scene=Path(temp);io,seen=self.io(scene)
                target=io.run if location=='run' else io.native_session
                (target/'synthetic-current-payload.json').write_bytes(b'x'*(40*1024))
                budget=self.budget(scene);budget.bind_live(io)
                with self.assertRaisesRegex(ValueError,'cannot reserve'):
                    io.request('new-read','ck3_query_army_strengths',{'army_ids':[1]})
                self.assertEqual(seen,[])

    def test_prepared_metadata_exact_proof_and_scene_are_required(self):
        with tempfile.TemporaryDirectory()as temp:
            scene=Path(temp);io,_=self.io(scene)
            p=scene/'prepared-a02.json'
            prepared={'machine_id':'synthetic','assets_root':str(scene),'state_dir':str(io.state_dir),
                      'checkpoint':{'source':{'save':{'sha256':'b'*64}}}}
            raw=json.dumps(prepared).encode();p.write_bytes(raw)
            pin={'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            proof={'proof_chain':[{'files':[pin]}]}
            self.assertEqual(relay.prepared_native_session(prepared,pin,proof,assets=scene,
                machine='synthetic',normal_save_sha256='b'*64),(io.state_dir,io.native_session))
            with self.assertRaisesRegex(RuntimeError,'exact prepared'):
                relay.prepared_native_session(prepared,pin,{'proof_chain':[]},assets=scene,machine='synthetic')
            wrong={**prepared,'state_dir':str(scene.parent/'outside-state')}
            with self.assertRaisesRegex(RuntimeError,'escapes scene'):
                relay.prepared_native_session(wrong,pin,proof,assets=scene,machine='synthetic')
            with self.assertRaisesRegex(RuntimeError,'input differs'):
                relay.prepared_native_session(prepared,pin,proof,assets=scene,machine='synthetic',normal_save_sha256='c'*64)

    def test_meter_refuses_inconsistent_or_outside_native_session(self):
        with tempfile.TemporaryDirectory()as temp:
            scene=Path(temp);io,_=self.io(scene)
            io.native_session=scene/'state-a01/native-session'
            with self.assertRaisesRegex(ValueError,'state/native-session'):
                self.budget(scene).bind_live(io)
            io.native_session=scene.parent/'outside-native-session'
            with self.assertRaisesRegex(ValueError,'state/native-session'):
                self.budget(scene).bind_live(io)

if __name__=='__main__':unittest.main()
