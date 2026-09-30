from pathlib import Path
from datetime import datetime,timezone
import json,urllib.request,hashlib,shutil,subprocess,sys,importlib.metadata
ROOT=Path(__file__).resolve().parent
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def command(name,argv):
    p=ROOT/'bootstrap-logs'/name;write(p.with_suffix('.argv.json'),argv)
    with p.with_suffix('.stdout.txt').open('xb') as out,p.with_suffix('.stderr.txt').open('xb') as err:r=subprocess.run(argv,stdout=out,stderr=err)
    write(p.with_suffix('.receipt.json'),{'exit_code':r.returncode,'at_utc':datetime.now(timezone.utc).isoformat()})
    if r.returncode:raise RuntimeError(name)
def main():
    request=urllib.request.Request('https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest',headers={'User-Agent':'ck3-full-six-chapter-a04-fixed-ie'})
    release=json.load(urllib.request.urlopen(request,timeout=30));write(ROOT/'release-query.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'release':release})
    if release['draft'] or release['prerelease']:raise RuntimeError('not formal release')
    asset=next(a for a in release['assets'] if a['name'].endswith('.whl'));path=ROOT/'inputs'/asset['name'];path.parent.mkdir(exist_ok=True)
    with urllib.request.urlopen(asset['browser_download_url'],timeout=45) as src,path.open('xb') as out:shutil.copyfileobj(src,out)
    actual=digest(path)
    if actual.lower()!=asset['digest'].split(':')[-1].lower():raise RuntimeError('wheel SHA mismatch')
    version=release['tag_name'].lstrip('v')
    if importlib.metadata.version('xar-promo-toolchain')!=version:command('install-latest-formal-wheel',[sys.executable,'-m','pip','install','--upgrade',str(path)])
    if importlib.metadata.version('xar-promo-toolchain')!=version:raise RuntimeError('installed version mismatch')
    ffbin=Path('C:/Users/1/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin')
    env={'at_utc':datetime.now(timezone.utc).isoformat(),'python':sys.executable,'python_version':sys.version,'promo_version':version,'edge_tts_version':importlib.metadata.version('edge-tts'),'pillow_version':importlib.metadata.version('pillow'),'release':release['html_url'],'wheel_url':asset['browser_download_url'],'wheel_sha256':actual,'wheel_local':str(path),'ffmpeg':str(ffbin/'ffmpeg.exe'),'ffprobe':str(ffbin/'ffprobe.exe'),'repo_fixed_base':'d5f3c51215439b23f578c8973d5d74ac01f1493c','no_game_or_desktop':True,'human_signoff':'not-provided'}
    write(ROOT/'environment.json',env)
    for name in ['--version','--help']:command('promo-'+name.strip('-'),[sys.executable,'-m','xar_promo',name])
    for name in ['start-run','preserve','validate','audit','review','build']:command(name+'-help',[sys.executable,'-m','xar_promo',name,'--help'])
    print(json.dumps(env))
if __name__=='__main__':main()
