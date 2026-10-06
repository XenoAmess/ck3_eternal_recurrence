"""Seal Root's already completed direct review of 18 decoded final-movie images.

This records an AI still-image review and verifies its bounded inputs. It does not
watch the whole movie, listen to audio, infer native update moments or sign off.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

BASE = Path('C:/ck3-war-episode04-research-20261004-a01')
OUT = BASE / 'e4-Review01-Root-actual-coded18-review-a01'
INDEX = BASE / 'e4-final-review01-a01/final-coded-samples-a01/INDEX.json'
CLOSED = BASE / 'e4-final-review01-a01/CLOSED-MOVIE-DELIVERY-a01.json'
FREEZE = BASE / 'e4-Review01-Root-actual-row-freeze-a01/Root-final-story-freeze.json'
MOVIE_SHA = 'a1abb0f2abaa06f3fd38839123e9f4ddd4c4218f8dd15e0965732d3596c69346'

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def bounded_pin(path, expected=None):
    path = Path(path)
    require(path.is_file() and path.stat().st_size < 5_000_000, 'Bounded evidence file required')
    data = path.read_bytes()
    pin = {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if expected:
        require(pin['bytes'] == expected['bytes'] and pin['sha256'] == expected['sha256'].lower(), 'Evidence bytes/SHA differ')
    return pin, data

notes = {
    'C01-04-chapter-context': 'Chinese/English subtitle visible and readable. Independent-sample card states supply 300 with one missing soldier, separate integer +1 and weighted merge inventory. Independent replay label distinguishes map background from research statements.',
    'C02-05-chapter-context': 'Independent replay label and enlarged 1086 / supply300/300 HUD readable. Both subtitles state the first replay day14-to15 supply change from about291.23 to300.',
    'C03-09-chapter-context': 'Chinese/English subtitles state all27 regiment identities and maximum strengths unchanged. Independent replay label and siege-event HUD remain readable; screenshot alone does not prove cause.',
    'C04-05-chapter-context': 'Independent-sample card explicitly distinguishes Jan25 progress61.875%, remaining about3.08days and UI4days/Jan29 forecast. Both subtitles readable; background marked independent replay.',
    'C05-01-center': 'Opaque overview card states A reachedLondon, Bday38 conditions changed/observation stopped, C first observedday77 with sampling deviations, and noABCwinner. Subtitle questions and source-context banner readable.',
    'C05-04-center': 'Card shows B27 split15+12,3337+3342=6679, originalregiment checks and explicitly independent qualification background rather than this action. No subtitle is visible at this sampled instant; this is not an assertion about entire paragraph coverage.',
    'C05-05-center': 'ActualC May21 paused terminal replay label. Map army6689 and HUD101/300 with red1% visible. Card states arrival observation interval(75,77], net+10, original27/max6747, supply110.38to101.90 and sampling/cause boundaries. Both subtitle lines readable.',
    'C05-08-center': 'Bcard separates childday20to21 supply110.38to100 from Mainday31to32 supply106.14to126.14. Qualification background explicitly separate, and paused postwrite clip wording visible. Chinese/English subtitle agrees with child window.',
    'C05-10-center': 'ActualB Apr12 paused replay label, army6690 and supply100/100 visible. Card explains expected113.06109 cap100/actual100, original27 plusnew1/1, commanderchange causeunknown and no merge-click instant claim. Bilingual subtitle readable.',
    'C05-14-center': 'Background explicitlyA independenthistoricalreplay. Card retains Bday38 stopped/52remaining/new28th1/1/commanderunknown, noLondoncomparison, Cplanned1/actual2 sampling and no winner. Bilingual Bstop subtitle readable.',
    'C05-15-center': 'A historical-background label readable. OpaqueA resultcard states day51 firstobservation, interval(49,51], original27/net+10/max6747/supply106.14, no per-update casualty/refill ledger. No subtitle visible at this sampled instant.',
    'C05-16-center': 'C May21 paused terminal label with6689 and101/300 visible. Cashcard separately names Anet16.06 and Cnet15.82, no proven marchpayment/embarkfee, nocauseledger and noABCwinner. Both subtitles say netchange.',
    'C06-10-center': 'A independenthistoricalbackground label. Closingcard keeps Aarrival/Cday77 observation, Bconditionschanged/nocomparison, Csamplinglimitations, originalcohortscope and starvation/paymentledgerunknown. Both subtitles readable.',
    'C05-14-B-postmerge-start': 'ActualB Apr12 paused replay label, map6690/supply100/100. Limitscard retains new28th1/1 and Bstop/noLondoncomparison. Both subtitle lines about aligning date/event are readable.',
    'C05-14-final-A-bridge': 'Background is visiblyA and labeledA independenthistoricalreplay. Chinese/English subtitle explicitly returns to whole-army direct-routeA; limitscard also names this transition.',
    'C05-16-A-opening': 'A historicalreplay source label and London siege6689 visible. Chinese/English subtitle says netdecrease16.06. Cashcard names Afirst/Cafter and explicitly avoids classifying netcash as payment.',
    'C05-16-C-cash-context': 'C May21 paused terminal source label,6689/101/300/red1% visible. Chinese/English subtitle says onlynetchange, with separate Anet16.06/Cnet15.82 and ledgerunknown card.',
    'final-coded-tail': 'Lastcodedframe52073 retains readable closingevidence/boundarycard and independentqualificationreplay label. No subtitle visible at this exact final frame. No sampledframe clipping or black final picture observed.'
}

index_pin, index_data = bounded_pin(INDEX, {'bytes':15494,'sha256':'50d691f2c102c9959f3d7bb4bc39f851f1b3396f085985ed9327e9d65f107c01'})
closed_pin, closed_data = bounded_pin(CLOSED, {'bytes':4673,'sha256':'3ddb222eaabcb8c1db767fdb335b8b98259147abb145a3f4d156f9e7470ab2f3'})
freeze_pin, _ = bounded_pin(FREEZE, {'bytes':25852,'sha256':'975ade3d256a8e84511e3206dbb60c7f04bf2131d9bc053850b26d8c0eb4caa6'})
index, closed = json.loads(index_data), json.loads(closed_data)
require(index['movie'] == closed['movie'], 'Actual movie bindings differ')
require(index['movie']['bytes'] == 1199061934 and index['movie']['sha256'].lower() == MOVIE_SHA, 'Wrong final movie subject')
require(len(index['samples']) == 18 and set(notes) == {s['label'] for s in index['samples']}, 'Exact18 actual samples required')
samples = []
for sample in index['samples']:
    pin, _ = bounded_pin(sample['PNG']['path'], sample['PNG'])
    require(Path(pin['path']).parent == INDEX.parent, 'Unexpected sample directory')
    with Image.open(pin['path']) as im:
        require(im.size == (1920,1080), 'Wrong decoded pixel geometry')
    require(sample['actual_video_pts'] == sample['frame_zero_based'] * 1600 and sample['time_base'] == '1/48000', 'Wrong original codedframeclock')
    samples.append({'label':sample['label'],'frame_zero_based':sample['frame_zero_based'],
                    'actual_video_pts':sample['actual_video_pts'],'time_base':sample['time_base'],
                    'PNG':pin,'Root_direct_view_original_1920x1080':True,
                    'visible_findings':notes[sample['label']], 'sample_blocker':None})
OUT.mkdir(exist_ok=False)
result = {'schema':'xar.e04.Root-actual-coded18-image-review.v1',
          'created_utc':datetime.now(timezone.utc).isoformat(),
          'state':'ROOT_ACTUAL_18_CODED_IMAGE_REVIEW_NO_BLOCK', 'reviewer':'/root AI assistant',
          'movie':index['movie'],'index':index_pin,'closed_movie_delivery':closed_pin,'Root_story_freeze':freeze_pin,
          'review_method':'Root directly viewed all18 final-MP4 decoded PNGs through view_image(detail=original), in3batches of6, then recorded actual visible findings. This script checks bounded filebindings only.',
          'samples':samples,'blockers':[], 'whole_movie_rehashes':0,
          'full_movie_video_decode_audit':False,'full_AAC_timing_or_audio_listening_review':False,
          'full_continuous_source_clean_review':False,'native_game_event_exact_PTS_review':False,
          'human_full_1x_review':False,'human_signoff':False,
          'decision_scope':'No blocker observed in these18 static codedframes; actual wholemovie automatedaudit and humanfull1xreview are separate.'}
target = OUT / 'Root-coded18-NO-BLOCK.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps(bounded_pin(target)[0],ensure_ascii=False))
