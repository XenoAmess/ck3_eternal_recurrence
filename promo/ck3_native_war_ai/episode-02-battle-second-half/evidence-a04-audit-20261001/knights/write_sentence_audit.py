from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTERNAL = Path("C:/Users/1/ck3-a04-mechanism-evidence-20261001/knights-attempt-02")
raw = json.loads((EXTERNAL / "input-audit.json").read_text(encoding="utf-8"))
def load(name):
    return json.loads(Path("C:/w/ep2a03/ck3_autonomous_player/src/xar_autoplayer/simulation/data", name).read_text(encoding="utf-8"))
maim = load("ck3_1_19_0_6_episode01_messina_knight_maim_replay_v3.json")
next_maim = load("ck3_1_19_0_6_episode01_messina_knight_maim_next_input.json")
selector = load("ck3_1_19_0_6_episode01_messina_knight_selector_native_parity.json")
kill = load("ck3_1_19_0_6_episode01_messina_knight_kill_writeback.json")
growth = load("ck3_1_19_0_6_episode01_day26_runtime_weights_v1.json")
next_kill = load("ck3_1_19_0_6_episode01_messina_knight_kill_next_input_v1.json")

# The source JSON carries the exact Chinese sentence and individual claims.
# These are the audit's separately assessed observations, layers and limits.
defs = [
("static-definition + historical-native", "骑士人物事件与兵团current/soft/hard伤亡是不同路径；039→040名单不变而属性变化。", "当前a08画面可示名单和勇武列；不证明历史人物。", "无超出本句的断言；不把所有人物风险当作已证。"),
("independent-real-UI", "直接审阅a08原尺寸静帧：11名骑士，第4行同名人物12勇武，第5行7勇武。", "原图可直接匹配；两个同名人物不能唯一绑定CharacterID。", "精确PTS未保存，10s只为requested seek；无历史34333身份。"),
("independent-real-UI + boundary", "单帧同时显示人数11、勇武7；并无同人前态。", "匹配当前静帧。", "本句诚实指出无时间差；无须为11→7补假画面。"),
("static-definition + historical-native + recomputation", "同版defines中每勇武damage50/toughness10；039→040有效勇武×1.75×50/10等于原生属性。", "a08是规则示意背景；未实采a08同帧效能，不能计算该人的有效属性。", "原版50/10静态定义可用；不构成每日杀人数。"),
("historical-native + saved-state-provenance", "039 d5源档D978…→d6后档9ACA…；040逐字节加载9ACA…，历史capture raw_video=null。", "历史039/040原UI未留存；实际board左a08明确标示另次示例，不能当历史。", "历史原UI缺失已口播并上屏，属于已声明画面边界。"),
("historical-native + save-readback", "039新增side1 knight_maimed_by_enemy：34333被47032致残；d6存档34333 alive_data=true/dead_data=false。", "无039事件实录；右栏原生记录可核，a08左栏另次。", "没有当前a08对应34333的前后实拍。"),
("historical-native difference", "039源列表已有47029/33435 wounded；最终2条，新增差集仅34333/47032 maimed一条。", "历史UI无；前后trace列表差集支持本句。", "不能把累计战报整份当日增量。"),
("save-readback + stock-localization", "039同源d5→d6，34333新增one_legged+wounded_1，基础勇武3→3；中文名为独腿/受伤。", "历史前后人物卡未留存；a08不显示该trait组合。", "不能把静态trait修正-4与-2直接相加解释有效净差。"),
("save-readback + executed-entry identity", "039同源47032威望300→450，基础勇武10→10；成长实际entry选中第0项。", "历史人物威望/成长前后UI未留存。", "039调整后运行时权重未直接捕获；本句仅说实际选项与存档差。"),
("byte-exact save reload + native paused input", "039保存9ACACDE3…，040 checkpoint_source同SHA；date_raw53146368、paused=true、snapshot/control/v3同revision。", "历史冷载UI无；原始native回件与capture支持。", "040为同保存状态冷载下一暂停帧，不证事件当日即时刷新时点。"),
("historical-native input", "039→040 knights24→24/regiments51→51，Reg61 current_soldiers1→1。", "历史名单UI无；a08人数11不同源，不参与此对拍。", "补画面需原档同源前后名单，不能用a08代替。"),
("historical-native input + save-readback", "34333有效勇武11→7；效能raw175000→175000/scale100000；存档基础勇武3→3。", "历史有效属性UI无；当前a08勇武7不是同人净差。", "不指定同日实际伤亡已在哪一步重算。"),
("historical-native input + arithmetic", "11×1.75×50=962.5；原生effective_damage_raw96250000/100000=962.5。", "右栏历史记录/复算；a08左栏只示人数。", "数值是属性，不是当天杀人数。"),
("historical-native input + arithmetic", "7×1.75×50=612.5；040原生effective_damage_raw61250000/100000=612.5。", "历史UI无，数据与计算同源匹配。", "当前a08没有该角色效能实采，不借图宣称其伤害612.5。"),
("historical-native input + arithmetic", "11×1.75×10=192.5→7×1.75×10=122.5；24人名册保持。", "历史右栏数据可核，当前左图另次。", "只证明本次保存态的下一暂停输入变弱。"),
("units boundary + historical-native input", "12个其他兵团current_soldiers有正常伤亡变化；damage为属性，不能等同每日杀人数。", "原生兵团差异无真实历史UI。", "归因范围诚实；不扩成整场人数差都由致残造成。"),
("historical-native selected-row identity", "020 day26/native_event_load_index11、root33437/Reg65，对应stock knight_killed。", "020原UI缺失；a02击杀通告独立。", "不得称当前a02也直接读取了选择器。"),
("historical-native candidate source + static filter/reconstruction", "020源骑士ID序列19人；勇武门槛后compact14人，原生selector count14。", "候选列表/门槛为内部值，不存在可用原版UI清单。", "只针对这次事件分支，不能外推所有骑士事件。"),
("exact-build static algorithm + native parity", "RVA0x19F4760以尾项填洞重查；fixed projector对同次v3谓词重建顺序并命中原生结果。", "内部容器顺序只能用图示，不以UI排序替代。", "无通用分布声明。"),
("native index + recomputation", "native compacted[8]=34120；稳定删除的相同index8为54140；0-based8是第9项。", "原生记录与图示匹配；a08人物行无关。", "不把UI行顺序或姓名当原生候选顺序。"),
("native local RNG state + exact-build recomputation", "counter1117324859→1117324860/salt0；复算draw31=1400813912，%14=8；无候选weight分支。", "随机数非UI/钩子直接draw字段；旁白明确复算。", "不把020 root draw26436929或070 list draw51510340混入。"),
("native selected candidate + appended BattleEvent", "020 selector word1=0x8548=34120；新增BattleEvent右侧34120，两者一致。", "无020原实录；原生trace为证。", "仅此一次选择执行对拍，currenta02 selector UNKNOWN仍保留。"),
("historical-native character boundary", "020 fire边界5：33437 death_marker=false、effective prowess4、current_regiment65且反链匹配。", "无原人物界面；左a08与右历史边界均有独立标签。", "边界5不是最终死亡状态；currenta02前边界false不能推出d27存活。"),
("historical-native character boundary + save-readback", "020 final边界6 death_marker=true、prowess2、regiment0；同run存档基础2→2。", "020原UI无；a08不构成死者画面。", "不把effective4→2称基础技能-2；不填currenta02空final行。"),
("same-run save-readback", "020 d27后档dead_data=true/alive_data=false、death_date1066.12.30/reasondeath_battle/killer34120；34120两种威望各+150。", "原版人物死因和威望UI缺失；已绑定原始与Rakaly melted bytes。", "死亡发生日12/30可存入12/31后档；不能替当前a02生命状态。"),
("independent historical attempt provenance", "070自C127…第26日源档冷载，独立raw begin/finish/v3与020分开。", "070原UI无；来源卡明确切换。", "相同源档不等于020续帧。"),
("native runtime weight bytes", "070 listcall14权重int32[40,30,15]、bytes280000001E0000000F000000、positive total85。", "内部权重无原版UI；右记录卡正确。", "不是每日死亡/成长概率或所有角色永久比例。"),
("native local RNG state + weighted-choice recomputation", "070 listcounter1462316485；draw51510340，floor(draw×85/2^31)=2；选entry0/no_op。", "旁白明确复算；原生记录实际entry身份另核。", "不使用mod85，不把根节点draw当成长抽签。"),
("direct executed entry identity", "selected_entry_identity_token等于entry_node_identity_tokens[0]；selected_growth_branch_matches_original=true。", "实际原生指针身份可核，无人物UI。", "不是仅因基础勇武未变而倒猜分支。"),
("byte-exact historical save reload + native paused input", "036保存CD0648…第27日后档；038 checkpoint_source同SHA，paused/date53146872、query revision一致。", "036/038原始名单UI无；左a08另次示例。", "不能串成020/070连续录像。"),
("historical-native roster delta", "03669团/30骑士→03868团/29骑士；ID差集仅65与33437，保留基础行逐对象一致。", "只有原生读取证明此名册；currenta02界面11→10不能替换。", "需要同源真实名单画面才可补该历史可视化。"),
("historical-native retained input + limitation", "038仍含34120，prowess7；full_casualty_state_identical_proven=false。", "历史名册/属性UI无；输入行可核。", "相同base_inputs不证明所有soft/hard/隐藏状态相同。"),
("separate-attempt provenance", "020 traceD5F044…；070 finish35ADD1…；036 trace713DB2…及后档CD0648…/038v3独立。", "三组原UI未留存；来源切换标签避免连续错觉。", "本句为必要来源边界；各attempt不能互填。"),
("independent-real-UI", "a02相邻4918/4919帧PTS232.533/232.567、同UI日期1066.12.30，骑士11→10。", "两原尺寸图直接审阅；raw clip原速，当前数据事实匹配。", "总人数11→2是另一字段；净少1不能唯一绑定33437死亡；无d27状态。"),
("independent-real-UI + unresolved edit promise", "a02 PTS233.0与233.5/235.5清晰通告，骑士10、日期12/30；243.5通知已消失但count/date保持。", "原图可读；actual a04用原速raw233.0..243.867，只有scale/pad，final842.5s未放大通告。", "机制事实受支持；旁白“我们放大”未交付。需同帧inset或标注冻结放大，不改为d27。"),
("evidence boundary", "a02无selector字段、final读取失败；实录只示当前人数/通知，不能证明020/070/036/038路径。", "独立a02实录与历史卡分离正确。", "此句诚实保留UNKNOWN，不能因为没证明历史路径而把事实UI判RED。"),
("historical-native input synthesis", "039→040致残者24人名册保留/有效属性下降；独立036→038移除33437。", "历史UI缺失明示，当前a08/a02只为各自示例。", "结论限定已核后档链；不声明currenta02d27死亡已读到。"),
("declared unknown scope", "full mutable write set/未来daily transitions/whole-battle probability均未证明；本片不讲041治疗已结束。", "来源卡准确，未配虚构治疗画面。", "其他分支、条件权重和治疗结果不是本章现有断言；不用扩为新blocker。"),
]
rows=[]
for i,(u,d) in enumerate(zip(raw["utterances"],defs),1):
    layers, observed, ui, gap=d
    rows.append({**u, "claims": [f["claim"] for f in u["facts"]], "evidence_layers": layers.split(" + "),
                 "audited_observation": observed, "native_readout_and_independent_UI_relation": ui,
                 "conclusion": "FACT_SUPPORTED_VISUAL_PROMISE_UNRESOLVED" if i==35 else "SUPPORTED_WITH_DECLARED_BOUNDARIES",
                 "unproven_mechanism_assertion_in_a04": False,
                 "gap": gap, "historical_UI_missing_is_RED": False})
inventory=raw["source_inventory"]
extra=[]
for name in ("a04-k035-842p5.png", "raw-a02-233p5.png", "raw-a02-233p5-notice-crop.png"):
    p=EXTERNAL.parent/"knights-attempt-01"/name
    b=p.read_bytes();extra.append({"path":str(p).replace("\\","/"),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest().upper()})
for name in ("raw-a02-243p5.png","raw-a02-235p5-notice-crop.png"):
    p=EXTERNAL/name;b=p.read_bytes();extra.append({"path":str(p).replace("\\","/"),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest().upper()})
summary={"schema":"ck3.a04.knights.sentence-audit.v1", "created_at_utc":datetime.now(timezone.utc).isoformat(),
         "readiness":"38_SENTENCES_AUDITED_1_VISUAL_MAPPING_ISSUE_CURRENT_NEXTDAY_STILL_UNKNOWN",
         "final_a04_timeline_range_seconds":[raw["chapter_global_start"],raw["chapter_global_start"]+raw["chapter_duration"]],
         "narration_matches_frozen_source":all(u["timeline_zh_matches"] and u["final_story_zh_matches"] for u in rows),
         "support_summary":{"sentences":38,"unsupported_mechanism_assertions_found":0,"visual_mapping_issues":1,
                            "human_1x_review_performed":False,"new_live_evidence":False},
         "source_inventory_note":"155 local files independently hashed. One incidental contact-identity original_case pin differs from the old a03 fact-pack inventory; this file is not an input to any of the 38 knight assertions or the three matching reprojects. No expected hash was refreshed to hide the mismatch.",
         "current_a02":raw["current_a02"],"historical_reprojection":raw["reprojection"],
         "input_audit_path":str(EXTERNAL/"input-audit.json").replace("\\","/"),
         "mapping_issue_evidence":extra,
         "capture_priority":[
             {"priority":1,"need":"New independent d26→d27 same-run capture: target33437 life block/death cause/killer, native roster plus actualUI date/count, source/receipt/SHA bound.","closes":"new run's nextday status; never rewrites failed currenta02"},
             {"priority":2,"need":"Same-source maim post-save target34333: actual trait/prowess/countUI under independently labeled new coldload.","closes":"visualizes saved injury state; not proof of original039 exact UI"},
             {"priority":3,"need":"k035 sameframe notification inset from source233.0–235.5 safe visible span, or explicit frozen PTS233.5 inset.","closes":"existing visual enlargement promise; no game needed"}],
         "sentences":rows,"source_inventory":inventory}
json_text=json.dumps(summary,ensure_ascii=False,indent=2)+"\n"
with (HERE/"sentence-audit.json").open("x",encoding="utf-8",newline="\n") as f:f.write(json_text)
md=["# a04 骑士章逐句证据审计（2026-10-01）","",
"38 句机制断言均有对应证据或明确边界；未发现把当前 a02 次日人物状态冒称已证的句子。k035 的‘放大通告’是实际成片未兑现的画面承诺，需修剪辑。完整原件路径、大小、SHA、逐句 claims 与实际 timeline 见同目录 `sentence-audit.json`。",
"","历史039→040、020、070、036→038均单列，原UI未留存；当前a08/a02不替它们证明因果。当前a02 final trace失败，33437次日生命状态及选择器仍UNKNOWN。旧历史证据不关闭这个缺口。",
"","a04骑士章为470.900–886.467秒。project story、最终sources/story及timeline的38句中文逐句完全一致。固定原件重投影039→040、036→038和020 selector均与冻结输出相同。155件本地文件独立哈希；旧a03 fact pack里无关contact original_case的pin与fixeda04文件不同，已保留差异，不参与本章结论。",
"","| key | 中文原句 | 原版证据与画面关系 | 结论与缺口 |","| --- | --- | --- | --- |"]
for row in rows:
    md.append("| "+" | ".join([row["key"],row["zh"],row["audited_observation"]+" "+row["native_readout_and_independent_UI_relation"],row["conclusion"]+"："+row["gap"]]).replace("|与","／与")+" |")
md+= ["","补证顺序：新独立run的33437次日状态优先；保存态人物卡/名单可视化随后。k035同帧inset可离线修复。当前a02 PTS233.0–243.867片段属案例第26日/1066-12-30，不是第27日/12-31；检查233.5与235.5帧有通告，243.5帧已消失，不能宣称全段通告持续存在。", "", "本次未启动CK3、Steam、录制器或桌面操作，未修改旧素材，未提交、推送或接收master内容。人工1×完整审片和clean span认证仍未完成。"]
with (HERE/"sentence-audit.md").open("x",encoding="utf-8",newline="\n") as f:f.write("\n".join(md)+"\n")
print(HERE/"sentence-audit.json")
