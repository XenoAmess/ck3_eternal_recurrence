"""Create a separate immutable render attempt from completed narration and boards."""
from pathlib import Path
import argparse,importlib.metadata,json,shutil,sys
import compose_research_a08 as c
import review_story_a04 as p
def main(source):
    run=source/'render-attempt-a01';run.mkdir(exist_ok=False)
    for n in ('logs','audit','sources'):(run/n).mkdir()
    latest=p.read(p.command(run,'latest-formal-release',['gh','release','view','--repo','XenoAmess/xar_promo_toolchain','--json','tagName,assets,isDraft,isPrerelease,url']))
    env=p.read(source/'sources/environment.json');wheel=c.exact(env['wheel']);version=importlib.metadata.version('xar-promo-toolchain')
    c.require(not latest['isDraft'] and not latest['isPrerelease'] and latest['tagName'].lstrip('v')==version and any(a['digest'].split(':')[-1].upper()==wheel['sha256']for a in latest['assets']),'Latest formal installed wheel differs')
    p.write(run/'release-query.json',{'at_utc':p.stamp(),'release':latest,'wheel':wheel,'installed_version':version})
    inputs=[(source/'timeline.json','timeline.json'),(source/'board-revision-a02/edit.json','edit.json'),(source/'claim-catalog.json','claim-catalog.json'),(source/'project-config.json','project-config.json')]
    for src,name in inputs:shutil.copyfile(src,run/name)
    for src,name in [(Path(c.__file__),'composer.py'),(Path(__file__),'render-entrypoint.py'),(Path(p.__file__),'producer.py'),(Path(c.notice.__file__),'notice.py'),(Path(c.boards.__file__),'boards.py')]:shutil.copyfile(src,run/'sources'/name)
    shutil.copyfile(source/'sources/environment.json',run/'sources/environment.json')
    p.write(run/'input-freeze.json',{'at_utc':p.stamp(),'source_narration_attempt':str(source),'inputs':[p.ref(src)for src,n in inputs],'source_snapshots':[p.ref(x)for x in sorted((run/'sources').glob('*.py'))],'human_signoff':'not-provided'})
    p.command(run,'toolchain-version',[sys.executable,'-X','utf8','-m','xar_promo','--version'])
    p.command(run,'start-run',[sys.executable,'-X','utf8','-m','xar_promo','start-run',str(run/'project-config.json'),'--run-id','episode02-a08-render-20261002-a01','--run-directory',str(run/'native-run')])
    p.command(run,'validate-run',[sys.executable,'-X','utf8','-m','xar_promo','validate',str(run/'native-run/run-manifest.json')])
    c.render(run)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--source-run',required=True,type=Path);main(a.parse_args().source_run)
