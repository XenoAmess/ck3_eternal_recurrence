"""Portable no-media checks for bounded commands, native direct artifacts and gaps."""
from pathlib import Path
import json
from types import SimpleNamespace
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from faith_power_promo.full_episode import (Inputs,build,bounded,cue_duration,direct_register,peak_budget,pin,visual_command)
from xar_promo.model import new_project_config
from xar_promo.operations import start_run
from xar_promo.project import load_document
from xar_promo.render import RenderOptions,plan_render


class FullEpisodeTests(unittest.TestCase):
    def test_full_worst_case_fits_future_three_gib(self):
        budget=peak_budget(1860,168)
        self.assertLess(budget['peak_new_bytes'],3*1024**3)
        self.assertEqual(budget['media_CAS_copies'],0)
        with self.assertRaises(ValueError):peak_budget(1860+1/30,168)
        with self.assertRaises(ValueError):peak_budget(1800,169)

    def test_stock_render_plan_has_vbv_and_file_cap(self):
        plan=plan_render(ffmpeg='ffmpeg',video_input=Path('visual.mp4'),audio_input=Path('voice.mp3'),
            partial_output=Path('partial.mp4'),final_output=Path('final.mp4'),audit_directory=Path('audit'),
            options=RenderOptions(2560,1440,30,10,preset='veryfast',crf=21))
        argv=bounded(plan,10,audio=True).commands[0].spec.argv
        self.assertIn('-maxrate',argv);self.assertIn('-bufsize',argv);self.assertIn('-fs',argv)
        self.assertEqual(argv[argv.index('-crf')+1],'21')

    def test_native_direct_register_does_not_copy_media(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);cfg=root/'config.json'
            cfg.write_text(json.dumps(new_project_config('test-project','test','zh-CN',['zh-CN','en'],'a','p').to_dict()),'utf-8')
            run=start_run(cfg,run_id='direct-test',run_directory=root/'run')
            actual=run.parent/'derived/direct/actual.mp4';actual.parent.mkdir(parents=True)
            actual.write_bytes(b'unit-test direct artifact bytes; not a media qualification')
            before=list(run.parent.rglob('*.mp4'))
            direct_register(run,[('test.actual','deliverable',actual,'video/mp4')])
            loaded=load_document(run,check_files=True)
            self.assertEqual(loaded.run.artifacts[-1].path,'derived/direct/actual.mp4')
            self.assertEqual(before,list(run.parent.rglob('*.mp4')))
            with self.assertRaises(ValueError):direct_register(run,[('test.actual','deliverable',actual,'video/mp4')])

    def test_null_result_slots_and_visual_gaps_refuse_before_output(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); audio=root/'audio.bin';audio.write_bytes(b'unit stub')
            request=root/'request.json';request.write_text(json.dumps({'request':{'text':'规则'}}),'utf-8')
            rows=[];baseline=[]
            for index in range(158):
                row={'id':f'E01-T{index:03}','zh':'规则','en':'Rule','claim_ids':[],'shot_ids':[],
                    'audio':pin(audio),'speech_duration_seconds':.3,'duration_seconds':cue_duration(.3),'visual_parts':None}
                rows.append(row);baseline.append({**row,'entry_id':row['id'],'kind':'measured-cue','provider_request':pin(request)})
            assembly=root/'assembly.json';assembly.write_text(json.dumps({'entries':baseline}),'utf-8')
            doc={'schema':'ck3-faith-power-full-edit-v1','scope':'episode01-full-review','machine_id':'unit-fixture',
                'assembly_plan':pin(assembly),'cues':rows,'excluded_cues':[],
                'result_slots':{'E01-L01':None,'E01-L02':None,'E01-L03':None},'sequence':[r['id'] for r in rows]}
            inputs=Inputs(doc); inspection=inputs.inspect()
            self.assertFalse(inspection['ready_to_build'])
            self.assertTrue(any('E01-L01' in gap for gap in inspection['gaps']))
            output=root/'must-not-exist'
            with self.assertRaises(ValueError):build(SimpleNamespace(output=output),doc,inspection,inputs,{})
            self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
