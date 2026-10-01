"""Create a bound probe and actual pending-human-review package for final bytes."""
from pathlib import Path
import argparse,sys,json
from xar_promo.media import parse_ffprobe_json,write_bound_media_probe
import review_story_a04 as p
def main(run):
    final=p.read(run/'final-artifact.json');media=Path(final['path']);probe=parse_ffprobe_json((run/'audit/final-probe.json').read_bytes());bound=run/'audit/native-bound-media-probe.json'
    write_bound_media_probe(bound,media_path=media,probe=probe)
    timeline=p.read(run/'timeline.json');story=run/'human-review-storyboard.json'
    p.write(story,{'chapters':[{'id':c['id'],'title':c['title'],'start_seconds':round(c['global_start'],6),'end_seconds':round(c['global_start']+c['duration'],6)}for c in timeline['chapters']]})
    args=[sys.executable,'-X','utf8','-m','xar_promo','review',str(media),'--storyboard',str(story),'--probe',str(bound),'--output-directory',str(run/'pending-human-review'),'--audit-directory',str(run/'native-review-audit'),'--ffmpeg',str(p.FFMPEG)]
    p.command(run,'native-review-plan',[*args,'--plan-only'])
    p.command(run,'native-pending-human-review',args)
    print(json.dumps({'package':str(run/'pending-human-review'),'state':'pending-human-review','human_signoff':'not-provided'}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run',required=True,type=Path);main(a.parse_args().run)
