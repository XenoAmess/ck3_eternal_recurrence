"""Preserve the first boards and create larger genuine UI crops for rendering."""
from pathlib import Path
import argparse,copy,json
from PIL import Image,ImageDraw
import compose_research_a08 as c
import compose_review_boards_a04 as b
import review_story_a04 as p
def main(run):
    root=run/'board-revision-a02';root.mkdir(exist_ok=False);(root/'visuals').mkdir()
    edit=copy.deepcopy(p.read(run/'edit.json'));specs=p.read(run/'board-spec.json');receipts={}
    for key,row in specs.items():
        src=Image.open(row['source_image']);im=Image.new('RGB',(1920,1080),b.BG);d=ImageDraw.Draw(im)
        b.fit_text(d,(40,28),row['title'],1830,45,b.INK);b.fit_text(d,(44,100),row['case'],1820,26,b.GOLD);d.line((40,145,1880,145),fill=b.FAINT_RULE,width=2)
        if key in ('knights-k024','knights-k025'):
            who='victim'if key.endswith('k024')else'killer';sources=[]
            for i,(phase,date)in enumerate([('before','12.29'),('after','12.30')]):
                path=c.R148/(phase+'-'+who+'-character-window.png');_,crop=b.source_crop(path,[0,0,600,550]);x=40+i*465
                b.fit_text(d,(x,190),date+'：原版人物、技能与威望',450,25,b.GOLD);b.paste_fit(im,crop,(x,240,450,540));sources.append({'source':p.ref(path),'crop_xyxy':[0,0,600,550]})
        elif key=='knights-k030':
            sources=[]
            for i,(phase,side,label,rect)in enumerate([('before','left','12.29 我方11',[990,1058,1258,1372]),('after','left','12.30 我方10',[990,1080,1258,1372]),('before','right','12.29 对方19',[1315,880,1548,1372]),('after','right','12.30 对方19',[1315,880,1548,1372])]):
                path=c.R148/(phase+'-'+side+'-roster-desktop-original.png');_,crop=b.source_crop(path,rect);x=40+i*232
                b.fit_text(d,(x,190),label,226,23,b.GOLD);b.paste_fit(im,crop,(x,235,225,565));sources.append({'source':p.ref(path),'crop_xyxy':rect})
        elif key=='reinforcement-r037':
            sources=[]
            for i,(phase,date)in enumerate([('before','12.14'),('after','12.15')]):
                path=c.R149/(phase+'-width-window.png');_,crop=b.source_crop(path,[819,950,1740,1440]);y=190+i*312
                b.fit_text(d,(40,y),date+'：完整战斗窗、提示与底部',930,25,b.GOLD);b.paste_fit(im,crop,(40,y+36,930,265));sources.append({'source':p.ref(path),'crop_xyxy':[819,950,1740,1440]})
        else:
            b.fit_text(d,(40,164),'原版整帧定位',930,26,b.MUTED);b.paste_fit(im,src,(40,205,930,145))
            _,crop=b.source_crop(row['source_image'],row['crop_xyxy']);b.fit_text(d,(40,375),'完整原版战斗窗放大',930,27,b.GOLD);b.paste_fit(im,crop,(40,417,930,395));sources=[{'source':p.ref(row['source_image']),'crop_xyxy':row['crop_xyxy']}]
        d.rounded_rectangle((1015,190,1880,815),radius=18,fill=b.PANEL,outline=b.FAINT_RULE,width=2);b.fit_text(d,(1040,212),row['diagram_title'],812,32,b.GOLD);y=282
        for line in row['diagram_lines']:
            chunks=b.wrap(d,line,770,32)
            if len(chunks)>2:raise ValueError('Diagram exceeds two lines')
            for text in chunks:d.text((1050,y),text,font=b.font(32),fill=b.INK);y+=43
            y+=18
        if y>810:raise ValueError('Diagram exceeds content area')
        for i,text in enumerate(b.wrap(d,row['footer'],1790,24)):d.text((45,830+i*31),text,font=b.font(24),fill=b.MUTED)
        d.rectangle((0,900,1920,1080),fill=b.BG);d.line((0,900,1920,900),fill=b.GOLD,width=2)
        out=root/'visuals'/(key+'.png')
        with out.open('xb')as f:im.save(f,format='PNG')
        shot={**edit['utterances'][key],'image':str(out),'rendered_image':p.ref(out),'original_UI_sources':sources,'layout_revision':'a02-large-genuine-ui-crops','previous_board':p.ref(run/'visuals'/(key+'.png'))};edit['utterances'][key]=shot;receipts[key]=sources
    p.write(root/'edit.json',edit);p.write(root/'source-crop-receipts.json',receipts);p.write(root/'source-freeze.json',{'composer':p.ref(__file__),'prior_edit':p.ref(run/'edit.json'),'new_edit':p.ref(root/'edit.json')})
    print(json.dumps({'larger_original_UI_boards':len(receipts),'old_boards_preserved':True}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run',type=Path,required=True);main(a.parse_args().run)
