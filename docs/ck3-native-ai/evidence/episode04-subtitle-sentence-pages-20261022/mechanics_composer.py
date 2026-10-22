"""Thin 1080p/30 planner over the accepted public render and ASS APIs."""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
import html
from pathlib import Path
import re
from PIL import ImageFont

from xar_promo.audio import AudioMixSpec, AudioStem
from xar_promo.render import GeneratedTextFile, RenderOptions, RenderPlan, ass_burn_in_filter, plan_render
from xar_promo.subtitles import AssCue, AssDocumentConfig, AssStyleConfig, SubtitleTrackConfig, render_ass_document
from mechanics_contract import SERIES_PALETTE, Cue, KnowledgeCard, RawWindow, Visual, Voice, frames_for, need


@dataclass(frozen=True)
class CueClock:
    frames: int
    raw_frames: int
    card_frames: int


def clock(voice: Voice, raw: RawWindow | None) -> CueClock:
    speech = frames_for(voice.seconds)
    if raw is None:
        return CueClock(speech + 30, 0, speech + 30)
    if speech <= raw.frames:
        total = raw.frames
    else:
        total = max(speech + 30, raw.frames + 150)
    return CueClock(total, raw.frames, total - raw.frames)


def chinese_pages(value: str, font: ImageFont.FreeTypeFont) -> tuple[str, ...]:
    """Keep each sentence on one screen; wrap its two lines at a readable boundary."""
    pages: list[str] = []
    closing = '，。！？；：、,.!?;:）】》”’'

    def fits(line: str) -> bool:
        return len(line) <= 32 and font.getlength(line) <= 1370

    def wrap(sentence: str) -> str | None:
        if fits(sentence):
            return sentence
        # Chinese numbers and Arabic decimal amounts remain intact on each line.
        numbers = tuple(re.finditer(r'[零〇一二三四五六七八九十百千万亿两点]+|\d+(?:[.,]\d+)*', sentence))
        choices: list[tuple[int, int, int]] = []
        for offset in range(1, len(sentence)):
            left, right = sentence[:offset], sentence[offset:]
            if not fits(left) or not fits(right) or right[0] in closing:
                continue
            if any(match.start() < offset < match.end() for match in numbers):
                continue
            choices.append((0 if left[-1] in closing else 1,
                            abs(len(left) - len(right)), offset))
        if not choices:
            return None
        offset = min(choices)[2]
        return sentence[:offset] + '\n' + sentence[offset:]

    # The actual 47-cue corpus fits in two lines per complete sentence. Longer
    # future sentences may split at a clause boundary, never at an arbitrary word.
    for match in re.finditer(r'[^。！？；]+[。！？；]?|[。！？；]', value):
        sentence = match.group().strip()
        if not sentence:
            continue
        page = wrap(sentence)
        if page is not None:
            pages.append(page)
            continue
        clauses = re.findall(r'[^，、：]+[，、：]?|[，、：]', sentence)
        current = ''
        for clause in clauses:
            if current and wrap(current + clause) is None:
                current_page = wrap(current)
                need(current_page is not None, 'Chinese clause exceeds two readable lines')
                if current_page is None:
                    raise ValueError('Chinese clause exceeds two readable lines')
                pages.append(current_page)
                current = ''
            current += clause
        current_page = wrap(current)
        need(current_page is not None, 'Chinese clause exceeds two readable lines')
        if current_page is None:
            raise ValueError('Chinese clause exceeds two readable lines')
        pages.append(current_page)
    need(bool(pages), 'Empty subtitle')
    return tuple(pages)


def readable_groups(value: str, *, chinese: bool, font_path: Path) -> tuple[str, ...]:
    """Sentence pages for Chinese; retain the established English word wrapping."""
    font = ImageFont.truetype(str(font_path), 36 if chinese else 24)
    if chinese:
        return chinese_pages(value, font)
    tokens = re.findall(r'\S+\s*', value)
    lines: list[str] = []
    current = ''
    for token in tokens:
        candidate = current + token
        if current and (font.getlength(candidate) > 1370 or
                        (chinese and len(candidate) > 32)):
            lines.append(current.strip())
            current = token
        else:
            current = candidate
        if current and re.search(r'[。！？!?；;.]$', current.rstrip()):
            lines.append(current.strip())
            current = ''
    if current.strip():
        lines.append(current.strip())
    need(bool(lines), 'Empty subtitle')
    # At most two lines per screen; sentence ends remain valid phrase breaks.
    return tuple('\n'.join(lines[i:i + 2]) for i in range(0, len(lines), 2))


def subtitles(cue: Cue, voice: Voice, total_frames: int, font_path: Path) -> str:
    tracks = [
        SubtitleTrackConfig('zh', 'zh-CN', 2, AssStyleConfig('Chinese', 'Microsoft YaHei', 36,
            primary_colour='&H00CFE5F0', outline_colour='&H00131821',
            margin_left=192, margin_right=192, margin_vertical=119, outline=2, shadow=0)),
        SubtitleTrackConfig('en', 'en', 1, AssStyleConfig('English', 'Microsoft YaHei', 24,
            primary_colour='&H008DA9BB', outline_colour='&H00131821', bold=False, margin_left=192, margin_right=192,
            margin_vertical=38, outline=1.5, shadow=0)),
    ]
    events: list[AssCue] = []
    for language, value, chinese in [('zh', cue.zh, True), ('en', cue.en, False)]:
        groups = readable_groups(value, chinese=chinese, font_path=font_path)
        weights = [len(re.sub(r'\s+', '', group)) for group in groups]
        total = sum(weights)
        start = Decimal('0.10')
        available = voice.seconds - start
        need(available > 0, 'Voice too short')
        cursor = start
        for i, (group, weight) in enumerate(zip(groups, weights)):
            stop = (max(voice.seconds, Decimal(total_frames) / 30 - Decimal('0.10'))
                    if i == len(groups) - 1 else cursor + available * weight / total)
            need(stop > cursor, 'Invalid approximate subtitle interval')
            events.append(AssCue(f'{language}-{i}', language, float(cursor), float(stop), group))
            cursor = stop
    if cue.cue_id == 'N01-01':
        tracks.append(SubtitleTrackConfig('version', 'en', 3, AssStyleConfig('Version', 'Microsoft YaHei', 24,
            alignment=9, margin_left=32, margin_right=32, margin_vertical=18, outline=1, shadow=0)))
        events.append(AssCue('version', 'version', 0, min(5.0, total_frames / 30), 'CK3 1.20.0.4'))
    return render_ass_document(AssDocumentConfig(cue.cue_id, 1920, 1080,
                               duration_seconds=Decimal(total_frames) / 30), tracks, events,
                               available_font_names={'Microsoft YaHei'})


def knowledge_svg(card: KnowledgeCard) -> str:
    """The retained formula-card style, no rasterizer or process invoked here."""
    esc = html.escape
    rows = ''.join(f'<text x="132" y="{493 + i * 62}" font-size="33" fill="#F0E5CF" '
                   f'font-family="Microsoft YaHei">{esc(line)}</text>' for i, line in enumerate(card.rows))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">'
        f'<title>{esc(card.title)}</title><rect width="1920" height="1080" fill="#211813"/>'
        '<rect x="88" y="82" width="8" height="76" fill="#CBA56A"/>'
        f'<text x="120" y="134" font-size="48" fill="#F0E5CF" font-family="Microsoft YaHei">{esc(card.title)}</text>'
        '<rect x="112" y="205" width="1696" height="225" rx="18" fill="#35291F"/>'
        f'<text x="152" y="290" font-size="38" fill="#CBA56A" font-family="Microsoft YaHei">{esc(card.hero)}</text>'
        + rows + f'<text x="120" y="1000" font-size="23" fill="#BBA98D" font-family="Microsoft YaHei">{esc(card.note)}</text>'
        '<text x="1570" y="1060" font-size="21" fill="#BBA98D" font-family="Microsoft YaHei">CK3 1.20.0.4</text></svg>')


def cue_plan(cue: Cue, visual: Visual, voice: Voice, raw: RawWindow | None, card: Path,
             music: Path, ass: Path, *, work: Path, ffmpeg: Path,
             font_path: Path) -> tuple[RenderPlan, CueClock]:
    timing = clock(voice, raw)
    duration_seconds = timing.frames / 30
    source = card if raw is None else raw.source.pin.path
    output = work / (cue.cue_id + '.mp4')
    plan = plan_render(ffmpeg=ffmpeg, video_input=source,
        partial_output=output.with_suffix('.partial.mp4'), final_output=output,
        audit_directory=work / 'audit' / cue.cue_id,
        options=RenderOptions(1920,1080,30,duration_seconds,preset='veryfast',crf=21,
                              audio_bitrate='192k',pad_color='0x211813'),
        ass_path=ass, working_directory=work,
        audio_mix=AudioMixSpec((AudioStem('narration', voice.native.path),
            AudioStem('music', music, gain_db=-24, fade_in_seconds=1, fade_out_seconds=2)),
            duration_seconds=duration_seconds))
    need(len(plan.commands) == 1, 'Public cue composer changed')
    command = plan.commands[0]
    argv = list(command.spec.argv)
    at = argv.index('-filter_complex') + 1
    graph = argv[at]
    geometry = ('scale=1536:864:force_original_aspect_ratio=decrease:flags=lanczos,'
                'pad=1920:1080:192:0:color=0x211813,setsar=1')
    if raw is None:
        before = 'scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos'
        pad = 'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x211813'
        need(graph.count(before) == 1 and graph.count(pad) == 1, 'Public static geometry seam changed')
        graph = graph.replace(before, geometry.split(',pad=')[0], 1).replace(pad,
                                'pad=1920:1080:192:0:color=0x211813', 1)
    else:
        need(graph.startswith('[0:v]') and ';' in graph, 'Public AV graph seam changed')
        audio = graph.split(';',1)[1]
        live = (f'[0:v]trim=start_frame={raw.first}:end_frame={raw.end},setpts=PTS-STARTPTS,'
                + geometry + ',fps=30')
        # fps only normalizes the already qualified30fps recorder timestamps;
        # no atempo, interpolation, looping, tpad or duplicated tail is used on raw.
        if timing.card_frames:
            need(argv.count('-i') == 3, 'Narration/music input ordering changed')
            insertion = argv.index('-filter_complex')
            argv[insertion:insertion] = ['-loop','1','-i',str(card)]
            extra = timing.card_frames / 30
            graph = (live + '[live];[3:v]trim=duration=' + f'{extra:.9f}' + ',setpts=PTS-STARTPTS,' +
                geometry + ',fps=30[card];[live][card]concat=n=2:v=1:a=0,' +
                ass_burn_in_filter(ass) + ',format=yuv420p[v];' + audio)
        else:
            graph = live + ',' + ass_burn_in_filter(ass) + ',format=yuv420p[v];' + audio
    argv[argv.index('-filter_complex') + 1] = graph
    caption_filter = ass_burn_in_filter(ass)
    need(graph.count(caption_filter) == 1, 'One subtitle band per cue required')
    argv[argv.index('-filter_complex') + 1] = graph.replace(caption_filter,
        'drawbox=x=0:y=864:w=iw:h=2:color=0xCBA56A:t=fill,' + caption_filter,1)
    argv[1:1] = ['-threads','1','-filter_complex_threads','1','-nostats','-progress','pipe:1']
    argv[-1:-1] = ['-threads:v','1','-frames:v',str(timing.frames),'-profile:v','high','-level:v','4.0',
                   '-video_track_timescale','15360','-maxrate','4M','-bufsize','8M']
    content = subtitles(cue,voice,timing.frames,font_path)
    return replace(plan,commands=(replace(command,spec=replace(command.spec,argv=tuple(argv))),),
                   generated_files=(GeneratedTextFile(ass,content),)), timing
