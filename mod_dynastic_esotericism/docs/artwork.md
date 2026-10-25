# 宗族化密教：原创预览图

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
