# CK3 Autonomous Player

`ck3_autonomous_player/` 是【琉焰卿的永恒轮回】专用的 CK3 视觉智能体工程。Python 包名为
`xar_autoplayer`。它与 `tools/run_acceptance.py` 完全隔离：验收 runner 证明 mod 机制；这里的智能体只在
production、非 debug、仅加载本 mod 的正常游戏里扮演玩家。

## 当前完成度

**Phase A 已完成。** 提交 `11ab443050132341bb27f6f924d792772f397396` 的冻结候选在同一环境指纹下连续三次
通过 production、非 debug、单 mod、可见主菜单 isolation smoke：
`20260821T180045Z-a3c49b20`、`20260821T180248Z-7ad2dd83`、`20260821T180531Z-9c6bb34b`。
三份事件链均已重新计算 hash chain 并通过一致性校验，另行逐项检查的报告硬条件无失败。完整证据边界见
[Phase A 实机证据](../docs/autonomous-player-phase-a-evidence.md)。加固前的三次运行只保留为历史探索记录，不能作为
当前退出证据。

已实现：

- 仓库外持久 state/profile，且与仓库、真实 CK3 profile、Steam userdata、CK3 Workshop 根目录双向隔离。
- 通过 `tools/build_release.py` 构建 production-only 投影，不加载开发树或 acceptance/selftest 内容。
- `dlc_load.json` 精确只有 `mod/xar_autoplayer.mod`；outer descriptor 仅指向隔离 profile 内的投影。
- 原版 81 个声明默认规则，加 `xar_on`、`xar_inherit_100`、`xar_score_growth`，总计 84 个 setting。
- 简中、2560×1440、云存档关闭；`tutorial.txt` 只在首次创建，之后不读取、不清空、不回滚。
- 同一 state 的锁覆盖 prepare/verify/smoke；同一 CK3 安装的全局启动锁覆盖完整 smoke 启停周期。每次启动前和退出后
  都用 `tasklist` 与 WMI 双源清点 CK3，任一查询失败、格式异常或结果不一致都按 unknown 拒绝继续，绝不把查询失败解释成零进程。
- unsafe marker 在启动 watchdog 前建立；watchdog 先持有并复核 supervisor 的 PID、可执行路径和创建时间，之后才写 ready。
  CK3 以 `CREATE_SUSPENDED` 创建，先进入 kill-on-close Job、完成 WMI 身份验证并原子写入 launch record，resume 前还要让
  双源全局清点精确只看见这个新 PID，因此第一条 CK3 指令开始就在 Job 内。record 绑定 nonce、父 PID、可执行路径和创建时间；
  watchdog 只终止持有句柄后再次认证的进程对象，崩溃 fallback 要达到五秒稳定空窗。清理证明不完整时保留 unsafe marker，
  并禁止 postflight。
- OCR 连续两帧确认可见【新游戏】；每次启动前删除隔离 profile 的旧日志，再以新日志的唯一 session marker、精确单项
  enabled inventory、已安装 DLC mount 白名单、唯一隔离 mod mount 和零未知 mount 做 supervisor 取证，退出后再解析一次。
- OCR 推理默认固定本机 NVIDIA `CUDAExecutionProvider` 的 device 0；检测、方向分类与文字识别三段模型全部优先使用独显，
  doctor 会实际初始化三段 session 并报告 provider，无法使用 CUDA 时直接拒绝启动而不是静默退回 CPU。RTX 3080 上同一张
  2560×1440 CK3 实机帧的热态耗时约 0.52–0.55 秒，原 CPU 路径约 1.3–2.5 秒。
- 真实 profile 顶层文件、player/rulers/正常存档与 Steam 云存档条目在退出后回到语义 baseline，并连续稳定 5 秒；Workshop
  `ugc_*.mod` descriptor 内容哈希与已注册目标树的路径/大小/mtime 元数据只做退出后一次 baseline 比较。两者都不声称运行期间
  从未发生瞬时写入；Steam 自行刷新 `remotecache.vdf` 的允许字段单列报告。
- 游戏 exe、launcher、原版规则、DLC descriptor、outer descriptor、production manifest/tree、实际构建脚本、解释器与依赖均纳入
  selected-contract 指纹；smoke 还要求选中的 agent runtime 与 production release source 文件全部已被 Git 跟踪且无修改。
  没有真实指向当前提交的 tag 时
  `git_tag=null`，不会伪造 release provenance。
- shutdown attestation 显式记录 CK3/watchdog PID 与创建时间、Job 最终成员数、双源全局清点、watchdog 退出状态和控制文件消失；
  `cleanup_proven` 是这些条件的显式合取，只有它严格为 true 才允许受保护存储复核。`report.json` 先落
  `finalized=false, ok=false`；最终事件链逐项重算、链接和 tail 绑定验证成功后才原子转为 GREEN。
- 原六类基础 JSON schema 加两份 Phase B 可见 UI schema、首个 `growth100.v1` 策略假设和追加写入、带 SHA-256 链的 smoke
  事件流。Phase B 菜单竖切已用
  Draft 2020-12 在 GREEN/RED 回放中强制验证 observation 与 action receipt；其余策略 schema 的全面运行期验证和不可变
  episode store 仍属于 Phase E，不能把“JSON 可解析”称为已完成约束。

当前已实现本世婚姻与继承读取、巴勒莫战争闭环、原生存档/恢复、单代死亡结算、跨局策略记忆和单步自主循环。尚未完成的关键能力是
自然死亡实机终验、盟友战争的实际参战、动态战争目标比较、分割损失缓解，以及更多长期内政决策；游戏规则页视觉复核不阻塞这些玩法。

### 双后端与 MCP 高效模式

智能体现在按“一套 planner、多个 I/O backend”演进，OCR/键鼠不会被删掉：

- `GameplayStepExecutor` 与共用 runner 已从 `_drive_opening` 抽离；视觉代码通过 callback 接入。
- `GameplayBridgeDriver` 统一 snapshot、semantic step、wait-for-change 与 capabilities。
- `HybridGameplayDriver` 对已经实现的步骤优先走 Mod/DLL 快桥，其余步骤回落 OCR/快捷键/鼠标。
- `xar-ck3-mcp` 使用官方 MCP Python SDK v2，提供 capabilities、diagnostics、snapshot、planner、execute-step、
  save-checkpoint、select/resolve-event 与 wait-for-change 等 typed tools，以及 `ck3://capabilities`、
  `ck3://state/current` 两个 resources。
- `vision-report` 只读现有 session；`vision-session` 通过该 session 的文件队列执行原有视觉步骤；`mod` 通过独立数据 Mod
  读取结构化玩家/日期 snapshot；`hybrid` 用 Mod 快照与视觉动作拼成一个可直接切换的 backend。x64 DLL 已闭合
  `CREATE_SUSPENDED -> PID injector -> named pipe -> resume` 全链，并已接入 CK3 runtime 与纯原生 session。

完整架构与 DLL 逆向锚点见 [CK3 本地 API 与 MCP 桥接可行性](../docs/ck3-local-api-mcp-feasibility.md)。

当前加固候选还增加了两项基础能力：crash 路径已有历史本机 GREEN；纯视觉路径已完成离线 sealed lifecycle，仍未向真实 CK3
发送输入：

- `crash-smoke` 使用外层验证器、可牺牲 supervisor、detached watchdog 三个逻辑角色；Windows venv 可在 outer 与
  supervisor 之间增加一个经完整命令行和进程身份认证的 interpreter redirector。outer 必须先固定真实 supervisor
  的进程句柄并回写 acknowledgement，subject 收到它之前不得启动 CK3；ready、ack 与 armed 同时记录 UTC 和
  跨进程可比的 monotonic 时间，实时路径强制严格顺序，离线回放只验证归档记录值与内部关系一致。在 CK3 已 resume、可见主菜单且
  单 mod load attestation 成立后，通过固定进程句柄终止 supervisor。CK3 与两个合成 Job 子孙必须全部退出、命名 Job
  必须销毁、watchdog 必须正常退出、全局 CK3 清点必须连续 5 秒为空，之后才允许 protected postflight。两帧主菜单、
  handoff、supervisor ready/ack、armed、三份控制文件、watchdog final、production manifest 和日志前缀均复制进证据包；
  在同一 validator、仓库代码与 OCR runtime 下，整个 run 目录可更换父目录后回放，但它不是跨机自包含归档。报告固定声明
  `integrity=unkeyed_sha256`、`historical_execution_authenticity_proven=false`：它能复算已实现的 schema/manifest 关系、PNG→OCR 与哈希链，
  但不逐项把每个 event payload 的全部语义重新绑定到 report；
  不能在没有密钥或外部信任根时证明一份历史归档必然来自真实执行；实机资格仍以本轮外层 verifier 的当场 OS 观察为准。
- `recover-stale-control --run-id <finalized-RED-run-id>` 只处理一次明确指定、已完成且仍保留 unsafe marker 的 crash RED。
  它重新认证源证据、当前全部进程均不存在、命名 Job 已销毁和双源 CK3 清点为空，再把 control 文件逐项按原哈希归档；
  unsafe marker 的 compare-and-swap 归档是最后一次 recovery 证据/控制提交，之后不再写 recovery report 或 artifact
  （锁实现仍可清理自己的 owner 文件）。恢复会生成独立 report，固定声明
  `historical_cleanup_proven=false`、`current_absence_proven=true`，绝不修改旧 report、把旧 RED 升成 GREEN，或在启动前自动清标记。
  write-ahead report 在 marker 提交前已含条件式 `ok=true`；该字段不能单独视为成功，必须由
  `validate_recovery_report()` 同时验证 active marker 已消失且归档 marker 的 SHA-256 匹配。
  旧 RED `20260821T211059Z-crash-833b9587` 已由恢复 `20260821T215805Z-recovery-46a3518c` 按此协议归档；
  旧 report SHA-256 未变，恢复只解除启动阻塞，不资格化那次 RED。
- Phase B 的纯视觉底座已经建立 PID/创建时间/可执行路径绑定的 CK3 窗口捕获、OCR/像素屏幕分类、短期 HMAC 分阶段授权、
  点击前后状态反证和 fail-closed 导航。`menu-smoke` 已接入专用 CLI、sealed supervisor 生命周期和公开 GREEN/RED 回放；当前
  动作白名单精确只有主菜单【新游戏】，并显式禁止大厅【开始】。权威输入 WAL 位于本次 run 的主 `events.jsonl`，不是独立
  UI 日志。无害 Win32 helper 与离线截图回放已经通过；真实 CK3 已发生过一次目标内鼠标移动，但还没有提交按钮输入，不能据此
  声称已经完成菜单导航或能开局。

上述段落保留 `menu-smoke` 的历史边界；功能性 `opening-smoke` 已在提交 `c8a27d5`、环境
`f54ca88ac450ae8d2c4d7401e115695069ac10781e2a37e8af14cc5d3521304d` 下取得首轮交易闭环 GREEN
`20260822T102802Z-opening-4cc459ce`。它依次完成【新游戏】、1066 罗贝尔、【开始】、接受【终末之契】、
【那么，开始此生】、策略选择首个祝福和策略选择首个咒痕，七次动作均为 `SendInput accepted=2/2`。本轮可见策略选择
【普通-生活方式：兵棋的余局（+500军事经验）】与【普通-生活方式：千面的哑剧（-1000谋略经验）】，最终连续两帧
识别 `map_hud`，随后完成 Job/tree/global inventory 清理。该 run 建立了首个可计分开局基线；下一功能切片是受控地图经营。

提交 `106278f`、环境 `f11b248ccc09bb80b5a9d92f0b9e3bc19646af333d21ccd0961183d583c09cbe` 的
`20260822T111130Z-opening-a27391b9` 进一步完成第八次 `SendInput accepted=2/2`：从地图 HUD 点击玩家头像，双帧确认
`player_character`。可见 OCR 识别罗贝尔本人、配偶、玩家继承人与 7 名臣属；最终截图人工复核为正确的玩家角色页，
退出后的 Job/tree/global inventory 清理仍为 GREEN。这是第一条真实地图内状态读取能力。

提交 `67aa50a` 的 `20260822T153549Z-opening-69644bad` 已完成 17 个真实动作：七步开局、玩家角色页读取、
军事【权威重心】选择与确认，并以速度 5 将日期从 1066-09-15 推进至 10-10 后暂停；最终 `map_hud`、
`elapsed_days=25`、`ok=true` 且进程树归零。执行器随后改为优先使用 CK3 原生快捷键：事件选项用
`Shift+数字`，角色页用 F1，确认用 Enter，关闭用 Esc，速度用 `5`，暂停/继续用 Space；鼠标只保留
主菜单、书签和没有可靠直达键的生活方式控件。提交 `d99331a` 的实机 `20260822T155740Z-opening-b33c1328`
已确认该链 GREEN：11 个键盘动作和 6 个鼠标动作全部到达正确后置画面，总耗时约 216 秒，日期推进 17 日，
最终 `map_hud` 且清理完整。提交 `bdd9956`、环境
`e0187715652fe969bfa36b306d3a432752cbc89133ef8c64b83ae07ae2c3b031` 的实机
`20260822T162844Z-opening-33bdd96f` 又识别到首个普通事件【诺曼人的西西里】及三个可见选项，使用
`Shift+1` 选择【所有这些，甚至还有更多，都会是我的！】并确认事件消失；全程共 18 个动作，其中 12 个键盘、
6 个鼠标，日期从 1066-09-15 推进至 11-06 后暂停，最终 `map_hud`、`ok=true` 且清理完整。下一价值切片是
持续处理多个事件，并依据可见收益而不是固定第一项选择。该切片已由提交 `f6bba36`、环境
`eb7479741e26a9688720951129b8c376cf19b1471cab2ffd7ea2490939ec6ec0` 的实机
`20260822T170117Z-opening-eaeef47a` 完成：目标三个普通事件，实际处理【诺曼人的西西里】以及四页连续疾病事件链，
共 5 个事件页、22 个动作（16 键盘、6 鼠标），日期推进 451 日至 1067-12-10 后暂停并完整清理。选项按可见文本
收益评分后使用 `Shift+N`；等待期只对事件区域做不落盘 OCR 预检，同一真实截图约 `0.172s`，全屏约 `0.456s`，
五事件 run 的归档大小仍与此前单事件 run 基本相同。下一价值切片是扩大事件类型覆盖并加入地图经营决策。

提交 `75642ca`、环境 `e3f8504582f19b19cd0ed10b3d3b04303c519064e20be6eddd8546631df66135` 的实机
`20260822T172415Z-opening-d20b8adb` 又把原版快捷键用于地图经营读取：处理【诺曼人的西西里】后暂停，依次用
F2/F3/F4/F8 打开并关闭【我的领地】【军事】【内阁】【决议】，每个面板均由两帧 OCR 确认并归档可见文本。26 个动作中
20 个为键盘、6 个为没有可靠直达键的开局鼠标动作；可见状态包括 254 金、约 2203 兵、4.9 月收入、五席内阁和当前决议
列表。带红叉的【扩大公国领地】等决议没有被误当成可执行动作。最终为暂停的 `map_hud`，tracked cleanup 完整。
下一价值切片原定从 F2 领地面板进入可建造直辖领地，读取实际建筑候选并选择负担得起的经济建筑；该切片已由提交
`c16e22f`、环境 `86d5e8847bd0591dfa4f9811544f7eb979b4da1d79c63254fca50b79e8f2f3a4` 的实机
`20260822T190656Z-opening-bfa943a7` 完成。执行器用 F2 进入领地面板，在没有原生快捷键的普通空建筑槽仅使用一次
固定 UI 合约点击，再从三个可见候选中按经济文本选择第 3 项【等级1：简易牧场】；候选显示成本 150、赋税
`+0.50/月`，点击【修建】后由地产行的【个月内完工】文案确认建设已经启动。全程 31 个动作中 22 个为键盘、
9 个为没有可靠直达键的可见控件点击，最终返回暂停的 `map_hud`，报告 `ok=true` 且 tracked cleanup 完整。

提交 `226d80e` 曾在同一环境 `219c77d9d5e8b7e50e32314f2f8fcb57130fedc3c853880677e4149c425556ba`
下通过 ordinary `20260822T005515Z-03f296c7` 与 post-resume crash
`20260822T005727Z-crash-38023ffc`，随后执行第一次真实菜单竖切
`20260822T010001Z-menu-193c8062`。它在任何 UI WAL、receipt、鼠标移动或 `SendInput` 前因
`bound CK3 client lost foreground; refusing input` 安全 RED；tracked cleanup、全局空清点和 protected/production postflight
均通过。该次运行促成了 DMTF/UTC ISO 进程创建时间的严格同一时刻比较、DLC mount 引擎顺序回放，以及持久化
`foreground_activation_planned -> armed -> finished` 的一次性 exact-HWND 前台事务。事务只允许一次 direct
`SetForegroundWindow` 与至多一次 caller→当前 foreground thread 的严格 attach/detach fallback；detach 或身份状态未知时
立即 RED，绝不重试。`GetLastInputInfo` 相等只是一项采样观察，不是“无人输入”的证明。修订后的公开 validator 已能原样接受
这份历史 RED，但不会把它升级为 GREEN；当前 runtime 已改变，所以上述资格不能用于下一次真实尝试。

加固提交 `af3df58` 在新环境 `31e68f6d8e439643a7ff8fcb6029d72f93a85ead2d74bb58d24042c382753f72`
下重新取得 ordinary `20260822T020912Z-7dc8269d` 与 crash
`20260822T021144Z-crash-b010d18c` 两项 GREEN；随后唯一一次菜单 run
`20260822T021436Z-menu-c9b3d667` 因客户区右下角存在 `(2130,1095)-(2560,1392)` 的外部置顶窗口而安全 RED。
公开回放确认主链没有 `visible_main_menu_attested`、任何 `ui_*` WAL、action receipt、鼠标移动或 `SendInput`；cleanup 与
protected/production postflight 完整。运行后的只读活体查询把 HWND 定位为 Kaspersky `avpui.exe` 的 WPF `AlertWindow`，但该
身份没有被原 run 归档，只能作为事故诊断，不能升级为历史证明。自主玩家不会自动关闭或点击安全软件通知，同一 run/候选也不重试。

提交 `38fd5fa` 把 ordinary 证据升级为 self-contained format v2；新环境
`75f8c6b0271d82183ba2d345a48e4a191e36ea2fd85d98b9a8d30327ce6c7367` 下 ordinary
`20260822T033531Z-9a595275` 与 crash `20260822T033759Z-crash-f289e776` 均通过公开回放。唯一一次菜单 run
`20260822T034104Z-menu-49f9b8bd` 在输入前丢失前台并安全 RED：前台事务曾以 `already_foreground` 完成，随后两份
2560×1440 全黑启动帧都通过 capture 前后 foreground/遮挡 guard，第三次 capture 的前或后 guard 才检测到丢焦。主链没有
`visible_main_menu_attested`、任何 `ui_*`、navigation、action/receipt 或 `SendInput`，清理与 postflight 完整。该版本只保存了固定
错误字符串，未保存失败瞬间的实际 foreground HWND/PID/TID，因此不能事后断言是外部进程、同 CK3 进程的另一 HWND 还是空前台；
在补齐结构化 loss snapshot 前不得盲目重试。

提交 `c8531be` 已把这条诊断链接入 sealed lifecycle。它在环境
`925b8deafa0053fffb2522b86770bb377fbbb5e28a28e53a559ce1ecc40584cc` 下取得 ordinary v2
`20260822T045930Z-6ce9874f` 与 crash `20260822T050200Z-crash-95b63c14` 两项公开回放 GREEN，随后只执行一次
`20260822T050447Z-menu-0eae4606`。该 run 在 `capture.pre_grab`、sequence 2 保存了一个与目标同为全屏矩形、
不同 PID、class 精确为 `Ghost` 的 actual foreground；其 owner `OpenProcess` 被拒，所以进程 image/creation 只能归档为
`unknown`，绝不能事后追认成 `dwm.exe` 或把 Ghost 当 CK3 代理。主链没有 `visible_main_menu_attested`、任何 `ui_*`、
navigation、action/receipt、鼠标移动或 `SendInput`；Job、watchdog、control、双源 inventory、protected 与 production
postflight 全部通过。这是结构完整的安全 RED，不是菜单导航成功，也不允许原 run 或原候选重试。

提交 `39860a0` 在任何 `SetForegroundWindow`、`AttachThreadInput` 或输入前增加 exact-target 响应稳定门：总等待不超过
30 秒且受场景 deadline 限制；以 250 ms cadence 对目标 HWND 发送
`SendMessageTimeoutW(WM_NULL, SMTO_BLOCK|SMTO_ABORTIFHUNG|SMTO_ERRORONEXIT)`，`IsHungAppWindow=true` 只作 veto。
只有至少 21 个响应样本在 250–500 ms 间隔内连续覆盖至少 5 秒才可继续；hung、无响应、调度空洞、进程/窗口/输入 tick
变化都会清零或直接 RED。门前做完整 WMI/唯一窗口认证，门内与门后只用 pinned handle 和 exact HWND/PID/TID/rect 本地复核；
last sample→gate finish、gate finish→每次窗口 mutation/完成也都限制为 500 ms。证据嵌入 finished attestation，并以
`foreground_protocol_version=2` 要求所有新 GREEN/RED 的 completed foreground 都不可删除该 gate；无版本兼容只钉住四份既有
零输入 RED 的 run ID 与 final-event digest。该提交在环境
`d343278a3e2d046c7aadc2ad90d75640aadca483b3192801234f4e8a096befa2` 下取得 ordinary v2
`20260822T060233Z-be4794fb` 与 crash `20260822T060508Z-crash-123c80f3` 两项 GREEN，随后只执行一次
`20260822T060758Z-menu-fc73b5c5`。

该真实 run 在稳定主菜单、fresh frame 和 `ui_input_armed` 后把鼠标移到 `(600,558)`，随后 hover OCR/截图完成；最终提交前，原
caller 控件 token 已约 5.85 秒，超过单一 5 秒 TTL，故以 `visible control token expired at input submission` 安全 RED。
receipt 明确记录 `pointer_input_may_have_occurred=true`、`button_click_may_have_occurred=false`、`send_input.accepted=null`：
`SendInput` 没有被调用，没有 LEFTDOWN/LEFTUP，也没有点击。Job 由 1 排空至 0，进程树、watchdog 和四类 control 均消失，
双源 CK3 inventory 为空，protected baseline 与 production tree 后置复核通过。原 run/候选不得重试，且这不是书签页 GREEN。

根因不是屏幕或身份漂移，而是一个 caller 的 5 秒授权错误地横跨 fresh capture、WAL、鼠标移动和较慢的 hover OCR。修订保持
caller token 的 5 秒 TTL，但它只负责动作 admission；fresh frame 再签发 5 秒 `fresh_move` lease，绑定该帧、target、caller
父授权与本动作绝对 deadline，hover frame 再签发 5 秒 `hover_click` lease，绑定该帧、同一 target、fresh lease 父授权与同一
deadline。两份 lease 都一次性消费，分别紧邻鼠标移动与 `SendInput`；任何 capture 在绝对 deadline 后才返回也必须拒绝，
postcondition 只能使用动作 deadline 的剩余时间，不能重新获得完整 timeout。新报告写入
`visible_action_protocol_version=2`，公开回放复算分阶段授权、父链、WAL 和时序；上述旧 run 仅以 run ID 和 final-event digest
`aef3dc4d0dc6bbcaf117dfaabc1d27b263309ec2f58cab5b9a14aa4ffb46396d` 固定只读兼容，不能通过删除版本字段授权新输入。
该协议已在 2026-08-22 的真实菜单候选中让 `SendInput` 完成 2/2 提交；其后发现的问题分别来自隔离 profile
遗漏中国教程提示开关，以及公开 validator 错把已归档的 post-click 转场帧当成 capture sequence 断裂，而不是 lease 再次过期。

下一次输入资格只接受 self-contained format v2 ordinary GREEN；live 扫描与新 menu archive 都拒绝 v1。v1 仅为已经冻结、外层同样为
RED 且没有任何 `ui_*` 输入 WAL、bookmark、navigation、action/receipt 的历史菜单 run 保留只读兼容；纯观察 PNG/JSON 可以保留，
绝不能据此授权新输入。v2 最终报告先在同目录临时文件完成 flush/fsync，成功后才原子替换 provisional，避免 barrier 失败后留下
可被下一次命令误认的 GREEN。所有 SHA-256 仍是无密钥内部一致性证明，不是历史真实性签名。

上述改动改变了受指纹保护的 runtime，因此旧提交的 Phase A 三连只证明历史冻结候选，不自动为后来实现背书。
runtime 实现提交 `98d55caf3ed4a398b0a3bd7bc8e6ee16591d8f26` 已重新准备 profile，并在同一环境 SHA-256
`5e7fb63ef98a7fd802caa864b64c593053c68bfb5f1798321cde6b02d6cd0d5f` 下通过普通 `smoke`
`20260821T215910Z-780cd6cb` 与 post-resume `crash-smoke` `20260821T220127Z-crash-adc0ac63`。
这些历史 ordinary report 是 format v1；对应的 `validate_smoke_report()` 只重算无密钥事件链、final tail 与 finalized/ok，load、cleanup、
protected 和 production 硬字段当时另行逐项核对。新生成的 format v2 ordinary report 则把两帧 PNG/OCR、初次与退出后 debug 前缀、
diagnostics、进程/Job/控制文件、protected snapshot、production manifest 和完整 artifact inventory 都改为 run-relative 归档，并由同一
公开 validator 深度回放。`validate_crash_report()` 继续回放 crash 归档的 schema 与内部一致性。两类资格仍只证明单 mod 可见主菜单、
受控退出与崩溃回收，`valid_score_episode=false`，不证明 Growth+100 已在大厅实际采用。ordinary/crash 的历史主菜单观察器可能用合成
Alt 获取前台，因此只能说“没有作出游戏内玩法选择”，不能把它们写成全程零输入证据。当前 Phase B
改动已改变 runtime 指纹，因此这对旧 run 只能作为历史证据，不能资格化尚未提交的新候选。最新测试数以本次提交前的完整
`unittest discover` 报告为准；离线/无害 helper 通过不能替代同环境本机门禁。

## 运行

使用项目现有桌面依赖环境：

```powershell
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" doctor
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" prepare-profile
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" verify-profile
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" smoke
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" crash-smoke
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" menu-smoke --timeout 180
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-smoke --ordinary-events 3 --timeout 900
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-replay --observation <observation.json> --check steward-development-active
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-step --step steward-development --timeout 240
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-step --step economic-event-cycle --timeout 240
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-step --step save-checkpoint --timeout 240
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-step --step restore-checkpoint --timeout 240
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-step --step auto-turn --timeout 240
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-step --step auto-run --timeout 900
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-step --step death-terminal --timeout 240
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" strategy-review
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" opening-dev-session --timeout 21600
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" recover-stale-control --run-id <finalized-RED-run-id>
& "tools\.venv\Scripts\python.exe" -m pip install "mcp==2.0.0"
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\mcp_server.py" --driver vision-report --transport stdio
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\mcp_server.py" --driver vision-session --transport stdio
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\mcp_server.py" --driver mod --userdir <isolated-ck3-userdir> --transport stdio
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\mcp_server.py" --driver hybrid --userdir <isolated-ck3-userdir> --transport stdio
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\mcp_server.py" --driver native-headless --pipe-name '\\.\pipe\xar_ck3_bridge_mcp' --transport stdio
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\mcp_server.py" --driver hybrid-fallback --pipe-name '\\.\pipe\xar_ck3_bridge_mcp' --userdir <isolated-ck3-userdir> --state-dir <XarAutoplayer-state> --transport stdio
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" --bridge-mode native-headless --bridge-pipe '\\.\pipe\xar_ck3_bridge_mcp' --bridge-dll <xar_ck3_bridge.dll> --bridge-injector <xar_ck3_bridge_injector.exe> native-session --timeout 21600
```

`vision-session` 与 `hybrid` 需要由新代码启动的 `opening-dev-session`；它在 run 目录公开 `bridge/inbox`/`outbox`，MCP 请求与
stdin 共用同一主线程命令处理，因此策略、MCP daemon 和大多数 Python driver 改动不要求重启这一局 CK3。数据 Mod 原型位于
[`mod_bridge/`](mod_bridge/README.md)，原生桥与离线注入路线位于 [`native_bridge/`](native_bridge/README.md)。

`native-headless` 是纯原生模式：只使用注入 DLL 的 named pipe 状态与命令，缺少能力时返回 `unsupported`，不会调用 OCR、
键盘、鼠标、窗口激活或视觉 fallback，因此它是 CK3 最小化运行的目标模式。`hybrid-fallback` 是明确允许回落的另一配置，顺序为
native → data Mod → vision session；窗口最小化或窗口可见性无法确认时，vision 分支会拒绝执行，而不会把 CK3 偷偷恢复到前台。
两者都通过 `ck3_get_capabilities` 公布 mode、fallback、最小化与当前 native action 列表。当前 exact-build native DLL 已发布
日期 tick、1–5 档速度、暂停、地图就绪、本地玩家、玩家角色生死、当前事件、待处理角色互动与 checkpoint
submission snapshot，并开放 `pause-map`、`resume-map`、`set-speed-1..5`、`select-event-option-N`、
`accept/reject-pending-character-interaction`、`save-checkpoint` 与进程级 `restore-checkpoint`。MCP 还提供
`ck3_auto_turn`，用同一 planner 选择并执行一次当前可用的原生步骤。2026-08-23 已在真实
CK3 1.19.0.6 的最小化窗口上完成无 OCR/键鼠实测：90 次复合回合推进 94 个游戏日；连续后台推进发现实例 14 的
五选项事件并以原生命令选择第 1 项，随后观察到实例 15；原生 checkpoint 落盘为约 63 MB 的
`xar_checkpoint.ck3`，历史新进程曾用 `-continuelastsave` 恢复到同一 `date_raw=53167488`。当前 typed restore 已改用
`-loadsave=xar_checkpoint` 直接指定该文件，并绑定 size/SHA、保存日期与本局角色，避免后续 autosave 改变“最后存档”。native driver 会锁定首次可玩
snapshot 的 `episode_character_id`，restore 后仍保持该 ID；玩家死亡或 CK3 已切换 played `CharacterID` 都在本项目的
一代制规则下直接产生 `death-terminal`，不会继续扮演继承人。可选的 primary-heir 字段只用于当前生命的策略信息。
原生战争层现已支持显式枚举宣战理由、宣战、征兵、行军、强制要求与解散军队；2026-08-23 的最小化实测中，
`declare-war-29097-11-0` 后 snapshot 真正出现 `war_id=16777290`，CK3 进程仍响应且窗口保持最小化。主动婚配查询与提交协议也已接入；
同次实测查询正常返回但该存档没有可用候选，因此主动婚配提交仍标为待实机候选验证。收到的角色互动已可原生接受或拒绝。

纯原生模式需要两个并行进程：先启动 `mcp_server.py --driver native-headless` 建立 pipe server，再用上面的
`agent.py ... native-session` 创建 suspended CK3、注入 DLL 并恢复游戏。`native-session` 监管 PID/Job，stdin 接受
`status`/`stop`；同时在 `<state>/native-session/bridge` 接受纯原生 `restore-checkpoint`，停止当前受管进程后以同一
pipe/DLL 和 `-loadsave=xar_checkpoint` 重启。若旧进程的 CK3 窗口已最小化，生命周期 supervisor 会把新 PID 的窗口也恢复为
最小化。MCP driver 只有观察到新连接代次中稳定的 `map_ready` snapshot，并核对保存日期、角色与 checkpoint bytes 后才返回恢复成功；整个路径
不导入 vision、OCR 或输入模块。2026-08-24 的实机闭环已验证 PID `25336→126204`、日期
`53168688→53168664`、generation `1→2`，且新旧 SDL 窗口都保持 `IsIconic=true`。它拒绝
`hybrid-fallback`，且该步骤不会隐式回落。允许视觉回落时仍使用
`opening-dev-session --bridge-mode hybrid-fallback ...`，因为只有该命令提供 vision-session 的主线程 inbox/outbox。

日常 gameplay 开发不再把每次修改都当成发布验收。`opening-replay` 在不启动 CK3 的情况下直接重放已归档 OCR；
`opening-step` 从隔离 autosave 的主菜单【继续游戏】进入，只执行一个步骤；`opening-dev-session` 则保持一个受控 CK3
进程默认保持六小时存活，从 stdin 接收建设、存档恢复、婚姻、当前生命继承评估、战争、死亡结算、
`strategy-review`、`status` 和 `stop`，每次 gameplay 命令前热加载 perception/control/policy
模块。这样修改画面判断或策略后可在同一进程继续测试。只有 mod/runtime/启动参数改变、需要确定性复位，或功能里程碑验收时，
才重新执行完整 cold-start 与 ordinary/crash/opening 链。development step/session 明确不构成 release qualification 或有效得分局。

### 当前可玩能力（2026-08-23）

同一个未重启的 CK3 development session 已实际完成：从原生存档恢复、读取罗贝尔的配偶/继承人/7 名子女与分割继承风险、
缔结丹麦订婚、发动并以 100% 战争分数赢得巴勒莫圣战、解散军队，以及用 CK3 原生暂停菜单保存四个检查点。战争的
`war-move-palermo` 旧命令名现兼容地转到已实测成功的“搜索巴勒莫头衔 → 悬停确认堡垒 → 右键进军”流程，不再使用失败过的
裸地图坐标。

本项目按一代制 roguelike 运行：玩家死亡即结束本局，不规划或执行继承人玩法。有继承人时，原生【继续扮演】只作为让 mod
延迟投递【轮回终结】结算事件的技术载体；智能体将速度降到 1、只等待结算、记录最终分数，继承人 gameplay action 固定为 0，
随后立即返回主菜单。无继承人时则直接使用注入原生继承窗的【退出到菜单】。每个终局摘要写入
`%LOCALAPPDATA%\XarAutoplayer\strategy\one-life-history.json`，`strategy-review` 可在不绑定 CK3、不跑 OCR 的情况下读取上一局
战争、婚姻、分割风险、检查点和分数，并生成下一局优先级。死亡流程已有历史实机截图重放与完整模拟链测试；当前常驻存档尚未
自然死亡，因此不得把它写成已完成的死亡实机验收。

`auto-turn` 已把上述离散命令接成单步自主循环：根据当前 session 的成功结果选择尚未完成的王朝、婚姻、战争或存档里程碑；
里程碑完成后进入 `life-advance`，每次用速度 5 推进一个约 10 秒的现实时间窗口，处理可见事件并保证结束时暂停，每三个推进回合
自动生成一次原生 CK3 存档。实机同一 PID 已完成多次自主推进，并自动保存
`阿普利亚公爵，罗贝尔_1068_09_24.ck3`。随后自主回合识别并处理真实事件【锈迹斑斑的工具】，把日期推进到 1069-01-21，
再自动保存 `阿普利亚公爵，罗贝尔_1069_01_21.ck3`。普通事件、盟友参战和死亡终端共用一次预览 OCR 后，实机回合从 41.3 秒降到
26.75 秒。第一版 180 秒事件等待曾把地图留在运行态，并漏掉丹麦【召集加入战争】信函，造成盟友
关系实际下降 20；现有循环把无事件视为正常有界结果、主动暂停，并单独识别外交信函，优先用 `Shift+2` 履行本世联盟。该修复来自
实际玩法损失，不是理论归档加固。

常驻 `opening-dev-session` 的标准输入还接受 `auto-run N`（`1..20`，省略 N 默认 3）：它连续执行 N 个 `auto-turn`，每个子回合
保留自己的规划、动作与结果；普通错误立即停止，只有已知的可见事件打断或死亡终局会转入下一策略步骤。实机 `auto-run 2` 已连续处理
【锈迹斑斑的工具】两页事件；后续另一批次先按历史自动保存
`阿普利亚公爵，罗贝尔_1069_05_08.ck3`，再把日期推进至 1069-06-25。持续模式因此不需要人工逐条重复发送 `auto-turn`。

默认运行状态在 `%LOCALAPPDATA%\XarAutoplayer`，可用 `XAR_AUTOPLAYER_STATE_DIR` 或
`--state-dir` 改写，但安全检查拒绝仓库、真实玩家目录、Steam userdata 与 Workshop 的父目录或子目录。

`smoke` 会在仓库外创建：

```text
XarAutoplayer/
  profile/
    mod/xar_autoplayer.mod
    mod-content/xar-production/
    player/game_rules/presets.txt
    dlc_load.json
    tutorial.txt
    xar-autoplayer-environment.json
  runs/<run-id>/
    events.jsonl
    report.json
    artifacts/
  recoveries/<recovery-id>/
    report.json
    artifacts/
  control/
```

## 安全与合法性边界

- 策略只能消费截图、OCR、模板结果和玩家可见 tooltip/账簿/事件/结算。
- `debug.log` 只由 supervisor 压缩成 enabled-mod 与 mount 证明，原文永不进入观察或策略层。Phase B 接入 policy 前必须实现
  单独进程与字段白名单序列化边界，不能只依赖 Python 模块约定。
- 禁止 debug mode、控制台、内存/存档解析、隐藏变量、acceptance marker/wire、教程位读取和回档重掷。
- Phase B 接入正式局后的目标契约是：未知屏幕只允许在已视觉认证暂停控件时暂停，否则留证并由 supervisor 终止；不采用
  验收 runner 的盲点恢复策略。当前 Phase A/候选只会等待【新游戏】两帧稳定 OCR，超时留证并在清理证明完成后终止，
  尚没有已接线的通用未知窗口暂停能力。
- 工程 smoke、识别调试和环境失败永不计入得分榜或训练策略结论。

## 分层架构

```text
supervisor: profile / production projection / PID / attestation / integrity
       ↓
perception: window capture / OCR / templates / screen classifier
       ↓
state: visible facts + uncertainty + temporal reducer
       ↓
control: safe action catalogue + precondition + postcondition evidence
       ↓
policy: survival / contract / dynasty / economy / war / XAR bargains
       ↓
episodes: append-only evidence / settlement / validity / metrics
       ↓
memory: cross-run retrieval / constrained reflection / strategy experiments
```

历史 Phase A 基线已落在 `src/xar_autoplayer/{environment,integrity,locking,rules,runtime,process_watchdog}.py`；加固 runtime 已重新通过
普通 smoke 与 crash-smoke。后续模块只有在上一层的结构/一致性测试和对应本机门禁都通过后才接入正式局，避免把固定坐标脚本误称为
会玩 CK3 的智能体。

## 路线图

1. **Phase A（已完成）**：committed candidate 已连续三次通过 production、非 debug、单 mod 主菜单 isolation smoke；每次都保留
   非零引擎 diagnostics 的原始证据，且受保护存储在退出后回到同一语义 baseline。原生 Windows Job/句柄测试和两次启动期
   fail-closed RED 覆盖失败契约；加固 runtime 的 resume 后 supervisor 崩溃注入也已通过本机门禁。
2. **Phase B（进行中）**：纯视觉菜单/大厅/规则页/地图 HUD 驱动；点击必须有后置反证。真实 `opening-smoke` 已完成
   主菜单 → 1066 罗贝尔 →【开始】→接受契约→首轮祝福/咒痕→地图 HUD→玩家角色页；下一竖切执行首个角色发展或宫廷治理动作。
3. Phase C：先完成“罗贝尔 1066 → 契约 → 当铺 → 首轮垂青 → 十年低风险经营 → 自然死亡结算”的首个合法竖切，
   再扩到多种角色类型的有效整局基线后退出本阶段。
4. Phase D：婚育、议会、生活方式、建设、宣战理由、军队和领地的分层规划器。
5. Phase E：不可变 episode、截图回放集、策略版本、局后复盘与少量受控实验。
6. Phase F：同一时间线保存续玩、崩溃隔离、资源预算与连续多局。
7. Phase G：按版本、DLC 指纹、政府、开局等级与余烬位阶分榜，持续优化真实最终分数。

Phase A 的 GREEN 只表示 `acceptance_claim=isolated_single_mod_visible_main_menu_only`。本机前端会枚举既有 Steam Cloud
存档 meta，因此即使 `cloud_save=no`，旧 PoD 存档中的规则和贴图引用仍会形成非零 `error.log`；enabled inventory 与 mount
反证证明 PoD 没有被加载。本 smoke 以 `clean_engine_boot_required=false` 和 `engine_diagnostics.zero_diagnostics=false`
记录这条边界，不把它升级为“零错误启动”。Growth+100 规则是否在
大厅实际采用、教程通知能否在正式局持续落盘，以及正常 UI 开局仍是 Phase B/C 的视觉硬门禁。

真实 Win32 helper-window 的 DPI、client/screen 坐标、Z-order、WMI 空路径与单批次 `SendInput` 门禁已经通过；UI 截图、双帧
观察、receipt、像素 patch、固定 contract 和主 `events.jsonl` 也已进入正式 menu report 与公开 validator。环境
`531e529f7b301330e902ecf7b44821a462a83ffd9dd4359b23a8482a73590057` 的真实 `menu-smoke`
`20260822T081240Z-menu-f3d8a8a5` 已 finalized GREEN：点击【新游戏】为 `SendInput` 2/2，随后两帧稳定识别书签大厅并完成清理。

玩法基线见 [knowledge/ck3/gameplay-v1.md](knowledge/ck3/gameplay-v1.md)，本 mod 的高分映射见
[knowledge/mod/growth100-scoring-v1.md](knowledge/mod/growth100-scoring-v1.md)。
