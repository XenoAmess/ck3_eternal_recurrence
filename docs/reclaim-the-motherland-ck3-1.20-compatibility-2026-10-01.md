# 重整河山：CK3 1.20.0.2 源码兼容迁移

2026-10-01 状态：**GREEN_L0_ONLY_RUNTIME_PENDING**。本轮只完成源码迁移、静态合同、解析和构建；新版实机验收仍待根执行者完成。历史 `0.4.0` 的 CK3 `1.19.0.6` 发布与验收记录保留原样，不能外推为新版 GREEN。

产品为 `mod_reclaim_the_motherland`，Workshop item 为 `3798404599`。本轮未修改 `descriptor.mod` 的产品版本或 `supported_version`，未调整旧原生 ABI，也未启动 CK3、提交、推送或上传 Workshop。

## 冻结的游戏身份

- CK3：`1.20.0.2`，Steam build `25588574`。
- 本机安装：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`；仓库游戏参考目录指向此安装。
- EXE SHA-256：`ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`。
- 原版七份文件、六个定义的全文与解析后 body SHA 固定在 [reclaim_the_motherland_vanilla_1_20_0_2.json](../tools/reclaim_the_motherland_vanilla_1_20_0_2.json)。文件范围涵盖 interactions、scripted modifiers、mandate decision、threshold values、dynastic-cycle effects、ministry triggers 和 government flags。
- 对比基线为外置 `C:/workspace/ck3-upgrade-20261001/baseline/vanilla-text/game` 的旧版 `1.19.0.6` 文本快照。

## 原版变化与本产品投影

| 范围 | 新原版变化 | 本轮迁移 |
| --- | --- | --- |
| 提议附庸 | 旧五个锚点移入 `offer_vassalization_interaction_ai_acceptance_diplomacy`；品级奖励变为 `10 × (actor tier − recipient tier − 1)`，双方天朝再乘二 | 新建私有 general 与 diplomacy，仅从本产品覆盖的 offer interaction 重定向；其余原版消费者继续调用原版 modifiers |
| 后朝身份政策 | 原版品级公式已变，照搬旧公式会失去固定奖励合同 | 后朝仍在差距大于一级时固定 `+10`，恢复王国/帝国拒绝项，取消双方天朝倍乘及通用霸权 `+10`；保留其余新版接受项 |
| 最近独立 | 原政策绑定释放者的主要头衔与确切后朝 title object | 继续使用 `1825` 天、精确后朝 marker 和当前持有者，接受项为 `-50` |
| 三省六部 | 原版新增 `government_uses_ministry_budget` flag | 保留新增 budget flag 和 celestial flag，只沿用既有唯一后朝 entitlement 分支；天朝仍拥有优先权 |
| 群雄割据 | 原版把 realm-name event 移到弱高阶头衔销毁之后 | 原版规则的改名副本完整刷新；自定义规则中的同一执行顺序同步迁移，旧皇帝、忠臣、留任大臣排除条件保留 |
| 夺取天命 | 原版调整 `is_shown` 条件顺序 | 重新投影新原版，只插入已有 shown、valid、AI 三处后朝锁；`51%` 判定与委托原版 effect 的路径保留 |
| 标准朝号 | 七份文件 hash 改变，但原版朝号 key 集合仍为同一 `89` 项 | 仅刷新生成器 provenance；九语言生成本地化字节均未变化 |

`gen_reclaim_vassalization_override.py` 生成两个文件：offer interaction 只替换一个 general 调用，私有 general 只替换一个 diplomacy 调用，私有 diplomacy 中只插入五处批准的定制。静态检查逐项逆转这些投影，恢复后的定义必须匹配冻结原版 body SHA。

`gen_reclaim_native_overrides.py` 生成原版 shattering 的改名副本、ministry override 和 mandate override。三份产物均有 `GENERATED FILE` 标记，修改必须通过生成器。逆投影同时校验它们能恢复到确切原版定义。

恢复天命仍委托原版 `tgp_claim_mandate_of_heaven_effect`。新原版在该 effect 中改用 government flag 判断天朝，并在创建五位大臣时设置 faith 与 rite；本产品没有复制或另建这套原版机制。

## L0 与解析证据

验证解释器为仓库 `tools/.venv/Scripts/python.exe`，Python `3.14.7`。产品合同测试 `20` 项、构建测试 `10` 项、静态校验、两个生成器的 `--check` 与 deterministic 双构建均通过。运行时 inventory 从 `35` 增为 `36`，新增的一个文件只承载两个私有 scripted modifiers。五份 scripted-effect 文件的顶层定义数为 `7/1/1/1/1`。

十二个身份向量直接执行新原版及生成结果中三个目标 modifier 的解析树，并验证普通 actor 保留新原版数值。示例：天朝霸权对天朝王国、公国、伯国的原版身份合计为 `30/50/70`，后朝为 `-40/10/10`；普通伯国的原版合计为 `40`，后朝为 `10`。这些数值只覆盖高阶拒绝、宽品级差和霸权三项，不能当作完整 AI 接受度。

附加 title-memory 负控覆盖变量到期、另一后朝、缺失 marker 和持有者交接。旧有规则、忠诚优先级、继承同一 title object、任职身份、`50%/51%` 边界及禁止强制退位合同也全部通过。

解析器为本机 `open_kaishek` commit `522ac2d93bd6c534a6a242a227057de40a8977c1` 的 packaged CLI `0.1.0-cli`，JAR SHA-256 为 `6ac143ebf03f3e1a041dff01b2d808e60de8e289d18cebf9855682f0a80b6d82`。只使用 `corpus --require-corpus` 的 parser 模式：源码与 staging 均为 `16/16` 文件、`99459` bytes、零 diagnostics，corpus SHA-256 均为 `6f7814d5bab7e3a887b802e983482332b54fd0cf60a92e45ba459dba06c1f381`。目前没有 CK3 `1.20` semantic profile，旧 `1.19` validator 未用于新版语义 GREEN。

外置永久证据：

- `C:/workspace/ck3-upgrade-20261001/audits/reclaim-the-motherland-compatibility.json`：产品汇总，绑定 exact EXE、原版合同和源码字节。
- `.../audits/rmtm-l0-001/`：首次全部 L0 与源树 parser 输出。该次仅新测试模型对缺失 variable scope 的处理 RED，失败原样保留。
- `.../audits/rmtm-l0-002/`：修正测试模型后，20 项合同测试、实际构建与 staging parser GREEN；此修正没有改变运行时源码。
- staging：`.../audits/rmtm-l0-002/build`，manifest：`build.manifest.json`，ZIP：`build.zip`。
- manifest SHA-256：`5d6e856cd86891b9396b23e578841422521ff4c461cfe200f38baf8274c920c4`。
- ZIP SHA-256：`0d4d96ce356b748f25f433d58bb489b6983969dd2611677cd43be16e3b0a1fc7`。

日常静态门禁继续检查九语言结构，七语正式发布审计仅通过 `validate_reclaim_the_motherland_static.py --release-localization` 或正式 `--release` 构建启用；本轮没有翻译或发布。

## 后续实机入口

先对新版外置 fixture 做 parser-only 和 exact-build 预检。旧 `1.19` 原生 bridge 不可用于 `1.20`；待新版原生能力有独立证据后，再按 [产品验收方案](../mod_reclaim_the_motherland/docs/acceptance-plan.md) 使用一次性 userdir 和本轮 36 文件 staging 验收。

最低矩阵包括：自定义与原版 shattering 两条规则；旧皇帝直辖地与忠臣 realm/title identity；唯一 ministry entitlement、九席任职及预算界面；后朝与普通 actor 的真实 offer interaction 理由和接受度；title-bound `-50` 的继承交接及自然到期；`50%/51%` 天命边界、后朝锁和恢复效果；后朝继承、命名与旧存档幂等迁移。

L0 和 parser GREEN 不能替代上述游戏行为验收，也不能代替 Workshop 发布、公开 Change Notes 回读或新版 release changelog。
