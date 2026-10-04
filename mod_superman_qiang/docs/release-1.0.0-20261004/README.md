# 《超人强》1.0.0 首发发布报告

2026-10-04，首次发布（initial baseline），没有上一公开版本。[Steam Workshop 3812991990](https://steamcommunity.com/sharedfiles/filedetails/?id=3812991990) 的真实上传、订阅下载、公开内容和完整更新说明均已验；[GitHub Release](https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/superman-qiang-v1.0.0) 两个附件已实际下载并逐字节核对。Steam 已恢复离线，屏幕 CAS 4130→4131 释放。仓库交付以随后的 `repository-delivery.json` 实际 master commit/push 为准。

源 tag `superman-qiang-v1.0.0`，commit `7e5ddd481466b7a9df104fd5c6340f473f909aff`。22 运行文件与 A0004 source `2873141e76177f52e218aa7da05e75cbdd312fc1` 的受验收字节完全相同；后续证据提交不移动 tag、不改变运行包。

| 验证 | 实际结果与证据 |
| --- | --- |
| L0 | 正式双构建及 verify GREEN；[初始正式包](formal-build.snapshot.json)、[ID绑定包](idbound-build.snapshot.json)。[exact-source 官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37162929721) SUCCESS，原始响应见 [CI快照](official-ci.snapshot.json)。 |
| L1–L3 | [实机汇总](../acceptance-1.0.0-20261004.md)：26 计划ID、9真实gate、42核心矩阵及补充保存/边界，中文正常UI、旧档、百万经验、安全上限和真重载。该汇总冻结于正式构建之前，内含当时PENDING历史状态；本报告补足实际正式与发布事实。 |
| 原生上传 | 新ID3812991990；Create/Submit result1、legal=false；同ID追加一张实机媒体。成功回执与所有原始SHA见 [发布快照](publication.snapshot.json)。 |
| 订阅下载 | callback1313 与3406精确ID/App1158310/result1；下载前cache确实不存在；实际 `C:/SteamLibrary/steamapps/workshop/content/1158310/3812991990` 完整22文件、917102 bytes，manifest逐文件一致，无源码复制。 |
| 公开页面 | owner76561198273714027、App1158310、public visibility0、标题与描述精确；tag原文 `Gameplay / Balance<U+0020> / Events`，仅字段两端ASCII空格规范化后比较，原始RED保留。 |
| 依赖 | [完整匿名sidebar证据](dependencies.snapshot.json) 实际 required DLC/items 两数组为空；不从API字段缺失推断。 |
| 封面/媒体 | 匿名CDN200；封面640×640、778046B、SHA732deee357a6d322340fa9e6bb6d7b619b8c9da44b3c68711c23154079df863f；media strip1/index0、1024×768、170086B、SHAd0d0adbaf28445d0aa1ced1de5351374337c6921a67919a9743bbf2dbb2eaa8d。字节和解码像素完全一致，root直接审图通过。 |
| 完整Change Notes | 同entry `1791072096` 先A974字/26行/ae97…，后B1011字/29行/7a7713bad58d200264ed5227e1b755e24abb2287ac6d3ee02ef30b4903f3c9b0。原生B submit成功但公开仍A，保持Steam离线，通过既有owner页ValuePattern全文读回、保存，再新匿名context确认该条正文真正替换；[全文B](steam-change-notes-B.txt)和[匿名回读](public-readback.snapshot.json)。 |
| GitHub附件 | ZIP802525B/SHA551901e384931fb5d465f0eaca3327ef357d004d4e290b7bc205c24cc40c3564；IDbound manifest4075B/SHAb85bcac67af7998453c93346201cc8b738df055aba223316bff394cc42a0685f；[实际下载核对](github-assets.snapshot.json)。 |
| 注册和收尾 | canonical外层 `C:/Users/1/Documents/Paradox Interactive/Crusader Kings III/mod/superman_qiang.mod` 指向IDbound正式staging、仅外层保留remote_file_id；两内层无ID、native无注入。实际离线新图已审；[CAS释放](screen-release.snapshot.json)。 |

[机器证据索引](artifact-index.json) 保留原始C盘文件bytes/SHA，JSON快照统一LF但原件不改写。[发布原始492文件索引](publication-raw-index.snapshot.json) 与 [实机1605资产索引](../acceptance-1.0.0-20261004.raw-index.json) 一并保全。匿名helper仅验证metadata/notes/cover/media，其依赖字段仍not_observed、整体ok=false；独立完整DOM依赖证据补足这一项，没有覆盖原回执。

[永久首发changelog](../../../docs/release-changelogs/superman-qiang/1.0.0.md) 与 Steam Change Notes 为独立交付物。本版本仅 CK3 1.20.0.3 中文实机通过；其他语言仅格式认证，未验多人、移除、成就、全部DLC或其他版本。R0006/R0007 RED、R14流程偏差与未知formatter来源等保留在各实机报告。

2026-10-04 仓库交付完成：永久发布报告和首发changelog已随 `0b59784726f696f736e4638f750cbe9fc0eafb86` 实际普通推送至master，随后远端ref和提交树独立读取确认；正式tag仍为原source，当前22运行文件仍与发布manifest一致。[实际仓库交付回执](repository-delivery.json)。
