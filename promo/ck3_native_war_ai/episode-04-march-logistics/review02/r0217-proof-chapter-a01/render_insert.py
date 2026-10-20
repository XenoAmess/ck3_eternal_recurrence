"""One R0217 continuous-window review insert, using existing music and no TTS."""
from dataclasses import replace
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
from PIL import ImageFont
from xar_promo.render import RenderOptions,plan_render,ass_burn_in_filter,execute_render_plan
from xar_promo.process import run_command
from context import *

MOVIE=ROOT/'work-a01/R0217-COUNTY-17-DEBITS-236-SUBTOTAL-36s-REVIEW-a01.mp4'
MANIFEST=ROOT/'run-a01/run-manifest.json'

def stamp(seconds):
 c=round(seconds*100); h,c=divmod(c,360000); m,c=divmod(c,6000); s,c=divmod(c,100); return f'{h}:{m:02d}:{s:02d}.{c:02d}'
def main():
 sys.stdout.reconfigure(encoding='utf-8')
 cap=admitted()
 # Frozen by the producer only after Root's direct view of the six raw JPEGs.
 choice=json.loads((ROOT/'ROOT-WINDOW-CHOICE.actual.json').read_bytes())
 assert choice['machine_id']==MACHINE and choice['run_id']==RUN_ID and choice['Root_direct_raw_samples_reviewed'] is True
 start=float(choice['source_start_seconds']); game=float(choice['game_seconds']); card=float(choice['card_seconds']); duration=game+card
 assert duration==36 and 0<=start<start+game<=83.133 and 3<=card<=8
 assert pin(MUSIC)=={'path':str(MUSIC),'bytes':30726160,'sha256':'fda2464fb4b06cd9a2f0196e5c40ca311eb693ec263c996e4ccc24a6ada8803f'}
 work=MOVIE.parent; assert not work.exists(); work.mkdir()
 zh=[ '画面军队计数：6746 → 6510（净−236）', '实体兵槽：6741 → 6505；与画面计数分列。', '17次已核实的县进入实际扣兵，小计236。', '5个空DATA调用当前v2排除；县总额仍未知。' ]
 en=[ 'UI count: 6,746 to 6,510, net -236.', 'Physical soldiers: 6,741 to 6,505. These are separate readouts.', '17 verified county-entry debit calls; subtotal: 236.', 'Five empty-DATA calls are excluded by v2. The county total is unknown.' ]
 font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',38); english=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
 assert all(font.getlength(t)<=1680 for t in zh) and all(english.getlength(t)<=1680 for t in en)
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CN,Microsoft YaHei,38,&H00E1F2F8,&H00E1F2F8,&H00131820,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,8,120,120,0,1
Style: EN,Arial,25,&H00ACD2E1,&H00ACD2E1,&H00131820,&H00000000,0,0,0,0,100,100,0,0,1,1,0,8,120,120,0,1
Style: Label,Microsoft YaHei,22,&H006CBFE9,&H006CBFE9,&H00131820,&H00000000,0,0,0,0,100,100,0,0,1,1,0,7,30,30,0,1
Style: Card,Microsoft YaHei,52,&H006CBFE9,&H006CBFE9,&H00131820,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,8,120,120,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 lines=[header,
  f'Dialogue: 9,0:00:00.00,{stamp(duration)},Label,draft,0,0,0,,{{\\an9\\pos(1870,35)}}审阅草稿',
  f'Dialogue: 2,0:00:00.00,{stamp(game)},Label,scope,0,0,0,,{{\\an7\\pos(45,880)}}R0217 · 同一场第七日记录']
 for i,(cn,eng) in enumerate(zip(zh,en)):
  a=i*game/4; b=(i+1)*game/4
  lines.extend([f'Dialogue: 5,{stamp(a)},{stamp(b)},CN,,0,0,0,,{{\\an8\\pos(960,925)}}{cn}',f'Dialogue: 4,{stamp(a)},{stamp(b)},EN,,0,0,0,,{{\\an8\\pos(960,993)}}{eng}'])
 a,b=stamp(game),stamp(duration)
 lines.extend([
  f'Dialogue: 4,{a},{b},Card,,0,0,0,,{{\\an8\\pos(960,150)}}已核实17次县进入实际扣兵',
  f'Dialogue: 5,{a},{b},Card,,0,0,0,,{{\\an8\\pos(960,330)\\fs104}}小计236人',
  f'Dialogue: 5,{a},{b},Card,,0,0,0,,{{\\an8\\pos(960,550)\\fs54}}县总额仍未知',
  f'Dialogue: 4,{a},{b},EN,,0,0,0,,{{\\an8\\pos(960,690)\\fs32}}17 verified calls. Subtotal 236. County total unknown.',
  f'Dialogue: 3,{a},{b},Label,,0,0,0,,{{\\an8\\pos(960,835)\\fs30}}5个空DATA调用当前v2排除；不以小计追认县总额。',
  f'Dialogue: 3,{a},{b},Label,,0,0,0,,{{\\an8\\pos(960,935)\\fs24}}同一场第七日实录 · 未授整卡完成、正式动态或人工签核'])
 ass=work/'captions.ass'
 with ass.open('x',encoding='utf-8',newline='\n') as f: f.write('\n'.join(lines)+'\n')
 config={'format_version':1,'kind':'xar_promo_project_config','project':{'id':'ck3-e04-r0217-narrow-debit-subtotal-review','title':'R0217：17次扣兵与236人小计审阅插片'},'pipeline':{'adapter':'generic','preset':'default'},'locales':{'narration':'zh-CN','subtitles':['zh-CN','en']},'constraints':{'duration_limit_seconds':40},'chapters':[{'id':'r0217-proof','type':'documentary','state':'planned','title':{'zh-CN':'同一场第七日县进入扣兵小计'},'cues':[{'id':'r0217-proof','narration':{'zh-CN':'无口播；只复用原有配乐与画面文字。'},'subtitles':{'zh-CN':' '.join(zh),'en':' '.join(en)}}]}]}
 write('project/promo-project.json',config)
 cli('config-validate','validate',ROOT/'project/promo-project.json','--json')
 cli('start-run','start-run',ROOT/'project/promo-project.json','--run-id','r0217-proof-review-a01','--run-directory',MANIFEST.parent)
 cli('run-started-validate','validate',MANIFEST,'--json')
 options=RenderOptions(1920,1080,30,duration,preset='veryfast',crf=21)
 plan=plan_render(ffmpeg=FFMPEG,video_input=RAW,audio_input=MUSIC,partial_output=work/'movie.partial.mp4',final_output=MOVIE,audit_directory=work/'audit',options=options,ass_path=ass,start_seconds=start,working_directory=ROOT)
 command=plan.commands[0]; argv=list(command.spec.argv); graph_index=argv.index('-filter_complex')+1
 burn=ass_burn_in_filter(ass)
 graph=(f'[0:v]trim=duration={game:.6f},setpts=PTS-STARTPTS,scale=1536:864:flags=lanczos,pad=1920:1080:192:0:color=0x211813,setsar=1,fps=30,drawbox=x=0:y=864:w=1920:h=216:color=0x35291F:t=fill,drawbox=x=0:y=864:w=1920:h=3:color=0xCBA56A:t=fill,format=yuv420p[game];'
  f'[2:v]trim=duration={card:.6f},setpts=PTS-STARTPTS,setsar=1,fps=30,format=yuv420p[card];'
  f'[game][card]concat=n=2:v=1:a=0,fps=30,trim=duration={duration:.6f},setpts=PTS-STARTPTS,{burn},format=yuv420p[v];'
  f'[1:a]atrim=duration={duration:.6f},asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume=-17dB,afade=t=in:st=0:d=1,afade=t=out:st={duration-3:.6f}:d=3[a]')
 argv[graph_index]=graph
 argv[graph_index-1:graph_index-1]=['-f','lavfi','-i',f'color=c=0x211813:s=1920x1080:r=30:d={card:.6f}']
 argv[1:1]=['-threads','1','-filter_complex_threads','1']
 argv[-1:-1]=['-threads:v','1','-frames:v',str(int(duration*30)),'-profile:v','high','-level:v','4.0','-video_track_timescale','15360']
 plan=replace(plan,commands=(replace(command,spec=replace(command.spec,argv=tuple(argv))),))
 write('PLAN.actual.json',{'schema':'xar.e04.r0217-proof-render-plan.v1','machine_id':MACHINE,'observed_at_utc':now().isoformat(),'run_id':RUN_ID,'admission':pin(CAP),'intake':pin(ROOT/'INTAKE.actual.json'),'Root_window_choice':pin(ROOT/'ROOT-WINDOW-CHOICE.actual.json'),'raw':cap['input_raw'],'music':pin(MUSIC),'ASS':pin(ass),'implementation':pin(Path(__file__)),'source_window':{'start_seconds':start,'end_seconds':start+game,'continuous_source':True,'speed':1.0},'game_seconds':game,'card_seconds':card,'total_seconds':duration,'frames':int(duration*30),'argv':argv,'exact_Chinese_statements':zh,'new_TTS_calls':0,'other_run_footage':False,'source_raw_QA_repeated':False,'county_total_debit':None,'R04_entire_card_closed':False,'formal_dynamic_credit_added':0,'human_signoff':False})
 execute_render_plan(plan,command_runner=lambda spec,*,audit_directory:run_command(spec,audit_directory=audit_directory,run=guarded_run))
 assert identity(RAW)==cap['input_raw_fresh_identity']
 write('ENCODE.actual.json',{'machine_id':MACHINE,'observed_at_utc':now().isoformat(),'run_id':RUN_ID,'movie':pin(MOVIE),'plan':pin(ROOT/'PLAN.actual.json'),'status':'ENCODED_PENDING_NEW_BYTES_QA','usage':usage(),'new_TTS_calls':0,'human_signoff':False,'formal_dynamic_credit_added':0})
 cli('preserve-movie','preserve',MOVIE,'--run-manifest',MANIFEST,'--artifact-id','r0217-proof-review-a01','--collection','derived','--role','deliverable')
 cli('preserved-run-validate','validate',MANIFEST,'--json')
 print(json.dumps({'movie':pin(MOVIE),'plan':pin(ROOT/'PLAN.actual.json'),'usage':usage()},ensure_ascii=False))

if __name__=='__main__': main()
