"""Exercise the actual 47-cue project through its ASS producer and consumer."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

from PIL import ImageFont

ORIGINAL = Path('C:/ck3-e04-resume-20261020-a01/r22-mechanics-render-a01')
BASE = ORIGINAL.parent
HERE = Path(__file__).parent
sys.path.insert(0, str(ORIGINAL))
from mechanics_contract import Editorial, Voice, array, obj, integer


def main() -> int:
    # Import candidate by its actual directory before the frozen dependency path.
    sys.path.insert(0, str(HERE))
    from mechanics_composer import readable_groups, subtitles

    project = BASE / 'r22-n05-weight-explainer-a01/promo-project.mechanics.N05-a01.json'
    editorial = Editorial.parse(json.loads(project.read_bytes()))
    assets = obj(json.loads((BASE / 'r22-mechanics-voice-assets-a01/ASSETS.actual.json').read_bytes()))
    voices = {voice.cue_id: voice for voice in (Voice.parse(row) for row in array(assets['actual_voice_cues']))}
    override = obj(json.loads((BASE / 'r22-n05-weight-explainer-a01/ASSETS.actual-a01.json').read_bytes()))
    voice = Voice.parse(override['voice_override'])
    voices[voice.cue_id] = voice
    timeline = obj(json.loads((BASE / 'r22-mechanics-full-a01/attempt-a02/FULL-TIMELINE.actual.json').read_bytes()))
    frames = {str(row['cue_id']): integer(row['frames'], 1) for row in (obj(value) for value in array(timeline['entries']))}
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    font = ImageFont.truetype(str(font_path), 36)
    reports: list[dict[str, object]] = []
    page_count = 0
    output = HERE / 'ass'
    output.mkdir(exist_ok=False)
    for cue in editorial.cues:
        pages = readable_groups(cue.zh, chinese=True, font_path=font_path)
        page_count += len(pages)
        if ''.join(pages).replace('\n', '') != cue.zh:
            raise ValueError('Chinese text changed: ' + cue.cue_id)
        if any(not re.search(r'[\w\u4e00-\u9fff]', page) for page in pages):
            raise ValueError('Punctuation-only page: ' + cue.cue_id)
        for page in pages:
            lines = page.splitlines()
            if len(lines) > 2 or any(len(line) > 32 or font.getlength(line) > 1370 for line in lines):
                raise ValueError('Subtitle geometry exceeded: ' + cue.cue_id)
        content = subtitles(cue, voices[cue.cue_id], frames[cue.cue_id], font_path)
        dialogue = [line.split(',', 9) for line in content.splitlines() if line.startswith('Dialogue:')]
        zh = [row for row in dialogue if row[3] == 'Chinese']
        # Read actual ASS output; remove only the producer's q2 override and N line break.
        recovered = ''.join(re.sub(r'\{\\q2\}', '', row[9]).replace('\\N', '') for row in zh)
        if recovered != cue.zh or len(zh) != len(pages):
            raise ValueError('ASS producer/consumer text differs: ' + cue.cue_id)
        target = output / (cue.cue_id + '.ass')
        target.write_text(content, encoding='utf-8', newline='\n')
        reports.append({'cue_id': cue.cue_id, 'pages': list(pages), 'ASS_bytes': target.stat().st_size,
                        'ASS_sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    first = readable_groups(editorial.cues[0].zh, chinese=True, font_path=font_path)
    if any(page.startswith('上限') or page == '。' for page in first):
        raise ValueError('Actual N01-01 regression persists')
    report = {'schema': 'xar.e04.subtitle-sentence-pages-check.v1',
              'machine_id': 'desktop-3fevhd2-1c74096080',
              'observed_at_utc': datetime.now(timezone.utc).isoformat(),
              'cues': len(reports), 'results': reports, 'actual_ASS_consumer_verified': True,
              'full_movie_reencoded': False, 'human1x': False,
              'project_sha256': hashlib.sha256(project.read_bytes()).hexdigest(),
              'candidate_sha256': hashlib.sha256((HERE / 'mechanics_composer.py').read_bytes()).hexdigest()}
    (HERE / 'CHECK.actual-a01.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'cues': len(reports), 'pages': page_count,
                      'actual_ASS_consumer_verified': True, 'full_movie_reencoded': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
