"""Fresh a08 attempt: explicitly distinguish historical A01 from current R149."""
from pathlib import Path
import argparse,copy,json,shutil
import compose_research_a08 as c
import review_story_a04 as p
def main(source,target):
    old=p.read(c.P/'project/review-story-a08-story.json');original=p.ref(c.P/'project/review-story-a08-story.json')
    u=next(u for chapter in old['chapters']if chapter['id']=='reinforcement'for u in chapter['utterances']if u['id']=='r005')
    u['zh']='要查清这一步，先看历史A01的原生记录卡；我们也从同一检查点另开本轮回放，对入口、返回和首次出伤复核。'
    u['en']='First read the historical A01 native cards. We also reload the same checkpoint independently in this run to recheck join entry, return and first damage.'
    a01=next(u for chapter in p.read(c.V7/'claim-catalog.json')['chapters']if chapter['id']=='reinforcement'for u in chapter['utterances']if u['id']=='r005')
    u['facts']=copy.deepcopy(a01['facts'])+u['facts'];old['revision']='a08-finite-case-research-closure-source-transition-a02'
    path=c.P/'project/review-story-a08-story.json';path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    previous=source/'render-attempt-a01';final=p.read(previous/'final-artifact.json');c.exact(final)
    require=p.read(previous/'audit/machine-report.json');c.require(require['passed']is True and require['artifact']['sha256']==final['sha256'],'Previously audited exact render required')
    c.V7=previous;c.AUDIO=source
    c.prepare(target)
    p.write(target/'source-transition-correction.json',{'previous_frozen_authoring':original,'new_authoring':p.ref(path),'previous_render':final,'previous_narration':str(source),'actual_runtime_overrides':{'V7':str(previous),'AUDIO':str(source)},'scope':'Only r005 narration changes; historical A01 cards stay historical and R149 new UI keeps its actual source labels.','human_signoff':'not-provided'})
    c.narrate(target)
    shutil.copyfile(previous/'edit.json',target/'edit.json')
    p.write(target/'edit-input-freeze.json',{'previous_exact_edit':p.ref(previous/'edit.json'),'new_exact_edit':p.ref(target/'edit.json'),'new_UI_boards_retained':25})
    c.render(target)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--source-run',required=True,type=Path);a.add_argument('--run',required=True,type=Path);args=a.parse_args();main(args.source_run,args.run)
