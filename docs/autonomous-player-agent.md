# CK3 自主高分玩家智能体路线图

## 状态与启动门槛

- 状态：**2026-08-21 正式启动；2026-08-22 Phase A 实现候选完成，退出标准仍待 committed-candidate 三连复验，尚未形成有效得分局**。
- 实现目录：[`ck3_autonomous_player/`](../ck3_autonomous_player/README.md)。Python 包名 `xar_autoplayer`，运行状态固定放在仓库外。
- 当前候选的加固前探索运行曾证明 production、非 debug、单 mod 能够在隔离 profile 到达可见主菜单并退出；旧证据不满足
  当前安全契约，必须等提交后三连通过才形成现版本证明。该 smoke 不是“会玩”，也不计入策略数据。
- 原有 30–40 年被动 soak/stability/telemetry 仍是固定验收场景，不扩张成自主玩家，也不冒充数值平衡或智能体证据。
- 这是独立于 `tools/run_acceptance.py` 的长期工程。acceptance runner 证明机制是否正确；自主玩家负责在正常规则下长期游玩并尽量取得更高分，二者不得混用目标或测试入口。

加固前的三次探索性 GREEN：`20260821T162104Z-cf348a71`、`20260821T162305Z-9a403bc6`、
`20260821T162451Z-5e882b17`。它们早于新鲜日志 epoch、跨进程锁、认证 watchdog、Job Object 和扩展环境复核，只作为
问题发现记录，**不再是当前 Phase A 退出证据**。当前候选必须提交后重新 prepare，并在同一新环境指纹下连续三次通过。

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
- 退出后反证真实 CK3 profile 顶层文件、player/rulers/正常存档、Steam userdata 云存档条目、Workshop `ugc_*.mod` descriptor
  内容哈希，以及已注册 Workshop 目标树的路径/大小/mtime 元数据清单回到 baseline 并连续稳定 5 秒；这不等价于完整内容哈希，
  也不等价于证明运行期间从未发生瞬时写入。持久 `tutorial.txt` 首次创建后不读、不清空、不回滚。
- selected-contract 指纹覆盖游戏 exe/launcher/原版规则、DLC descriptor、production source/tree/manifest、outer descriptor、
  关键 agent/build/watchdog 代码、解释器和包版本；正式 smoke 要求所有选中 runtime 与 production release source 文件均已被
  Git 跟踪且 clean。开发构建没有
  当前提交的真实 tag 时记录 `git_tag=null`，不得伪装 release。报告先写 `finalized=false, ok=false`；最终 hash-chain 事件落盘后
  还要逐项重算 digest、previous link 和 tail/report 绑定，全部通过才原子写成 finalized GREEN，避免中断留下假阳性报告。
- 2026-08-22 实测：Steam 客户端运行时，即使 `cloud_save=no` 且使用隔离 `-userdir`，每次 non-debug CK3 退出仍会改写 `userdata/<account>/1158310/remotecache.vdf` 的顶层 `ChangeNumber` 和文件时间。智能体把这两个 Steam 自有元数据单独记入 before/after 证据并允许变化；比较前只规范化该整数，云存档条目的路径、大小、时间、SHA、同步状态及其余字节仍须完全一致。除此以外的 userdata 差异一律判失败。该结论为本机 1.19.0.6 + 当前 Steam 客户端实测，不回写或恢复真实文件。
- 同机还实测：`cloud_save=no` 不阻止主菜单枚举既有 Steam Cloud 存档 meta。旧 PoD 云存档中的 17 个规则 key 与两张贴图引用
  和 fresh `error.log` 逐项匹配；但 fresh enabled inventory 只有本 mod，mount 也只有官方 DLC 与隔离 production tree，故这不是
  第二个 mod 被加载。Phase A smoke 明确允许归档这类非零诊断，并写 `clean_engine_boot_required=false`、
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
| A. 隔离环境 | 专用 CK3 用户目录、production mod、固定分辨率/语言、认证看门狗、环境与存储反证 | committed candidate 连续三次只加载本 mod 到可见主菜单；失败路径不遗留无人守护的 CK3 |
| B. UI 驱动底座 | 窗口分类、OCR、可靠点击、地图/HUD/事件通用恢复 | 无策略参与时可稳定运行数小时并保存完整证据 |
| C. 合法基线玩家 | 固定规则策略完成开局、经营、事件、死亡和结算 | 至少完成多种角色类型的有效整局基线 |
| D. 分层规划 | 增加战争、婚姻、领地、经济、生活方式、契约和交易决策 | 决策均有可审计状态输入和理由，分数不低于固定基线 |
| E. 经验记忆与复盘 | episode schema、检索记忆、大模型局后复盘和策略版本化 | 新局能引用相关旧经验，错误经验可回滚和追踪来源 |
| F. 持续重复游玩 | 自动结算、归档、下一局、异常隔离、成本/磁盘/运行时上限 | 在无人值守窗口内连续完成多局且不破坏环境 |
| G. 高分优化 | 角色分层基准、受控实验、风险调整和排行榜 | 在固定基准上形成可重复的持续提升趋势 |

## 近期实施清单

- 已完成候选：专用用户目录、存档隔离、非 debug production staging 单 mod 挂载；六类版本化 schema 草案；版本/mod/agent
  指纹、跨进程锁、认证 watchdog、Job 与单次 smoke 超时。
- 部分完成：OCR 目前只验证主菜单【新游戏】；连续运行停止条件已有版本/mod 漂移和进程安全门禁，但尚缺磁盘、费用与重复失败预算。
- 未开始：游戏窗口分类回放集；与 acceptance 状态隔离的 OCR/模板/焦点/点击驱动层；独立 policy 进程及字段白名单；安全动作白名单；
  开始游戏、处理事件、推进时间、死亡结算的最小合法策略；多角色固定基准；模型调用预算；带证据计数和版本回滚的策略记忆。

## 风险

- CK3 的状态空间、动态地图和事件种类远大于当前 acceptance UI，不能假设固定坐标脚本可以直接扩展为玩家。
- OCR 正确不等于语义正确；所有高风险动作都需要点击后反证和可恢复边界。
- 大模型容易从单局随机结果过拟合，必须用多局证据、对照实验和策略版本控制约束。
- 游戏、DLC、语言、UI 缩放或 mod 更新都会使视觉模型和策略基准漂移，episode 必须记录完整环境指纹。
- 长期无人值守会消耗模型费用、磁盘和机器时间，必须先有硬预算和看门狗再开放持续循环。
