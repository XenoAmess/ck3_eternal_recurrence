# XQOL administrative / meritocratic native1066 entries

状态：READY_FOR_BOUNDED_GOVERNMENT_UI_ACCEPTANCE / NOT_RUN。只证明冻结文件和现成 loader 形状可用，不证明实机玩家、政府、继承法、候选或 GUI 已验。

本目录独占两套新 profile；原 unused-government-profiles-01/admin、merit 的33-file seeds完全保留。每套新37文件 = 原生产27 + 配置5 + 外层 product.mod1 + 资格 fixture4。只加载 product 与 government-qualification；不加载防御11fixture，不使用宋帝 current-actor scope / QR，不运行防御日控制器。

## 冻结入口

- index：`C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/package-index-ready-02.json`，59866 B，SHA-256 `7981f2e5abddfc5c4e247df599914fb3befb1d51d7d11d94bd6fdec4882499ba`。
- support：`C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/support-files-ready-01.json`，1213 B，SHA-256 `23cc0c0ceb5917e29d92cdbd65eafbea33c31d39d2bf28f0264fb49e195d60b8`。
- allocator：`C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/allocate_government_source09_ready02.py`，SHA-256 `a6ac3ccc173e077c4930a424657afb305183a208d51134770a6dcf0f3cd53643`。
- launcher：`C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/launch_government_source09_ready02.py`，SHA-256 `301d93e283020cd6bbca2c52c0ebc0392d6e3d1215f20c63f756f78cbd9076b4`。
- finite receipt：`C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/government-entry-finite-shape-receipt-02.json`，SHA-256 `813d25b433edc4d595515d776a5a39f19d2188a586e0fc6232bf037c35da6d16`；10有限合同/文件用例、6 AST/compile、两份实际生产 policy loader 和两个入口 validate 函数通过。模拟 binding 用例没有实机信用。

工作目录必须 `C:/workspace/ck3_eternal_recurrence`。下面的 aNN、ACTUAL_* 均须换成当时真实值；不得预造 lease、CAS、LIVE、PID、截图或亲阅人。

## 一次 allocator

行政制：

```text
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -X utf8 C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/allocate_government_source09_ready02.py admin aNN --index C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/package-index-ready-02.json --support C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/support-files-ready-01.json --previous-live ACTUAL_LAST_CLOSED_QOL_LIVE --previous-keeper ACTUAL_QOL_KEEPER_ROOT --previous-release ACTUAL_QOL_SCREEN_RELEASE_JSON --latest-screen-release ACTUAL_LATEST_INTERVENING_SCREEN_RELEASE_JSON
```

贤能制：同命令的第一个参数改为 `merit`，aNN 使用另一个全局未使用编号；前序必须传此次真正已闭合的实机/keeper/release。如果没有中间 screen epoch，可不传 `--latest-screen-release`。

allocator 原闭合断言完整继承：outer finished/thread/cleanup、native shutdown/cleanup_proven/job0/treegone、四路进程库存空、控制文件不存在、keeper thread退出、release真实resources[]且sequence递增、无 CK3/keeper/controller/raw/thin残留、干净 lease anchor、新单用 ledger、冻结33-derived profile和Source092638文件。前序 stop/null/shutdown1只按既有实际cleanup证明清场，不改写成OS0；本场正式正常GUI退出/OS0仍独立必验。

返回 LIVE/task/sequence 后，由唯一前台执行者取得新 keeper 与当场 fresh offline/recovery/challenge 原图证据。不得以本卡、旧图、nonce ACK 或这里的文件检验代替直接亲阅离线模式。复用现有 `C:/workspace/ck3-upgrade-20261003/screen_keeper.py` 和已有 fresh offline/challenge 卡，不新增工具或假审流程。

## 一次 launcher

```text
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -X utf8 C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/launch_government_source09_ready02.py --index C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/package-index-ready-02.json --run-root ACTUAL_NEW_LIVE --keeper-root ACTUAL_NEW_KEEPER_ROOT --proof ACTUAL_NEW_OFFLINE_RECOVERY_JSON --challenge ACTUAL_NEW_CHALLENGE_JSON --observed-nonce ACTUALLY_READ_SECOND_FRAME_NONCE --reviewer ACTUAL_DIRECT_FOREOPERATOR
```

`--reviewer` 必须是亲自查看当前原始图的实际执行者；helper 不自动声称 Root。它仍核当场nonce/时限、实际keeper OWNED_CAS/task、无旧CK3、冻结全部输入和未launch，然后唯一 Popen；管理员没有在本轮执行 allocator/launcher。

## 真实准入流程

1. 复用已验 MCP typed Robert1066 Start 一次。Source09 typed前端选人只支持 Robert，本卡没有声称有 e_byzantium/e_goryeo 的 typed直接选择工具。
2. 新 hidden fixture 在同一原生1066 D0检查实际 `title:e_byzantium.holder` 或 `title:e_goryeo.holder` 存活、原政府、独立身份、原对应title、原AI身份；只执行一次已有 `set_player_character`。随后通过目标scope的另一 hidden event 在真实目标ROOT检查 human/政府/title/独立性并输出资格与scope原始日志。没有改政府、title、法、候选filter/score、宗教或关系，也没有业务代填。
3. 行政要求真实 `administrative_government` / empire / independent；贤能要求真实 `meritocratic_government` / empire / independent。原 generic fullRoot binder 要 actual same Start PID/gen、同bookmark D0、snapshot和root的同一living actor、实际政府/tier/liege、真实 .3 provenance，两个递增pump epoch才稳定。资格 BEGIN/PASS/DONE各1、FAIL0；重复/失败/超时 fatal且不重放 Start。
4. Source09 service.py4566–4639、4721–4725 已将 envelope 的 government/player/title/provenance 与 nested campaign_root_context 精确核对。入口使用这些现成实际 mirrors；未伪填field或script characterID，也没有改变原generic binder函数。
5. 首次 raw `map_ready=true` 必须立即提醒唯一前台看当前原图，无论active_event是否null。原生 intro可能是GUI overlay；本场没有宋scope typedintro optin。若需清场，只按已有 actual event context或当前原图合法操作一次；不等资格报告deadline，不blind选、不自动重放Start。既有 raw helper：`C:/workspace/ck3-upgrade-20261005/xqol-payment03-live-monitor-agent-01/observe_native_state_changes_01.py --live ACTUAL_NEW_LIVE --output-dir NEW_EXCLUSIVE_RAW_OUTPUT`，由现有只读10秒watch入口复用。
6. 原400s readiness/资格时限保留。initial-map等待 paused/map/actualalive/.3/native_campaign/eventnull；initial-root要求 actual government、independent、living player和empire。episode_projection仍native_campaign，不伪造one_life/episode ID。实机未满足时保留FAIL，不称READY业务。

## law 与五块任命边界

资格fixture只输出真实 natural direct-vassal law presence/absence：行政 `appointment_succession_law`；贤能 `meritocratic_appointment_succession_law`、`meritocratic_military_appointment_succession_law`。这些OBSERVED marker不计入任命通过；absence明确GAP。

holder实际ID来自本场 root/query/GUI，不能猜整数或把 `e_*`/`d_*` 脚本key传入native title_id。先从真实候选governor核对应实际继承法，再开真实候选完整列表；百万tooltip只有独立人类玩家自然存在于该title完整候选池才能做off/on/off。军事贤能必须是真实军事合同和相应法；不存在则保持GAP，不能清filter、伪合同或以军职不存在造PASS。两场都只验本政府的实际块，不将天朝minister当 governor。

决定面板可使用 Source09现成 open/query/select；Confirm固定Vivhite专用，XQOL确认/任命/slider/tooltip仍按现有GUI卡实际操作。原卡：`C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/POST-DEFENSE-APPOINTMENT-SLIDER-CARD-01.md`。候选任命先于slider保存；保存会真实改信，cancel先验、save最后验，不能破坏未验候选资格后回推。

## 正常收尾

用当前原图/实际窗口正常GUI Quit to Desktop，实际native exit/OS0与job0/treegone/inventory[]/controlabsence/threadcleanup全部回读；不可用退出ACK或kill代替。需要结束hold时，排一次本cell原 `finish-hold-plan.json`：

```text
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -X utf8 C:/workspace/ck3-upgrade-20261005/root_queue_control_once_01.py --live ACTUAL_NEW_LIVE --plan C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/admin/finish-hold-plan.json --name government-admin-finish-once.json
```

贤能使用 `merit/finish-hold-plan.json` 与另一name。原host9ea→737d finish-closeout守卫保留：只有合法闭合状态才收尾；无第二claim/新daycontroller。keeper真实退出后按实际lastsequence CAS release，保存清场与屏幕resources[]；本卡没有预写未来CAS。

## 通用源码小补丁交付

`C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/generic-government-whitelist-01.patch` 仅将 frontend_fixture_start_contract.py 的 gov whitelist 增加 administrative_government / meritocratic_government 两值。原feudal/celestial保持，unknown依旧拒绝，generic binder函数/真实twoepochs不动。它已应用到独立immutable overlay供本入口使用，未修改Source09原2638、DLL916b或共享仓库；Root可按授权把这份小补丁单独合回master。本卡不把 overlay 或shape检验记成任命实机PASS。
