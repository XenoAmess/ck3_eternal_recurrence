"""Explicit phase routing for the frozen a08 attempt, with chapter-aware audit."""
from pathlib import Path
import argparse,json,sys
import compose_research_a08 as composer
import review_story_a04 as p
def audit(run):
    final=p.read(run/'final-artifact.json');composer.exact(final)
    output=p.command(run,'final-audit-probe',[str(p.FFPROBE),'-v','error','-show_format','-show_streams','-show_chapters','-of','json',final['path']]);probe=p.read(output);p.write(run/'audit/final-probe.json',probe)
    video=next(s for s in probe['streams']if s['codec_type']=='video');audio=next(s for s in probe['streams']if s['codec_type']=='audio');timeline=p.read(run/'timeline.json');edit=p.read(run/'edit.json');checks={}
    checks['video']=video['codec_name']=='h264' and video['width']==1920 and video['height']==1080 and video['r_frame_rate']=='30/1'
    checks['audio']=audio['codec_name']=='aac' and int(audio['sample_rate'])==48000 and audio['channels']==2
    checks['duration']=abs(float(probe['format']['duration'])-final['duration_expected'])<.15
    checks['six_chapters']=len(probe.get('chapters',[]))==6
    for i,(c,a)in enumerate(zip(timeline['chapters'],probe.get('chapters',[]))):checks['chapter_'+str(i)]=abs(float(a['start_time'])-c['global_start'])<.01 and abs(float(a['end_time'])-(c['global_start']+c['duration']))<.1 and a.get('tags',{}).get('title')==c['title']
    for c in timeline['chapters']:
        for u in c['utterances']:
            shot=edit['utterances'][u['key']];checks[u['key']]=bool(u['facts']) and all(Path(f['source_path']).is_file()for f in u['facts']) and Path(u['audio']).is_file() and Path(shot['image']).is_file() and p.ass_text(u['zh'],40).count(r'\N')<=1 and p.ass_text(u['en'],100).count(r'\N')<=1
    checks['a02_timed_notice_retained']=edit['utterances']['knights-k035']['raw_notice_inset']==composer.notice.RAW_INSETS['knights-k035']
    checks['no_old_whole_AAC']=final['whole_previous_AAC_reused']is False
    p.command(run,'full-AV-decode',[str(p.FFMPEG),'-hide_banner','-nostdin','-v','error','-i',final['path'],'-map','0:v:0','-map','0:a:0','-f','null','-'])
    checks['full_AV_decode']=True
    report={'at_utc':p.stamp(),'artifact':final,'checks':checks,'passed':all(checks.values()),'human_signoff':'not-provided','full_1x_human_review':False,'audit_source':p.ref(__file__)}
    p.write(run/'audit/machine-report.json',report)
    composer.require(report['passed'],'Machine audit failed; retained report identifies failing checks')
    print(json.dumps({'checks':len(checks),'passed':True,'human_review':'pending'}))
def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('phase',choices=['boards','render','audit']);a.add_argument('--run',type=Path,required=True);args=a.parse_args()
    root=args.run/'phase-entrypoints';root.mkdir(exist_ok=True)
    snapshots=[args.run/'sources'/name for name in ('composer-source.py','composer.py') if (args.run/'sources'/name).is_file()]
    composer.require(len(snapshots)==1,'Exactly one explicit frozen composer layout required')
    p.write(root/(args.phase+'-source.json'),{'at_utc':p.stamp(),'runner':p.ref(__file__),'composer':p.ref(composer.__file__),'original_frozen_composer':p.ref(snapshots[0])})
    {'boards':composer.make_boards,'render':composer.render,'audit':audit}[args.phase](args.run)
if __name__=='__main__':main()
