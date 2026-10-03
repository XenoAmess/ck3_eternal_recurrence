# 本地化验收范围排查与整改（2026-10-03）

用户再次明确：**实机验收只使用简体中文；英文及其他语言仅做格式检查。** 本规则覆盖本仓库各产品的开发、验收和正式发布。非中文不要求语义、术语、母语审阅、游戏内显示、布局或截断签核。

## 为什么扩大了范围

旧 `AGENTS.md` 的发布策略写着“执行完整的国际化差异、占位符、术语、格式和游戏内验证”。旧 `docs/localization-workflow.md` 又要求目标语言人工术语、人格和游戏内截断签核，并把既有“中文实机、其他语言格式”的方法限定为 More Tenets Slots 单一产品。执行者错误地把这些旧要求应用到本次两个维护版的发布检查，没有优先执行用户已经明确的中文实机范围。

代码中也有两类扩大入口：`tools/run_ox_here_loc_smoke.py` 默认选择 `all`，会为全部语言运行真实游戏；多个产品的发布校验器把与英文相同的内容、外语术语或特定文字种类作为失败条件。它们不是格式检查，因此已按当前指令整改。错误的执行范围属于执行者责任，旧提示不能覆盖用户指令。

## 当前规则及修改入口

| 入口 | 当前行为 |
| --- | --- |
| [AGENTS.md](../AGENTS.md)、[翻译工作流](localization-workflow.md)、[测试流程](testing-workflow.md) | 简体中文语义审阅和实机；非中文只检查格式。旧发布 QA 的非中文签核要求已明确退役。 |
| 两个维护版各自 README、适配/测试/发布计划及状态报告 | 取消外语实机和组合语言计划；英文过程记录不能计作中文实机通过。见[统一范围说明](two-maintained-mods-testing-scope-2026-10-03.md)。 |
| [牛来实机 runner](../tools/run_ox_here_loc_smoke.py) | CLI 默认及唯一选择为 `l_simp_chinese`；直接调用入口也拒绝 `all` 和非中文。其离线本地化检查覆盖其他语言格式。 |
| 自动升级建筑、天朝经商贪腐、驱策朝贡国、肃清曼荼罗、体验优化、重整河山及法理征服的本地化校验入口 | 退役非中文语义、术语、文字种类、英文相同内容等门禁；保留 key、编码/BOM、header、解析、转义及保护 token 检查。简体中文产品机制检查保留。 |
| 主 mod 和白绮静态校验入口 | 仅对简体中文检查功能说明和自然正文合同；英文 branding、外语正文逐字内容及数字语义不再是验收门禁。既有 key/header/token 检查、历史合同身份及生成器字节复现要求保留。 |
| [天朝 361 发布本地化预检](../mod_zhongguo_style/tools/prepare_release_localization.py)及正式构建器 audit 消费入口 | 非中文 audit 使用格式检查标签，发布构建继续要求报告身份、精确文件覆盖及当前 bytes/SHA；旧语义标签不构成当前门禁。见[专属说明](../mod_zhongguo_style/docs/release-localization-format-policy-2026-10-03.md)。 |
| 本次任务的外置启动 helper | `review_and_start.py` 和 `live_session.py` 在写入离线审阅或加载启动模块前校验实际 `pdx_settings.txt`，仅允许唯一的 `l_simp_chinese` 设置；语言重载/组合准备入口同样拒绝非中文实机。 |

正常翻译生成仍可以要求保持原意、语气和目标语言表达。这是生成意图，不能扩展为非中文人工语义审阅或发布签核。非中文格式通过只记作 `format-certified`，不能称作语义、母语或实机通过。

## 排查边界与证据

已搜索仓库 instruction/prompt/skill 文件、现行本地化与发布文档、runner、validator 和 builder，并检查 `C:/Users/Administrator/.codex` 的 instruction/prompt/skill 文件名及相关匹配片段。全局搜索没有发现要求本项目多语言实机的匹配；未读取凭据、配置全文、会话或历史日志。初始路径清单覆盖仓库 12 个及全局 46 个 instruction/prompt/skill 路径，完整 argv、命中及文件摘要保全在 `C:/workspace/two-mod-maintenance-20261003/localization-prompt-inventory-R0001/`。该清单记录排查时刻，不将旧命中数当成整改后的结果。

历史实机报告、原始配置、截图、失败 attempt 和旧 audit snapshot 保持原样；需要解释的现行入口增加日期化退役说明。已取得的英文实机记录是历史诊断，后续中文验收使用新 attempt，不改写旧记录。冻结的 CK3 MCP 消费执行树没有改动。

本轮验证只覆盖修改的范围，不启动游戏、Steam 或翻译 API：

- 牛来：29 项 runner/格式检查直接单测通过，另有 4 项相关能力覆盖检查通过。证据 `localization-runner-final-verification-R0001/report.json`，SHA-256 `e9fd3ebf647c43f0c7a894d4c9f75b136c1ddbf88b703c7b4dfaa2d5bea06847`。
- 五个共享格式校验入口：18 项定向检查通过；体验优化对应已有单测通过。证据 `shared-localization-format-validators-R0001/freeze-and-review.json`，SHA-256 `bc9bf9f8320ac2035b9a4077bb32c5d9321e612011df00e031cab91b29d8497e`。
- 重整河山：7 项定向单测通过；36 个运行时文件摘要未改变。证据 `reclaim-format-gate-scope-R0001/report.json`，SHA-256 `fe7875331e6c575495711fa445e49dc484ab2cd76833d985219ba708721bfa7d`。
- 法理征服：3 项直接分支检查通过，接受格式有效的英文相同外语内容，仍拒绝缺 key 和错误 header。证据保存在该产品 `docs/language-format-policy-check-2026-10-03.json`。
- 天朝 361 预检：23 项直接单测通过；未改 229 个运行时/本地化文件。精确源码及 stdout/stderr 保存在 `zhstyle-format-policy-probe-20261003-02/`。
- 天朝 361 构建消费方：3 项直接测试通过，覆盖新格式标签接受、旧语义标签拒绝、source/target SHA 过期、缺文件及精确清单；旧 canonical 报告字节未变。证据保存在 `zhstyle-format-consumer-probe-20261003-01/freeze.json`。
- 外置启动保护：实际中文配置接受、实际英文配置拒绝，两个启动入口的保护均早于副作用边界。证据 `chinese-launch-guard-verification-R0001/report.json`，SHA-256 `9c84261f763a00928c81272c2656960def7e47c71e9e7258340b557e7cb00d96`。

以上相对证据路径均位于 `C:/workspace/two-mod-maintenance-20261003/`。后续新增源码、文档或执行入口必须沿用本规则，不能因旧报告、模型可理解某语言或发布指令而恢复外语实机和语义门禁。

## 最终复查补齐

初包推送后，只读复查继续发现了遗漏，逐项报修，未把初包称作全仓终态：天朝经商贪腐 README/旧审阅页、重整河山旧方案、天朝 361 正式 schema 与两个运行时专题、自动升级建筑三期计划和体验优化旧审阅页仍有旧范围；白绮及主 mod 静态校验还有外语自然正文、branding、数字语义或普通英文词要求。相关现行入口已同步当前范围，历史正文只追加日期化退役说明。原始漏项观察保存在 `localization-final-readonly-audit-R0001/audit-report.json`，SHA-256 `c191eb34da3e62a10e2ff568b081801e92bb4a477e7b1aea39cb656a3c7c365a`；这是当时的报修清单，不能当作尾包完成证明。

非中文自然正文空值检查也统一退出内容门禁；空字符串仍必须符合语法、key 和保护 token 等格式要求。缺失必需引擎表达式的空值仍会失败，不能把可解析的空值称作翻译完成。简体中文的可见正文非空及功能语义检查继续保留。

尾包定向验证：

- 白绮、主 mod 和五个共享检查入口：7 个直接测试方法及 13 项新增分支检查通过。9 个修改源文件语法及差分检查通过；白绮的生成器复现、历史合同读取、解析和 token 函数保持原样，其他 helper 除新增中文语言条件外 AST 一致。证据 `vivhite-localization-format-policy-R0001/freeze-and-review.json`，SHA-256 `8a5fbb737d565b9e6d78a5c8b37f856b0c73159da194379fbc41a75f9260c46e`。
- 天朝 361 七语 release translation loader：4 项直接测试通过，格式合法空字符串可加载，非字符串、缺/多 key 和顺序漂移仍失败，来源 SHA 过期的候选不加载。1032 个运行时文件字节未变，CN/EN 作者数据规格保留，未重新生成；证据 `zhstyle-release-translation-empty-probe-20261003-01/freeze.json`。

尾包不重跑旧语言实机，不刷新旧报告，不把语义门禁移除写成外语翻译或实机通过。首包 `fa28a0f0f9661fe9e63219f61de31dcce7f779b6` 的两个官方工作流均 completed/success；此结果只绑定首包，后续提交另核对其 exact HEAD。

## 已知格式问题及后续工作

天朝 361 的实际全文件格式 audit 发现七种外语 core 文件各缺 37 个当前 key，并有 key 顺序漂移；mechanisms 文件格式检查没有该问题。诊断保存在 `zhstyle-format-policy-probe-20261003-01/key-format-diagnostics.json`。这是现有文件的真实格式 RED，本次没有通过改报告、弱化格式检查或补造翻译把它写成 GREEN；该产品正式发布前仍须修复并生成绑定当前字节的格式报告。旧 canonical snapshot 继续保留为历史记录，不再证明当前标签或文件状态通过。普通 push/PR 不以该产品正式 release audit snapshot 的时效为门禁。

本次两个第三方维护版的目标继续有效：分别完成剩余简体中文实机、测试报告和独立新 Workshop 发布。多语言实机计划已取消，不再是待办项。

## 2026-10-03 外置控制入口补充勘误

后续只读检查又发现两个外置入口遗漏，已先保全各自精确旧字节再修正：

- `configure_holding_reload.py` 原入口会切换英文；原片和回执保存在 `holding-legacy-reload-cn-guard-20261003-01/`。兼容入口现仅委托既有 `configure_locale_reload.py`，参数固定为 `mod_change_holding_types simp_chinese`，拒绝语言覆盖参数。重载仍由既有简中配置与来源存档 SHA 守卫处理。
- `game_keyboard.py` 原 paste 分支接受任意 `switchlanguage ` 前缀；现只接受归一化后文本精确等于 `switchlanguage l_simp_chinese`，原有 scan/key 和文件读取分支不变。原片、修正源码、差分及布尔 guard 检查见 `external-cn-control-scope-addendum-20261003-01/{game_keyboard-original.py,game_keyboard-cn-guarded.py,addendum.json,verification.json}`；结果为 `SOURCE_GUARD_GREEN_NOT_EXECUTED`，其含义仅为源码检查通过。

上述两个入口均未执行，没有屏幕、剪贴板、游戏启动或 profile 写入；冻结的 `C:/tm-screen` 消费树及当前 `live_session.py` 没有改动。旧历史记录保持原样，补充证据根仍为 `C:/workspace/two-mod-maintenance-20261003/`。这项勘误不证明 holding R5 已启动或中文实机通过，实际验收继续等待新 attempt 的原生日志与清晰中文画面。

## 2026-10-03 后续简体中文实机完成记录

上述源码守卫检查与实际实机证据分开保留。后续法理征服 R0003 完成九组72项综合语义断言、普通中文宣战和公国战争保存重载，已知诊断限制见[本产品中文报告](../mod_de_jure_conquest/docs/cn-live-acceptance-2026-10-03.md)。地产类型转换 R0005 在简体中文 profile 完成12项唯一断言、六种中文决议名称、400金币费用显示与完整无遮挡警告；实际付款另引用早前简体中文 R0002，详见[本产品当前测试报告](../mod_change_holding_types/docs/test-report-2026-10-03.md)。两游戏均已停止并释放屏幕占用。历史外语 attempt 继续只作过程证据，未计入任何中文签核；其他八语仍仅做格式检查。上述结果不等于两产品已经发布。
