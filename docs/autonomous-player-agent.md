# CK3 自主高分玩家智能体路线图

## 状态与启动门槛

- 状态：**2026-08-21 正式启动；2026-08-22 历史 Phase A 冻结候选已通过三连复验，加固 runtime 已通过普通 smoke + post-resume crash-smoke；Phase B 可见 UI 驱动仍未实机输入，尚未形成有效得分局**。
- 实现目录：[`ck3_autonomous_player/`](../ck3_autonomous_player/README.md)。Python 包名 `xar_autoplayer`，运行状态固定放在仓库外。
- 提交 `11ab443050132341bb27f6f924d792772f397396` 的冻结候选已在同一环境指纹下连续三次证明 production、非 debug、
  单 mod 能够在隔离 profile 到达可见主菜单，并由 supervisor 终止后证明进程树归零；三次 `ck3_exit_code=1`，不证明
  游戏内 graceful exit。该 smoke 不是“会玩”，也不计入策略数据；证据清单见
  [Phase A 实机证据](autonomous-player-phase-a-evidence.md)。
- 原有 30–40 年被动 soak/stability/telemetry 仍是固定验收场景，不扩张成自主玩家，也不冒充数值平衡或智能体证据。
- 这是独立于 `tools/run_acceptance.py` 的长期工程。acceptance runner 证明机制是否正确；自主玩家负责在正常规则下长期游玩并尽量取得更高分，二者不得混用目标或测试入口。

当前 Phase A 退出证据：`20260821T180045Z-a3c49b20`、`20260821T180248Z-7ad2dd83`、
`20260821T180531Z-9c6bb34b`。三次共享环境指纹
`4a02303bea47dd23dd70d3577618031e075dfd4e4d5d94df713cb37e5d78e0ab`。三份事件链均重新计算 hash chain 并通过一致性校验，
报告语义硬条件另行逐字段断言通过；hash chain 不是有密钥的数字签名。

这组三连绑定旧冻结提交，只证明该提交的 Phase A。后来加固 runtime 实现提交
`98d55caf3ed4a398b0a3bd7bc8e6ee16591d8f26` 已重新准备 profile，并在同一环境 SHA-256
`5e7fb63ef98a7fd802caa864b64c593053c68bfb5f1798321cde6b02d6cd0d5f` 下取得普通 `smoke`
`20260821T215910Z-780cd6cb` 与 post-resume `crash-smoke` `20260821T220127Z-crash-adc0ac63` 两份 GREEN。
这只给该 runtime 的可见主菜单、单 mod load、受控退出与崩溃回收资格；两份均为 `valid_score_episode=false`，不能写成已会游玩。

加固前的三次探索性 GREEN：`20260821T162104Z-cf348a71`、`20260821T162305Z-9a403bc6`、
`20260821T162451Z-5e882b17`。它们早于新鲜日志 epoch、跨进程锁、认证 watchdog、Job Object 和扩展环境复核，只作为
问题发现记录，**不是当前 Phase A 退出证据**。

### Phase A 已固化的启动契约

- 用 `tools/build_release.py` 在仓库外专用 profile 内构建 production-only 投影，禁止直接加载开发树。
- outer descriptor 只含一个指向该投影的绝对 `path`，内层 descriptor 禁止 `remote_file_id`。
- `dlc_load.json.enabled_mods` 精确为 `["mod/xar_autoplayer.mod"]`；DLC 与 mod 分开记录，`disabled_dlcs=[]` 保留玩家拥有的 DLC。
- 游戏规则完整重建为当前原版 81 个声明默认 setting，加 `xar_on`、`xar_inherit_100`、`xar_score_growth`。
- 使用 `ck3.exe -gdpr-compliant -userdir=<专用 profile>` 非 debug 直启；同一 state 与同一 CK3 安装分别持有跨进程锁。
  启动前与退出后用 `tasklist`、WMI 双源清点 CK3；任一来源失败、格式异常或集合不一致都视为 unknown，而不是“没有进程”。
- unsafe marker 在 watchdog bootstrap 前建立；watchdog 先持有并复核 supervisor 的 PID、可执行路径和创建时间才写 ready。
  CK3 以 `CREATE_SUSPENDED` 创建，依次完成 kill-on-close Job 分配、WMI 身份复核、原子 launch record，并在 resume 前让
  双源全局清点精确只看见新 PID，之后才恢复主线程。record 绑定随机 nonce、父 PID、CK3 路径及 WMI 创建时间；崩溃清理只终止持有句柄后
  再次认证的进程对象，并要求五秒稳定空窗。只有 Job 成员为零、双源全局清点为空、watchdog 已认证退出且控制文件全消失，
  `stop_tracked` 才返回 `cleanup_proven=true` 的结构化 shutdown attestation；调用方只接受该显式合取。否则留下 unsafe marker、
  拒绝后续 prepare/launch 并禁止 protected postflight。
- 启动前删除隔离 profile 的旧日志；到主菜单后连续两帧 OCR 确认可见【新游戏】，再要求新日志只有一个 session marker、
  enabled inventory 精确单项、唯一隔离 mod mount、所有其他 mount 都在已安装 DLC descriptor 推导的白名单，未知 mount 为零；
  退出后再解析一次。该压缩证据只属于 supervisor，Phase B 前还须用独立 policy 进程和字段白名单形成能力隔离。
- 退出后反证真实 CK3 profile 顶层文件、player/rulers/正常存档与 Steam userdata 云存档条目回到 baseline，并连续稳定 5 秒；
  Workshop `ugc_*.mod` descriptor 内容哈希及已注册目标树的路径/大小/mtime 元数据只做退出后一次 baseline 比较。这不等价于
  Workshop 目标树完整内容哈希，也不等价于证明运行期间从未发生瞬时写入。持久 `tutorial.txt` 首次创建后不读、不清空、不回滚。
- selected-contract 指纹覆盖游戏 exe/launcher/原版规则、DLC descriptor、production source/tree/manifest、outer descriptor、
  关键 agent/build/watchdog 代码、解释器和包版本；正式 smoke 要求所有选中 runtime 与 production release source 文件均已被
  Git 跟踪且 clean。开发构建没有
  当前提交的真实 tag 时记录 `git_tag=null`，不得伪装 release。报告先写 `finalized=false, ok=false`；最终 hash-chain 事件落盘后
  还要逐项重算 digest、previous link 和 tail/report 绑定，全部通过才原子写成 finalized GREEN，避免中断留下假阳性报告。
- 2026-08-22 实测：Steam 客户端运行时，即使 `cloud_save=no` 且使用隔离 `-userdir`，部分直启退出会改写 `userdata/<account>/1158310/remotecache.vdf` 的顶层 `ChangeNumber`，稳定运行也会刷新文件时间；正式三连中 `ChangeNumber` 均为 `12→12`，只有 mtime 变化。智能体把这两个 Steam 自有元数据单独记入 before/after 证据并允许变化；比较前只规范化该整数，云存档条目的路径、大小、时间、SHA、同步状态及其余字节仍须完全一致。除此以外的 userdata 差异一律判失败。该结论为本机 1.19.0.6 + 当前 Steam 客户端实测，不回写或恢复真实文件。
- 同机还实测：`cloud_save=no` 不阻止主菜单枚举既有 Steam Cloud 存档 meta。旧 PoD 云存档中的 17 个规则 key 与两张贴图引用
  和 fresh `error.log` 逐项匹配；但 fresh enabled inventory 只有本 mod，其他 mount 均命中由已安装 `.dlc` descriptor 推导的
  白名单或唯一隔离 production tree，故这不是第二个 mod 被加载。Phase A smoke 明确允许归档这类非零诊断，并写 `clean_engine_boot_required=false`、
  `engine_diagnostics.zero_diagnostics=false`；GREEN 的窄定义仅是
  `isolated_single_mod_visible_main_menu_only`，不能称为干净引擎启动。

## 长期目标

建立一个专门游玩 CK3 与本 mod 的智能体。它通过截图、OCR、模板匹配和经过结果验证的鼠标操作感知并控制游戏，在不作弊的前提下完成整局游戏、读取死亡结算、总结经验、更新策略记忆并自动开始下一局。长期评价目标是有效局的真实最终分数持续提升，而不是只把流程走完。

智能体需要同时具备：

- 可靠的 CK3 UI 状态识别和机械操作能力。
- 战略层、中期经营层和事件选择层的分层决策能力。
- 对本 mod 计分、契约、祝福/诅咒、商店和继承机制的显式理解。
- 基于大模型的局后复盘、经验压缩、策略检索和假设生成能力。
- 无人值守地反复开局、游玩、结算、归档和恢复异常的能力。
- 可审计的分数、操作轨迹、截图、策略版本和模型调用记录。

## 不作弊边界

正式基准局只能使用玩家正常可获得的信息和操作。

| 允许 | 禁止 |
|---|---|
| production-only、非 debug 的正式 mod | 控制台命令、debug mode、acceptance/selftest 脚本 |
| 玩家可见 UI、tooltip、账簿、事件和死亡结算 | 读取内存、隐藏 scope、内部变量或未向玩家展示的随机结果 |
| 截图、OCR、模板匹配和鼠标操作 | 修改游戏/mod 脚本来影响当局结果 |
| 公开规则、项目公开计分文档和历局经验 | 修改存档、tutorial 位、游戏规则文件或 Workshop 缓存来增益 |
| 正常保存并在同一时间线继续游戏 | 回档重掷、复制存档分叉择优、死亡后撤销结果 |
| 局后读取玩家可见分数并做统计 | 用工程诊断日志为当局决策泄露隐藏信息 |

工程调试可以使用 debug 日志定位 UI 驱动故障，但该次运行不得计入分数榜、训练样本或策略优劣结论。

## 目标函数与有效局

- 主指标：死亡结算显示的真实最终分数。
- 次指标：跨存档余烬位阶、每游戏年得分、有效存活年数、契约完成度和分数组成。
- 有效局必须从合法新游戏开始，使用预先声明的角色类型、规则和 mod 版本，直至该统治者死亡并完成结算。
- 崩溃、UI 驱动失控、工程日志介入、规则漂移或作弊边界破坏的运行只记为基础设施失败，不参与策略评分。
- 不允许仅追求长寿掩盖低效率；比较策略时同时报告总分、分数/年和生存期。

## 计划架构

| 模块 | 职责 |
|---|---|
| 桌面监督器 | 启动/聚焦 CK3、看门狗、现场备份、崩溃恢复、资源和时限控制 |
| 感知层 | 截图、OCR、图标模板、窗口分类、地图/HUD/事件/人物/账簿状态抽取 |
| 动作层 | 鼠标移动与点击、滚动、拖拽、点击后像素反证、失败重试和证据截图 |
| 状态模型 | 把视觉结果归一为角色、资源、领地、战争、家庭、契约、交易和风险状态 |
| 策略规划器 | 制定长期目标，选择战争、婚姻、建设、生活方式、契约和商店策略 |
| 事件决策器 | 结合当前状态、风险预算、历史经验和可见 tooltip 选择事件选项 |
| 局管理器 | 新开局、规则/角色确认、周期推进、死亡识别、结算归档和下一局启动 |
| 经验记忆 | 保存结构化决策、结果、失败模式、策略版本、适用条件和置信度 |
| 大模型复盘器 | 局后总结得失、提出可验证假设、合并重复经验并生成下一局计划 |
| 评估器 | 校验有效局、计算指标、比较策略、生成趋势图和可复现实验报告 |

## 学习闭环

每一局生成不可变 episode 记录，至少包含游戏/mod/策略版本、角色和规则、关键时间点截图、结构化观察、动作及理由、结果反证、重大事件、死亡原因和完整分数组成。

局后由大模型执行受约束复盘：

1. 区分 UI 驱动失败、随机波动和策略错误。
2. 找出高收益决策、资源瓶颈、致死风险和错失机会。
3. 将结论写成带适用条件、证据局数和置信度的策略条目。
4. 对冲突经验保留双方证据，不因单局结果直接覆盖旧策略。
5. 为下一局只提出少量可检验变化，避免同时改变全部策略而无法归因。
6. 定期压缩长期记忆，保留原始 episode，不让摘要成为唯一证据。

策略提升使用跨局比较和预先声明的实验条件；禁止通过同一存档回滚选择最佳随机结果。

## 分阶段实施

| 阶段 | 内容 | 退出标准 |
|---|---|---|
| A. 隔离环境（已完成） | 专用 CK3 用户目录、production mod、固定分辨率/语言、认证看门狗、环境与存储反证 | committed candidate 已连续三次只加载本 mod 到可见主菜单；原生 Job/句柄测试与启动期 fail-closed RED 覆盖当前失败契约 |
| B. UI 驱动底座（进行中） | 窗口分类、OCR/像素反证、可靠点击、地图/HUD/事件通用恢复 | 首个单动作菜单竖切已完成离线 sealed lifecycle 与公开回放；尚未向真实 CK3 输入 |
| C. 合法基线玩家 | 固定规则策略完成开局、经营、事件、死亡和结算 | 至少完成多种角色类型的有效整局基线 |
| D. 分层规划 | 增加战争、婚姻、领地、经济、生活方式、契约和交易决策 | 决策均有可审计状态输入和理由，分数不低于固定基线 |
| E. 经验记忆与复盘 | episode schema、检索记忆、大模型局后复盘和策略版本化 | 新局能引用相关旧经验，错误经验可回滚和追踪来源 |
| F. 持续重复游玩 | 自动结算、归档、下一局、异常隔离、成本/磁盘/运行时上限 | 在无人值守窗口内连续完成多局且不破坏环境 |
| G. 高分优化 | 角色分层基准、受控实验、风险调整和排行榜 | 在固定基准上形成可重复的持续提升趋势 |

### Phase B 接线顺序（2026-08-22 候选）

1. 先用三个逻辑角色的 crash probe 验证 supervisor 在 CK3 resume 后消失时，kill-on-close Job 与 detached watchdog 能回收 CK3；
   Windows venv 可额外产生一个经认证的 interpreter redirector，但它不替代真实 supervisor 身份。outer 必须完成
   supervisor-ready → 精确句柄 pin → acknowledgement，subject 收到 acknowledgement 前禁止启动 CK3；三阶段同时记录
   UTC 与跨进程可比的 monotonic 时间。实时路径强制 `ready < acknowledgement < armed`；无密钥回放只能验证归档中的
   三个记录值和字段关系自洽，不能证明历史顺序真实发生。
   subject 把 CK3 及合成父子进程加入同一个 nonce 命名的 kill-on-close Job。外层验证器不持有 Job handle，只固定
   supervisor、CK3、合成父、合成子、watchdog 的精确进程句柄；
   命名 Job 对象销毁、五个句柄退出、watchdog 返回 0、四类控制文件消失、双源 CK3 清点连续 5 秒为空，必须全部成立。
2. crash probe 的策略输入仍为空。`debug.log` 前缀只被归档并复算单 mod/mount 证明，不传给 UI 或策略层；该运行明确
   `valid_score_episode=false`。清理合取未完成时禁止 protected postflight，并保留 unsafe marker。
   对这种 finalized RED，只能显式运行 `recover-stale-control --run-id <run-id>`：它在双锁内重新验证源归档、所有记录进程
   当前均不存在、命名 Job 不存在和双源 CK3 清点为空，随后按哈希归档 control 文件并把 unsafe marker 的 CAS 作为最后一步。
   恢复报告只证明 `current_absence_proven=true`，固定保留 `historical_cleanup_proven=false`；源 RED 字节不变，也不会获得
   `cleanup_proven` 或有效局资格。write-ahead report 的 `ok=true` 只是一项条件式声明；必须由 `validate_recovery_report()`
   同时观察 active marker 已不存在、归档 marker 哈希匹配才成立。
3. 视觉驱动先只接 `main_menu -> bookmark_lobby`。观察必须绑定 CK3 PID、WMI 创建时间、可执行路径、HWND、client rect 与
   2560×1440 简中 UI 契约；当前合成负例、历史截图回放与无害 Win32 helper 中的转场叠影、已知教程/确认 modal、遮挡或
   多屏同时命中会返回 unknown。真实 CK3 上仍须继续冻结新负例，不能把这组结论扩大成所有 modal 已被识别。
4. 动作只接受由当前 observation 签发、5 秒内有效、一次性消费的控件 token。点击前先重新捕获 fresh frame 并重定位；在任何
   鼠标移动或游戏输入前把保守的 `ui_input_armed` 写入并 fsync 主 `events.jsonl`，再执行 hover 与最终无 OCR、无落盘像素/
   前台命中复核。点击后必须连续两帧看见声明的下一屏。
5. 第一轮实机探索只探测并冻结大厅【游戏规则】、类别【游戏模式】、三个 production 规则卡与 Apply 的实际 bbox/文案。
   在规则页尚未完成同卡标题—选项关联验证前，禁止点击大厅【开始】。

真实 Win32 helper-window 的 DPI、client/screen 坐标、Z-order、WMI 空路径与单批次 `SendInput` 已实测；固定 UI contract、
截图、双帧 observation、receipt、hover/final patch 和主 `events.jsonl` 也已进入 menu report 与专用公开 validator。首次真实
点击前剩余门禁是：提交当前 runtime、重新 `prepare-profile`，随后在同一新 environment 下依次取得 ordinary smoke 与
post-resume crash-smoke GREEN；最后才允许一次真实 `menu-smoke`。未知模态、真实 CK3 hover patch 漂移或后置状态超时都只
保留 RED，不得重试。

第一次真实菜单竖切已按这套资格门禁运行：提交 `226d80e`、环境
`219c77d9d5e8b7e50e32314f2f8fcb57130fedc3c853880677e4149c425556ba`、ordinary
`20260822T005515Z-03f296c7`、crash `20260822T005727Z-crash-38023ffc`，菜单 run 为
`20260822T010001Z-menu-193c8062`。它在任何 `ui_*` WAL、action receipt、鼠标移动或 `SendInput` 前检测到 CK3
不在前台并安全 RED；cleanup、全局空清点和 protected/production postflight 完成。事故没有产生点击，也不算一次成功导航。
修订后的窗口协议在唯一 HWND 绑定后先持久化 `foreground_activation_planned/armed`，只允许一次 direct
`SetForegroundWindow` 与至多一次 caller→当前 foreground thread 的严格 attach/detach fallback，成功再写 finished
attestation；attach/detach、身份、前台或采样状态任一未知都不重试。COM WMI 的 DMTF 创建时间与 PowerShell CIM 的 UTC ISO
创建时间按严格解析后的同一 UTC 时刻比较；DLC mount 保留引擎日志顺序但仍要求白名单和不重复。旧 RED 已能原样公开回放，
但修订改变 runtime 指纹，下一次尝试前必须重新提交、prepare，并取得新的同环境 ordinary/crash 双 GREEN。

提交 `af3df58` 随后在新环境
`31e68f6d8e439643a7ff8fcb6029d72f93a85ead2d74bb58d24042c382753f72` 下取得 ordinary
`20260822T020912Z-7dc8269d` 与 crash `20260822T021144Z-crash-b010d18c` 两项 GREEN。唯一一次后续菜单 run
`20260822T021436Z-menu-c9b3d667` 在稳定主菜单观察前发现客户区被外部置顶窗口遮挡而安全 RED；主链只有 single-mod 与
foreground planned/armed/finished，之后直接 tracked stop/postflight/final，没有任何 `ui_*`、receipt、鼠标移动或 `SendInput`。
事后只读 Win32/WMI 活体查询将该 HWND 定位为 Kaspersky `avpui.exe` 的 WPF `AlertWindow`，但原 run 只绑定了 HWND 与矩形，
因此产品身份只是诊断线索而不是可回放历史证明。合法自主玩家不应沿用 acceptance runner 的已知弹窗自动关闭逻辑；外部窗口必须
由用户自行处理，原 RED 和原候选均不得重试。

普通 smoke 归档随后升级为 format v2：所有视觉、双 debug 前缀、diagnostics、process/shutdown、protected 与 production 证据均为
run-relative artifact，最终 event 绑定 report-body hash，最终 report 先在同目录临时文件完成 flush/fsync 后才原子替换 provisional。
公开 `validate_smoke_report()` 对 v2 从 PNG 重跑固定 OCR、从日志字节重解析 load/诊断并复核完整 manifest；v1 仍只按历史浅契约读取。
live 菜单资格与新 menu archive 一律要求 v2；只有外层同样是 RED 且没有任何 `ui_*` 输入 WAL、bookmark、navigation、action/receipt 的
冻结历史 run 才能只读兼容 v1；纯观察 PNG/JSON 可以保留，但绝不据此授权输入。该深回放仍是无密钥 archive schema/内部一致性证明，
不是历史真实性签名。

提交 `38fd5fa` 随后生成首份 self-contained ordinary v2 资格：环境
`75f8c6b0271d82183ba2d345a48e4a191e36ea2fd85d98b9a8d30327ce6c7367`，ordinary
`20260822T033531Z-9a595275`，crash `20260822T033759Z-crash-f289e776`。两者公开重放均 GREEN 后，只执行了一次
`20260822T034104Z-menu-49f9b8bd`。该 run 的 foreground transaction 为 `already_foreground`，没有 SetForeground/attach/合成输入；
两次已归档观察均是通过前后窗口 guard 的 2560×1440 全黑启动帧，第三次采集的前或后 guard 才报 foreground lost。事件链没有 visible 主菜单、
`ui_*`、navigation、action/receipt 或 SendInput，退出清理与 postflight 完整。旧异常只含字符串，无法把丢焦绑定到实际 HWND/PID/TID；
这项未知必须由下一提交的只读瞬时 snapshot 闭合，而不是以延时或再次抢前台猜测性重试。

提交 `c8531be` 已把该 snapshot 接入 sealed lifecycle，并在新环境
`925b8deafa0053fffb2522b86770bb377fbbb5e28a28e53a559ce1ecc40584cc` 下先后取得 ordinary v2
`20260822T045930Z-6ce9874f` 与 crash `20260822T050200Z-crash-95b63c14` GREEN。唯一菜单 run
`20260822T050447Z-menu-0eae4606` 在 `capture.pre_grab`、sequence 2 冻结 actual foreground：raw/root HWND 为全屏
`Ghost` class、PID 与绑定 CK3 不同；owner `OpenProcess` 被拒，因此 process identity 明确为 unknown，不能补写成事后查询到的
`dwm.exe`，也不能把 Ghost 当 CK3 代理。该 run 没有 visible 主菜单、`ui_*`、navigation、action/receipt 或 SendInput；cleanup、
双源空清点、protected 与 production postflight 均通过，所以它是安全 RED 而非导航成功。

下一候选在任何前台 mutation 前新增响应稳定门：exact CK3 HWND 的 `WM_NULL` 必须以 250 ms cadence 获得至少 21 个、
相邻 250–500 ms、连续跨度至少 5 秒的 responsive 样本；`IsHungAppWindow` 仅作 veto，任一 hung/nonresponsive、调度空洞、
identity/geometry/input-tick 变化或 30 秒/场景 deadline 到期都在零输入下 RED。完整 WMI/唯一窗口认证只在门前执行；门内与门后
使用 pinned handle 和 exact HWND/PID/TID/rect，本地 freshness 从最后样本一直限制到 direct、attach、第二次 Set 与完成点各不超过
500 ms。finished attestation 与 public replay 绑定这些样本，新 `foreground_protocol_version=2` 禁止新 RED 删除 gate 后降级；
四份旧零输入 RED 只按 run ID + final-event digest 固定兼容。该候选尚未真实运行；提交会使 `925b...` 资格失效，必须新 prepare、
同环境 ordinary v2/crash GREEN 后才允许一次新的 menu-smoke。

动作收据的独立格式契约是 `schemas/visible-control-action-receipt-v2.schema.json`；它描述可见控件执行器的审计收据，
不是通用 `action-v1` 策略动作的迁移版本。

crash 证据包使用 run-relative artifact manifest；报告中为法证保留的运行时绝对路径只与“原执行目录”绑定，因此整个
`runs/<run-id>` 复制到其他父目录后仍可从副本重放。GREEN 与任何声称 `cleanup_proven=true` 的 RED 共用同一清理语义验证器；
RED 不能用一个布尔字段绕过进程、watchdog、控制文件、production manifest 或空窗证明。

该重放的信任模型固定为 `unkeyed_sha256`，声明仅为 `archive_schema_and_internal_consistency_only`，并显式记录
`historical_execution_authenticity_proven=false`。验证器会从归档 PNG 重跑同一 OCR、复算字段关系与无密钥 hash chain，但无密钥归档
不能阻止拥有整包写权限的人从零伪造；它也不逐项把每个 event payload 的全部语义与 report/artifact 重新交叉绑定。
目录搬移回放仍要求同一 validator、仓库代码与 OCR runtime，并非跨机自包含。“本机真实发生过”只能来自外层 verifier
当场固定的 OS 进程句柄与用户观察，不能由复制后的文件独立认证。

## 近期实施清单

- 已完成候选：专用用户目录、存档隔离、非 debug production staging 单 mod 挂载；原六类基础 schema 加两份可见 UI schema；版本/mod/agent
  指纹、跨进程锁、认证 watchdog、Job 与单次 smoke 超时。
- 部分完成：`menu-smoke` 已离线接通主菜单/书签双帧 OCR+像素分类、固定 UI contract、一次性控件 token、单批次点击、主链 WAL、
  sealed 启停与 GREEN/RED 归档回放；无害 Win32 helper 已实测，但真实 CK3 输入仍为零。持续运行仍缺磁盘、费用与重复失败预算。
- 尚未实机接线：规则页、角色选择、HUD/事件通用状态机，以及独立 policy 进程与字段白名单。
- 未开始：规则页/事件/HUD 的模板资产冻结；
  开始游戏、处理事件、推进时间、死亡结算的最小合法策略；多角色固定基准；模型调用预算；带证据计数和版本回滚的策略记忆。
- Phase B 接入 policy 前的 crash 门禁已由 `20260821T220127Z-crash-adc0ac63` 本机 GREEN：完整 CK3 Job tree 回收、
  可做内部一致性重放的归档、真实 profile/Steam 的退出后语义 baseline 均通过；Workshop 只证明 descriptor 内容哈希与
  已注册 target 的 path/size/mtime 元数据在退出后一次 baseline 比较中相同。该门禁没有发送游戏输入，不能替代
  当前提交后的同环境重新资格化与首次真实可见 UI 输入门禁。
- 2026-08-22 的第二次真实 crash probe `20260821T211059Z-crash-833b9587` 已进入可见主菜单并完成单 mod attestation，
  但 watchdog 与 kill-on-close Job 并发回收 CK3 时，`TerminateProcess` 返回 `ERROR_ACCESS_DENIED`；旧实现只等精确 pinned
  handle 1 秒，因而安全地 finalize 为 RED、保留四类 control 且不做 protected postflight。该事故促成统一 20 秒精确句柄
  排空、独立 fallback/quiet 预算、结构化 watchdog-failure 归档及上述显式恢复协议；它仍不是 crash 门禁 GREEN。
- 修订提交 `98d55caf3ed4a398b0a3bd7bc8e6ee16591d8f26` 的下一次 crash probe
  `20260821T220127Z-crash-adc0ac63` 已 GREEN：supervisor 以精确句柄退出码 77 注入，CK3 与两个 sentinel 随命名
  kill-on-close Job 回收，watchdog 返回 0，四类 control 消失，双源 CK3 清点连续 5 秒为空，之后才执行 protected postflight。
  同轮普通 smoke 为 `20260821T215910Z-780cd6cb`；两者共享上述环境指纹。普通 validator 只复算事件链/finalization，
  其 load、cleanup、protected 与 production 语义字段另行逐项断言；crash validator 才重放完整归档内部一致性。

## 风险

- CK3 的状态空间、动态地图和事件种类远大于当前 acceptance UI，不能假设固定坐标脚本可以直接扩展为玩家。
- OCR 正确不等于语义正确；所有高风险动作都需要点击后反证和可恢复边界。
- 大模型容易从单局随机结果过拟合，必须用多局证据、对照实验和策略版本控制约束。
- 游戏、DLC、语言、UI 缩放或 mod 更新都会使视觉模型和策略基准漂移，episode 必须记录完整环境指纹。
- 长期无人值守会消耗模型费用、磁盘和机器时间，必须先有硬预算和看门狗再开放持续循环。
