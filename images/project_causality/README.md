# 《project因果律》人物与宣传视觉资产

本目录保存《project因果律》及副标题“伪天司的辉煌愿景”的人物视觉锚点与宣传片章节图。人物原图由项目所有者在
2026-09-18 明确指定并要求复制入库；其余图片由 OpenAI 图像生成能力基于该原图制作。

## 人物身份合同

所有后续衍生图必须保持以下稳定特征：

- 青年感、中性气质的动漫人物；
- 蓬松白色短发及原图刘海轮廓；
- 鲜红眼睛、苍白肤色、平静克制的神情；
- 黑色高领斗篷与深色服装；
- 胸前红、黑、白三色圆形旋纹徽记；
- 青色幽焰作为唯一固定超自然视觉母题。

人物是项目主理人的视觉化身和全片引路者，不是 CK3 实机角色，也不代表自动玩家已经具备人格或完整自治能力。概念图进入宣传片时必须按
`DIAGRAM` 或 `VISION` 标注，不能冒充 gameplay、acceptance evidence 或 production-live agent footage。

## 资产表

| 文件 | 规格 | 用途 | SHA-256 |
|---|---|---|---|
| [`character/humanized_avatar_source.png`](character/humanized_avatar_source.png) | 原始 PNG | 唯一身份参考源；不得被衍生图反向覆盖 | `31218C41C1756CC4641A70828B2C381E744C988B13FA1F376B73066E6564DF8A` |
| [`character/humanized_avatar_anchor.png`](character/humanized_avatar_anchor.png) | 1024×1536，透明 PNG | 可复用人物立绘；用于合成、转场与片尾 | `BE7B09B11082ED5C937AA69D7AD7E5DB5255210A939996D7C000765C6EB8712D` |
| [`promo/project_causality_key_art.png`](promo/project_causality_key_art.png) | 1672×941 PNG | 片名主视觉、封面候选、片尾回环底图 | `E7C13CBDBB262ECB5C65955F87EF78C21ED18F145741E31493D06C10AA876062` |
| [`promo/chapter_spell.png`](promo/chapter_spell.png) | 1672×941 PNG | “咒”章节卡 | `572242CBCFFE1540C1AAC3ACB67F2D272696A58D29DBD7E278DF42EC7CCEB6E5` |
| [`promo/chapter_method.png`](promo/chapter_method.png) | 1672×941 PNG | “术”章节卡 | `E829D6C80DD8ABE673EFAD1D92CBAACA123DF7EF98EDBF86A1CD57593C390DBF` |
| [`promo/chapter_principle.png`](promo/chapter_principle.png) | 1672×941 PNG | “道”章节卡 | `3F91C832194483DEF2611CC6B756A0606611C29DDFEA0200CA53823B34E79D94` |
| [`promo/chapter_vision.png`](promo/chapter_vision.png) | 1672×941 PNG | “辉煌愿景”章节卡与四 Loop 终幕 | `20651DBF9D9261E9605CAFF0DC3A695CBBC6A9C1A546BD21250EBB486DF421C8` |

## 使用规则

1. 图片中不烧录标题、字幕或状态标签；文字由剪辑工程统一叠加，以便修订与双语适配。
2. 章节图只负责建立情绪和结构隐喻；产品功能、自动玩家能力和测试结论仍必须使用真实素材证明。
3. 人物应出现在片名、四幕章节入口和终幕，但不持续覆盖实机画面，避免遮挡 UI 或把人物误认成产品功能。
4. 二次生成必须继续以 `humanized_avatar_source.png` 为首要身份参考；不得只拿任一衍生图继续漂移。
5. 如需裁切，优先保持脸、胸前徽记和青焰完整；不得镜像徽记、改色或替换其图形。

完整生成输入见 [generation-prompts.md](generation-prompts.md)。
