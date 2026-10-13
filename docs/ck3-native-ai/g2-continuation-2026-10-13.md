# G2 接续实施（2026-10-13）

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
