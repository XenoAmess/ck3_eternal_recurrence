"""Extract actual final MP4 frames; root must view them before recording review."""
from pathlib import Path
import argparse,json
from PIL import Image,ImageDraw
import review_story_a04 as p
import compose_review_boards_a04 as b
def main(run):
    final=p.read(run/'final-artifact.json');timeline=p.read(run/'timeline.json');root=run/'frame-review';root.mkdir(exist_ok=False);shots={}
    for c in timeline['chapters']:
        for u in c['utterances']:
            if u.get('visual',{}).get('kind')=='research_closure_card' or u['key']=='reinforcement-r005':shots[u['key']]=(u['global_start']+min(2,u['duration']/2),'corrected research cue')
        shots['chapter-'+c['id']]=(c['global_start']+1,'chapter entry')
    notice=next(u for c in timeline['chapters']for u in c['utterances']if u['key']=='knights-k035')
    for offset in (.5,3):shots['notice-'+str(offset)]=(notice['global_start']+offset,'historical a02 inset timing')
    rows=[]
    for key,(t,scope)in shots.items():
        out=root/(key+'.png');p.command(run,'frame-'+key,[str(p.FFMPEG),'-hide_banner','-nostdin','-n','-ss',f'{t:.6f}','-i',final['path'],'-frames:v','1','-threads','1',str(out)])
        rows.append({'key':key,'seconds':t,'scope':scope,'frame':p.ref(out)})
    p.write(root/'frame-index.json',{'artifact':final,'frames':rows,'human_full_1x_review':False,'root_actual_frame_review':'pending'})
    for begin in range(0,len(rows),4):
        sheet=Image.new('RGB',(1920,1160),b.BG);d=ImageDraw.Draw(sheet)
        for i,row in enumerate(rows[begin:begin+4]):
            x=(i%2)*960;y=(i//2)*580;d.text((x+12,y+7),row['key']+'  '+f"{row['seconds']:.3f}s",font=b.font(24),fill=b.GOLD);im=Image.open(row['frame']['path']).resize((960,540),Image.Resampling.LANCZOS);sheet.paste(im,(x,y+40))
        with(root/('contact-'+str(begin//4+1).zfill(2)+'.jpg')).open('xb')as f:sheet.save(f,quality=94)
    print(json.dumps({'frames':len(rows),'contact_sheets':(len(rows)+3)//4,'actual_frame_review':'pending'}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run',required=True,type=Path);main(a.parse_args().run)
