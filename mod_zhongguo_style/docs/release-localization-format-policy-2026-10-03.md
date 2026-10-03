# 发布本地化检查范围（2026-10-03）

用户当前要求：仅简体中文进行真实游戏验收；英文、法文、德文、日文、韩文、波兰文、俄文和西班牙文只检查格式。其他语言不要求实机画面、语义审阅、术语审阅或母语签核，格式合法的英文占位也不构成内容门禁。

普通翻译生成仍使用共享 `make_prompt` 的翻译目的、meaning/tone 指令、英文来源和简中参考。生成语境与结果检查分别处理；不得把生成指令写成外语质量验收要求。此次没有调用翻译服务，没有改动任何本地化或运行时文件。

## 工具行为

`tools/prepare_release_localization.py` 的候选加载、单 key 修复、来源迁移、候选归集、apply 前检查与正式 audit 统一执行该范围。保留严格 JSON/字符串结构、key 清单与顺序、UTF-8/BOM、准确语言 header、YML 语法、保护 token、原始引号/转义、非法换行和 U+FFFD 检查。LF 与 CRLF 均可加载。

非简中不再因与英文相同、复制参考文本、目标文字类别、混合文字、外语术语、工资或申诉表述触发拒绝、拆批或质量重试。兼容函数名 `candidate_quality_errors`、`targeted_quality_errors` 与 `candidate_residuals` 保留；这些函数不再对非简中执行内容门禁。简中四项 3.25 结算数值、申诉扣款与俸禄扣减数值、3.75/3.5/3.25 奖励矩阵检查仍保留。同年重复结算的决议/trigger/effect 机制断言仍保留。

正式 audit 的检查标识改为 `utf8_bom`、`header`、`syntax`、`key_order`、`protected_tokens`、`value_encoding`。候选 JSON audit 另外绑定来源 plan、完整 index 与文件哈希。GREEN 仅证明列明的格式条件，不证明翻译质量或真实游戏验收。

## 本次验证与实际边界

直接单测 `tools/test_prepare_release_localization.py` 共 23 项通过，涵盖英文副本/混合文字的格式接受、缺 key/token 的拒绝、BOM/header/UTF-8/语法失败、格式失败的有界重试、简中数值语义和同年结算机制。没有执行外语翻译 API 或游戏。

2026-10-03 的真实文件格式 audit 保全于外置目录 `C:/workspace/two-mod-maintenance-20261003/zhstyle-format-policy-probe-20261003-01/`：`policy-probe.json`、`audit-stdout.txt`、`key-format-diagnostics.json`。结果为 **RED**：七种非中英语言的 core 文件各有 199 个 key，当前英文 core 有 236 个 key，均缺 37 个 scoreboard dossier/detail key，并存在 key 顺序漂移。mechanisms 文件未报告格式错误。此 RED 是实际格式问题，未因取消语义门禁而忽略；待负责来源/生成结构的工作包修复后，必须使用新的 attempt 验证。此次核对的产品内非 docs 的 229 个 JSON/YML 文件字节未改变。

历史已冻结的质量审阅及失败报告不改写。现有 canonical `docs/release-localization-audit.json` 没有被此次工具改动覆盖，不能把旧报告重标为本次新格式 audit。

## 调用方衔接

根目录 `tools/build_mod_zhongguo_style_release.py` 的 `LOCALIZATION_AUDIT_CHECKS` 对报告标签作精确校验；必须与上述新标签同步。`tools/test_build_mod_zhongguo_style_release.py` 使用该常量生成测试报告。CI `.github/workflows/static-ci.yml` 调用直接单测及 `prepare_release_localization.py audit --write-report ...`，后续由根任务整体验证。此次工具单测通过不代表整个发布构建或仓库 CI 已通过。

### 2026-10-03 消费方补齐说明

构建器现在使用与 producer 相同的六项格式标签，并明确报告不证明非简中内容或实机验收。直接消费测试接受准确的新标签，拒绝旧 `quality`、`no_english_placeholders`、`target_script` 标签，且继续拒绝 SHA 过期、被引用文件缺失及不完整的 4 来源/14 目标清单。

历史 canonical 报告仍保留原字节；它的旧标签已不满足当前格式合同，不能直接用于当前正式构建，也不能只改标签冒称重新验证。七语各缺 37 个 key 和顺序漂移的真实格式 RED，留待该产品正式发布工作修复并生成新的实际 audit。本次仅修正检查范围和消费合同，不构成“中郭”发布任务，不补译或改动运行时文件。

已核对 CI 的全文件格式 audit 只在 `workflow_dispatch` 或 `zhongguo` 产品 tag 触发；普通 push 不要求刷新该历史报告。该边界不取消产品正式发布前的真实格式门禁。
