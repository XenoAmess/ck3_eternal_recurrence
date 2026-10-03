# 《超人强》1.0.0 本地化覆盖

2026-10-04 已补全法语、德语、波兰语、日语、西班牙语、俄语与韩语，共 **70 条翻译**。每种语言与简体中文、英文使用相同的 10 个 key；本产品没有刻意为空的隐藏 key。

英文与其余七种外语的结果为 **format-certified**。格式认证覆盖 UTF-8 BOM、精确 header、可解析性、重复 key、key 集合，以及 scope、数值格式、图标、格式标记与转义 token；它不代表语义、母语、游戏内布局或实机验收。简体中文的语义和实机结果由[产品验收方案](test-plan.md)及其实际报告记录，本报告只认证文件格式。

## 当次 CK3 语言来源

实际安装为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`，CK3 **1.20.0.3**、Steam build **25652598**。EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

从实际 `launcher/settings-layout.json` 中唯一的 `name=language`、`provider=lang` 项读取九个 `options[].value`，逐项核对 `game/localization/<language>/` 目录及原版 `.yml` 精确 header。layout SHA-256 为 `649319eebff6212e1993e54bd0dc652c35e2158f77909ed9fb8bd840f2648eb9`。完整原版样本路径与摘要保存在[来源和格式收据](localization-coverage.sources.json)。`jomini/` 没有被计入产品语言集合。

| 目录语言 | 精确 header | key 数 | 文案来源 | 文件 SHA-256 |
| --- | --- | ---: | --- | --- |
| simp_chinese | `l_simp_chinese:` | 10 | `runtime_data.py` 简中源文案 | `b4c808e3a67e21b1bc6d344580488c815c0fab245d81cf88851beed72078d448` |
| english | `l_english:` | 10 | `runtime_data.py` 英文参考 | `a270901986cd0b3733812d3e26e444aecd419fd2d44a9f7861703ab0633e8c41` |
| french | `l_french:` | 10 | MiniMax-M3 字符串候选及 token 同步 | `f8d628b8033945ee0f06d0d368632c3d8f1b63e8f2b3ae98eea3fbf6b7a00a75` |
| german | `l_german:` | 10 | MiniMax-M3 字符串候选及 token 同步 | `7d653ec6137bc3163a5b13d25f4912eccdbe5a91a22c03bc0c47c7978a88dc97` |
| polish | `l_polish:` | 10 | MiniMax-M3 字符串候选及 token 同步 | `221b6ee8ff5983c3ac554f54c5fee5cbd818197624f2adcefc64eb43176beaa3` |
| japanese | `l_japanese:` | 10 | MiniMax-M3 字符串候选及 token 同步 | `f1e620ad650adc77c2a643ddf480d3d471463df8f313944f2f1eb06f2559f834` |
| spanish | `l_spanish:` | 10 | MiniMax-M3 字符串候选及 token 同步 | `af55f39cdc097394c8c2c985e706c9bfe6169f8495cf3e1ea9cf2cf6fa8b5014` |
| russian | `l_russian:` | 10 | MiniMax-M3 字符串候选及 token 同步 | `382d04caab5a78ed123960901b6f3743b6892f057924ea8f03e7d14de94a4912` |
| korean | `l_korean:` | 10 | MiniMax-M3 字符串候选及 token 同步 | `f0ed9843fd4fd69170b15720ffdc6034bf0b0fae8d066db44d60346f86127864` |

## 候选与应用过程

执行前只确认 `MINIMAX_API_KEY` 已配置，没有输出或保存其值。所用解释器为 `tools/.venv/Scripts/python.exe`，Python **3.14.7**。中英文由运行时开发代理定稿后按精确 bytes 冻结；七语是独立静态文件，`gen_runtime.py` 只生成中英文。

复用仓库唯一的[候选生成器](../../tools/translate_localization_minimax.py)，SHA-256 `774e41a9268c775ca8c0c7a3efa503abedbd11a70185fcc95006cdf499e63115`。模型为 **MiniMax-M3**，并发数 4，每次只发送同一组 10 个 key-value、英文参考、短语境与保护 token。MiniMax 仅返回翻译字符串 JSON，没有参与代码、文件选择、方案或验收判断。

2026-10-04 的完整冻结源、实际 argv、候选、stdout/stderr 摘要与格式应用收据永久保留于 `D:/ck3-experience-drain-feasibility-20261004/localization-20261004/attempt-01/`。候选调用 exit code **0**；候选 JSON SHA-256 为 `85537f33beb08fef2105bdb475ac63fe074506fce28e059a6a8a08481a2faab9`，stderr 为空。

执行命令由外置驱动组织，完整参数保存在收据；驱动调用的正式工具仍是 `tools/translate_localization_minimax.py`：

```text
tools/.venv/Scripts/python.exe D:/ck3-experience-drain-feasibility-20261004/translation_driver.py generate --attempt D:/ck3-experience-drain-feasibility-20261004/localization-20261004/attempt-01
tools/.venv/Scripts/python.exe D:/ck3-experience-drain-feasibility-20261004/translation_driver.py apply --attempt D:/ck3-experience-drain-feasibility-20261004/localization-20261004/attempt-01
```

应用前执行者核对严格 JSON、七语集合、10 个 key 集及保护 token，并确认中英文与冻结 SHA 完全一致；随后写入七个 `localization/<language>/sxad_l_<language>.yml`。应用后使用通用 `parse_ck3_localization`、`assert_protected_tokens` 对全部九语再做格式认证。所有检查通过；没有调用 CK3，也没有对非中文追加语义或实机检查。

随后运行时修正六项技能数值的显示入口：将 `sxad.1.desc` 中的 `Get<Skill>|0` token 改为 `MakeScope.ScriptValue('sxad_<skill>_value')|0`。七语仅对这六处 token 做机械替换，译文正文保持候选原样，新增 MiniMax 请求数为 0。旧源、候选及首次格式结果保留；新的中英文源、七语替换前 bytes、替换映射及九语格式结果保留于 `attempt-02-scope-skill-values/`，并追加到[跟踪收据](localization-coverage.sources.json)的 `token_sync`。上表记录这次同步后的当前文件摘要。

该步骤只验证 YML 与本地化 token，不执行 CK3 脚本或有限运行时语义，`open_kaishek` 预验记为 **not-applicable**。产品静态检查及确定性双构建由[发布流程](release-plan.md)的完整 L0 步骤覆盖，不以本地化格式结果替代它们。
