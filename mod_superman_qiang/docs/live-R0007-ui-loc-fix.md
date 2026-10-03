# R0007 查看界面错误与 A0004 本地化修复

2026-10-04，CK3 **1.20.0.3 / Steam build 25652598**。状态：**A0003 实际界面 RED；A0004 已修复源码并通过生成字节对比，修复后实机界面待验**。机制与勇武的原版惩罚抵消另见[通用技能专题](../../docs/ck3-native-ai/character-skill-trigger-readback-1.20.0.3-2026-10-04.md)。这页不替代完整机制验收或发布门禁。

玩家通过肖像右键的“查看性经验”互动，实际打开了 `sxad.1`；原生上下文确认 root 与 saved subject 都是角色 `31254`。但[原始截图](D:/ck3-experience-drain-feasibility-20261004/r7-ui-event-a01/screen.png)中只有末尾规则段，姓名、经验、六项技能和六项净账本全部缺失。截图 SHA-256 是 `12724e4e780e2aa1ce38ab769cdf3dea545569bbe455449e8ff400f229424f00`。

原始 `error.log` 的 `05:20:37` 段逐一记录14条动态数据链失败：`Failed to find type 'scope:sxad_view_subject'`、`Could not find promote`、`Failed converting statement`，最后是 `Data error in loc string 'sxad.1.desc'`。共42条数据链错误与1条本地化数据错误，完整日志和行738–780的摘录已经[外置保全](D:/ck3-experience-drain-feasibility-20261004/desktop-3fevhd2-1c74096080--superman-qiang--R0007/ui-loc-attribution-runtime-a01/ui-loc-evidence.json)，收据 SHA-256 为 `4e64831e2ea99578e60f0d1c1fe225443d0ba80598f5abd565c45026fc1a75e6`。事件只有一个 `desc`，没有多段选择；saved subject 存在，错误发生在本地化数据模型解析。

脚本中的 `scope:sxad_view_subject` 是合法作用域写法，本地化方括号中的角色数据引用则直接使用 `sxad_view_subject`。当前原版有以下明确先例，完整源码 SHA、行文本和输入身份在[永久证据索引](live-R0007-ui-loc-fix.evidence.json)中：

| 原版位置（相对 `game/`） | 实际数据链 |
| --- | --- |
| `localization/english/activities/coronation_activity_l_english.yml:413、415` | `[host.MakeScope.ScriptValue('…')]` |
| `localization/english/dlc/bp2/dlc_bp2_yearly_6_l_english.yml:180` | `[root_scope.MakeScope.ScriptValue('minor_gold_value')]` |
| `localization/english/decisions_l_english.yml:1759` | `[root_scope_temporary.MakeScope.ScriptValue('expand_duchy_max_size_value')]` |

A0004 仅在权威 `tools/runtime_data.py` 的中英文 `sxad.1.desc` 各替换14处前缀：`[scope:sxad_view_subject.` → `[sxad_view_subject.`，再运行生成器。七种外语执行同一 key 的机械 token 修正，各自其他23条译值保持。事件脚本、经验计数、技能账本、modifier、查询只读合同和11个非本地化生成文件字节保持；生成器本体保持。`gen_runtime.py --check` 的13个生成文件逐字节对比通过。

| A0004 冻结源码 | SHA-256 |
| --- | --- |
| `tools/runtime_data.py` | `fc8452e9e8ee482d1ce070cf086205e8b592754bfb1ced005c99d68e4c289784` |
| `localization/simp_chinese/sxad_l_simp_chinese.yml` | `29ac11c5a8ad6c2f5b115974658d6d32616fdcf03081bbd24ddaff06c285e25a` |
| `localization/english/sxad_l_english.yml` | `d16c7f9cd076096cc39f2734b496119d23d3630aa9dab23f16c3d07b3c49a59b` |

A0003 的生成器、权威数据与中英原始 bytes 另存[修改前输入目录](D:/ck3-superman-qiang-20261004/A0003-source-before-loc-datamodel-fix-20261004/preserved-inputs.json)，旧 builder、attempt、日志和截图不改写。外语原始候选、九语格式与来源 hash 的历史见[本地化记录](localization-coverage.md)。后续必须用新构建实际打开互动，确认姓名与13个数值完整显示、与独立变量/技能读回一致、查询无状态写入，并复查新日志没有本次数据链错误；源码和格式检查不能替代这些实际后置。
