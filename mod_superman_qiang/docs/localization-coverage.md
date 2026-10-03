# 《超人强》1.0.0 本地化覆盖

2026-10-04 已补全法语、德语、波兰语、日语、西班牙语、俄语与韩语。首次完成 **70 条翻译**，转移机制改为属性修正账本后追加 **28 条增量候选**（14 条新名称、14 条更新说明）；另将 12 个纯引用 alias 逐字同步到每种外语。当前每种语言与简体中文、英文使用相同的 **24 个 key**；本产品没有刻意为空的隐藏 key。

英文与其余七种外语的结果为 **format-certified**。格式认证覆盖 UTF-8 BOM、精确 header、可解析性、重复 key、key 集合，以及 scope、数值格式、图标、格式标记与转义 token；它不代表语义、母语、游戏内布局或实机验收。简体中文的语义和实机结果由[产品验收方案](test-plan.md)及其实际报告记录，本报告只认证文件格式。

## 当次 CK3 语言来源

实际安装为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`，CK3 **1.20.0.3**、Steam build **25652598**。EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

从实际 `launcher/settings-layout.json` 中唯一的 `name=language`、`provider=lang` 项读取九个 `options[].value`，逐项核对 `game/localization/<language>/` 目录及原版 `.yml` 精确 header。layout SHA-256 为 `649319eebff6212e1993e54bd0dc652c35e2158f77909ed9fb8bd840f2648eb9`。完整原版样本路径与摘要保存在[来源和格式收据](localization-coverage.sources.json)。`jomini/` 没有被计入产品语言集合。

| 目录语言 | 精确 header | key 数 | 文案来源 | 文件 SHA-256 |
| --- | --- | ---: | --- | --- |
| simp_chinese | `l_simp_chinese:` | 24 | `runtime_data.py` 简中源文案 | `a61f0411f95387115be9bce51d51286e6e5f2bf255838f23cac9ab8b686f60f8` |
| english | `l_english:` | 24 | `runtime_data.py` 英文参考 | `0f5c5b0afdaaff35ff80e1931b8c538d8b87d8d0103cd75fc3108b3720eaeda6` |
| french | `l_french:` | 24 | MiniMax-M3 字符串候选及 alias 同步 | `da3c09c73ada071d18859d2bba2eabe897fd49204bc663b2aeb58927ee16f29e` |
| german | `l_german:` | 24 | MiniMax-M3 字符串候选及 alias 同步 | `121b4cc9e3a454852a3f88c0acf2830263a5ba68f780131240dba0f8b5e2caf1` |
| polish | `l_polish:` | 24 | MiniMax-M3 字符串候选及 alias 同步 | `d36b32bae867bf67de4faeb226064f914421464f399fb0790748f5cf3b519dca` |
| japanese | `l_japanese:` | 24 | MiniMax-M3 字符串候选及 alias 同步 | `f53950734991b3652d87e8e81fb9096855a489667273d1e2cac78838097d1d88` |
| spanish | `l_spanish:` | 24 | MiniMax-M3 字符串候选及 alias 同步 | `5968b3b84b150235bb4fb052dcc263a1e6752cc8fd7360ca7bc6e71788b84945` |
| russian | `l_russian:` | 24 | MiniMax-M3 字符串候选及 alias 同步 | `ac7774c8951760656076448693f6421a84bd4c16074a40e8dca249cc97716f59` |
| korean | `l_korean:` | 24 | MiniMax-M3 字符串候选及 alias 同步 | `32cb0453632c19e3e7fe6322ce64d6a4d0a7c6cab51932ee75f1f7cb66a2a66e` |

## 候选与应用过程

执行前只确认 `MINIMAX_API_KEY` 已配置，没有输出或保存其值。所用解释器为 `tools/.venv/Scripts/python.exe`，Python **3.14.7**。中英文由运行时开发代理定稿后按精确 bytes 冻结；七语是独立静态文件，`gen_runtime.py` 只生成中英文。

复用仓库唯一的[候选生成器](../../tools/translate_localization_minimax.py)，SHA-256 `774e41a9268c775ca8c0c7a3efa503abedbd11a70185fcc95006cdf499e63115`。模型为 **MiniMax-M3**，并发数 4。首次每种目标语言只发送 10 个 key-value，属性修正机制的增量每语只发送 4 个 key-value，均附英文参考、短语境与保护 token。MiniMax 仅返回翻译字符串 JSON，没有参与代码、文件选择、方案或验收判断。

2026-10-04 的完整冻结源、实际 argv、候选、stdout/stderr 摘要与格式应用收据永久保留于 `D:/ck3-experience-drain-feasibility-20261004/localization-20261004/attempt-01/`。候选调用 exit code **0**；候选 JSON SHA-256 为 `85537f33beb08fef2105bdb475ac63fe074506fce28e059a6a8a08481a2faab9`，stderr 为空。

执行命令由外置驱动组织，完整参数保存在收据；驱动调用的正式工具仍是 `tools/translate_localization_minimax.py`：

```text
tools/.venv/Scripts/python.exe D:/ck3-experience-drain-feasibility-20261004/translation_driver.py generate --attempt D:/ck3-experience-drain-feasibility-20261004/localization-20261004/attempt-01
tools/.venv/Scripts/python.exe D:/ck3-experience-drain-feasibility-20261004/translation_driver.py apply --attempt D:/ck3-experience-drain-feasibility-20261004/localization-20261004/attempt-01
```

应用前执行者核对严格 JSON、七语集合、10 个 key 集及保护 token，并确认中英文与冻结 SHA 完全一致；随后写入七个 `localization/<language>/sxad_l_<language>.yml`。应用后使用通用 `parse_ck3_localization`、`assert_protected_tokens` 对全部九语再做格式认证。所有检查通过；没有调用 CK3，也没有对非中文追加语义或实机检查。

随后运行时修正六项技能数值的显示入口：将 `sxad.1.desc` 中的 `Get<Skill>|0` token 改为 `MakeScope.ScriptValue('sxad_<skill>_value')|0`。七语仅对这六处 token 做机械替换，译文正文保持候选原样，新增 MiniMax 请求数为 0。旧源、候选及首次格式结果保留；新的中英文源、七语替换前 bytes、替换映射及九语格式结果保留于 `attempt-02-scope-skill-values/`，并追加到[跟踪收据](localization-coverage.sources.json)的 `token_sync`。

最终生产机制使用六项净转移账本及永久 character modifier，源文案说明转移的是修正点、基础属性保持原值、原版百分比修正和取整仍继续作用。只翻译更新的 `trait_sxad_sex_experience_desc`、`sxad.1.desc` 与两个新名称 `sxad_absorbed_skill_modifier`、`sxad_drained_skill_modifier`，共 **4 × 7 = 28** 个增量字符串；其余 8 个原 key 的外语译值保持原样。六项属性各有 gain/loss modifier alias，12 个 alias 只含 `$sxad_<名称>$` 与原版 `$<skill>$` 保护引用和标点，由执行者逐字复制，未送入翻译。

增量候选、冻结中英源、七语原始 bytes、实际命令及九语最终格式报告保存在 `attempt-03-modifier-balance/`；调用 exit code **0**，stderr 为空，候选 SHA-256 为 `12ec14de06cdd43c58832e849b95e5520096a6ba9aec66a795d3ebc4c1e18e99`。[跟踪收据](localization-coverage.sources.json)的 `deltas` 保留该增量；上表记录最新24-key文件摘要。增量再次通过九语格式认证，包括新增六项余额 ScriptValue tokens 和所有 alias 引用，未进行非中文语义或实机检查。

该步骤只验证 YML 与本地化 token，不执行 CK3 脚本或有限运行时语义，`open_kaishek` 预验记为 **not-applicable**。产品静态检查及确定性双构建由[发布流程](release-plan.md)的完整 L0 步骤覆盖，不以本地化格式结果替代它们。
