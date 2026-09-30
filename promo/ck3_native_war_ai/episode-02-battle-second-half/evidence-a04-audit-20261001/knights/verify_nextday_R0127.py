"""Independent read-only review of preserved R0127 evidence; no CK3 calls."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE=Path(__file__).resolve().parent
ROOT=Path("C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-nextday-live-20261001-a03")
INDEX=HERE/"nextday-live-R0127.json"
STATUS=ROOT/"strict-save-check-attempt-01/saved-status-receipt.json"
EXPECTED_RUN="native-29829-f83be45dbbd9"
checks=[]
inventory={}
def read(p):return json.loads(Path(p).read_text(encoding="utf-8-sig"))
def ident(p):
    p=Path(p).resolve()
    if str(p) not in inventory:
        with p.open("rb") as stream:sha=hashlib.file_digest(stream,"sha256").hexdigest().upper()
        inventory[str(p)]={"path":str(p),"bytes":p.stat().st_size,"sha256":sha}
    return inventory[str(p)]
def check(name,condition,detail=None):
    checks.append({"name":name,"passed":bool(condition),"detail":detail})
def bind(val,name):
    actual=ident(val["path"])
    check(name,actual["sha256"]==val["sha256"].upper() and actual["bytes"]==val["bytes"],actual)
    return actual
def write_new(p,val):
    with p.open("x",encoding="utf-8",newline="\n") as stream:
        json.dump(val,stream,ensure_ascii=False,indent=2);stream.write("\n")
check("sealed_supplement_index",ident(INDEX)["bytes"]==1619186 and ident(INDEX)["sha256"]=="A9EE8C44927BEB4882019AC23DEE5A8DCA8C81167A34D41D9DF444B925C6D0EE")
check("strict_receipt_exact_bytes",ident(STATUS)["bytes"]==6984 and ident(STATUS)["sha256"]=="44663063AAA1E99D3C7959EBB45B17DA180B88707841BFA74432BCEC35A47722")
index,status=read(INDEX),read(STATUS)
check("run_identity",index["run_id"]=="desktop-3fevhd2-1c74096080--vanilla--R0127" and index["episode_run_id"]==EXPECTED_RUN and status["expected_episode_run_id"]==EXPECTED_RUN)
check("strict_status_scope",status["status"]=="SAVED_NEXTDAY_STATUS_OBSERVED" and status["saved_nextday_status"]=="DEAD" and status["target_character_id"]==33437 and status["old_a02_status"]=="UNKNOWN" and status["live_targeted_query"] is False)
for label,val in status["source_input"].items():bind(val,"strict_source_"+label)
for label,val in status["evidence"].items():bind(val,"strict_evidence_"+label)
for label in ("parser","rakaly"):bind(status[label],"pinned_"+label)
check("fixed_reader_pin",status["parser"]["sha256"]=="E80A2C025584528766B4C4BB73C8696B39525FCA52F27454B1FB26C9B4B52F30")
check("fixed_rakaly_pin",status["rakaly"]["sha256"]=="E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D")
spec=importlib.util.spec_from_file_location("r0127_frozen_saved_character_reader",status["parser"]["path"])
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
reparsed=[]
for i,val in enumerate(status["states"]):
    bind(val["save"],f"native_save_{i}");bind(val["melted"],f"preserved_melted_{i}")
    text=Path(val["melted"]["path"]).read_text(encoding="utf-8-sig")
    state=reader._character_snapshot(text,33437)
    check(f"independent_character_reparse_{i}",state==val["state"],state)
    meta_dates=re.findall(r"^\tmeta_date=([^\n]+)$",text,re.M)
    block=re.findall(r"^\t33437=\{\n(.*?)^\t\}",text,re.M|re.S)[0]
    direct_regiment_fields=re.findall(r"^\t+regiment=([^\n]+)",block,re.M)
    reparsed.append({"character":state,"meta_dates":meta_dates,"direct_regiment_field_values":direct_regiment_fields,
                     "save":val["save"],"melted":val["melted"]})
    argv=read(ROOT/f"strict-save-check-attempt-01/{'before' if i==0 else 'after'}-melt-command.json")["argv"]
    check(f"actual_melt_argv_{i}",argv==[status["rakaly"]["path"],"melt",val["save"]["path"],"--unknown-key","stringify","--format","ck3","--out",val["melted"]["path"]],argv)
    ident(ROOT/f"strict-save-check-attempt-01/{'before' if i==0 else 'after'}-melt-command.json")
    ident(ROOT/f"strict-save-check-attempt-01/{'before' if i==0 else 'after'}-melt.stdout.log")
    ident(ROOT/f"strict-save-check-attempt-01/{'before' if i==0 else 'after'}-melt.stderr.log")
check("unique_life_transition",reparsed[0]["character"]["alive_data_present"] is True and reparsed[0]["character"]["dead_data_present"] is False and reparsed[1]["character"]["alive_data_present"] is False and reparsed[1]["character"]["dead_data_present"] is True)
check("exact_saved_death_fields",{k:reparsed[1]["character"][k] for k in ("death_date","death_reason","killer_character_id")}=={"death_date":"1066.12.30","death_reason":"death_battle","killer_character_id":34120})
check("saved_base_prowess_unchanged",reparsed[0]["character"]["base_skill_values"][-1]==2 and reparsed[1]["character"]["base_skill_values"][-1]==2)
check("saved_before_regiment",reparsed[0]["character"]["regiment_id"]==65)
check("civil_dates_in_actual_saves",reparsed[0]["meta_dates"]==["1066.12.29"] and reparsed[1]["meta_dates"]==["1066.12.30"])
preflight,readback=(read(status["evidence"][k]["path"]) for k in ("preflight","readback"))
check("source_load_admitted",preflight["result"]=="READY_FOR_BOUNDED_LIVE_ATTEMPT" and readback["postcondition_verified"] is True)
for label,row in (("preflight",preflight["checkpoint_source"]),("readback",readback["source_checkpoint"])):
    check(label+"_source_pair",row["actor"]==29829 and row["date_raw"]==53146848 and row["source_episode_run_id"]=="native-29829-78c0d8f4b8a2" and row["save"]["sha256"]==status["source_input"]["save"]["sha256"] and row["receipt"]["sha256"]==status["source_input"]["receipt"]["sha256"])
request_rows=[]
for p in sorted((ROOT/"ck3-output/interactive-requests").glob("*.json")):
    req=read(p);ident(p)
    rp=ROOT/"ck3-output/interactive-requests-responses"/p.name
    res=read(rp);ident(rp)
    bind(res["request"],"request_bytes_"+p.stem)
    driver=res.get("driver_state",{})
    token=[driver.get(k) for k in ("pipe_name","connection_generation","bridge_pid")]
    check("driver_identity_"+p.stem,token==status["native_connection"],token)
    request_rows.append({"name":p.name,"request":req,"response":res})
byname={r["name"]:r for r in request_rows}
for label,date,snapname,savename,controlname in (
    ("before",53146848,"e2-05-d26-pre-advance-snapshot.json","e2-05-d26-before-save.json","e2-05-d26-native-control.json"),
    ("after",53146872,"new-d27-snapshot.json","new-d27-save.json","new-d27-native-control.json")):
    snap=byname[snapname]["response"]["body"];save=byname[savename]["response"]["body"];control=byname[controlname]["response"]["body"]
    check(label+"_snapshot_identity",snap["paused"] is True and snap["date_raw"]==date and snap["played_character"]["character_id"]==29829 and snap["episode_run_id"]==EXPECTED_RUN)
    check(label+"_save_revision",byname[savename]["request"]["arguments"]["expected_revision"]==snap["revision"],{"snapshot_revision":snap["revision"],"save_request":byname[savename]["request"]})
    check(label+"_control_revision",control["accepted"] is True and control["queried_revision"]==snap["revision"] and byname[controlname]["request"]["arguments"]["expected_revision"]==snap["revision"])
    checkpoint=save["checkpoint"]
    check(label+"_native_checkpoint",save["accepted"] is True and checkpoint["status"]=="saved" and checkpoint["date_raw"]==date and checkpoint["episode_character_id"]==29829 and checkpoint["episode_run_id"]==EXPECTED_RUN and checkpoint["sha256"].upper()==status["states"][0 if label=="before" else 1]["save"]["sha256"] and checkpoint["size"]==status["states"][0 if label=="before" else 1]["save"]["bytes"])
advances=[r for r in request_rows if r["request"].get("tool")=="ck3_execute_step" and r["request"].get("arguments",{}).get("step")=="life-advance"]
saves=[r for r in request_rows if r["request"].get("tool")=="ck3_save_checkpoint"]
check("one_advance_two_checkpoint_requests",len(advances)==1 and len(saves)==2)
advance=advances[0]["response"]["body"]
check("native_exact_one_day",advances[0]["response"]["result"]=="CALL_COMPLETED" and advance["starting_date_raw"]==53146848 and advance["ending_date_raw"]==53146872 and advance["elapsed_days"]==1 and advance["requested_horizon_days"]==1 and advance["paused"] is True)
source_snap=byname["d26-before-one-day-snapshot.json"]["response"]["body"]
check("advance_bound_to_saved_paused_state",source_snap["paused"] is True and source_snap["date_raw"]==53146848 and source_snap["revision"]==5 and advances[0]["request"]["arguments"]["expected_revision"]==5)
intent=read(ROOT/"evidence/one-day-intent.json");ident(ROOT/"evidence/one-day-intent.json")
finish=byname["knight-new-trace-finish.json"]["response"]
managed=finish["body"]["managed_trace"];trace=managed["trace"];checkpoint=managed["managed_checkpoint"]
check("trace_flags_retained",finish["body"]["accepted"] is True and finish["body"]["production_trace_ready"] is False and trace["status"]=="failed" and trace["failure_flags"]==1040)
check("managed_checkpoint_one_day",checkpoint["exact_one_day_observed"] is True and checkpoint["boundary_dates_match_checkpoint"] is True and checkpoint["detours_uninstalled"] is True and checkpoint["before"]["date_raw"]==53146848 and checkpoint["after"]["date_raw"]==53146872 and checkpoint["before"]["paused"] is True and checkpoint["after"]["paused"] is True and checkpoint["before"]["managed_daily_sequence_token"]==6100103 and checkpoint["after"]["managed_daily_sequence_token"]==6100103)
trace_summary={"outer_accepted":finish["body"]["accepted"],"outer_status":finish["body"]["status"],"status":trace["status"],"failure_flags":trace["failure_flags"],"record_count":trace["record_count"],"managed_checkpoint":checkpoint,
    "record_summaries":[{k:r.get(k) for k in ("boundary","capture_failure_flags","native_date_raw","full_mutable_transition_bundle_complete")} for r in trace["records"]],
    "selector_evidence_verified":False,"sole_causation_verified":False}
ui=[]
for label,date in (("d26-before","1066.12.29"),("d27-after","1066.12.30")):
    p=ROOT/"evidence"/(label+"-window.png");raw=p.read_bytes();width,height=struct.unpack(">II",raw[16:24])
    receipt=read(ROOT/"evidence"/(label+"-window-receipt.json"));ident(ROOT/"evidence"/(label+"-window-receipt.json"));bind(receipt["image"],label+"_png")
    check(label+"_image_identity",width==1024 and height==768 and receipt["pid"]==4496 and receipt["hwnd"]==264284 and receipt["mouse_inputs"]==0)
    ui.append({"image":ident(p),"width":width,"height":height,"pid":receipt["pid"],"hwnd":receipt["hwnd"],"direct_original_pixel_review":True,
               "observed_date":date,"paused_label_visible":True,"target_character_card_visible":False,"battle_knights_roster_visible":False,"death_notification_visible":False})
capture=read(ROOT/"ck3-output/capture-report.json");session=read(ROOT/"ck3-output/session-result.json")
ident(ROOT/"ck3-output/capture-report.json");ident(ROOT/"ck3-output/session-result.json")
sdk=read(index["sdk_completion"]["path"]);bind(index["sdk_completion"],"sdk_completion")
check("no_video_clean_span",capture["raw_video"] is None and capture["clean_spans"]==[] and capture["gameplay_recorder"]["state"]=="NOT_STARTED" and capture["human_1x_review_performed"] is False)
check("managed_process_cleanup",session["pid"]==4496 and session["ok"] is True and session["shutdown"]["cleanup_proven"] is True and session["shutdown"]["tree_gone"] is True and session["shutdown"]["job_active_processes_final"]==0 and session["shutdown"]["final_ck3_inventory"]["processes"]==[])
check("warmup_cleanup",session["frontend_first_warmup"]["warmup_shutdown"]["cleanup_proven"] is True and session["frontend_first_warmup"]["warmup_shutdown"]["tree_gone"] is True)
check("sdk_job_and_process_gates",sdk["identity_matches_profile"] is True and not sdk["process_gate_errors"] and all(not v for v in sdk["process_gates"].values()) and len(sdk["jobs"])==1 and sdk["jobs"][0]["state"]=="exited" and sdk["jobs"][0]["exit_code"]==0)
release_path=Path("C:/Users/1/ck3-a04-mechanism-evidence-20261001/root-attempt-03/knight-screen-release.json")
release=read(release_path);ident(release_path);released= json.loads(release["stdout"])
check("screen_lease_released",release["returncode"]==0 and released["ok"] is True and released["task"]["task_id"]=="war-knight-screen-20261001-a04" and released["task"]["resources"]==[] and released["task"]["last_sequence"]==3167)
for val in index["sources"]:bind(val,"controller_source_"+Path(val["path"]).stem)
# Verify critical read bytes against the frozen index without rehashing shadercache.
assets={str(Path(val["path"]).resolve()):val for val in index["process_assets"]}
for key,val in list(inventory.items()):
    if key in assets:check("frozen_index_match_"+Path(key).name,val["sha256"]==assets[key]["sha256"].upper() and val["bytes"]==assets[key]["bytes"])
old=read(HERE/"sentence-audit.json");ident(HERE/"sentence-audit.json");ident(HERE/"sentence-audit.md");ident(HERE/"capture-nextday-plan.json")
additions={
 "knights-k023":("PARTIAL_NEW_INDEPENDENT_REPLAY","R0127源保存态33437唯一存活，regiment65。","不证明020执行边界或有效勇武4；不是旧a02人物证据。"),
 "knights-k024":("PARTIAL_NEW_INDEPENDENT_REPLAY","R0127后保存态33437唯一死亡，前后基础勇武2→2。","不证明020死亡标记捕获边界、有效勇武4→2、实时反链清空或旧a02缺行。"),
 "knights-k025":("PARTIAL_NEW_INDEPENDENT_REPLAY","R0127同run后档明确death_date1066.12.30、death_battle、killer34120。","本次未另核击杀者威望两字段+150，不关闭选择器或完整因果。"),
 "knights-k033":("SOURCE_BOUNDARY_REINFORCED","新增独立R0127亦必须单列，不能剪成020/070/036→038/旧a02连续录像。","新run原始视频为空；不替代历史UI。"),
 "knights-k034":("OLD_UI_FACT_UNCHANGED_WITH_DATE_ERRATUM","旧a02画面12/30与11→10事实维持；原生d27数值在新run实际也显示12/30。","R0127截图无骑士列表；旧a02净少1未逐ID归因。旧审计将12/30片段判为非d27的转换文字需按新增勘误纠正。"),
 "knights-k035":("OLD_UI_FACT_UNCHANGED","旧a02通告/十名骑士/当天12/30仍由旧素材证明。","R0127地图截图没有通告；不是新的inset素材，也未认证影片clean span。"),
 "knights-k036":("UNKNOWN_BOUNDARY_RETAINED","旧a02 selector与33437次日人物状态仍UNKNOWN；R0127只增加自身保存态生命状态。","新runtrace同样failed/1040，不证明事件选择或唯一完整因果。"),
 "knights-k037":("PARTIAL_NEW_INDEPENDENT_REPLAY","新run保存态生命转移再次支持阵亡风险存在这一部分。","不证明036→038名册69→68/30→29；R0127未核全部名册差集或原生next-input属性。"),
 "knights-k038":("LIMITS_UNCHANGED","增加一个独立生命状态样本。","未建立完整风险分布、成长权重、未来刷新或治疗结果。")}
mapping=[]
for row in old["sentences"]:
    key=row["key"]
    category,addition,limit=additions.get(key,("OLD_SUPPORT_UNCHANGED_NO_NEW_DIRECT_EVIDENCE","该句沿用已审原来源证据；R0127没有新增直接证据。","不可用R0127替代其声明的来源、UI或机制口径。"))
    mapping.append({"key":key,"zh":row.get("zh",row.get("text",row.get("narration"))),"addition_category":category,"new_evidence_addition":addition,"remaining_limits":limit,"old_audit_modified":False})
report={"schema":"ck3.a04.knights.nextday-R0127-independent-verification.v1","created_at_utc":datetime.now(timezone.utc).isoformat(),
 "status":"VERIFIED_NEW_RUN_SAVED_LIFE_TRANSITION_WITH_TRACE_AND_UI_LIMITS" if all(c["passed"] for c in checks) else "VERIFICATION_FAILED",
 "reviewer":"a04_knights_evidence independent evidence review","run_root":str(ROOT),"run_id":index["run_id"],"episode_run_id":EXPECTED_RUN,
 "interpreter":{"path":sys.executable,"version":sys.version},"read_only_game_and_screen":True,"ck3_launches_this_verification":0,"desktop_inputs_this_verification":0,"master_intake":False,
 "index":ident(INDEX),"strict_receipt":ident(STATUS),"checks":checks,"all_checks_passed":all(c["passed"] for c in checks),
 "native_connection":status["native_connection"],"native_raw_date_pair":[53146848,53146872],"actual_saved_and_ui_dates":["1066.12.29","1066.12.30"],
 "saved_character_reparse":reparsed,"trace":trace_summary,"original_ui_review":ui,"old_a02_nextday_life_status":"UNKNOWN_UNCHANGED","old_a02_selector_status":"UNKNOWN_UNCHANGED",
 "cleanup":{"managed_session":session["shutdown"],"warmup":session["frontend_first_warmup"]["warmup_shutdown"],"sdk_completion":index["sdk_completion"],"screen_release_receipt":ident(release_path),"screen_release_sequence":3167},
 "sentence_mapping":mapping,"civil_date_errata":[
   {"old_file":"capture-nextday-plan.json","old_claim":"raw53146848=d26=1066.12.30; raw53146872=d27=1066.12.31","correction":"本次同原生源pair的实际save/UI是53146848→1066.12.29，53146872→1066.12.30；d26/d27仍为案例日编号。"},
   {"old_file":"sentence-audit.md","old_claim":"末段将旧a02 raw12/30片段称第26日而否定第27日；k025缺口举12/31后档","correction":"不能由12/30否定原生d27，且本次后档meta_date12/30。旧a02缺少的是人物逐编号生命状态/selector，而非画面日期必须12/31。历史020的日期文字未重跑核验；撤回未经原件支持的12/31解释。"}],
 "verification_limits":["Reparsed preserved melted bytes using the pinned existing parser, without remelting or launching CK3","No same-frame native CharacterID life query","No full event/selector causal chain","No new battle roster/character-card UI","No raw_video or clean-span certification; no human1x film signoff","Historical attempts and failed olda02 are not rewritten"],"critical_inventory":list(inventory.values()),"all_5185_assets_rehashed":False}
write_new(HERE/"nextday-live-R0127-verification.json",report)
md=["# 骑士次日保存态补证：R0127（2026-10-01）","",
 "独立复核结论：新 R0127 / `native-29829-f83be45dbbd9` 中，人物33437的源保存态为唯一存活、链接兵团65；推进一个原生日后，后保存态为唯一死亡，明确写入 `death_date=1066.12.30`、`death_battle`、击杀者34120。两档基础勇武均为2。原始存档、melted文件、请求、回件和同连接身份均重新核对大小与SHA，并独立重读33437块；完整核验见 `nextday-live-R0127-verification.json`。","",
 "原始WGC HWND前后PNG均为1024×768、PID4496/HWND264284，直接审阅显示暂停地图日期1066年12月29日→12月30日；melted meta_date一致。两图没有人物卡、骑士名册或击杀通告。","",
 "日期勘误：旧计划把native raw53146848/53146872标为12/30→12/31，晚了一天。此新run证明实际为12/29→12/30；案例日编号仍是d26→d27。旧审计末段称a02的12/30画面‘不是第27日’，以及k025缺口举‘12/31后档’的转换解释不能成立，应以本补证勘误为准。k017/k030的案例日编号与k034/k035实际画面12/30本身不受影响。旧计划、旧38句表、旧attempt均永久保留，不修改。","",
 "新run一次life-advance请求原生回件为elapsed_days=1、requested_horizon_days=1，raw53146848→53146872、暂停；前保存request绑定revision4，推进绑定暂停revision5，后保存绑定revision8。所有交互回件同pipe/connection_generation1/PID4496，保存态绑定同episode_run_id。","",
 "Trace外层accepted=true，但内部仍为failed、failure_flags1040，最终捕获边界有失败；这次补齐的是新run生命保存态，不是selector或完整唯一因果。旧a02的33437次日生命状态和selector永久维持UNKNOWN。后态parser的regiment=null也不单独证明实时人物↔兵团反链清空。","",
 "清理回执证明实际运行树与warmup树退出、SDK job exit0、CK3/录制器/注入器清单为空；screen lease以sequence3167释放。无新原视频、无clean span认证、无影片人工1×签核。","",
 "| 旧句 | 可补充的R0127证据 | 仍保留的边界 |","| --- | --- | --- |"]
for row in mapping:
    md.append(f"| {row['key']} | {row['new_evidence_addition']} | {row['remaining_limits']} |")
md += ["","直接可并列补强的机制部分是k023的源保存态ID/存活/reg65、k024的后保存态死亡及基础2→2、k025的死亡日期/死因/击杀者字段，均需单独标注R0127来源。k037只补强死亡风险本身，不能替代036→038完整名册证据。其余句沿用原来源或明确保留限制。","",
 "仍需补证的优先事实：若要解释本次事件选择，需合格的新selector捕获；若要展示人物状态，需同run CharacterID33437身份绑定的真实人物卡/名单画面；若要解释退出名册与有效属性，需要本次前后逐ID名册/兵团/属性读取。成长权重、击杀者威望两字段、治疗和未来每日刷新均未因这次保存态补证新增证明。","",
 "本复核未启动Steam/CK3/录制器、未做屏幕输入、未修改游戏或旧证据、未拉取master、未提交或推送。"]
with (HERE/"nextday-supplement.md").open("x",encoding="utf-8",newline="\n") as stream:stream.write("\n".join(md)+"\n")
print(json.dumps({"status":report["status"],"checks":len(checks),"hashes":len(inventory),"failed":[c for c in checks if not c["passed"]],"sentences":len(mapping)},ensure_ascii=False))
if not report["all_checks_passed"]:raise SystemExit(2)
