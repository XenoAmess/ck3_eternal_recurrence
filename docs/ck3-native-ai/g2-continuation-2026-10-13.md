# G2 接续实施（2026-10-13）

> 最新状态：fresh15实际完成两个Service周期（LIFE提交→独立applied材料及Service SAVE），循环日期推进0，第三AUTO在婚配投影查询RED。已定位Native前置遗漏exact1.20.0.4，修复/增量B13待执行。B12完整owner-tree已在fresh14/15暂停地图hidden场景实际通过；不授可见关闭或战争信用。完整30回合演示、选定目标、胜战及跨代仍未完成。见[fresh15实绩与纠正](g2-fresh15-life-material-and-marriage-gate-2026-10-13.md)。下方旧阶段记录保留。

接续 [休假交接](../handover/2026-10-13-g2-native-maintainer-vacation-handoff.md)，实施输入为干净的 `6feaef84953fdaf0d26244744a5c4ddbb75286c6`。用户要求的 64 个并行研究任务按 M0–M7、每组协调者兼研究者及七个专项执行；本次复用原任务继续实施，没有将任务数当作能力完成度。

## 首包实现与验证边界

| 组 | 实施结果 | 定向验证与剩余边界 |
| --- | --- | --- |
| M0 | 普通策略接入已有守方白和；多战争先消费已资格终局；runner 接受既有 terminal_score_defeat；统一只读终局材料摘要 | 白和 1、多战争 7、runner 1、摘要 5 个新增用例通过。actual4 最终接收方 evaluator 的 flag0 来源仍未闭合，保持 unavailable；没有编造答复 |
| M1 | 核心完整、可选规则未知的同帧根查询可用；根查询省去完整 history 复制；透传 nullable immediate_liege；当前风险材料与实际 Driver 形状一致 | 根查询消费 1、history 所有权 1、liege 4、实际风险链 2 个新增用例通过；风险摘要不声称解决分封或最优继承 |
| M2 | .1070.c 明确有界选择理由，新增军队的独立材料比较；Feast 当前意见 utility；Rite fulfillment 材料；自然派系要求独立适配器 | 19 个新增 leaf/dispatch 用例及 Rite Service 连接用例通过。`.1001` 缺少完整当前军事决策输入，适配器不自动选择；不以任意兵力阈值替代来源 |
| M3 | 在原事件循环和 SDK 队列中包装既有继承交接，先保留 pending，再消费原 completed，采用后立即返回 successor SAVE 对 | 9 个新增异步用例首次通过；30 回合 fresh 演示仍在角色/episode 改变处停交 Root，不把离线夹具算自然继承 |
| M4 | MCP 透传既有 LIFE 配置；赠礼 preview 稳定优先危险且未开战派系；原 tier-one 建设目标优先占用既有有界扫描预算；已解决赠礼可独立读回 | LIFE 与赠礼注册连接用例通过；建设扩展矩阵先复现 RED、最小修复后 GREEN；未扩大扫描 cap。通用 Council task 来源研究不等于新增实机能力 |
| M5 | 强攻传入 commands；四个资源消费层允许合法 ArmyID 0；目的地专属拒绝继续现有候选；宣战保留原请求并核唯一实际战争身份；婚配关系字段保留 | 新增强攻、路线、ArmyID、Driver 连续性及 Service latch 用例通过。非空开战脚本仍须实际 tuple/Node 和具体 operator 来源，不能由 CB 名字授权 |
| M6 | 普通 Service 回合复用现有 Sway completion、termination、opinion 观测；runner 使用同一实现；终止轮询不复制完整 history；Sway startup 先建立 execution session | 新增连接及有限返回用例通过；startup 顺序回归为源码检查。已有 Feast bootstrap 保留，没有重复新增 API 或门禁 |
| M7 | 生命周期消费真实字典；bridge_pid、hello、launch PID 一致；supervisor 保留 queue/application 实际代际句柄，配对确认后才 RPC；pending 保持原 SDK、仅诊断和 collect 原请求 | 生命周期、代际/退出回执与连接握手的新增检查见外置逐项回执；wrapper 退出不能代替 application 内核退出。实际 cold recovery 另记 |

所有源码/离线夹具结果与实机结果分别记账。首包不重新验收旧 M0–M5 矩阵，不给 G2 总体、稳定战争、M6/M7 整局能力授予完成信用。

启动前实际进程检查还发现本机 venv `python.exe` 是重定向器。队列自身份按实际 base interpreter 核对；SDK application 直接启动同一 base interpreter，并显式加载固定 venv 依赖（含 `.pth`），要求 MCP 2.0.0。真实短进程检查独立于 Game；不能把 redirector wrapper 的 PID/退出码算作 SDK application。

实际短进程检查进一步发现 base Python 的全局 site 会遮蔽 venv MCP；新 application 使用 `-S`，然后显式 `site.addsitedir`，同时核对 MCP/stdio 模块真实路径。`real-bootstrap01/attempt03` 实际通过：wrapper 独立，queue/application 两个原句柄均 WAIT0/exit0，MCP 2.0.0、stdio、win32api、pythoncom 均来自获准 venv。首轮有限证明和 global-shadow RED 保留；只复验变更场景。赠礼三世界实际夹具验证也已完成：25 checks、零旧矩阵、零 queued actions；修正过的夹具首次 RED 保留。新测试 EXE 的 Defender 实际设置读回仍为 admin-required，不能称排除已生效。

## 输入、容量与构建

本机外置工作包 `R = D:/codex-ck3-background-spill/g2-remediation-20261013`，本次回执在 `R/resume01`，新开局 attempt 在 `R/fresh-robert02`；旧 `fresh-robert01` 及硬链接冻结输入保持原样。所有任务共用原 8 GiB 组预算；`STORAGE-CONTINUATION-ADMISSION.json` 记录续作实际容量检查，不新增 64 份预算。

原复核期限仍为 **2026-10-13 16:58:39.018273 UTC**，重型新写入最迟在前 15 分钟停止。冻结、原始返回、测试失败和派生资产均按 [统一存储策略](../storage-retention-policy.md) 在该时点复核；保留不是永久承诺。独立录像最多 1200 秒/1 GiB。

Native 增量构建：B7 只补编 bridge 与赠礼 router 两个直接链接 TU；B8 再补编 construction 一个 TU，并重建 612 成员 runtime archive、重新链接。没有全量重编或热替换 DLL。B8 的 retained 对象继续继承 B6/更早的混合来源，不能声称当前 HEAD 全树已重编。

```text
R/native-profile/build08/native.dll
18260992 B
SHA-256 75fa14e95e0deedb0db7e05b3530e238631d7fb475ecadfb542300bfbb57dc80
```

实际 compile/archive/link 均返回 0；Native 生产组当时合计 1,237,829,676 B / 2 GiB。源码顺序修复、编译成功、实际冷载和业务效果是不同证据层级。

## 新罗贝尔实机记录

首包提交时尚未启动新 Game/录制。后续须由 Root 在新 clean freeze、任务总线 CK3/屏幕独占、已接受的 Steam 离线确认下执行：独立录制开始且文件增长、亲审首帧后，route/New Game/1066 Robert Start 各一次，核初始角色、日期、ordinary/no-pact 生命周期和 SAVE 对，再运行完整普通规划器。最多 30 turns，每 5 turns 核对并保存；unknown 保留原结果与原请求，不重送。

实际日期推进、动作结果、配对 SAVE、录像、Node 输入和正常/强制退出分别追加当次回执；本段准备状态不能充当这些事实。

## 外置交付索引

- M0：`R/resume01/m0/{white-peace,multiwar,cold-terminal,postconditions}`；最终接收方保留来源缺口。
- M1：`R/resume01/m1/{history01,lane1,lane2,lane4,continuity01}`。
- M2：`R/resume01/m2/coordinator/DELIVERY01.json` 与各 leaf 首次/更正回执。
- M3：`R/resume01/m3/DELIVERED.json`。
- M4：`R/resume01/m4/coordinator/FREEZE-DELIVERY.json` 与建设 RED→GREEN、LIFE、赠礼连接回执。
- M5：`R/resume01/m5` 中 Strategy 集成和各首次结果。
- M6：`R/resume01/m6/ordinary-sway/{DELIVERY,FREEZE-SOURCE-PINS}.json`。
- M7：`R/resume01/m7` 及 `R/fresh-robert02` 中 harness 固定与逐项验证回执。

外置证据到期回收后须明确记录原件不可读，不以同名文件冒充原始证据。


### Fresh startup source preflight correction

Fresh02 stopped before Game creation because the sparse checkout omitted the tracked `ck3_workshop_mcp` package required by the production builder. Fresh03 froze its 16 source files from exact HEAD; startup then stopped before Game creation because local `.idea` editor files failed the release source allowlist. The builder now treats `.idea` as an excluded development directory. The actual source check passed and none of the 100 allowlisted release files include IDE files; local files were preserved. Both failed attempts retain their original closure receipts. No gameplay or war result is credited.


### Fresh04 actual runtime and pre-RPC failure

B8 actually cold-loaded into fresh CK3 PID244488 at03:40:57Z; Game and decision window were assigned to Desktop1 while Desktop2/foreground stayed unchanged. Dedicated OBS actually recorded, grew, and its pre-selection main-menu/decision frames were personally reviewed; an initial black source frame remains preserved. No frontend selection RPC was submitted. The SDK queue/application actual retained handles both exited1: the faction round argument was present but incorrectly used `g2-robert-fresh02-20261013`, violating the R<number> constructor contract. The Game did not exit after normal WM_CLOSE; owned Job cleanup exited1 and proved the tree gone. This is startup failure, not normal closure or gameplay credit.

Two actual recorder defects are fixed in source: overlay identity now queries the actual process image on its FILETIME handle (venv sys.executable can be a different redirector); owned OBS retries only read-only startup profile/collection code207 within the original40-second loop. Other failures still abort, and StartRecord is never retried. The existing recorder custody contracts pass. Fresh05 uses a new state/pipe and explicit R2026101305; B8 is unchanged. Original attempts/receipts/video remain available until the group review deadline.

## Fresh05：实际开局、过早超时及镜头 RED

输入为干净的 `4c90e76b05fc9f5d43d9bc1696fec606afc54729`，B8 不变。实际 Game PID269280、creation FILETIME134363373210468099，03:55:21Z 创建；queue PID250588 与 application PID179832 在任何 RPC 前由 supervisor 保留各自实际代际句柄。原生路线查询、New Game、固定 Robert Start 各提交一次，前两项通过。Start 于04:04:22.217882Z提交，04:06:23.620516Z 返回“已提交，但120秒内没有独立观察到暂停地图”；原始0003错误保留，没有重送开始动作。

Root亲审末帧019确认显示罗贝尔头像、1066年9月15日及暂停HUD。M1在录像中找到最早相同业务画面的sample009（04:09:17.464847Z，Start后295.247秒）。这只是像素观察；没有取得初始semantic、SAVE或普通回合，不能追认原Start响应为verified。**有效普通回合0、日期推进0、已选战争目标0、获胜战争0。**

用户指出镜头落在地图左上阴影，Root确认画面问题。现有热点跟随仅在普通auto回合之前调用，Fresh05因Start超时尚未到达该入口；选择器也没有和平领地fallback。后续修复须以实际当前玩家资本/领地字段选择初始锚点，核对原生camera结果和定位后像素，再进入普通循环，不能以暂停HUD或Invoke ACK证明镜头正确。

独立录像 `R/custody-recorder01/recordings/db363dda-ffc8-402c-888a-13be4debce48.mkv` 实际715,072,156B、1189.966秒、2560×1440/30fps、平均4,807,345bps，SHA-256 `d44288c7f906369cc44fc522c1d56fa7d44785267aba7115ef13a335f589e08d`。原cleanup记录输入移除ACK后立即读取仍附着，未自动关闭OBS；Root随后在同一实际OBS代际PID219540上确认已无输入、output inactive，只对唯一主窗口发送一次WM_CLOSE，实际WAIT0/exit0。原失败未覆盖，另有`ROOT-FRESH05-RECORDER-NORMAL-CLOSE.json`纠正回执。个人OBS PID114680保持同一FILETIME运行，未操作。

到原deadline，queue实际exit1、application exit0；Game在一次WM_CLOSE后未退出，owned Job清理实际exit1/tree_gone。keeper停止、最后序号3641，以CAS释放为3646，未称正常Game闭场。新录像修复使输入移除只提交一次并有界轮询只读完成状态，关闭只命中唯一OBS主窗口；16项定向测试通过，包括4项新增异步移除/主窗口场景。

04:25:48Z闭场及重写入前清点：25,577文件、去重文件逻辑3,399,837,077B/原8GiB，Native组1,237,939,382B/2GiB，D卷实际free1,236,275,294,208B，大于保守预留601,295,421,440B。物理allocation未测，不冒充物理占用；原16:58:39.018273Z复核期限不变，无删除。证据在`R/resume02/ROOT-FRESH05-CLOSE-STORAGE-AUDIT.json`及`R/fresh-robert05`。

64任务第二轮源码研究已交付至`R/resume02/m0`至`m7`，保留各专题来源和未资格边界，不声称闭场时仍有64任务运行。[REA评估](rea-evaluation-2026-10-13.md)是额外明确委派：可用于静态值追踪与证据整理，尚未安装或用于实机，不能替代普通规划器或Native来源资格。

## Fresh06 修复输入，实机结果待追加

Start 的地图等待与后续暂停泵推进改为共享一次 transition 总预算，新的600秒配置不会变成两个600秒窗口；新增4项及仅受影响旧2项定向场景通过。普通Service补齐LIFE开局阶段消费，已有focus和新focus的独立读回都能完成开局阶段，runner仍使用其已有外层checkpoint所有权，避免重复SAVE。

热点选择器增加同帧完整根查询的实际玩家首府/持有county首府fallback，保留战斗、围城、移动及战争目标优先级，并保留合法ArmyID0。安装版本的EXE字面量独立核对确认`screen_edge_scroll_mode_disabled`，没有从本地化key猜拼写；新managed profile生成禁用配置并在manifest中记录语义合同，旧冻结profile不改。新增2项配置/漂移场景通过。**这些源码和配置结果尚不证明镜头实际稳定；进入普通循环前还须Root亲审定位后的录像像素。**

录像新增会话内合作停止文件，仍由原FileGrowthWatch独占一次StopRecord，不发全局stop；新增1项定向场景通过。新外置supervisor在实际SDK退出后，绑定同一Game/session请求录像合作停止，有界等原cleanup再关闭Game；2项代际/零重送离线场景通过。录像时长按实际Game剩余时间预留清理，不延长1500秒Game上限或原组期限。

M5补齐actual4路线成功预览的既有供给附件。B9只重编c0375 adapter TU，实际compile/archive/link返回0；612成员中611个名称和payload精确保留B8，496项实际sourceDependencies匹配固定输入。

```text
R/native-profile/build09/native.dll
18260992 B
SHA-256 a1f05041f9357172a2407b27413da088547e891ea4ddf68adda593646180be8e
```

B9闭场Native组1,439,770,291B/2GiB；共享逻辑3,930,495,735B/8GiB。没有覆盖actual4 adapter分支的适用旧fixture，编译不冒充该分支业务测试；B9本段只记COMPILED_LINKED，冷载与新局结果另记。非空开战脚本参战来源仍partial，未借供给附件修复放宽宣战资格。

## Fresh06：镜头与初始 SAVE 通过，首个普通回合发现原生 GUI 读取故障

干净输入 `9d8682f38f84fd33af9e36c354a03e5058d2a5b8` 包含显式换 episode 后重开 LIFE 门禁的窄修复及新增继任者用例。B9 实际冷载到 Game PID209992、creation `20261013062234.926143+000` / FILETIME134363461549261435，新 profile、pipe、state 均未复用旧存档。桌面1放置完成，桌面2和用户前台保持原值；独立录像实际开始、文件增长，Root亲审 `sample-001-scene.png` 主菜单与决策文本后才启动 SDK。Steam 沿用用户离线保证，不声称取得新离线像素。

实际 queue PID168836/FILETIME134363463987337808 与 application PID246088/FILETIME134363464006684583 在 initialize 前由 supervisor 保留句柄并配对。route、New Game、固定 Robert key Start 各执行一次。Start3 于06:27:59.967448Z提交，27.548244秒后返回 accepted/verified/postcondition_verified；原生角色31254、episode `native-31254-28581d9b21a6`、raw日期53144328、暂停且地图就绪。运行时ID不能照搬旧29829；本轮记录实际ID及固定bookmark选择，未另造历史ID映射证明。

camera4 从同帧 CampaignRoot 实际首都2619选择 `b_trani / c_apulia`，原生当前/目标坐标 `[1898,0,2444]`、zoom174/index4、settled/postcondition_verified。Root亲审sample012明确显示特拉尼和阿普利亚半岛，后续sample016仍保持同一地图位置；AUTO9 的原生跟随也返回 already_centered。**本场暂停期间初始定位及后续观测通过；尚无日期推进中热点切换或战时稳定性结论。** 当前profile实读 edge-scroll disabled，manifest及实际启动路径匹配；settings整体哈希已被游戏改变，运行时设置getter未读取。

独立 semantic5 与 camera 的角色/日期/episode 保持一致，完整生命周期字典 ordinary/xar_off/no-pact 匹配环境。SAVE6 实际 saved，68,948,462B，SHA-256 `567106ae5e77037960cca9bdca458114680f3198a9c1984be641baf2a2075869`，history_index3；episode seed 同内容。独立 Driver 回执为 `WRITE_REPLACE_RETURNED_NOT_FSYNC`、replaced、write_replace_returned/save_binding_verified=true。本段授初始 SAVE 配对，不授自然继承、successor SAVE、LIFE receipt checkpoint或冷恢复验收。

full_loop7 已启动完整普通规划器。首个 AUTO9 用时4.171270秒，MCP is_error=false，但业务 status=blocked、phase=war_declared_overview、selected_step=null。当前概览 presence unknown/query_attempt observed；原始AUTO9与control7错误保留，队列暂停而未重送。实际 Driver history index6 的 Native 查询 ticket104/pump94892/thread220836 已证明owner线程，却返回 available=false、root_observed=false、`war_declared_window_read_failed`。此理由合并了多个完整GUI树读取失败分支，不能猜为预算耗尽，更不能将未知改为窗口不存在。**本场有效普通回合0、日期推进0、已选战争目标0、获胜战争0。**

06:40:24Z keeper检测工作树短暂出现变更后停止；后续Git状态干净，具体瞬态原因仍核对。实际SDK queue exit1/application exit0；Game保护清理exit1/tree_gone，不记正常关闭。录像合作停止已由原worker接收，但supervisor在失去lease后提前结束等待，原录像failed理由为Game HWND消失。原cleanup仍证明 inputs_unbound=true、独立OBS主窗口正常exit0且未强杀。overlay已关闭，keeper最后3815，Root于3853完成CAS释放。原失败、cleanup与新修正候选分别保留。

第三轮按8组×8人重新调度既有研究线程，部分协调者/子线程遇到capacity或流错误，按实际状态记账，不声称持续64运行。来源在 `R/resume03/m0` 至 `m7`：新增闭合既有115B `3F90870` CPU搜索叶；TLS epoch复制与收尾仍有两处传递缺口，事后采样不能证明调用前资格。B9供给附件尚未接入普通移动选择；非空宣战来源及目标逐候选资格扫描仍未完成，未放松门禁。M6未到达业务路径。

06:48:44Z闭场重写入前清点：31,148文件，去重文件逻辑4,666,159,135B/原8GiB，Native组1,439,775,780B/2GiB，实际free1,234,942,812,160B，大于预留601,295,421,440B。物理allocation未知，原复核期限不变，无删除。下一诊断仅改受影响Native TU，沿既有自由文本理由记录首失败类别和有限计数，保留2048 widgets/8192 edges及所有资格检查；编译、冷载、具体故障修复另记。

Fresh06录像独立核验：577,863,617B、961.866秒、2560×1440/30fps、h264/aac、4,806,188bps，SHA-256 `304845c6b01cb0dac923e5be42edfb014ec6f484f6e2fc9f8386bab852cfa558`。汇总 `R/fresh-robert06/ROOT-FRESH06-ACTUAL-CLOSED-EVIDENCE.json` 保留逐响应耗时/投影大小/文件SHA及原Native失败材料；未将MCP投影大小冒充Native线缆返回量，也未将整个Driver文件大小冒充history大小。

B10于07:15:11Z实际编译/链接成功，`R/native-profile/build10/native.dll` 为18,265,600B，SHA-256 `e1f19fbaeed2ef395a384a45c5657e5a00608534ca1ae23c0ab24dcaa9ba4d66`。受影响c0339原在direct link中，因此只替换一个direct object，保留其成功B6 owner macros/env/include及实际依赖；B9的612个archive成员全部原样保留，未重建archive。诊断源码100,519B/SHA `1bf6f0652b8cce0941b29126a5ae026a1946fb25105ed5bfb26808f05bb65bb1`。仅授COMPILED_LINKED/diagnostic_only；未冷载，未授业务修复。准备脚本缺Counter导入的首次失败在编译前发生并原样保留，生产compile仅执行一次。

## Fresh07：诊断闭合2048节点耗尽；B11窄修复待实机

干净 `cedaece5bd96551ffe11aaa4e06144158c5d12c6`，B10实际冷载到PID255104、creation `20261013072207.758188+000`。独立短录像首帧亲审后，固定route/New Game/Robert Start各执行一次；Start3 verified耗时28.662秒，actor31254、raw日期53144328、episode `native-31254-90748ce85441`。camera4 settled，Root亲审sample003为清晰Trani/Apulia；semantic5及初始SAVE6再次配对通过。

首个普通AUTO9仍blocked，但实际Native原始history now明确：

```text
war_declared_window_read_failed:widget_budget_exhausted;at=908;queued=2048;edges=2048;matches=1;count=3;child=2
```

它证明完整owner树的2048节点预算耗尽；虽已遇到一个目标，剩余树未读完，窗口状态仍unknown，不能提前授absent/hidden或忽略重复目标。原始response9、control7、Driver原件与汇总`R/fresh-robert07/ROOT-FRESH07-ACTUAL-CLOSED-EVIDENCE.json`保留。有效普通回合、日期推进、选定战争目标及获胜战争仍均0。

本场原SDK实际queue PID257992/FILETIME134363507241088845 exit1、application PID240740/FILETIME134363507260398493 exit0；错误退出不计正常SDK成功。录像合作停止和等待修复实际通过：COMPLETED、238.566秒、143,371,631B、SHA-256 `2106d2ac5aaf3a5fb275563c4f20498ecdad02e4f8e7a35cef3d34ad57916d1b`，inputs_unbound=true、独立OBS实际正常exit0、无failed。Game一次WM_CLOSE后仍未退出，owned cleanup exit1/tree_gone；keeper无failure、已停止，最后3870，CAS释放3872。录像正常关闭与Game强制清理分别记账。

补充Fresh06瞬态来源：M1 core_resources报告其cmd探针把未转义的`>`解释为重定向，在仓库根产生仅本任务临时文件`601295421440+65536`（2249B），mtime为06:39:58.3983982Z，随后精确删除。其原线程工具回执chunk为6f0504/0f6528/204fac，未有外置回执，creation与精确删除时间未测；这与06:40:24Z keeper失败时间相近，属于有依据的相关性，尚不冒称独立因果证明。

B11修复仅为完整owner遍历设置独立16,384 widgets/65,536 edges上限，通用GUI导出2048上限保持原值。私有生产helper使用有界vector和set，节点查重为O(logN)；全部可达节点和边验证完成后才发布目标。新增12场景调用同一生产helper，包括4097节点早见目标/完整不存在、16384边界、16385耗尽、晚到不可读、重复/环/null/多目标等。Root将原fixture的main作宏别名包装为DLL导出，由Python ctypes实际调用一次：08:05:20Z编译0、12/12 FIRST GREEN，无新EXE。CMake补充独立fixture入口，不需链接完整Native闭包。

B11只重编c0339并重链，实际`R/native-profile/build11/native.dll`为18,269,696B，SHA-256 `d4b4ad1a6f217b4b6333d9a41a5dd8ec4deb2b62be6baecfb762f06831c2e5f4`。首编译因固定旧include链没有新helper而失败，原日志保留；新增只包含此helper的固定overlay后，c0339-repair01编译及link均0。实际依赖逐项与预编译pin核对，B9归档612成员全部保留。这里只授源码/fixture/COMPILED_LINKED，业务修复及大树完整实读待新冷载。

07:45:18Z闭场清点：36,497文件，去重文件逻辑5,278,247,743B/8GiB、Native1,460,612,590B/2GiB、free1,234,304,090,112B。B11重链后Native1,482,212,434B，free1,234,275,143,680B，预留及原期限通过；无删除或期限续展。

## Fresh08：完整owner树超过16384节点；B12边界复验

B11在干净`014b6e5632012e9fe4dfc14fc76a6df36ad8ca36`新局冷载，Game PID236588/creation `20261013081431.919983+000`。Root亲审主菜单sample011、定位后sample014，Start3 verified耗时26.316650秒，camera4 centered，初始semantic5/SAVE6配对通过。episode为`native-31254-00b44069f38f`、日期仍53144328。

AUTO9原响应仍blocked，实际Native理由为`war_declared_window_read_failed:widget_budget_exhausted;at=8711;queued=16384;edges=16387;matches=1;count=5;child=1`。这只闭合原2048不足的原因，**B11的16384上限仍不足，未授实机修复成功**。有效普通回合、日期推进、目标及胜战均0；SDK未重送原动作。独立录像COMPLETED，1010.666秒/607,243,400B，SHA-256 `3cd5c4e28b03fe05d42b1305afdc658f96a733b0a89fc46cb4c584b6d202415c`，合作停止后OBS实际exit0。Game仍一次WM_CLOSE后force cleanup；keeper无failure/最后3885、CAS释放3886。

B12仅将私有完整树固定上限扩大到262,144 widgets/1,048,576 edges，通用导出2048保持不变；完全读完才发布目标、所有未知检查继续有效。相同12场景针对新预算边界重新验证通过，明确为已有场景复验、0新增独立场景；Root仍通过DLL导出调用原fixture，未产生EXE。实际B12编译/link各一次返回0，保留归档612成员；DLL为18,269,696B，SHA-256 `28c01334e474a712180c94782d72c0880d7360e49296dbc82e73e23e9416b648`。新header SHA `2fb29e51ff65a298e9c2d8a696fa2c23478b23dfe821ce582a296879a89ee4c5`。实际完整树读取及普通回合仍待fresh09冷载，不以扩大预算直接授成功。

08:36:30Z闭场清点：41,889文件、去重文件逻辑6,389,357,330B/8GiB、free1,233,159,507,968B；B12后Native1,503,007,789B/2GiB。原容量、601,295,421,440B系统/其他任务预留及16:58:39Z期限保持，无删除或续期。原件与逐响应成本在`R/fresh-robert08/ROOT-FRESH08-ACTUAL-CLOSED-EVIDENCE.json`，清点在`R/resume02/ROOT-FRESH08-CLOSE-STORAGE-AUDIT.json`。
