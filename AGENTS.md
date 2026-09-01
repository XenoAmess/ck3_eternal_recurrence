# 琉焰卿的永恒轮回（AGENTS 指南）

## 项目结构

- `XenoAmess_s_Eternal_Recurrence/` — CK3 mod 源目录；正式发布只使用 `build_release.py` 生成的 staging
- `Eternal_Recurrence_Vivhite_Courtier/` — 白绮特供独立版源目录；正式发布只使用 `build_vivhite_release.py` 生成的 27 文件 staging
- `Crusader Kings III/` — 游戏本体目录（仅作参考/逆向用，已被 .gitignore 排除）
- `docs/` — 知识库（跨存档存储机制、GUI 系统、语法踩坑），改机制前先读
- `docs/autonomous-agent-progress/` — 自动游玩智能体的统一目标/路线图、日报、周报、月报与日/周计划会入口；能力状态必须回链原生专题与实机证据
- mod 通过用户目录的 `mod/XenoAmess_s_Eternal_Recurrence.mod`（path 指向本仓库）注册
- 原版 Steam 创意工坊物品 id：**3784706360**；白绮独立版 id：**3787304042**。
  `remote_file_id` 的 canonical 副本**只能留在各自用户目录外层 .mod，不能同步进仓库内层 descriptor.mod**。
  启动器在首次/更新上传成功时都会把该字段临时写进 staging 内层 descriptor 并原样发布；上传前预存该字段仍会导致
  "Mod descriptor validation failed"。上传后必须重建 staging，恢复无 ID 的正式树。
  更新工坊 = 改仓库内容 → 启动器 Mods → 上传 Mod 选同一物品再传一次。预览图用 mod 根目录的 `thumbnail.png`
  （启动器约定俗成按 mod 根目录找此文件名，同其他 dev mod）；descriptor 里 `picture="thumbnail.png"`
- 原版工坊描述维护在 `workshop/description.bbcode`；README 全量图、工坊精简图和六张 Steam media strip 的来源、裁切和 commit-pinned GitHub raw URL 规则见 `workshop/main_screenshots.md`。白绮独立版维护在 `workshop/vivhite_description.bbcode`，主视觉与八张实机图顺序在 `workshop/vivhite_screenshots.md`。改完描述到对应物品页「编辑标题与描述」整段替换

## Steam 创意工坊发布 Changelog

- 本仓库内每个独立 mod 产品，每次正式发布或更新到 Steam 创意工坊成功后，都必须编写一份**相对上一公开版本**的 changelog，
  永久保存为仓库跟踪文件并提交、推送到 `master`。统一路径为
  `docs/release-changelogs/<product-key>/<version>.md`；首次发布没有上一版本时，必须明确标为 initial baseline。
- 每份 changelog 至少记录：产品与 Workshop item ID、当前/上一版本、发布日期、当前/上一 tag 与 commit、玩家可见新增/变更/修复、
  兼容或存档迁移、已知限制，以及正式构建和实机验收证据链接。草稿可以在发布前准备，但只有实际上传成功后才能写入最终发布事实。
- Workshop 上传、订阅缓存复核和对应 changelog 的 `master` commit/push 缺一不可；没有永久入库的 changelog，不得把该次 release
  标为完成。历史 changelog 不得覆盖删除；勘误必须追加带日期的更正记录。

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
py tools/compose_ox_here_key_art.py                         # 牛来主视觉 → 640×640、低于 1 MB thumbnail
py tools/compose_ox_here_workshop_media.py --artifacts <run> # 牛来 GREEN 实机截图 → 四张低于 2 MB JPEG
py tools/compose_trait_stars.py                             # 10 级特质星标 → 120×120 RGBA DDS
py mod_zhongguo_style/tools/gen_361_mechanisms.py           # 361 目录、领域合同与制度卡
py mod_zhongguo_style/tools/gen_361_b1_runtime.py           # B1 跨周期绩效季与共同上司 barrier
py mod_zhongguo_style/tools/gen_scoreboard_snapshot.py      # 考核榜固定快照槽与 GUI 投影
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

## 可复用宣传视频工具链

- 可复用实现位于 `xar_promo_toolchain/`；用户入口、真实命令与能力边界以其 `README.md`、
  `docs/architecture-and-migration.md` 和当前 `<verified-python> -m xar_promo --help` 为准。禁止为尚未接入的 library API
  虚构 CLI 命令，也不得把 plan、命令 ACK、schema 通过或单项自动检查写成“成片已验”。
- 严格保持四层边界：
  1. **通用包** `xar_promo_toolchain/src/xar_promo/` 负责 `ProjectConfig`、每次 attempt 的 append-only `RunManifest`、配置快照、
     content-addressed 素材、TTS、字幕/布局、媒体探测、进程与审计原语；不得内置某个 mod 的文案、角色、声线或发布凭据。
  2. **Skill** `xar_promo_toolchain/codex-skill/promo-video-pipeline/` 只提供操作方法、检查清单和能力路由；Skill 不是运行时实现，
     不能授权额外副作用，也不能声称不存在的命令或验收能力。
  3. **CK3 adapter** `xar_promo_toolchain/src/xar_promo/adapters/ck3/` 只读验证既有 capture report、timeline、evidence index、原始录像、
     marks 与 clean spans；不得启动 CK3、用 OCR 猜缺失状态、修复/覆盖 RED attempt，或承载某个项目的故事与发布政策。
  4. **项目 preset** `xar_promo_toolchain/src/xar_promo/presets/` 加各项目 checked-in config 负责章节、文案、语言、声线、时长、
     真实角色/测试 UI 等项目政策；各项目 legacy wrapper 在迁移期继续保持原 CLI、sidecar 与输出兼容。
- 当前冻结的 `xar-promo 0.1.0` CLI 只有下列十个命令；命令角色和副作用必须按表解释：

  | 命令 | 角色与副作用边界 |
  | --- | --- |
  | `init` | 新建 checked-in `ProjectConfig` 与首个绑定 run；已有目标拒绝覆盖。 |
  | `start-run` | 从当前 config 的精确字节创建另一个 `RunManifest` 与 config snapshot。 |
  | `validate` | 只读验证 config/run/legacy manifest；`--structure-only` 明确跳过引用文件 bytes/SHA 检查。 |
  | `preserve` | 把一个既有文件复制进不可变 content-addressed storage，并 append artifact 记录。 |
  | `signoff` | 在人工 1× 完整审阅后 append 对精确 artifact bytes 的 `approved`/`rejected` 决定。 |
  | `plan` | 必须显式给 `--composer MODULE:ATTRIBUTE`；永远只读，不建 workdir、不调用 provider，`--validate-only` 只用于显式声明同一合同。 |
  | `build` | 对原生 run 执行项目 composer；成功和 RED 的完成产物、partial、stdio 与 phase history 都必须保全。 |
  | `audit` | 写入并保全自动 audit 及其 evidence；不得读取、推断或写入人工 approval。 |
  | `review` | `--plan-only` 只读；否则只生成 `pending-human-review` 包，绝不记录 signoff。 |
  | `export` | 按显式 policy 验证或生成离线 bundle；`--dry-run`/`--validate-only` 不写目标，任何模式都不上传或发布。 |

  adapter/preset 只经本地注入或 Python entry-point 组 `xar_promo.adapters`、`xar_promo.presets` 解析；`plan`/`build`
  的 composer 是项目提供的可 import callable，不属于 registry，也不得被工具链猜测或自动发现。
- `ProjectConfig` 是可审阅的 checked-in 意图；每次 capture/render/audit attempt 必须创建独立 run/workdir，保存当时配置的
  精确字节快照。不得让后续配置修改重新解释旧证据，也不得把失败 attempt 改写成 GREEN。
- **所有过程素材永久保留，默认不清理**：raw 录像/截图/音频、脚本、TTS 请求与返回、字幕、生成卡、章节段、concat 输入、
  中间编码、partial、失败 attempt、命令 argv、`stdout`/`stderr`、probe、timeline、evidence/audit/review 报告、sidecar、
  manifest 历史和最终成片都属于过程资产。重跑使用新 run/workdir；不得为“收口”删除或覆盖旧素材。
- 自动 validation/audit/review package 只证明它声明并 hash 绑定的机器条件，**不等于人工按 1× 完整观看，也不等于 signoff**。
  人工签核必须发生在实际 1× 完整审阅之后，记录审阅人、结果、时间/说明，并绑定被审成片的精确 bytes + SHA-256；
  工具不得自行制造 approval。重新编码或替换任何字节后，旧人工签核自动不适用于新文件，必须重新审阅。
- 工具链的 build、audit、review、export 都不等于外部发布。每个 mod 仍必须走自己的 release staging、实机验收、
  Steam Workshop 上传、订阅缓存复核与 changelog 流程；宣传视频上传到外部平台同样需要独立明确授权。
- secondary/detached worktree 运行宣传工具链或其他依赖型 Python 验收时，先使用该 worktree 内约定的相对 `.venv`。
  若相对 venv 不存在，只能**显式指定并先验证**主 worktree 的 venv 解释器，同时把 `PYTHONPATH`/工作目录绑定到当前
  secondary worktree 源码并在报告中记录解释器路径、版本和依赖 probe。禁止静默回落到缺依赖的裸 `py`/系统 Python，
  再把 `ModuleNotFoundError`、缺 Pillow/edge-tts 或找不到媒体工具误判为代码 RED；这类问题在完成解释器与依赖复核前只能标为 environment RED。

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
执行三套产品 L0，并离线测试 MiniMax 候选调用器；手动触发时生成三套 ZIP/manifest，`v*`、
`vivhite-v*`、`ox-here-v*` 分别生成对应正式产物。官方 runner 没有 CK3、Steam 授权和
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
- **普通开发 push/PR 的 CI 不得强制运行七语发布审计，也不得因为 release audit snapshot 暂时落后而阻塞功能开发。**七语正式 audit 只在用户明确进入发布阶段后，由对应发布 tag 或人工 release workflow dispatch 触发；发版前必须补跑并通过，不能永久跳过。
- 发布翻译优先让 `MiniMax-M3` 承担低风险、机械性的字符串翻译。开始任何翻译修改前只检查 `MINIMAX_API_KEY` 是否存在；若不存在，立即停止且不得修改项目，严禁输出、记录或暗示 Key 内容。
- MiniMax 只能接收最小必要的 key-value、语境和保护 token，并只返回合法 JSON；不得让它分析项目、决定 key/文件、编写或审查代码、操作文件或判断验收结果。所有修改、审计和验证由当前执行者亲自完成。
- 完整调用边界、提示词、审计清单和交付格式见 `docs/localization-workflow.md`，执行发布国际化前必须先读。

## Git 约定

- **每次任务执行完成后，默认 `git commit` + `git push`**（无需另行确认，也不要等人工验证，直接提交推送）
- 提交信息用英文，简明描述改动
- `origin/master` 是唯一集成真相，默认从最新 master 直接开发。只有具体隔离、真实并发或高风险 live 理由才建
  `wip/<topic>`；必要发布线才用 `release/<product>-<version>`。分支必须登记 reason/base/owner/acceptance/deadline，
  成品及时合入，等待 exact master SHA 官方 CI GREEN 后删除 local + remote ref。
- **谨慎创建 Git 分支不等于限制 Agent 子线程。** 能按文件所有权、运行现场或依赖边界安全拆分的工作应主动使用多 Agent
  并行；各线程仍共同服务于 `master`，可在同一工作树修改互不重叠文件，或使用基于 exact master 的 detached worktree。
  detached worktree 不是新分支；若产生提交，必须尽快回合 `master`，不得因此保留长期游离 ref。
- 禁止 force-push。并发推送先 fetch/复核 remote master；远端移动时停止 push，rebase 到新 master、复测后普通 fast-forward push。
- 冻结 evidence 使用 detached HEAD 与根目录 `.xar-frozen-evidence.json`；不得把历史 runtime clone 当开发线。仅当写 marker 会
  改变所有者已冻结的 dirty tree 时，才可用记录 exact HEAD/status/diff hash 的中央 machine-readable ledger 代替。删除 branch ref
  绝不授权删除 worktree、clone、构建目录或 process assets。完整规则与跨 common-dir/独立 clone 清单见
  `docs/branch-management.md`。

## 自动游玩 Agent 进度报告

- 统一入口为 `docs/autonomous-agent-progress/README.md`；终极目标、真实能力边界与完整后续工作维护在
  `docs/autonomous-agent-progress/goal-and-roadmap.md`。它们是进度索引，不替代 `docs/ck3-native-ai/` 的原生 AI
  专题、ABI 合同、`docs/testing-workflow.md` 或冻结 live artifact。
- **每天在次日 00:00（Asia/Shanghai）收口前一自然日的** `docs/autonomous-agent-progress/daily/YYYY-MM-DD.md`；如果周末也开展
  项目工作，同样创建当天日报。同一天有多个里程碑时持续更新同一文件，午夜正式收口时必须逐项对照当天早会，标明
  “完成 / 部分完成 / 未完成 / 取消”，另列计划外完成项；未完成项必须写原因与是否顺延。
- **前一日日报收口后必须立即召开新一天早会**，写入
  `docs/autonomous-agent-progress/meetings/daily/YYYY-MM-DD.md`。早会列出当天按优先级排序的可交付项、验收条件、依赖、非目标与
  计划调整规则；不得在晚间倒填成仿佛 00:00 已知的计划。确需补录时必须标明真实补录时间与当时已经完成的基线。
- **每个有项目工作的 ISO 周必须创建或更新** `docs/autonomous-agent-progress/weekly/YYYY-Www.md`。周报作为滚动报告随日报更新，
  并在下周一 00:00（Asia/Shanghai）正式收口；收口时必须逐项对照该周计划会，规则与日报对照相同。
- **前一周周报收口后必须立即召开新一周计划会**，写入
  `docs/autonomous-agent-progress/meetings/weekly/YYYY-Www.md`，列明本周目标、优先级、验收条件、依赖和明确非目标。补录不得冒充
  周初原始计划。下一份周报必须链接并逐项核对这份计划会。
- **每个自然月的 27 日 00:00（Asia/Shanghai）必须创建或更新**
  `docs/autonomous-agent-progress/monthly/YYYY-MM.md`。月报既总结上次月报截止以来的增量，也维护截至本次截止的完整能力清单、
  诚实 readiness 边界和下一阶段主线；首次月报允许以项目迄今的累计能力盘点作为基线。
- 日报和周报至少写明：完成了什么、正在做什么、为什么做、能力/readiness 变化、测试与 live artifact、RED/阻点、
  下一步、相关 commit/push。报告模板分别位于 `docs/autonomous-agent-progress/daily/TEMPLATE.md` 与
  `docs/autonomous-agent-progress/weekly/TEMPLATE.md`；日/周计划会模板位于 `docs/autonomous-agent-progress/meetings/`。
- **日报和周报只要求文字报告，不再要求也不默认制作配套视频。** 已存在的日级、周级或阶段性录像可以作为历史证据素材
  继续引用，但视频缺失不影响日报完成或周报收口，也不得把历史素材冒充当月正式成片。
- **每份月报必须配套一条截至当月截止时的完整能力 show-off 视频。** 视频未产出或未通过媒体、字幕和内容抽检时，月报只能
  标记为“未完成/重制中”，不能算正式交付。月报视频统一采用**英语为主叙事，简体中文作为画面内副标题/字幕**：开场、阶段卡、
  游戏过程 lower-third 与最终证据卡都必须中英双语；英文保持主要视觉层级。中文字幕必须按句意断句，并按实际渲染宽度自动
  换行，禁止单行穿出安全区或被画面裁切。月报必须记录成片路径、时长、分辨率、编码、SHA-256、对应 live artifact 索引及
  诚实能力边界。视频是展示层，不替代 artifact/ABI/live evidence。
- 视频与 sidecar 默认输出到 `artifacts/demos/YYYY-MM-DD/`，录制规范与索引见
  `docs/autonomous-agent-progress/demos/README.md`。可复用录制器应提交进仓库；大体积成片不进 Git，但必须在报告中留下
  可核验路径和哈希。
- 状态必须严格区分 `research`、`static-ready`、`fixture-live`、`production-live primitive`、
  `production-live loop` 和 `complete`。没有真实 paused artifact 时不得写 live；ACK、schema 字段、单元测试或单场 fixture
  不得冒充完整 OODA。失败 attempt 必须保留，并区分 harness RED 与 capability RED。
- 多代理并行时，负责实际工作包的代理必须把可核验的结果、测试、artifact/commit 和遗留项写入当天/当周报告，并让这些记录
  能在月报截止时汇总；若协调者
  正在编辑同一文件，则先发送这些字段，由协调者合并，不能因避免冲突而漏报。

## 工作流程规则

### 0. 必要性与成本优先（最高优先级）

- 如果不能用用户明确需求、当前真实故障、可复现测试、运行日志或现有数据证明必要性，严禁花费用户的模型额度和时间研究、设计或实现额外安全边界。不得在安全相关领域因为“理论上可能”“更完美”“纵深防御”而自行扩张任务；本条不限制正常的功能优化、故障修复、架构改进和主动推进。
- 提议任何新的门禁、限制、威胁模型或防御性机制前，必须先给出简短的必要性证据与预期收益；证据不足就立即停止该方向，回到用户要求的功能、稳定性和运营结果。
- 不得把假设性的 symlink、gitlink、prompt 篡改、路径逃逸等场景自动升级为当前任务；只有已经发生、能复现、用户明确要求，或存在迫近且不可逆的数据损失/凭据泄露风险时才处理。
- 本项目追求相对安全、可观测、可记录、可回退，不追求耗费大量额度证明“绝对安全”。优先采用最小有效修复并及时提交；不得以安全之名重新收紧复盘模型的文件范围或恢复全仓门禁。
- **交付节奏优先，禁止过度核对与过度谨慎。** 对同一结论只做一次与风险相称的验证；已有可核验证据、测试结果和失败 artifact 直接复用，不重复跑同一检查、不为理论风险扩展审计。验证完成即提交并继续下一个工作包；只有新证据改变结论或用户明确要求时才重新核对。

## 自动游玩 Agent：价值优先与安全边界

- **在本项目中，安全问题如果不能用可复现实证证明会影响实际使用，就不得进行任何处理。** 不得为其修改代码、补测试、扩展 schema/WAL/证明协议、阻断实机运行或启动额外审计。
- “影响实际使用”仅指可观察的真实后果，例如 CK3 自动游玩流程失败、实际发生非预期输入、真实数据损坏、进程无法可靠回收，或生产代码路径中可稳定复现的同类故障。必须先给出对应的实际运行证据或直接覆盖生产路径的确定性复现。
- 仅有理论可能、手工重签/改写本地归档、生产者不可达的伪造状态、纯取证或内部一致性瑕疵、未实际出现的异步/TOCTOU 窗口，都不构成处理依据；发现后立即停止展开，不得把它们升级为 blocker、HIGH 或下一次实机前置门禁。
- 自动游玩功能价值始终优先：先交付可见的游戏里程碑与完整“观察 → 决策 → 操作 → 验证”循环，再处理已有实证的可靠性问题。测试数量、证据链完整度和审计覆盖率不得替代实际可玩能力作为完成标准。
- **性能优化必须保持玩法策略中立。** 严禁为了提高游戏日/分钟而降低对外宣战意愿、降低继续战争或参战意愿、提高投降/议和意愿、回避本应进行的战斗，或以任何其它改变战争选择与结果偏好的方式投机取巧。允许优化的对象是墙钟、暂停频率、重复查询、规划与调度开销、原生速度档位和等价执行路径；性能 A/B 必须保持相同策略输入、war-entry/continuation/termination 决策合同与后置结果语义。若优化会改变战争意愿或终局选择，它必须按独立玩法策略变更评审，且其吞吐提升不得计作性能收益。
- **观测能力优先于反复判定“不可知”。** 自动玩家因缺少 CK3 内部状态而无法作出高价值决策时，默认下一项施工必须是：冻结 exact build → 逆向对应原生字段/查询 → 新增只读 native bridge capability 与 MCP 查询口 → 用实机 paused snapshot 验收 → 再恢复策略执行。不得长期用 `unknown`、`unavailable` 或缺字段作为来回转圈的理由。只有 ABI/版本证据尚未闭合、且已明确记录缺口与下一项可施工入口时，才允许暂时 fail-closed；命令 ACK 仍不得冒充状态观测。
- **MCP 能力合同与 provider 实现均已获授权。** 不再存在“只写能力合同、不实现 provider”的项目约束。发现天朝二期或 G2 的真实 MCP blocker 时，应先冻结最小 typed 合同，随后直接实现 native bridge/provider、静态测试与 exact-build 实机验收；不得把合同文档本身冒充能力完成，也不得因可实现 provider 而扩成与当前 blocker 无关的平台重构。并行调度期间，天朝二期在完全完成前优先级最高，G2 次之；MCP 施工服务于这两条主线，不得中断正在运行的有效 CK3 长局。正式路径继续 MCP-first，OCR 不参与状态真值、导航或 GREEN 判定。
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
- 上述“原生 AI 研究优先”是施工前置和输入账本，**不是要求照抄原生实现**。原生树落盘后，为尽快解除整局游玩 blocker，
  可以先交付最小、确定、可验证的策略；必须把未采用的原生输入/分支、质量差距和替换入口记入对应专题或
  `docs/autonomous-agent-progress/one-generation-blocker-ledger.md`，再依据 production outcome 持续校准。
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
- 唯一已授权例外是独立 `ox_here/` mod：AI 可以低意愿使用“牛来”，所有层级每 12 个月检查一次，执行后冷却
  **恰好 1 年且永远不得提高到 1 年以上**。该例外不得外推到主 mod 或白绮独立版；权威权重与实机边界见
  `docs/court-position-mechanics.md`。
- 第二个已授权例外是独立 `mod_zhongguo_style/`：有地、在世、天朝制公爵及以上 AI 管理者可静默运行 361 后台考核；
  伯爵和男爵只能被考核，不能建立 cohort、分配配额或校准别人。该例外只覆盖此 mod，不能外推到主 mod、白绮版或其他政府。
- 所有脚本文件 **UTF-8 BOM**；yml 缺 BOM 直接不加载
- script values 目录是 `common/script_values`（**不是** scripted_values）
- `is_tutorial_lesson_completed` 是 interface trigger，只能用于 customizable_localization / GUI，游戏状态脚本禁用
- on_action 同名键**覆盖不合并**，扩展用 `on_actions = { 自定义钩子 }` 模式
- 自定义顶层窗口必须在 `gui/scripted_widgets/` 注册才会实例化
- `Tutorial` 数据上下文只存在于 tutorial_window 本体
- 教程课程自动完成用 `trigger_transition`（课程文件内），不要试图从外部点按钮
- 游戏语言非英语时，customizable_localization 的 key 必须在**当前语言**的 yml 里存在（不吃英文回退）；
  用于事件选项名时该 key 本身也要有静态 yml 条目，否则运行期显示 raw key
