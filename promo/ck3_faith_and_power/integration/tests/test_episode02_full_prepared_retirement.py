"""Real public consumer checks with tiny fixtures; no FFmpeg, TTS or game runs."""
from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from faith_power_promo import full_episode as common
from faith_power_promo.formal_episode import FormalInputs
from xar_promo.render import execute_render_plan as actual_execute_render_plan
from test_value_v3_formal import small_metadata_fixture, forbid_media_reads, native_project


class ReachedConcat(RuntimeError):
    pass


class FullPreparedRetirementTests(unittest.TestCase):
    @staticmethod
    def doc():
        return {'scope':'episode02-formal-review',
                'prepared_visual_policy':common.FULL_PREPARED_RETIRE_POLICY}

    @staticmethod
    def rows(total=1800,count=80,longest=120):
        ordinary,extra=divmod(total-longest,count-1)
        return [{'duration_seconds':longest}]+[
            {'duration_seconds':ordinary+(i<extra)} for i in range(count-1)]

    def test_full_actual_rows_budget_keeps_quality_and_all_encoded_clips(self):
        rows=self.rows();budget=common.document_budget(self.doc(),rows,profile=common.EPISODE02_PROFILE)
        old=common.peak_budget(sum(r['duration_seconds'] for r in rows),len(rows),profile=common.EPISODE02_PROFILE)
        single=max(common.media_limit(r['duration_seconds'],audio=False) for r in rows)
        self.assertEqual(budget['prepared_visual_bytes'],single)
        self.assertEqual(budget['narrated_segment_bytes'],old['narrated_segment_bytes'])
        self.assertEqual(budget['concat_deliverable_bytes'],old['concat_deliverable_bytes'])
        self.assertEqual(budget['graphics_metadata_audio_audit_scratch_bytes'],common.SIDE_BYTES)
        self.assertEqual(budget['peak_new_bytes'],single+2*old['narrated_segment_bytes']+common.SIDE_BYTES+old['conservative_packet_overshoot_bytes'])
        self.assertEqual(budget['peak_new_bytes'],1_847_010_910)
        self.assertEqual(budget['required_workers'],1)
        self.assertEqual(budget['geometry'],[2560,1440,30]);self.assertEqual(budget['crf'],21)
        self.assertEqual(budget['video_maxrate_bps'],3_000_000);self.assertEqual(budget['video_bufsize_bits'],3_000_000)
        self.assertEqual(budget['audio_bitrate_bps'],192_000);self.assertEqual(budget['media_CAS_copies'],0)

    def test_full_budget_uses_actual_longest_cue(self):
        rows=self.rows(longest=180)
        budget=common.document_budget(self.doc(),rows,profile=common.EPISODE02_PROFILE)
        self.assertEqual(budget['prepared_visual_bytes'],common.media_limit(180,audio=False))
        with self.assertRaises(ValueError):
            common.document_budget(self.doc(),[{'duration_seconds':2041}],profile=common.EPISODE02_PROFILE)

    def test_no_policy_preserves_existing_full_budget(self):
        rows=self.rows()
        self.assertEqual(common.document_budget({'scope':'episode02-formal-review'},rows,profile=common.EPISODE02_PROFILE),
                         common.peak_budget(sum(r['duration_seconds'] for r in rows),len(rows),profile=common.EPISODE02_PROFILE))

    def test_full_policy_rejects_other_scope_and_profile(self):
        for scope,profile in [('episode02-review-segment',common.EPISODE02_SAMPLE_PROFILE),
                              ('episode01-formal-review',common.EPISODE02_PROFILE),
                              ('episode02-formal-review',common.DEFAULT_PROFILE),
                              ('episode02-formal-review',common.EPISODE02_SAMPLE_PROFILE)]:
            with self.subTest(scope=scope,profile=profile.id),self.assertRaisesRegex(ValueError,'Full prepared'):
                common.document_budget({**self.doc(),'scope':scope},[{'duration_seconds':10}],profile=profile)

    def test_excerpt_policy_cannot_authorize_full(self):
        with self.assertRaisesRegex(ValueError,'rules/preview'):
            common.document_budget({**self.doc(),'prepared_visual_policy':common.PREPARED_RETIRE_POLICY},self.rows(),profile=common.EPISODE02_PROFILE)

    def test_unknown_policy_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unknown exact'):
            common.document_budget({**self.doc(),'prepared_visual_policy':'unverified-delete'},self.rows(),profile=common.EPISODE02_PROFILE)

    def formal_fixture(self,root):
        doc,media=small_metadata_fixture(root)
        doc.update(self.doc(),excluded_cues=[])
        slots={f'required-{i:02}':None for i in range(24)}
        voices=common.read(Path(doc['voice_authoring_catalog']['path']))
        voices['new_live_result_voice_slots']=slots
        path=root/'voices24.json';path.write_text(json.dumps(voices),'utf-8')
        doc['voice_authoring_catalog']=common.pin(path);doc['pending_result_slots']=deepcopy(slots)
        profile=root/'full-profile.json';profile.write_text(json.dumps(common.EPISODE02_PROFILE.to_mapping()),'utf-8')
        doc['render_profile']=common.pin(profile)
        config=common.read(Path(doc['project_config']['path']));config['constraints']={'duration_limit_seconds':2040}
        project=root/'full-project.json';project.write_text(json.dumps(config),'utf-8');doc['project_config']=common.pin(project)
        return doc,media

    def test_real_formal_consumer_keeps_all24_null_results_and_build_refuses(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);doc,media=self.formal_fixture(root)
            with forbid_media_reads(media):result=FormalInputs(doc,common,metadata_only=True).inspect()
            self.assertFalse(result['ready_to_build']);self.assertFalse(result['fullrender_admitted'])
            self.assertEqual(sum('result still unbound' in s for s in result['gaps']),24)
            output=root/'must-not-exist'
            with self.assertRaisesRegex(ValueError,'Full build refused'):
                common.build(SimpleNamespace(output=output),doc,result,None,{})
            self.assertFalse(output.exists())

    def test_real_formal_consumer_rejects_removed_required_slot(self):
        with tempfile.TemporaryDirectory() as name:
            doc,_=self.formal_fixture(Path(name));doc['pending_result_slots'].pop('required-00')
            with self.assertRaisesRegex(ValueError,'preserve every pending'):
                FormalInputs(doc,common,metadata_only=True).inspect()

    def test_full_policy_does_not_inherit_empty_rules_preview_exception(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);doc,_=self.formal_fixture(root)
            voices=common.read(Path(doc['voice_authoring_catalog']['path']));voices['new_live_result_voice_slots']={}
            path=root/'empty-voices.json';path.write_text(json.dumps(voices),'utf-8')
            doc['voice_authoring_catalog']=common.pin(path);doc['pending_result_slots']={}
            doc['review_content_kind']='rules-and-previews-only'
            self.assertFalse(common.rules_preview_segment(doc,voices))
            with self.assertRaisesRegex(ValueError,'preserve every pending'):
                FormalInputs(doc,common,metadata_only=True).inspect()

    def test_real_formal_consumer_still_marks_required_omitted_as_gap(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);doc,media=self.formal_fixture(root)
            doc['pending_result_slots']['required-00']={'status':'omitted','reason':'not yet filmed'}
            with forbid_media_reads(media):result=FormalInputs(doc,common,metadata_only=True).inspect()
            self.assertIn('required-00: required value-v3 result omitted',result['gaps'])
            self.assertFalse(result['ready_to_build'])

    def exercise_build_to_concat(self,root,*,bad_probe=False,workers=1):
        def file(name,data):
            p=root/name;p.write_bytes(data);return common.pin(p)
        rows=[]
        for cue in ['cue-a','cue-b']:
            rows.append({'id':cue,'zh':'规则。','en':'Rule.','claim_ids':['rule'],'shot_ids':[],
                         'speech_duration_seconds':1.0,'duration_seconds':common.cue_duration(1),
                         'audio':file(cue+'.voice.bin',b'fixture narration; no media decode'),
                         'visual_parts':[{'kind':'diagram','duration_seconds':common.cue_duration(1),
                           'disclosure':'Fixture diagram','image':file(cue+'.png',b'fixture image; no pixel read')}]})
        profile=root/'profile.json';profile.write_text(json.dumps(common.EPISODE02_PROFILE.to_mapping()),'utf-8')
        cfg=native_project(rows);cfg['constraints']={'duration_limit_seconds':2040}
        config=root/'project.json';config.write_text(json.dumps(cfg),'utf-8')
        doc={**self.doc(),'machine_id':'synthetic-consumer-fixture','render_profile':common.pin(profile),'project_config':common.pin(config)}
        source=root/'input.json';source.write_text(json.dumps(doc),'utf-8')
        runtime=root/'runtime.json';runtime.write_text(json.dumps({'ffmpeg':file('ffmpeg.bin',b'never executed'),
          'ffprobe':file('ffprobe.bin',b'never executed'),'subtitle_font':{'file':file('font.bin',b'never loaded'),'family':'Fixture Font'}}),'utf-8')
        args=SimpleNamespace(output=root/'output',repo=root,runtime=runtime,input=source,workers=workers)
        inputs=common.Inputs({});inspection={'ready_to_build':True,'rows':rows,'budget':common.document_budget(doc,rows,profile=common.EPISODE02_PROFILE)}
        snapshots=[];commands=[]
        def fresh(repo,runtime,output):common.write(output/'fresh-runtime.json',{'fixture':True});return {}
        def prepare(argv,audit,reason):Path(argv[-1]).write_bytes(b'prepared fixture, not rendered media');commands.append(tuple(argv));return SimpleNamespace(stdout='',stderr='')
        def runner(spec,*,audit_directory):Path(spec.argv[-1]).write_bytes(b'voiced fixture, not encoded media');commands.append(spec.argv);return SimpleNamespace(exit_code=0)
        def render(plan):return actual_execute_render_plan(plan,command_runner=runner)
        def probe(ffprobe,path,audit):
            path=Path(path);voice=path.name.endswith('.voice.bin');visual=path.name.endswith('.visual.mp4')
            streams=[] if voice else [{'codec_type':'video','codec_name':'h264','width':2560,'height':1440}]
            if voice or (not visual and not bad_probe):streams.append({'codec_type':'audio','codec_name':'aac'})
            return {'format':{'duration':str(1.0 if voice else rows[0]['duration_seconds'])},'streams':streams}
        original=common.review_concat_plan
        def concat(ffmpeg,paths,media,audit,scope):
            paths=list(paths);self.assertEqual([p.name for p in paths],['cue-a.mp4','cue-b.mp4'])
            self.assertTrue(all(p.is_file() for p in paths));self.assertFalse(list(media.glob('*.visual.mp4')))
            plan=original(ffmpeg,paths,media,audit,scope)
            manifest=plan.generated_files[0].content
            self.assertTrue(all(p.name in manifest for p in paths))
            snapshots.append(paths)
            raise ReachedConcat('Actual public concat planner received every retained encoded clip')
        with ExitStack() as stack:
            for name,value in [('background_music',lambda *a,**kw:{'file':rows[0]['audio']}),('fresh_runtime',fresh),
              ('available_memory',lambda:8*1024**3),('run_process',prepare),('media_duration',probe),
              ('subtitle',lambda *a:'[Script Info]\n'),('font_render_planner',lambda *a:common.plan_render),
              ('execute_render_plan',render),('review_concat_plan',concat)]:stack.enter_context(patch.object(common,name,value))
            stack.enter_context(patch.object(common.ImageFont,'truetype',return_value=SimpleNamespace(getname=lambda:('Fixture Font','Regular'))))
            if workers!=1:
                with self.assertRaisesRegex(ValueError,'single worker'):common.build(args,doc,inspection,inputs,{})
                self.assertFalse(args.output.exists())
            elif bad_probe:
                with self.assertRaisesRegex(ValueError,'complete voiced AV'):common.build(args,doc,inspection,inputs,{})
                direct=args.output/'native-run/derived/direct'
                self.assertTrue((direct/'cue-a.visual.mp4').is_file());self.assertTrue((direct/'cue-a.mp4').is_file())
                self.assertFalse(snapshots)
            else:
                with self.assertRaises(ReachedConcat):common.build(args,doc,inspection,inputs,{})
                self.assertEqual(len(snapshots),1)
                receipts=list((args.output/'native-run/derived/receipts/prepared-retirement').glob('*/deleted.json'))
                self.assertEqual(len(receipts),2)
                self.assertTrue(all(not common.read(p)['prepared_exists_after'] for p in receipts))
        return commands

    def test_actual_build_public_renderer_retirement_and_concat_keep_every_clip(self):
        with tempfile.TemporaryDirectory() as name:
            commands=self.exercise_build_to_concat(Path(name))
            for argv in commands:
                self.assertEqual(argv[argv.index('-maxrate')+1],'3000000')
                self.assertEqual(argv[argv.index('-bufsize')+1],'3000000')

    def test_actual_build_bad_voiced_probe_keeps_both_files(self):
        with tempfile.TemporaryDirectory() as name:self.exercise_build_to_concat(Path(name),bad_probe=True)

    def test_actual_build_full_retirement_refuses_parallel_workers_before_output(self):
        with tempfile.TemporaryDirectory() as name:self.exercise_build_to_concat(Path(name),workers=2)


if __name__=='__main__':unittest.main()
