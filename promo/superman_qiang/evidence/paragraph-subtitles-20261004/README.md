# 整段字幕修订证据

用户审阅 A0002 实际影片后要求字幕连续显示整段。本次项目 [composer](../../tools/player_trailer_composer.py) 将十场旁白分别制成一个完整字幕 cue；每场从口播开始显示，到场尾淡出前结束，不按 SentenceBoundary 替换短句。原有 `zh-CN-XiaoxiaoNeural` 音频、十场完整文案与 26 个真实 SentenceBoundary 均保留。旧版 31 cue 报告、旧 run、旧成片没有覆盖。

最终源码 SHA-256 为 `23aea5e4b8b838cdd62717fdcd456fd260bf0f32ef4c2d752307c790453d798d`。配置及项目登记插件未改；仍使用 Microsoft YaHei 46 px，字幕安全区为 `[230, 880, 1460, 140]`。SQP-05 的新女王镜头固定 1.0 倍取景，避免额外推镜裁去皇冠；其他艺术镜头保留缓慢推进。

检查结果：

- 十场各一个完整 cue，共十个；换行前后字符与批准旁白完全一致，全部为两行。
- 以实际字体测量，每行最大 1342 px，小于 1460 px 安全宽；逐行字框和 3 px 描边均通过安全区检查。
- 十份 ASS 已使用真实 FFmpeg/libass 烧录成 1920×1080 PNG；实际白字像素边界在 y=936–1016，全部位于字幕安全区。Pillow 字框与 libass 实际像素测量分别保留，未将二者混为同一个测量。
- 最终源码生成的十份 ASS 与实际烧录 smoke 的输入逐字节一致；Python 编译与本项目脚本规则检查 GREEN。
- `subtitle-layout-report.json` 保持 `scenes` 结构，明确记录 paragraph policy、总 cue 数、每场唯一 cue 的完整原文、起止时间、两行文本、实测字框、安全区与保留边界数量，便于最终影片检查。

[布局报告](subtitle-layout-report.json)、[最终源码预检](preflight-receipt.json)与[实际 libass 像素测量](ffmpeg-render-report.json)为本次证据副本。全部原始过程永久保留于 `C:/ck3-superman-qiang-promo-20261004/composer-paragraph-A0001/`，包含旧源码精确副本、layout-A0001/A0002/A0003、十份 ASS、十张烧录图、每条命令的 argv/stdout/stderr/receipt 与检查脚本。第一次换行结果虽符合宽度，但会在词中间断行，已保留并改为优先按中文标点换行；最终选择 layout-A0003。

这些检查只证明完整字幕与字体烧录行为；最终 A0004 影片由主执行者使用新的 native run 构建、探测与交付。本预检没有执行最终影片 render，没有记录人工 approval。
