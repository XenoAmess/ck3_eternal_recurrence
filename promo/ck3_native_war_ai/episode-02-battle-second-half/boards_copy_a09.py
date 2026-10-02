"""Update source-bound war boards for the complete a09 editorial audit."""
from pathlib import Path
import copy,json
from PIL import Image,ImageDraw
import review_story_a04 as p
import compose_review_boards_a04 as b
from compose_copy_bgm_a09 import PREVIOUS,R148,bykey,require

DETAILS={
 'pursuit-p030':('非零掩护：公式已知，实机待补',['败方 S = Σ(有效掩护 × 当天软伤)','现有甲05样本：S = 0','尚无非零 S 的同帧输入与次日账','本片不将零掩护对拍推广到此分支']),
 'pursuit-p030a':('两种非零掩护分支',['T = Σ(有效坚韧 × 当天软伤)','P = 0.5 × Σ(胜方有效追击 × 当前量)','额外 = max(P − S, 0)','P > S：保底 = 0.05T','P ≤ S：保底 = max(0.05T − S + P, 0.01T)']),
 'pursuit-p030b':('下一次实机要采齐什么',['分别取得 0 < S < P 与 S ≥ P 的样本','同帧：双侧属性、修正、顺序与冻结池','次日：逐团软伤与可读硬伤','原始整数、截断与尾账逐项对拍','状态：两种分支的原版样本仍待补']),
 'knights-k004':('骑士战斗力如何进入属性',['E = 界面骑士战斗力百分数 ÷ 100','伤害 = 有效勇武 × 50 × E','坚韧 = 有效勇武 × 10 × E','100% = 1 倍；175% = 1.75 倍','这里算属性，不能直接解释成击杀人数']),
 'knights-k004a':('175% 的每点勇武收益',['骑士战斗力：175% → E = 1.75','每点有效勇武：50 × 1.75 = 87.5 伤害','每点有效勇武：10 × 1.75 = 17.5 坚韧','后段以历史039→040原生读数核验']),
 'knights-k006':('若弗鲁瓦被穆罕默德致残',['历史039：若弗鲁瓦 Geoffroy｜34333','对手：穆罕默德 Muhammad｜47032','新增战报：致残；若弗鲁瓦仍存活','名字来自同源存档与原版汉化绑定']),
 'knights-k009':('穆罕默德：威望增加，成长抽空',['历史039：穆罕默德 Muhammad｜47032','威望：300 → 450（+150）','成长列表：选中第0项空条目','基础勇武仍为10；不能宣称勇武成长']),
 'knights-k012':('若弗鲁瓦：人数保留，有效勇武下降',['若弗鲁瓦 Geoffroy｜34333','有效勇武：11 → 7','骑士战斗力：175% → E = 1.75（未变）','保存中的基础勇武：3 → 3','历史039→040原生属性读数']),
 'knights-k013':('伤前伤害：11 × 50 × 1.75',['若弗鲁瓦｜34333｜伤前有效勇武11','伤害 = 11 × 50 × 1.75 = 962.5','同帧原生伤害属性：962.5','历史039：不是每日击杀人数']),
 'knights-k014':('伤后伤害：7 × 50 × 1.75',['若弗鲁瓦｜34333｜伤后有效勇武7','伤害 = 7 × 50 × 1.75 = 612.5','零四零原生伤害属性：612.5','致残后人数仍为1，伤害属性下降']),
 'knights-k015':('坚韧也受骑士战斗力影响',['伤前：11 × 10 × 1.75 = 192.5','伤后：7 × 10 × 1.75 = 122.5','两值分别对上历史039→040原生读数','一人规模未变；伤害与坚韧均下降']),
 'knights-k017':('本轮击杀：图尔吉塞与阿姆鲁',['R0148｜1066.12.29 → 12.30','死者：图尔吉塞 Turgise｜33437','击杀者：阿姆鲁 Amr｜34120','与前段历史致残样本分开']),
 'knights-k026':('成长在死亡提交之前',['先由骑士选择器确定阿姆鲁｜34120','威望写入 +150 → 独立成长抽签','成长结束 → 战报与死亡请求 → 提交','本轮成长实采：第56项空条目','其他成长结果以下按原版静态规则解释']),
 'knights-k026a':('成长抽签的三个结果',['原版静态规则：基础权重 60 : 30 : 10','空条目：没有成长','第二项：基础勇武 +1','第三项：添加或推进剑术大师','实际权重还受人物与文化条件修正']),
 'knights-k026b':('空条目的权重随学识变化',['空条目：60 − 2 × 击杀者有效学识','拥有 warfare_legacy_3 时，再 × 0.5','基础勇武 +1：脚本权重保持30','三项归一化后才得到条件下的抽取占比','权重不是击杀概率']),
 'knights-k026c':('剑术大师：条件如何加权',['初始10；军事教育 +5','战斗教育：+4 / +8 / +12 / +16','已有剑术大师 +15；精明/良好体魄各 +10','良好智力：+5 / +15 / +30','对应文化 ×3；经验≥100则整项权重归零']),
 'knights-k026d':('剑术大师项不等于勇武加十',['没有剑术大师：添加该特质','已有且经验<100：经验 +10','经验50与100：进入更高等级','+10写入的是经验，不是基础勇武','此处是原版静态规则；本轮抽中空条目']),
 'knights-k026e':('历史实采权重：40 : 30 : 15',['另一份同版第26日回放','实采权重：40、30、15；总和85','这是包含人物条件后的历史结果','不能移作本轮R0148的三个权重']),
 'knights-k026f':('35.29% 对应哪一个条件',['历史第26日：30 ÷ 85 ≈ 35.29%','只表示当时勇武+1项的抽取占比','历史实采选第0项；本轮也抽到空条目','成长抽签的占比不是死亡风险']),
 'knights-k026g':('成长之后还有骑士功绩分支',['原版静态规则：领主与标记条件','可能记录功绩，供玩家领主后续奖励','本轮 followup57 没有执行子效果','没有执行不等于所有人物都不会执行']),
}

def draw_large(run,key,row,old):
    """Retain readable original crops for the finite character/roster cases."""
    if key not in ('knights-k024','knights-k025','knights-k030','reinforcement-r037'):
        return b.board(run,key,row)
    im=Image.new('RGB',(1920,1080),b.BG);d=ImageDraw.Draw(im);sources=old['original_UI_sources']
    b.fit_text(d,(40,28),row['title'],1830,45,b.INK);b.fit_text(d,(44,100),row['case'],1820,26,b.GOLD);d.line((40,145,1880,145),fill=b.FAINT_RULE,width=2)
    for i,item in enumerate(sources):
        _,crop=b.source_crop(item['source']['path'],item['crop_xyxy'])
        if key=='reinforcement-r037':x,y,w,h=40,190+i*312,930,265;label=['12.14 完整原版战斗窗','12.15 完整原版战斗窗'][i]
        elif len(sources)==4:x,y,w,h=40+i*232,190,225,565;label=['12.29 我方11','12.30 我方10','12.29 对方19','12.30 对方19'][i]
        else:x,y,w,h=40+i*465,190,450,540;label=['12.29 原版人物页','12.30 原版人物页'][i]
        b.fit_text(d,(x,y),label,w,24,b.GOLD);b.paste_fit(im,crop,(x,y+40,w,h))
    d.rounded_rectangle((1015,190,1880,815),radius=18,fill=b.PANEL,outline=b.FAINT_RULE,width=2);b.fit_text(d,(1040,212),row['diagram_title'],812,32,b.GOLD);y=282
    for line in row['diagram_lines']:
        lines=b.wrap(d,line,770,32);require(len(lines)<=2,'Diagram too wide')
        for text in lines:d.text((1050,y),text,font=b.font(32),fill=b.INK);y+=43
        y+=18
    require(y<=810,'Diagram too tall')
    footer=b.wrap(d,row['footer'],1790,24);require(len(footer)<=2,'Footer too tall')
    for i,text in enumerate(footer):d.text((45,830+i*31),text,font=b.font(24),fill=b.MUTED)
    d.rectangle((0,900,1920,1080),fill=b.BG);d.line((0,900,1920,900),fill=b.GOLD,width=2)
    out=run/'visuals'/(key+'.png');out.parent.mkdir(exist_ok=True)
    with out.open('xb') as f:im.save(f,format='PNG')
    return {**old,'image':str(out),'rendered_image':p.ref(out),'spec':row,'original_UI_sources':sources,'layout_revision':'a09-readable-original-ui'}

def make_boards(run):
    story=p.read(run/'sources/story.json');oldstory=bykey(p.read(PREVIOUS/'timeline.json'));edit=copy.deepcopy(p.read(PREVIOUS/'edit.json'));specs={};retained=[]
    for c in story['chapters']:
        for u in c['utterances']:
            key=c['id']+'-'+u['id'];old=edit['utterances'].get(key);prior=oldstory.get(key)
            changed=prior is None or u['zh']!=prior['zh'] or u['en']!=prior['en'] or key in DETAILS
            if not changed:retained.append(key);continue
            if old and old.get('kind')=='raw-excerpt':
                old['evidence']=u['facts'];old['a09_copy_reviewed']=True;continue
            if old and 'spec' in old:row=copy.deepcopy(old['spec'])
            elif c['id']=='pursuit':row=copy.deepcopy(edit['utterances']['pursuit-p030']['spec'])
            else:row=copy.deepcopy(edit['utterances']['knights-k026']['spec'])
            if key in DETAILS:
                row['title'],row['diagram_lines']=DETAILS[key];row.pop('highlight_line',None)
            if key.startswith('knights-k026') and key!='knights-k026':
                row.update({'case':'原版静态成长规则｜历史实采另行标明','diagram_title':'原版规则与样本范围','footer':'左栏是本轮原版画面定位；右栏规则来自原版脚本。非空成长分支未在本轮执行。'})
                if key in ('knights-k026e','knights-k026f'):row['case']='历史第26日实采｜与本轮R0148分开'
            if key in ('pursuit-p030','pursuit-p030a','pursuit-p030b'):
                row.update({'case':'原版静态公式｜非零败方掩护实机仍待补','diagram_title':'非零掩护：已知规则与验证缺口','footer':'左栏保留甲05零掩护实录；右栏是原版静态规则，不能充作非零掩护画面。'})
            shot=draw_large(run,key,row,old or {});shot['evidence']=u['facts'];shot['a09_copy_reviewed']=True
            if old and old.get('raw_notice_inset'):shot['raw_notice_inset']=old['raw_notice_inset']
            edit['utterances'][key]=shot;specs[key]=row
    require(set(edit['utterances'])==set(bykey(story)),'Visual coverage differs from 177 cues')
    edit.update({'kind':'a09-full-copy-audit-brown-gold','human_signoff':'not-provided','production_clean_admission':False})
    p.write(run/'board-spec.json',specs);p.write(run/'edit.json',edit)
    pins=sorted({Path(s['image']) for s in edit['utterances'].values() if s['kind']!='raw-excerpt'})
    p.write(run/'visual-input-freeze.json',[p.ref(path) for path in pins]);p.write(run/'board-coverage.json',{'new_boards':len(specs),'retained_reviewed_keys':retained,'total':len(edit['utterances']),'palette':[b.BG,b.PANEL,b.GOLD],'original_timed_notice_retained':edit['utterances']['knights-k035']['raw_notice_inset']})
    print(json.dumps({'new_boards':len(specs),'total':len(edit['utterances'])}),flush=True)
