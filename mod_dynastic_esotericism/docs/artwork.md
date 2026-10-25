# 宗族化密教：原创预览图

## 2026-10-26 原版轮廓风格修订（待实机）

用户在实际创建礼仪页面否决了下节的金红圆形树徽：其颜色、复杂度与原版主要教义图标不协调。金红图是已否决的历史输入，不能标为当前获认可的画面。

新候选使用同一内置 imagegen 技能，参考当前安装原版的三张教义透明轮廓以及用户截图，生成简单的家谱树／三个人物轮廓。源图：[des_dynastic_membership_native_mask_20261026.png](../tools/artwork/source/des_dynastic_membership_native_mask_20261026.png)，1254×1254 RGBA，184,659 B，SHA `751318bc6f91b32a7e257ee457d3166f38a9d12d401caccfcad32908681ed827`。模式为 built-in image_gen，`transparent_background=true`，没有 CLI/API fallback。

原版 `window_faith.gui` 的 `icon_doctrine` 经 `shared/icons.gui` 使用 `Icon_Flat_Standard`，添加 `colors_textured.dds` 第7帧的颜色，保留输入 alpha。因此运行素材必须是黑色 RGB 的透明轮廓，由游戏提供颜色；不应把金色、阴影或装饰圆盘直接画入纹理。原版 shader 的 add 运算与 alpha 保留见外置 `operator-reference/none-visible-r18-fix-a01/ICON-PIPELINE.md`。

[Java 导出配方](../tools/artwork/ExportDoctrineIcon.java) 将完整原图的 alpha 双三次缩放到120×120，并编码为 RGB 全0的 BGRA8 DDS。没有裁切、阈值化、描边、重绘或预览合成。两份运行纹理同为57,728 B，SHA `21444eed8611e441d70e77bfb94ac9219750b83a9b8574534ad07324a434be8a`。首次外置导出的默认 javac／java 原进程均退出0，实际14,400像素回读一致；详见 `operator-reference/icon-style-r18-a02/native-mask-export-a01/EXPORT.actual.json`。源码及正式包共用的校验只约束这两张教义纹理的原版格式，不改变用户的彩色信仰／纹章素材。

`machine_id: desktop-3fevhd2-1c74096080`；外置导出观察时间 `2026-10-25T19:33:37.770362700Z`，闭场后集成时间 `2026-10-25T19:43:45.417853Z`。新候选尚未经过游戏小尺寸视觉验收，不将生成／编码或测试通过称为用户认可。当前原图是可重建输入，2026-11-02复核用途；旧图、重复生成原件的保留沿用统一存储策略，复制不重置期限。

完整生成提示词及参考图角色记录：[native-mask-generation.json](evidence/native-mask-generation-2026-10-26.json)。

## 2026-10-26 金红专用图标（已被用户否决）

用户要求检查图标是否专用并生成新图。此前 `des_doctrine_dynastic.icon` 实际引用原版 `doctrine_pluralism_fundamentalist`，即选项仍使用原版原教旨主义图标；旧组图的简易树形 DDS 不等于选项已经使用专用图。

本次使用内置 `image_gen.imagegen` 全新生成金红家谱树徽记，真实透明背景，不使用原版图标或参考图。应用技能为 `C:/Users/1/.codex/skills/.system/imagegen/SKILL.md`，未使用 CLI/API fallback。原始 PNG 已复制进源码：[生成原图](../tools/artwork/source/des_dynastic_membership_generated_20261026.png)。两份运行 DDS 使用同一幅专为本模组生成的画面。

`machine_id: desktop-3fevhd2-1c74096080`；Java 格式导出实际结束于 `2026-10-25T18:19:48.151176Z`（北京时间 10 月 26 日）。默认 `javac -Xlint:all -Werror` 和默认 `java` 均退出 0。原始 PNG 为 1,949,246 B，SHA `f0f232960371884df1c8d6df1d63ea72ef31a40800f7e5699fc9dc9875599490`。原图位于 CODEX_HOME generated_images，源内副本逐字节一致。

当时 Java 只做双三次缩放到 120×120 并编码为带原 alpha 的 32 位 BGRA DDS；不裁切、不重绘、不增删画面元素。彩色导出配方保存在原提交 `6d38eadf8a4a48688835cbb41035d877bb3f4540`；当前配方已按上节改为原版alpha素材格式。历史导出逐像素解码回读一致；两份 DDS 各 57,728 B，SHA 均为 `7642ef5c0b837d2a21ee3a1363f86337274c2af1c89b9ec2da8a4d212d2e3071`。原图与实际 DDS 解码的 120 像素预览均已查看。

- 组图：[faith_doctrine_groups/des_dynastic_membership.dds](../gfx/interface/icons/faith_doctrine_groups/des_dynastic_membership.dds)，对应原版 `DOCTRINE_GROUP_TYPE_ICON_PATH`。
- 选项图：[faith_doctrines/des_dynastic_membership.dds](../gfx/interface/icons/faith_doctrines/des_dynastic_membership.dds)，对应 `DOCTRINE_TYPE_ICON_PATH`，由 `icon="des_dynastic_membership"` 引用。
- 两个路径都保留在正式显式清单，当时正式文件数为52；此前a03实际51文件构建记录不改写。仅GUI修订时正式清单为53文件；最终连同帝国领袖与纹章后的正式清单为56文件。

实际回执为 `C:/ck3-dynastic-esotericism-20261024/resume-product-a20/operator-reference/EXCLUSIVE-ICON-EXPORT-a01.actual.json`。施工使用 r1228/storage116 的 C512MiB/D1MiB 池；复制前 fresh 检查通过。较早 r1225 的复制准入因闲置 Core 预留及当时实际空间不足被拒绝，未执行复制；随后实际关闭未消费预留，不声称因此回收物理磁盘。图标生成、导出和打包检查不替代游戏实际显示及 Workshop 更新。

完整生成提示词（`transparent_background=true`，无参考图）：

```text
Use case: logo-brand. Asset type: original raster emblem for a 120 by 120 pixel doctrine-group icon in a medieval strategy game mod named Dynastic Esotericism. Create one distinctive original emblem of a sacred ancestral tree: one broad golden trunk unites three pairs of simple leaf-shaped heraldic medallions through clean branching lines; its roots join into a small interlaced knot. A single subtle circular ritual arc integrates with the tree, conveying a religious fellowship united as a dynasty. Restrained antique gold with small deep crimson enamel accents, slightly engraved and hand-painted medieval game-interface finish. Strong clean silhouette and broad shapes that remain readable when reduced to 48 pixels; balanced centered composition occupying about 80 percent of a square canvas. Genuine transparent background outside the emblem, preserve clean alpha edges. No text, no letters, no numbers, no watermark, no logos, no crown, no shield frame, no portrait, no game screenshot, no copied existing religious symbol or existing game icon. No background panel, no elaborate filigree, no glow cloud, no cast shadow outside the shape. Deliver a single finished emblem, not a mockup, sheet or alternatives.
```

新原图在源码内为当前重建输入，2026-11-02 复核使用情况。默认 CODEX_HOME 原件的实际文件时间为 `2026-10-25T18:10:24.436736Z`；其重复副本按同一起点及通用 raw_evidence 720 小时于 `2026-11-24T18:10:24.436736Z` 进入到期复核，复制不重置时钟，不自动删除仍被引用的输入。当前 DDS 是正式消费源资产，2026-11-02 复核是否仍在使用；后续替代及实际回收遵循仓库统一存储策略。

## 2026-10-25 用户提供的两教派图标

本次新增图标直接来自用户上传的 `信仰礼仪图标.zip`，不是重新生成的图片。ZIP SHA-256 为 `46e977c19a555ce9cbaa9eb3ee4981e7e63eab3dfbbb7eb126d1e7b43e6a9586`。

| 来源及用途 | 格式与处理 | SHA-256 |
| --- | --- | --- |
| 繁育教派.dds → `gfx/interface/icons/faith/des_procreation.dds` | 原始 256×256 RGBA DDS，逐字节保留 | `9314f9743394dd4622bb09c44e6161be00e68e712b32b2611ebc14d479436f72` |
| 白绮教派.png → `tools/artwork/source/des_vivhite.png` | 原始 1254×1254 RGBA PNG，作为源码资产保存，不进入正式包 | `8777b819cf085bc5a7935aa2c6bd1dcf01c487500a8874b84bf184d48209bcf5` |
| 白绮教派运行图标 → `gfx/interface/icons/faith/des_vivhite.dds` | Java 双三次缩放到 256×256，保留透明度，编码为 RGBA DDS；无裁切、重绘或内容增删 | `93e2354c6677368b8c76d9cba5fc783a8003599659ad8d99101a809d3a7c2371` |

实际导入由 Maven／Quarkus 工具模块的 `SectArtworkImporter` 执行；在首次构建前也支持同一 Java 源文件模式。构建后命令为 `java -jar <admitted-runner> artwork <uploaded-zip> <mod-source>`。两幅最终 DDS 均实际解码并查看，白绮源 PNG 也已查看。纹章使用同一图标的独立运行纹理副本，不能修改或覆盖用户原图。

`machine_id: desktop-3fevhd2-1c74096080`；实际导入观察时间 `2026-10-25T15:22:56.616725Z`，Java 原进程退出 0，耗时 2.881 秒。原命令、输出 pins 及当次容量观察在 `C:/ck3-dynastic-esotericism-20261024/resume-product-a20/artwork-import.actual.json`。本次施工准入为 r1217／storage105，仅限 C512MiB／D1MiB，不授予游戏或 Steam 下载资格。原文件保留和候选输出继续执行统一存储策略；上传源 ZIP 不是本任务清理对象。

本文件记录当前产品预览图的生成、消费格式导出与目视检查，不代表模组功能验收或 Workshop 发布已经完成。

## 来源与使用范围

- 模式：内置 `image_gen.imagegen`，单次全新生成；未使用 CLI/API fallback、外部参考图、游戏截图、原版图标或商标。
- 应用技能：`C:/Users/1/.codex/skills/.system/imagegen/SKILL.md`。
- 画面：深红黑金的宗教纹章和家谱树，象征礼仪共同体形成宗族；不表示额外玩法。
- 画内文字：`宗族化密教`、`DYNASTIC ESOTERICISM`。生成原图及最终 512×512 PNG 均已直接查看，五个中文字与英文拼写准确。
- 全图为本任务原创生成；未复用 CK3、Paradox 或其他产品素材。不据此宣称对其他素材拥有授权。

## 本机实测与文件身份

- `machine_id: desktop-3fevhd2-1c74096080`。
- 机器身份出处：本次执行 `py tools/ck3_live_run_id.py machine`，返回上述 ID。
- 导出观察时间：`2026-10-24T07:16:49.314882200Z`。
- 容量准入来源：`C:/ck3-dynastic-esotericism-20261024/capacity/CAPACITY-ADMISSION-r1145.actual.json`，本任务 C 卷 3 GiB、D 卷 5 MiB 预算；该回执不授予启动游戏资格。
- 导出实际回执：`C:/ck3-dynastic-esotericism-20261024/assets/artwork-export.actual.json`。

| 用途 | 精确路径 | 尺寸 | 字节数 | SHA-256 |
| --- | --- | --- | --- | --- |
| 内置工具原始输出 | `C:/Users/1/.codex/generated_images/01a16cc2-e753-7d40-b637-d82193ed77f7/exec-58913309-e66d-435c-9168-79b1558f0084.png` | 1254×1254 | 2,664,181 | `832adebd7255d6207f023868c73d3c415a7ffe73e7b7f3e50187d73336d2f581` |
| 外置任务原图副本 | `C:/ck3-dynastic-esotericism-20261024/assets/dynastic-esotericism-original.png` | 1254×1254 | 2,664,181 | `832adebd7255d6207f023868c73d3c415a7ffe73e7b7f3e50187d73336d2f581` |
| 正式消费预览图 | [`../thumbnail.png`](../thumbnail.png) | 512×512 | 545,337 | `3a81e6c88de042dc91ca88a0388b7a811be7030cbb3308a3e4a4e1813a40c17f` |

原图超过 1 MiB，故以同一画面做消费格式导出，没有再次生成。使用默认命令行 Java 的 `ImageIO`，双三次插值等比例缩至 512×512，编码为 RGB PNG；无裁切、文字叠加或内容增删。实际运行环境为 OpenJDK/GraalVM CE `25.0.4.1`，本机观察时间同上，来源为 `java --version`。导出程序位于 `C:/ck3-dynastic-esotericism-20261024/assets/ExportPreview.java`，使用 Java 源文件执行模式，未新增生产模块。程序读回验证最终 PNG 尺寸、`<1,048,576` 字节约束，并比较两份原图的 SHA-256。

## 完整提示词

```text
Use case: ads-marketing
Asset type: original square Steam Workshop preview illustration for the medieval strategy mod Dynastic Esotericism.
Primary request: a solemn, refined emblem that conveys a religious Rite becoming a single Dynasty. The central image is a clearly readable golden genealogical tree whose branching lines connect a small number of heraldic medallions, united within one original sacred circular crest. It should evoke a medieval religious fellowship and shared dynasty without implying any extra gameplay.
Scene/backdrop: plain near-black and deep crimson background, restrained symmetrical medieval manuscript border.
Style/medium: polished original medieval heraldic illustration, crisp clean silhouettes, restrained engraved gold detailing, extremely low visual noise.
Composition/framing: square image; central large gold tree-and-crest emblem occupies the middle; spacious distinct text areas above and below; strong shapes and large text remain clear as a small thumbnail.
Lighting/mood: dignified, solemn, gold softly illuminated against dark red.
Color palette: black, deep crimson, warm antique gold.
Text (verbatim): "宗族化密教" as the large, prominent Chinese title, with the five Chinese characters exactly correct; "DYNASTIC ESOTERICISM" as a smaller clean English subtitle. Both text lines must be clearly legible and spelled exactly.
Constraints: one complete square cover; original artwork only; no CK3 or Paradox logos, no game screenshots, no copied game icons, no watermark, no additional text; no portraits, no weapons, no combat, no crowns implying monarchy mechanics, no extra gameplay symbols. Do not use photographic grain, speckles, complex backgrounds, or tiny unreadable details.
```

工具参数为 `transparent_background=false`，未传参考图或历史图片。

## 存储复核

采用仓库统一 [存储策略](../../docs/storage-retention-policy.md) 与 [版本化参数](../../docs/storage-retention-policy.json) `1.0.0`。本机 ID、原件与副本身份见上表，复制不重置到期时钟。

- 两份大原图不放入 D 卷仓库。内置默认原件留在 CODEX_HOME，任务原图保存在 C 卷；两者均为 `raw_evidence`，按 720 小时判定于 `2026-11-23T07:16:49Z` 到期候选。`2026-10-25T07:30:00Z` 任务闭场复核重复副本及后续引用，不默认永久保存。
- `thumbnail.png` 是当前产品正式引用的源资产；继续保留原因是正式构建和后续发行使用，复核时间 `2026-10-31T07:16:49Z`。发布或替代后按当前引用与统一策略重新判定，不自动删除仍在用资产，不自动续期保护。
- 导出程序、实际回执与本说明属于小型重建配方和身份记录；按任务闭场统一清点，并在 `2026-11-23T07:16:49Z` 复核外置副本是否仍有用途。本次未执行删除。
