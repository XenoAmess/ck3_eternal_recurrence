"""One R215 month-boundary research insert through installed xar-promo."""

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

from xar_promo.audio import AudioMixSpec, AudioStem
from xar_promo.media import probe_media
from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.process import run_command
from xar_promo.render import RenderOptions, ass_burn_in_filter, plan_render
from xar_promo.sources import VIDEO, VisualProbeResult, VisualSource


ID = 'R215-R06-MONTH-NET10-INSERT'
MACHINE = 'desktop-3fevhd2-1c74096080'
MUSIC_GAIN_DB = -17.0


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def load(path):
    return json.loads(Path(path).read_bytes())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verified(path, ref):
    path = Path(path)
    need(path.is_file() and path.stat().st_size == ref['bytes'] and
         digest(path) == ref['sha256'], 'input changed: ' + str(path))
    return path


def artifact(run, run_path, identifier):
    matches = [r for r in run.artifacts if r.artifact_id == identifier]
    need(len(matches) == 1, 'missing exact preserved ' + identifier)
    return (Path(run_path).parent / matches[0].path).resolve()


def ass_time(seconds):
    centis = round(seconds * 100)
    hours, centis = divmod(centis, 360000)
    mins, centis = divmod(centis, 6000)
    secs, centis = divmod(centis, 100)
    return f'{hours}:{mins:02}:{secs:02}.{centis:02}'


def ass_escape(value):
    return value.replace('\\', r'\\').replace('{', r'\{').replace('}', r'\}').replace('\n', r'\N')


def make_ass(data):
    entries = data['captions']
    need(len(entries) == 2, 'expected exactly two provider sentence captions')
    lines = [
        '[Script Info]',
        'Title: R215 month-boundary net +10 research insert / review only',
        'ScriptType: v4.00+',
        'PlayResX: 1920',
        'PlayResY: 1080',
        'WrapStyle: 2',
        'ScaledBorderAndShadow: yes',
        '', '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        'Style: CN,Microsoft YaHei,38,&H00CFE5F0,&H00CFE5F0,&H00201813,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,8,120,120,0,1',
        'Style: EN,Microsoft YaHei,26,&H00C9C4BB,&H00C9C4BB,&H00201813,&H00000000,0,0,0,0,100,100,0,0,1,2,0,8,110,110,0,1',
        'Style: Label,Microsoft YaHei,21,&H006AA5CB,&H006AA5CB,&H00201813,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,7,20,20,0,1',
        '', '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
        f'Dialogue: 9,0:00:00.00,{ass_time(data["render"]["game_seconds"])},Label,review,0,0,0,,{{\\an7\\pos(40,878)}}R215 / RESEARCH INSERT / NO SIGNOFF',
    ]
    for row in entries:
        start, end = ass_time(row['start_seconds']), ass_time(row['end_seconds'])
        need(0 <= row['start_seconds'] < row['end_seconds'] <= data['render']['game_seconds'],
             'subtitle outside actual measured speech')
        lines.append(f'Dialogue: 5,{start},{end},CN,,0,0,0,,{{\\an8\\pos(960,908)}}{ass_escape(row["zh"])}')
        lines.append(f'Dialogue: 4,{start},{end},EN,,0,0,0,,{{\\an8\\pos(960,978)}}{ass_escape(row["en"])}')
    return '\n'.join(lines) + '\n'


def compose(config, run, *, config_path, run_path, workdir,
            adapter_factory, preset_factory, validate_only):
    del config_path
    need(adapter_factory()['id'] == config.adapter and
         preset_factory()['id'] == config.preset,
         'project adapter/preset differs from actual CK3 Review02')
    need(config.project_id == 'ck3-war-ai-episode04-r215-insert',
         'wrong one-cue render config')
    cues = [c for chapter in config.chapters for c in chapter.cues]
    need(len(cues) == 1 and cues[0].cue_id == ID,
         'render project must contain only R215 new cue')
    if run is None:
        need(validate_only, 'build requires native run and preserved small sources')
        input_path = os.environ.get('XAR_R215_RENDER_INPUT')
        need(input_path, 'explicit external plan input required')
        data = load(input_path)
        visual = verified(data['preview']['path'], data['preview'])
        audio = verified(data['audio']['path'], data['audio'])
        card = verified(data['card']['path'], data['card'])
    else:
        data = load(artifact(run, run_path, 'source.render-inputs'))
        visual = verified(artifact(run, run_path, 'source.preview18'), data['preview'])
        audio = verified(artifact(run, run_path, 'source.tts-audio'), data['audio'])
        card = verified(artifact(run, run_path, 'source.card'), data['card'])
    need(data['schema'] == 'xar.e04.r215-insert-render-inputs.v1' and
         data['machine_id'] == MACHINE and data['cue_id'] == ID and
         data['partial_review'] is True and data['human_signoff'] is False,
         'render input scope incorrect')
    # The theme stays at its tracked master path; hashing verifies the actual
    # body without making a second 30 MiB CAS copy inside this 32 MiB lane.
    music = verified(data['music']['path'], data['music'])
    need(music.name == 'quiet-courtly-tension.wav' and data['music_gain_db'] == MUSIC_GAIN_DB,
         'series theme or established gain changed')
    game_seconds = float(data['render']['game_seconds'])
    total_seconds = float(data['render']['total_seconds'])
    frames = int(data['render']['frames'])
    need(game_seconds == 18.0 and total_seconds == 21.0 and frames == 630 and
         data['render']['geometry'] == [1920, 1080] and
         data['render']['fps'] == 30,
         'R215 21s FHD30 contract changed')
    segment = SegmentDraft(
        ID, VisualSource(ID, VIDEO, visual, 'R215-month-boundary-review-preview',
                         metadata={'formal_dynamic_credit': False,
                                   'continuous_1x_review': False}),
        RenderOptions(1920, 1080, 30, total_seconds, preset='veryfast', crf=25),
        {'zh-CN': data['narration_zh'], 'en': data['subtitle_en']},
        prepared_narration=audio)

    def inspect(path):
        probe = probe_media(os.environ.get('WAR_PROMO_FFPROBE', 'ffprobe'), path,
                            audit_directory=Path(workdir)/'audit'/'probe-preview')
        stream = probe.video_streams[0]
        need((stream.width, stream.height) == (1280, 720), 'preview geometry differs')
        return VisualProbeResult('video/mp4', stream.width, stream.height)

    def subtitles(item, narration, *, workdir):
        del item, narration, workdir
        return make_ass(data)

    def planner(**kwargs):
        need(Path(kwargs['video_input']).resolve() == visual.resolve(),
             'unexpected visual input')
        need(Path(kwargs['audio_input']).resolve() == audio.resolve(),
             'unexpected TTS input')
        options = kwargs['options']
        need(options.duration_seconds == total_seconds, 'unexpected duration')
        mix = AudioMixSpec(
            stems=(AudioStem('original-voice', audio, gain_db=0.0),
                   AudioStem('single-series-theme', music, gain_db=MUSIC_GAIN_DB,
                             trim_duration_seconds=total_seconds, fade_in_seconds=1.0,
                             fade_out_seconds=3.0)),
            duration_seconds=total_seconds, sample_rate=48000, channels=2,
            normalize=False,
            metadata={'policy': 'one tracked theme, voice unchanged, theme -17dB, no ducking'})
        plan = plan_render(**{**kwargs, 'audio_mix': mix})
        need(len(plan.commands) == 1, 'upstream one-segment render plan changed')
        command = plan.commands[0]
        argv = list(command.spec.argv)
        graph_index = argv.index('-filter_complex') + 1
        existing_graph = argv[graph_index]
        old_video, audio_graph = existing_graph.split(';', 1)
        need(old_video.startswith('[0:v]trim=duration=21.000000') and
             '[1:a]' in audio_graph and '[2:a]' in audio_graph,
             'upstream render/mix graph seam changed')
        burn = ass_burn_in_filter(kwargs['ass_path'])
        game = (
            '[0:v]trim=duration=18.000000,setpts=PTS-STARTPTS,'
            'scale=1536:864:flags=lanczos,'
            'pad=1920:1080:192:0:color=0x211813,setsar=1,fps=30,'
            'drawbox=x=0:y=864:w=1920:h=216:color=0x35291F:t=fill,'
            'drawbox=x=0:y=864:w=1920:h=3:color=0xCBA56A:t=fill,'
            'format=yuv420p[game]')
        still = (
            '[3:v]trim=duration=3.000000,setpts=PTS-STARTPTS,'
            'scale=1920:1080,setsar=1,fps=30,format=yuv420p[card]')
        joint = (
            '[game][card]concat=n=2:v=1:a=0,fps=30,'
            'trim=duration=21.000000,setpts=PTS-STARTPTS,' + burn +
            ',format=yuv420p[v]')
        argv[graph_index] = ';'.join((game, still, joint, audio_graph))
        argv[graph_index-1:graph_index-1] = ['-loop', '1', '-framerate', '30',
                                             '-t', '3.000000', '-i', str(card)]
        argv[-1:-1] = ['-threads', '1', '-filter_threads', '1',
                      '-filter_complex_threads', '1', '-frames:v', str(frames)]
        return replace(plan, commands=(replace(command,
                         spec=replace(command.spec, argv=tuple(argv))),))

    return PipelineInvocation(
        PipelineDraft(config, (segment,),
                      Path('R215-R06-MONTH-INSERT-21s-REVIEW-NO-SIGNOFF.mp4'),
                      'r215-r06-month-insert-review-no-signoff', 'video/mp4'),
        PipelineDependencies(os.environ.get('WAR_PROMO_FFMPEG', 'ffmpeg'),
                             subtitles, run_command, inspect,
                             render_planner=planner), Path(workdir))
