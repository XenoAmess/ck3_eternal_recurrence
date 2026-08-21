# 琉焰卿的永恒轮回（AGENTS 指南）

## 项目结构

- `XenoAmess_s_Eternal_Recurrence/` — CK3 mod 源目录；正式发布只使用 `build_release.py` 生成的 staging
- `Crusader Kings III/` — 游戏本体目录（仅作参考/逆向用，已被 .gitignore 排除）
- `docs/` — 知识库（跨存档存储机制、GUI 系统、语法踩坑），改机制前先读
- mod 通过用户目录的 `mod/XenoAmess_s_Eternal_Recurrence.mod`（path 指向本仓库）注册
- Steam 创意工坊物品 id：**3784706360**（首次上传后启动器把 `remote_file_id` 写回用户目录 .mod）。
  注意：`remote_file_id` **只能留在用户目录外层 .mod，不要同步进仓库内层 descriptor.mod**——
  更新上传时启动器要回写内层 descriptor，带此字段会导致 "Mod descriptor validation failed" 上传失败。
  更新工坊 = 改仓库内容 → 启动器 Mods → 上传 Mod 选同一物品再传一次。预览图用 mod 根目录的 `thumbnail.png`
  （启动器约定俗成按 mod 根目录找此文件名，同其他 dev mod）；descriptor 里 `picture="thumbnail.png"`
- 工坊描述维护在 `workshop/description.bbcode`（BBCode，内嵌 4 张截图的 steamusercontent 直链）；改完描述到物品页「编辑标题与描述」整段替换

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
py tools/compose_trait_stars.py                             # 10 级特质星标 → 120×120 RGBA DDS
py tools/build_release.py --check                           # 临时双构建，验证 manifest/ZIP 可复现
py tools/build_release.py                                   # 生成 dist staging、manifest 与 deterministic ZIP
py tools/build_vivhite_release.py --check                   # 白绮独立版临时双构建
py tools/build_vivhite_release.py                           # 生成独立 staging、manifest 与 ZIP
```

八套脚本生成器及一套决议素材投影工具，**不要手改 `GENERATED FILE` 标记的文件**。计分参数只改 `tools/scoring_data.py`，
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

## 知识沉淀

- 干活中学到的新知识**当场同步进 `docs/`**，不要等任务收尾：尤其是 Paradox 脚本语言
  （trigger/effect 语义、作用域切换、求值时机）与 CK3 实现细节（加载顺序、暂停行为、
  启动器/工坊合并行为）的实证结论
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
