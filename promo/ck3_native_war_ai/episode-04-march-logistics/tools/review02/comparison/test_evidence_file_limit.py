"""Bounded evidence input qualification; large JSON is memory-backed, no game/raw read."""
import argparse,hashlib,importlib.util,json,stat,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--actual-admission',nargs=2)
parser.add_argument('--C-caller-fragment',type=Path)
parser.add_argument('--A-parser-fragment',type=Path)
opts,remaining=parser.parse_known_args();sys.argv=[sys.argv[0]]+remaining
spec=importlib.util.spec_from_file_location('r10_limited_subject',Path(__file__).with_name('r10_compare.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
SOURCE='c4992c304d196135d9590799d69ffb3c9f5510e6';MACHINE='synthetic-limits'

class Limits(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.scene=self.root/'scene';self.scene.mkdir()
        self.target=self.scene/'driver.json';self.target.write_text('{}')
        self.payload=b'{"memory_only":"'+b'x'*(17*1024*1024)+b'"}'
        self.row={'admitted':True,'machine_id':MACHINE,'source_head':SOURCE,
            'source_binding':{'new_clean_integrated_source_head':SOURCE},'scene_root':str(self.scene),
            'component_ceiling_bytes':{'driver':402653184},'new_scene_aggregate_bytes':1744830464,
            'quota_review_at_utc':'2026-10-16T07:45:01.597+00:00'}
        self.admission=self.root/'admission.json';self.write_admission()
        self.ref={'path':'scene/driver.json','bytes':len(self.payload),'sha256':hashlib.sha256(self.payload).hexdigest()}
    def write_admission(self):
        b=json.dumps(self.row).encode();self.admission.write_bytes(b)
        self.cap={'path':str(self.admission),'sha256':hashlib.sha256(b).hexdigest()}
    def admitted(self,**kw):
        return c.Evidence(self.root,max_file_bytes=2*c.MAX_FILE,capacity_admissions=[self.cap],
            expected_source_head=SOURCE,expected_machine_ids=[MACHINE],**kw)
    def backed(self,func):
        original_stat=Path.stat;original_read=Path.read_bytes;target=self.target;blob=self.payload;reads=[]
        def size(path,*args,**kw):
            if path==target:return SimpleNamespace(st_size=len(blob),st_mode=stat.S_IFREG|0o600)
            return original_stat(path,*args,**kw)
        def data(path):
            if path==target:reads.append(path);return blob
            return original_read(path)
        with patch.object(Path,'stat',size),patch.object(Path,'read_bytes',data):func(reads)
    def test_default_rejects_large_before_read_and_explicit_same_scene_reads_exact_bytes(self):
        def run(reads):
            with self.assertRaisesRegex(ValueError,'16MiB limit'):c.Evidence(self.root).raw(self.ref)
            self.assertEqual(reads,[])
            e=self.admitted();self.assertEqual(e.raw(self.ref),self.payload)
            e.check_runtime_pin(self.ref,{'machine_id':MACHINE,'source_head':SOURCE})
            self.assertEqual(len(reads),1)
            with self.assertRaisesRegex(ValueError,'actual runtime scene'):
                e.check_runtime_pin(self.ref,{'machine_id':'another-machine','source_head':SOURCE})
        self.backed(run)
    def test_wrong_pin_source_machine_or_scene_cannot_enlarge_input(self):
        original=dict(self.cap);self.cap['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'exact SHA'):self.admitted()
        self.cap=original
        for key,value in (('machine_id','another-machine'),('source_head','d'*40)):
            old=self.row[key];self.row[key]=value;self.write_admission()
            with self.assertRaisesRegex(ValueError,'machine/source/admitted'):self.admitted()
            self.row[key]=old;self.write_admission()
        self.row['scene_root']=str(self.root/'another-scene');self.write_admission()
        def run(reads):
            with self.assertRaisesRegex(ValueError,'16MiB limit'):self.admitted().raw(self.ref)
            self.assertEqual(reads,[])
        self.backed(run)
        with self.assertRaisesRegex(ValueError,'explicit32MiB opt-in'):
            c.Evidence(self.root,capacity_admissions=[self.cap])
        with self.assertRaisesRegex(ValueError,'explicit16MiB or32MiB'):
            c.Evidence(self.root,max_file_bytes=64*1024*1024)
    def test_C_caller_propagates_explicit_scope_and_keeps_default_limit(self):
        path=opts.C_caller_fragment or Path(__file__).parent.parent/'strategy_c/phased_relay.py'
        spec=importlib.util.spec_from_file_location('C_limited_caller_subject',path)
        C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
        config={'max_evidence_file_bytes':33554432,'evidence_capacity_admission':[[str(self.admission),self.cap['sha256']]]}
        runtime={'machine_id':MACHINE,'source_head':SOURCE}
        reader=C.Evidence([self.root],c,input_options=config,runtime=runtime)
        self.assertEqual(reader.limits.file_limit(self.target),33554432)
        self.assertEqual(C.Evidence([self.root],c).limits.file_limit(self.target),16777216)
        self.assertEqual(reader.limits.file_limit(self.root/'outside.json'),16777216)
        config['evidence_capacity_admission'][0][1]='0'*64
        with self.assertRaisesRegex(ValueError,'exact SHA'):
            C.Evidence([self.root],c,input_options=config,runtime=runtime)
    def test_A_explicit_parser_options_reach_bounded_reader(self):
        path=opts.A_parser_fragment or Path(__file__).with_name('strategy_a_stages.py')
        spec=importlib.util.spec_from_file_location('A_parser_subject',path)
        A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
        argv=['post']
        for key in ('repo','relay-source','consumer-root','consumer-manifest','plan','runtime','features-binding',
                    'evidence-root','context','request-helper','relay-sha256','request-helper-sha256',
                    'loaded-save-sha256','case-id','attempt','deadline-utc','army-id','native-carmy-id'):
            argv+=['--'+key,'1']
        args=A.parser().parse_args(argv+['--max-evidence-file-bytes','33554432',
            '--evidence-capacity-admission',str(self.admission),self.cap['sha256']])
        e=c.Evidence(self.root,**c.evidence_file_options(vars(args),source_head=SOURCE,machine_ids=[MACHINE]))
        self.assertEqual(e.file_limit(self.target),33554432)
        args=A.parser().parse_args(argv)
        self.assertEqual(c.Evidence(self.root,**c.evidence_file_options(vars(args),
            source_head=SOURCE,machine_ids=[MACHINE])).file_limit(self.target),16777216)
    @unittest.skipUnless(opts.actual_admission,'optional exact Root admission metadata smoke')
    def test_actual_root_admission_metadata_only(self):
        path,sha=opts.actual_admission;b=Path(path).read_bytes()
        self.assertEqual(hashlib.sha256(b).hexdigest(),sha)
        row=json.loads(b);root=Path(row['scene_root'])
        e=c.Evidence(root,max_file_bytes=2*c.MAX_FILE,capacity_admissions=[{'path':path,'sha256':sha}],
            expected_source_head=row['source_head'],expected_machine_ids=[row['machine_id']])
        held=root/'state-a01/native-session/army-query-history-results/army-query-0df79cc072a04033aefa0acd1b8798ba.json'
        self.assertEqual(e.file_limit(held),33554432)
        self.assertEqual(e.file_limit(root.parent/'foreign.json'),16777216)
        self.assertEqual(e.max_file_bytes,33554432)

if __name__=='__main__':unittest.main(verbosity=2)
