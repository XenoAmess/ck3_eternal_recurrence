"""Retain first candidate and clarify the static 175% example in a fresh run."""
from pathlib import Path
import argparse,copy,json
import compose_copy_bgm_a09 as c
import review_story_a04 as p
import compose_review_boards_a04 as b

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--previous',required=True,type=Path);a.add_argument('--run',required=True,type=Path);args=a.parse_args()
    c.PREVIOUS=args.previous;c.prepare(args.run);c.narrate(args.run)
    edit=copy.deepcopy(p.read(args.previous/'edit.json'));key='knights-k004a';old=edit['utterances'][key];row=copy.deepcopy(old['spec'])
    row.update({'case':'原版静态公式｜175% 教学示例','diagram_title':'骑士战斗力倍率示例','ui_label':'左栏只作原版界面定位','footer':'175%是计算示例；历史039→040的175%原生读数稍后对拍。左栏不作本轮175%的证据。'})
    shot=b.board(args.run,key,row);shot['evidence']=old['evidence'];shot['a09_copy_reviewed']=True;edit['utterances'][key]=shot
    p.write(args.run/'edit.json',edit);p.write(args.run/'board-spec.json',{key:row});p.write(args.run/'board-label-revision.json',{'reason':'Explicitly separate teaching175% example from current R0148 contextual UI','old_board':old['rendered_image'],'new_board':shot['rendered_image'],'previous_candidate':p.read(args.previous/'final-artifact.json')})
    p.write(args.run/'visual-input-freeze.json',[p.ref(path) for path in sorted({Path(s['image']) for s in edit['utterances'].values() if s['kind']!='raw-excerpt'})])
    c.render(args.run)
