# 琉焰卿的永恒轮回（AGENTS 指南）

## 项目结构

- `XenoAmess_s_Eternal_Recurrence/` — CK3 mod 源目录；正式发布只使用 `build_release.py` 生成的 staging
- `Eternal_Recurrence_Vivhite_Courtier/` — 白绮特供独立版源目录；正式发布只使用 `build_vivhite_release.py` 生成的 27 文件 staging
- `Crusader Kings III/` — 游戏本体目录（仅作参考/逆向用，已被 .gitignore 排除）
- `docs/` — 知识库（跨存档存储机制、GUI 系统、语法踩坑），改机制前先读
- `docs/autonomous-agent-progress/` — 自动游玩智能体的统一目标/路线图与日报、周报入口；能力状态必须回链原生专题与实机证据
- mod 通过用户目录的 `mod/XenoAmess_s_Eternal_Recurrence.mod`（path 指向本仓库）注册
- 原版 Steam 创意工坊物品 id：**3784706360**；白绮独立版 id：**3787304042**。
  `remote_file_id` 的 canonical 副本**只能留在各自用户目录外层 .mod，不能同步进仓库内层 descriptor.mod**。
  启动器在首次/更新上传成功时都会把该字段临时写进 staging 内层 descriptor 并原样发布；上传前预存该字段仍会导致
  "Mod descriptor validation failed"。上传后必须重建 staging，恢复无 ID 的正式树。
  更新工坊 = 改仓库内容 → 启动器 Mods → 上传 Mod 选同一物品再传一次。预览图用 mod 根目录的 `thumbnail.png`
  （启动器约定俗成按 mod 根目录找此文件名，同其他 dev mod）；descriptor 里 `picture="thumbnail.png"`
- 原版工坊描述维护在 `workshop/description.bbcode`；README 全量图、工坊精简图和六张 Steam media strip 的来源、裁切和 commit-pinned GitHub raw URL 规则见 `workshop/main_screenshots.md`。白绮独立版维护在 `workshop/vivhite_description.bbcode`，主视觉与八张实机图顺序在 `workshop/vivhite_screenshots.md`。改完描述到对应物品页「编辑标题与描述」整段替换

## 构建/生成

```powershell
py XenoAmess_s_Eternal_Recurrence/tools/gen_highscore.py   # 位阈值体系
py tools/gen_pools.py                                       # 祝福/诅咒奖池（100+100）
py tools/gen_contracts.py                                   # 本世契约、PB、图鉴与里程碑事件
py tools/gen_scoring.py                                     # 死亡计分 effect 与规则文档
py tools/gen_score_preview.py                               # 特质 hover 只读即时分数
py tools/gen_no_heir_gui.py                                 # 原生继承窗投影 + 无继承人结算注入
py tools/gen_balance_wire.py                                # 开发用长期平衡遥测位帧
py tools/extract_courtier_traits.py                         # 从当前原版 00_traits.txt 刷新元数据快照
py tools/gen_courtier_creator.py                            # 原版廷臣特质目录、元数据与冲突
py tools/gen_vivhite_courtier.py                            # 白绮独立版廷臣目录（独立快照/ervc 命名空间）
py tools/compose_decision_art.py                            # 三张决议源图 → 1100×440 DXT1 DDS
py tools/compose_vivhite_key_art.py                         # 白绮主视觉 → 独立版 640×640 thumbnail
py tools/compose_trait_stars.py                             # 10 级特质星标 → 120×120 RGBA DDS
py tools/build_release.py --check                           # 临时双构建，验证 manifest/ZIP 可复现
py tools/build_release.py                                   # 生成 dist staging、manifest 与 deterministic ZIP
py tools/build_vivhite_release.py --check                   # 白绮独立版临时双构建
py tools/build_vivhite_release.py                           # 生成独立 staging、manifest 与 ZIP
```

八套脚本生成器及两套素材投影工具，**不要手改 `GENERATED FILE` 标记的文件**。计分参数只改 `tools/scoring_data.py`，
再运行 `gen_scoring.py` 与 `gen_score_preview.py`；奖池条目改 `tools/pools_data.py`
（数据表）再跑 gen_pools.py；权威表 `docs/blessing-curse-pools.md` 由它导出。
计分生成器产出 `common/scripted_effects/xar_generated_scoring_effects.txt` 与
`docs/scoring-rules.md`；hover 生成器读取同一 schema 产出 `common/script_values/xar_generated_score_preview.txt`。
奖池稳定 ID 的独立冻结契约在 `tools/pool_semantic_contract.sha256`；普通 `gen_pools.py` 不更新它。
改池后必须先审阅权威表与 dispatcher diff，再用 `py tools/validate_static.py --print-pool-contract`
取得候选并显式更新契约，禁止为了消除校验错误盲目刷新。
契约原型、PB、图鉴、琉焰之视成长表和 28 个里程碑事件改 `tools/contracts_data.py`，再跑 `gen_contracts.py`；该生成器也产出 `common/traits/xar_traits.txt`。
无继承人结算 widget 改 `gui/xar_no_heir_settlement.gui`；原生继承窗投影必须运行 `tools/gen_no_heir_gui.py`，不要手改 `gui/window_succession_event.gui`。
长期平衡 wire 字段改 `tools/balance_wire_data.py`，再运行 `tools/gen_balance_wire.py`；两份生成结果仅供 development acceptance，release staging 必须整文件排除。
廷臣 trait 元数据快照在 `tools/courtier_traits_1_19_0_6.json`。改动或升级游戏版本时，先更新
`extract_courtier_traits.py` / `gen_courtier_creator.py` 内的版本、输出名和预期计数，再运行
`py tools/extract_courtier_traits.py` 从当前原版 `00_traits.txt` 刷新快照；审阅 snapshot diff 后才运行
`py tools/gen_courtier_creator.py`，并审阅生成的五类目录、224 项元数据与 95 组冲突。只运行生成器不会重新读取游戏文件。
三张决议源图位于 `images/decision_*.png`；修改后运行 `py tools/compose_decision_art.py`，不要手改
`gfx/interface/illustrations/decisions/decision_xar_*.dds`。静态校验会逐字节重建并检查 DXT1 输出。
白绮独立版主视觉源图为 `images/vivhite_courtier_key_art.png`；修改后运行
`py tools/compose_vivhite_key_art.py`，不要手改其 `thumbnail.png`。静态校验会逐像素重建并检查 PNG。
十级特质星标由 `tools/compose_trait_stars.py` 程序化生成；不要手改
`gfx/interface/icons/traits/_stars_10.dds`。原版只提供 0–5 级星标，静态校验会逐字节重建该 RGBA DDS。
位阈值体系生成器产出：`common/tutorial_lessons/xar_highscore.txt`、`common/customizable_localization/xar_generated_loc.txt`、
`common/scripted_guis/xar_generated_guis.txt`、`common/scripted_effects/xar_generated_effects.txt`、
`gui/xar_meta.gui`、`localization/*/xar_generated_*.yml`。

要扩上限：改生成器里的 `TIERS` 列表再跑一遍即可，旧纪录不丢（位是只增的）。

发布构建使用明确 allowlist，并从开发树渲染 production-only 投影：整文件排除 selftest/死亡探针/trait bridge，
再剥离 `# XAR_ACCEPTANCE_ONLY_BEGIN/END` 区域并展开 `# XAR_RELEASE_ONLY` 生产替代行；最终 staging 禁止出现测试标识。
未标记文件仍逐字节复制。禁止直接把 mod 源目录上传；正式上传只能使用 `build_release.py` 生成的 staging。

## 测试流程

**静态 L0（跨平台/CI）**：

```powershell
py -m pip install -r tools/requirements-static.txt
py tools/test_gen_no_heir_gui.py
py tools/test_build_release.py
py tools/test_build_vivhite_release.py
py tools/validate_static.py
py tools/validate_vivhite_static.py
py -c "import sys; sys.path.insert(0, 'tools'); import scoring_data; scoring_data.assert_reference_vectors()"
py tools/build_release.py --check
py tools/build_vivhite_release.py --check
```

**全自动验收（默认）**：

```powershell
& "tools\.venv\Scripts\python.exe" "tools\run_acceptance.py"
& "tools\.venv\Scripts\python.exe" "tools\run_vivhite_acceptance.py"
```

一键全流程（备份现场 → **静态 loc 校验** → 同步代码 → 过大厅 → 自测规则档全链断言 → 恢复现场），
GREEN/RED + 退出码，约 5-6 分钟。原理与坐标表见 `docs/testing-workflow.md`。
白绮 runner 默认串行验收独立加载及双 mod 两种加载顺序；使用 production projections、外部夹具和一次性
`-userdir`，不得读写真实工坊缓存。正式矩阵不加 `--keep-userdirs`。

**CI 边界**：`.github/workflows/static-ci.yml` 使用 GitHub 官方 `windows-latest`，在 push/PR
执行 L0，手动触发或 `v*` tag 时额外生成 ZIP/manifest。官方 runner 没有 CK3、Steam 授权和
可靠交互桌面，禁止调用 `run_acceptance.py` / `run_vivhite_acceptance.py` 或声称完成 L1-L3；真实游戏验收必须在本机运行并保存报告。

**⚠️ 改完代码游戏里看不到，先怀疑这个**：启动器把 dev .mod（带 remote_file_id）和工坊订阅合并，
游戏实际加载的是 **工坊缓存**（`Z:\SteamLibrary\steamapps\workshop\content\1158310\3784706360`，
播放集里生效的是 `mod/ugc_3784706360.mod`）。runner 每次跑前 robocopy 同步仓库 → 工坊缓存；
手动测试前也必须先同步（或直接 `robocopy XenoAmess_s_Eternal_Recurrence <工坊缓存> /MIR`）。

手动兜底（runner 不可用时）：
1. `Start-Process binaries/ck3.exe -ArgumentList "-debug_mode"` 启动
2. 日志：`Documents\Paradox Interactive\Crusader Kings III\logs\error.log`（解析/运行时错误）、
   `debug.log`（`debug_log` 标记，本项目用 `XAR:` 前缀）
3. 全局存储落盘文件：`Documents\Paradox Interactive\Crusader Kings III\tutorial.txt`
4. 流程性验证：新开局看商店事件 → 控制台 `die` → 结算事件 → 教程通知自动完成 → 再开新局看导入

## 文案人格（琉焰卿）

所有琉焰卿的台词/事件文案必须贴合此设定：

- **风格**：中二 + 奇幻，具有诱惑力、诱导性；从容不迫，永远像在等一笔迟早成交的生意
- **设定**：以人类的情感为食的咒间仲魔；**不会刻意告诉玩家自己的恶劣性**——恶意只藏在措辞的阴影里，表面永远温柔有礼
- 称玩家"旅人"，第一人称"我"；自称"琉焰卿"；把分数说成"分量/余烬"，把交易说成"典当/垂青/咒痕"
- 祝福诅咒奖池的权威定义在 `docs/blessing-curse-pools.md`，改池必须五处同步（表内列明）

## 本地化开发策略

- **日常功能修改只创作、修改和审阅简体中文与英文文案**。不要主动翻译或润色法、德、日、韩、波、俄、西七种语言；生成结构必须包含九语言时，可暂用英文占位以保持文件可加载，但不得把占位称为已完成翻译。
- 只有用户明确表示“要发布了”或给出等价发布指令后，才补齐其他语言，并执行完整的国际化差异、占位符、术语、格式和游戏内验证。日常静态校验中的 loc 结构检查不代表发布级国际化验收。
- 发布翻译优先让 `MiniMax-M3` 承担低风险、机械性的字符串翻译。开始任何翻译修改前只检查 `MINIMAX_API_KEY` 是否存在；若不存在，立即停止且不得修改项目，严禁输出、记录或暗示 Key 内容。
- MiniMax 只能接收最小必要的 key-value、语境和保护 token，并只返回合法 JSON；不得让它分析项目、决定 key/文件、编写或审查代码、操作文件或判断验收结果。所有修改、审计和验证由当前执行者亲自完成。
- 完整调用边界、提示词、审计清单和交付格式见 `docs/localization-workflow.md`，执行发布国际化前必须先读。

## Git 约定

- **每次任务执行完成后，默认 `git commit` + `git push`**（无需另行确认，也不要等人工验证，直接提交推送）
- 提交信息用英文，简明描述改动

## 自动游玩 Agent 进度报告

- 统一入口为 `docs/autonomous-agent-progress/README.md`；终极目标、真实能力边界与完整后续工作维护在
  `docs/autonomous-agent-progress/goal-and-roadmap.md`。它们是进度索引，不替代 `docs/ck3-native-ai/` 的原生 AI
  专题、ABI 合同、`docs/testing-workflow.md` 或冻结 live artifact。
- **每个工作日必须创建或更新** `docs/autonomous-agent-progress/daily/YYYY-MM-DD.md`。如果周末也开展项目工作，
  同样创建当天日报。同一天有多个里程碑时持续更新同一文件，并在当天最后一次任务提交/推送前再核对一次。
- **每个有项目工作的 ISO 周必须创建或更新** `docs/autonomous-agent-progress/weekly/YYYY-Www.md`。当前周报作为滚动报告，
  每个工作日随日报同步更新；最迟在该周最后一个工作日补齐本周结果、未闭合项和下周入口。
- 日报和周报至少写明：完成了什么、正在做什么、为什么做、能力/readiness 变化、测试与 live artifact、RED/阻点、
  下一步、相关 commit/push。报告模板分别位于 `docs/autonomous-agent-progress/daily/TEMPLATE.md` 与
  `docs/autonomous-agent-progress/weekly/TEMPLATE.md`。
- 状态必须严格区分 `research`、`static-ready`、`fixture-live`、`production-live primitive`、
  `production-live loop` 和 `complete`。没有真实 paused artifact 时不得写 live；ACK、schema 字段、单元测试或单场 fixture
  不得冒充完整 OODA。失败 attempt 必须保留，并区分 harness RED 与 capability RED。
- 多代理并行时，负责实际工作包的代理必须把可核验的结果、测试、artifact/commit 和遗留项写入当天/当周报告；若协调者
  正在编辑同一文件，则先发送这些字段，由协调者合并，不能因避免冲突而漏报。

## 自动游玩 Agent：价值优先与安全边界

- **在本项目中，安全问题如果不能用可复现实证证明会影响实际使用，就不得进行任何处理。** 不得为其修改代码、补测试、扩展 schema/WAL/证明协议、阻断实机运行或启动额外审计。
- “影响实际使用”仅指可观察的真实后果，例如 CK3 自动游玩流程失败、实际发生非预期输入、真实数据损坏、进程无法可靠回收，或生产代码路径中可稳定复现的同类故障。必须先给出对应的实际运行证据或直接覆盖生产路径的确定性复现。
- 仅有理论可能、手工重签/改写本地归档、生产者不可达的伪造状态、纯取证或内部一致性瑕疵、未实际出现的异步/TOCTOU 窗口，都不构成处理依据；发现后立即停止展开，不得把它们升级为 blocker、HIGH 或下一次实机前置门禁。
- 自动游玩功能价值始终优先：先交付可见的游戏里程碑与完整“观察 → 决策 → 操作 → 验证”循环，再处理已有实证的可靠性问题。测试数量、证据链完整度和审计覆盖率不得替代实际可玩能力作为完成标准。
- **观测能力优先于反复判定“不可知”。** 自动玩家因缺少 CK3 内部状态而无法作出高价值决策时，默认下一项施工必须是：冻结 exact build → 逆向对应原生字段/查询 → 新增只读 native bridge capability 与 MCP 查询口 → 用实机 paused snapshot 验收 → 再恢复策略执行。不得长期用 `unknown`、`unavailable` 或缺字段作为来回转圈的理由。只有 ABI/版本证据尚未闭合、且已明确记录缺口与下一项可施工入口时，才允许暂时 fail-closed；命令 ACK 仍不得冒充状态观测。
- 决策所必需的字段不能以“schema 已有但长期为 `null`”冒充观测口完成。`null` 只用于区分某一构建阶段或某一帧的读取失败与合法零值；若缺失字段仍使目标决策无法执行，就必须继续逆向并扩充同一 MCP，直到该决策的 readiness gate 能真实变为 `true`。部分查询只有在自身已经解锁独立、可见的游戏价值时才能单独收口。
- 禁止以寻找理论安全问题为目标派生多代理审计。安全审查只能针对已经影响实际使用的具体故障，修复范围以消除该故障所需的最小改动为限。
- **右下角通知已获持续清理授权。** 在本机执行 CK3 自动游玩或实机验收时，若出现 Windows、Chrome 或其他应用的右下角 Toast，立即关闭通知本身并保持系统 Toast 禁用，不必再次询问；不得点击通知正文，也不得让通知继续遮挡 CK3 控件或中断既定任务。
- **宗教域由项目所有者明确暂缓，只有战争中的圣战与婚姻中的必要判定两项窄例外。** 鉴于 CK3 近期版本将大规模重构宗教系统，在项目所有者明确通知“可以开始宗教相关内容”以前，不得深入探索或实现 faith/doctrine/tenet/fervor、改宗、宗教改革等通用宗教专用原生 AI 树、bridge、策略或实机矩阵。允许为完整战争 OODA 研究和实现圣战/大圣战所必需的最小观测、合法性、目标、费用、参战、军事行动与结束语义；也允许在婚姻候选、合法性、接受度、费用和结果确实依赖信仰时调用最小必要的原生判定。两类例外都应优先复用原生最终结果/原因，只把 faith/religion 保持为 opaque identity 或直接影响当前圣战/婚姻的最小输入，不得借例外扩展为通用信仰系统研究。holy order 仍暂缓。文化、创新、法律、政府和非宗教事件/决议照常推进；暂缓不等于宗教域已完成。

## 知识沉淀

- 干活中学到的新知识**当场同步进 `docs/`**，不要等任务收尾：尤其是 Paradox 脚本语言
  （trigger/effect 语义、作用域切换、求值时机）与 CK3 实现细节（加载顺序、暂停行为、
  启动器/工坊合并行为）的实证结论
- 任何会依据 CK3 原生 AI 行为调整自动玩家策略的工作，必须先按
  `docs/ck3-native-ai/README.md` 研究并更新对应的原生决策树：冻结游戏版本与 EXE SHA，优先读取原版
  AI 数据和 exact-build 调用链，必要时只读实机互证；同步维护 Mermaid 逻辑图并把未闭合分支画成虚线
  `unknown`。原生树及证据边界落盘后，才允许设计或修改我方 counter-policy；禁止先猜行为、后补文档。
- 原生树已经证明“某数据参与决策”、但当前 bridge/MCP 尚未发布该数据时，必须把补观测口列为策略工作的
  最高优先级依赖：先补只读查询和版本绑定 fixture，再实现依赖它的自动动作。文档中的 `unknown` 是逆向账本，
  不是停止采集数据的终态。
- 落点按类型分：语法/引擎坑 → `docs/grammar/pitfalls.md`（按错误信息索引，现象/原因/解法三栏）；
  测试流程/工具 → `docs/testing-workflow.md`；机制权威定义 → 对应专题文档（如 blessing-curse-pools.md）
- 标准：可复现、注明是否实测；存疑结论标「未查明」并写清绕开方案

## 硬性约束（血泪教训，详见 docs/）

- **一切内容只对玩家生效，AI 永远不得触发**。现有屏障：开局走 `every_player`（不含 AI）；死亡链要求
  `has_character_flag = xa_enabled`（该 flag 只能由玩家点契约获得）**且** `is_ai = no` 双闸门；GUI 桥走
  `GetPlayer`。今后新增任何事件/决议/互动/钩子，都必须挂在上述玩家限定链上（或自带等价闸门），
  禁止给 AI 留入口；新增 on_action 钩子时注意其本身对全场角色触发，effect 必须包 limit
- 所有脚本文件 **UTF-8 BOM**；yml 缺 BOM 直接不加载
- script values 目录是 `common/script_values`（**不是** scripted_values）
- `is_tutorial_lesson_completed` 是 interface trigger，只能用于 customizable_localization / GUI，游戏状态脚本禁用
- on_action 同名键**覆盖不合并**，扩展用 `on_actions = { 自定义钩子 }` 模式
- 自定义顶层窗口必须在 `gui/scripted_widgets/` 注册才会实例化
- `Tutorial` 数据上下文只存在于 tutorial_window 本体
- 教程课程自动完成用 `trigger_transition`（课程文件内），不要试图从外部点按钮
- 游戏语言非英语时，customizable_localization 的 key 必须在**当前语言**的 yml 里存在（不吃英文回退）；
  用于事件选项名时该 key 本身也要有静态 yml 条目，否则运行期显示 raw key
