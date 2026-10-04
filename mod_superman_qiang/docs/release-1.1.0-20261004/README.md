# 《超人强》1.1.0 正式更新报告

2026-10-04，[Steam Workshop 3812991990](https://steamcommunity.com/sharedfiles/filedetails/?id=3812991990) 已实际更新为1.1.0。新健康随机项、一步经验通知、成年男女封面、新中文介绍和五张媒体均已交付；完整更新说明、订阅下载及公开原图核对通过。Steam已恢复离线，屏幕CAS4242已实际释放。永久changelog与本报告的master交付由随后入库的 `repository-delivery.json` 记录。

当前源标签 `superman-qiang-v1.1.0` 指向 `f7fde816e295a62807ab636ee2d93cf307ea69cf`；上一公开版本 `superman-qiang-v1.0.0` 指向 `7e5ddd481466b7a9df104fd5c6340f473f909aff`。未发布的media-v1/media-v2保持历史，未作为上一版本。22文件正式包逐字节等于标签与R22使用的A0004；发布后文档提交不移动标签、不改变运行字节。

| 验证 | 实际结果与证据 |
| --- | --- |
| 正式构建 | [正式closure](formal-build.snapshot.json)、[逐文件对照](runtime-byte-equivalence.snapshot.json)、[manifest](mod_superman_qiang.manifest.json)：22文件allowlist，tag/source/A0004逐字节一致；内层descriptor无remote ID、没有测试夹具。ZIP806076B/SHA `bd85845dbc7c9ddb19749c14f6a4f20576d488619d7c7e035dab874f68b29cf4`；manifest4077B/SHA `e2a67b0e3ffaa26ec72f2c7cc4310f16946fe7fc9e7c155f05fc8af29678554c`。 |
| L0与CI | 生成一致性、九语格式、静态与负例、确定性构建已验。原标签两次CI因验收文档说明词汇失败；后续仅说明文字修正 `c821c19fd9ffe719b57831586b4c709952fab42f` 的[官方CI37182221607](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37182221607)全部成功，22运行文件不变；[完整修正边界](ci-documentation-correction.md)。不将后续成功改写成原工作流成功。 |
| 增量实机 | [验收汇总](../acceptance-1.1.0-20261004.md)：R19健康20场景、独立40角色保存字段与原生玩家75ticks变化；R20新进程重载；R21正常通知正文、持有人与只读；R22关闭确认后一次菜单点击直接出气泡。游戏实际1.20.0.3/build25652598。没有重跑首发42矩阵或验证全部语言、统计分布与真实寿命。 |
| 原生上传 | 同ID update，Create0/Submit1、EResult1/legal=false。[原生成功回执](native-submit.snapshot.json)完成时间UTC `2026-10-04T06:24:47.284641+00:00`；该字段是回执完成时间，并非单独API调用瞬间。全部实际transport/WAL与原始哈希见[发布closure](publication.snapshot.json)。 |
| 真实订阅 | 实际callback3406/App1158310/item3812991990/result1；下载前旧cache逐文件保全并移至新目录，真实cache不存在。新下载22文件与正式manifest全部匹配，subscribed/installed=true，needs_update/downloading/pending=false，无源码复制；[下载收据](native-download.snapshot.json)、[cache验证](cache-verification.snapshot.json)。 |
| 公开介绍 | 新匿名context/API与实际页面HTTP200，标题/owner/App/public visibility精确，完整BBCode1811字符、57行、SHA `1f0ddc2e92c487893c981657f82734c3e4e373e98eb6e129b6ee0c0853d0313c`；[冻结全文](description.bbcode)等于[公开全文](description.public.bbcode)。仅tag字段两端ASCII空格规范化，原始 `Balance ` 保留。 |
| 完整Change Notes | 新条目 `1791095091`，完整706字符、24行、SHA `958ed4f208adffefdfe985763057169039f65600086c3c7db677907514bffae9`，HTML解码及换行归一化后逐字精确。本次原生提交已实际公开，无owner编辑；[提交全文](steam-change-notes.txt)等于[公开全文](steam-change-notes.public.txt)，[匿名原始回读](public-readback.snapshot.json)。 |
| 公开封面与媒体 | 男女封面640×640、785139B、SHA `e70f54115bef351ee6e363bb116ee81bb25570f683cdc7606cf769b45d2b4f9b`；按序3张规则插画、正常勾引成功事件、普通NPC通知，五张原件均HTTP200、精确字节及解码像素一致。[回读](public-readback.snapshot.json)保留各CDN URL，[root逐图审阅](root-public-cdn-review.snapshot.json)绑定实际下载原件。 |
| 依赖 | [完整匿名sidebar](dependencies.snapshot.json)真实required DLC/items双空，完整DOM/header/section来源已绑定。不把API缺失字段当空数组。公开helper的dependency pending状态保持原样，由独立sidebar证据补足。 |
| GitHub下载 | [正式Release](https://github.com/XenoAmess/ck3_eternal_recurrence/releases/tag/superman-qiang-v1.1.0)已实际创建；ZIP和manifest均重新下载，bytes/SHA与正式原件完全一致，完整说明精确；[交付收据](github-assets.snapshot.json)。 |
| 注册与离线 | canonical用户目录外层 `.mod` 实际指向新正式stage、只外层保留ID。前后原图均直接审阅；先前黑webview与时钟落后记录保留，最终实际窗口变化、新像素、离线底栏和native/UI过程由[closure](publication.snapshot.json)及[root审阅](root-offline-image-review.snapshot.json)绑定。CAS4242 done/resources[]、keeper退出且failure=null；[释放收据](screen-release.snapshot.json)。 |

[发布冻结](publication-freeze.snapshot.json)、[永久发布索引](publication-artifact-index.json)和[完整外置过程索引](publication-raw-index.snapshot.json)保留全部原件的路径、bytes与SHA。选择最终 `closure-a02.json` 和 `raw-asset-index-a02.json`；原closure/index、失败预备尝试、旧cache、旧发布候选及所有素材保留，不覆盖。GitHub、正式构建及先前实机另由各自索引绑定。本目录准备阶段的索引与各验收报告包含当时pending状态，本报告补足实际发布事实。

健康每次原始修正转移0.00075，来源当前有效健康须至少3.00075，合格七类等权随机。该值略低于原版25岁起始衰老参数折算的一月期望健康损失；健康与寿命无固定换算，不能保证实际寿命最多或恰好变化一月。1.0.0存档可继续使用，原经验与六能力账本保留，缺失健康账本按0读取。未验证多人、成就、全部DLC组合或其他游戏版本，覆盖相同结算effect的模组需要合并。

[永久1.1.0 changelog](../../../docs/release-changelogs/superman-qiang/1.1.0.md)与Steam Change Notes分别交付。[首发报告](../release-1.0.0-20261004/README.md)及旧错误/夹具/日志事实保持历史。
