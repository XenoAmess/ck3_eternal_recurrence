"""Read-only CLI composer for final series-theme mixing of prepared a09 media."""
from pathlib import Path
from dataclasses import replace
import json
from xar_promo.audio import AudioMixSpec,AudioStem,plan_audio_mix
from xar_promo.pipeline import PipelineDependencies,PipelineDraft,PipelineInvocation,SegmentDraft
from xar_promo.process import CommandSpec,run_command
from xar_promo.render import RenderOptions,RenderPlan,PlannedCommand,plan_concat
from xar_promo.sources import VIDEO,VisualSource,VisualProbeResult
from compose_copy_bgm_a09 import OUTPUT,exact,require
import review_story_a04 as p

def compose(config,run,*,config_path,run_path,workdir,adapter_factory,preset_factory,validate_only):
    require(run_path is not None,'Native run required');root=Path(run_path).parent.parent
    dry=p.read(root/'dry-master.json');exact(dry);music=p.read(root/'music-policy.json');exact(music['source'])
    require(config.project_id=='ck3-war-ai-episode02-copy-audit-a09','Audited a09 project required')
    adapter_factory();preset_factory()
    duration=dry['duration_expected']
    mix=AudioMixSpec(stems=(AudioStem(stem_id='audited-narration',path=Path(dry['path']),gain_db=0),AudioStem(stem_id='series-theme',path=Path(music['source']['path']),gain_db=-17,fade_in_seconds=2,fade_out_seconds=8)),duration_seconds=duration,sample_rate=48000,channels=2,normalize=False,metadata={'policy':'same war-series theme loop; narrative 0dB, music -17dB; no normalization'})
    def render_planner(**kw):
        spec=kw['audio_mix'];plan=plan_audio_mix(spec,input_start_index=1,output_label='mixed')
        # Video is input0; narrative is input1; established series theme loops at input2.
        argv=[kw['ffmpeg'],'-hide_banner','-nostdin','-loglevel','warning','-n','-i',str(kw['video_input']),'-i',str(spec.stems[0].path),'-stream_loop','-1','-i',str(spec.stems[1].path),'-filter_complex',plan.filtergraph,'-map','0:v:0','-map','[mixed]','-map_metadata','0','-map_chapters','0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',f'{duration:.6f}','-movflags','+faststart',str(kw['partial_output'])]
        cmd=CommandSpec.create(argv,label='mix established war-series BGM with audited narration',cwd=kw['working_directory'],partial_artifacts=(kw['partial_output'],))
        return RenderPlan((PlannedCommand(cmd,Path(kw['audit_directory'])/'series-theme-mix'),),(),Path(kw['partial_output']),Path(kw['final_output']))
    def concat_planner(**kw):
        require(len(kw['segment_paths'])==1,'One full-episode mix required')
        plan=plan_concat(**kw)
        # A direct remux retains AAC skip-sample metadata for this single segment.
        argv=[kw['ffmpeg'],'-nostdin','-hide_banner','-loglevel','error','-n','-i',str(kw['segment_paths'][0]),'-map','0:v:0','-map','0:a:0','-map_metadata','0','-map_chapters','0','-c','copy','-movflags','+faststart',str(kw['partial_output'])]
        cmd=CommandSpec.create(argv,label='retain full-episode mixed audio and six chapters',cwd=kw['working_directory'],partial_artifacts=(kw['partial_output'],))
        return replace(plan,commands=(PlannedCommand(cmd,Path(kw['audit_directory'])/'concat'),))
    def subtitle_renderer(segment,narration,*,workdir):
        # All 177 bilingual cues are already burned into the prepared picture.
        return '[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'
    def visual_probe(path):return VisualProbeResult('video/mp4',1920,1080)
    segment=SegmentDraft('audited-full-episode',VisualSource('a09-dry-picture',VIDEO,Path(dry['path']),'audited-original-ui-and-records'),RenderOptions(1920,1080,30,duration),{},prepared_narration=Path(dry['path']),audio_mix=mix)
    return PipelineInvocation(PipelineDraft(config,(segment,),Path(OUTPUT),'a09-deliverable','video/mp4'),PipelineDependencies(str(p.FFMPEG),subtitle_renderer,run_command,visual_probe,render_planner=render_planner,concat_planner=concat_planner),Path(workdir))
