# 战争四期 Review02：三段局部预览实物

`machine_id: desktop-3fevhd2-1c74096080`；实际制作与自动检查观察时间：2026-10-18 03:15–03:21 UTC；主仓制作源 `7a342116d8aaa8a4c645941199c3ef1abd0a7c8f`。精确本机路径、大小和 SHA-256 见[小证据索引](evidence/episode04-review02-three-cue-preview-12004/source-index.json)。这些路径是来源机器的实际回执，跨机器不得当作现存路径或实机资格。

已生成 **Review02 的三段局部粗剪**：C01-01、C02-09、C03-08，共 2512 帧、30 fps、83.733333 秒、1920×1080，H.264/AAC MP4 9,576,602 B／SHA-256 `5d5f04f89afe1619d90fbcc8ad0cc950fde44aee8a4d03129816f2dca7c4d811`。只有 3/69 段进入此片；片头常驻 `PARTIAL PREVIEW / NO SIGNOFF / REVIEW / CLEAN PENDING / EVENT FRAME UNVERIFIED`。它不是完整 Review02，也没有 1× 连续人工审片、最终签核、正式动态镜头资格或外部发布。正式动态仍 **0/11**；研究、业务和 A/B/C 计数均不因本片增加。

| 预览顺序 | 用途与原片 | 精确源帧 | 成片帧数 | 资格边界 |
| --- | --- | ---: | ---: | --- |
| C01-01／E4-01 | R204 墨西拿地图战斗，替代 **Review02** 的 D13 静态说明卡作通用战场背景 | `[15,600)`；0.5–20.0 秒，585 帧 | 612 | 源尾帧明确 `tpad` 保持 27 帧／0.9 秒以匹配配音。保持段不是事件发生的 0.9 秒；不能借画面声称低库存、实际补员、付款、清晰行军或 R05/R06/ABC 结果。 |
| C02-09／E4-02 | R198 军事页面月补员开关的粗剪上下文 | `[780,1675)`；26.0–55.833 秒 | 895 | 不能据此推出 AI 补员结果或原生 callback 精确 PTS。 |
| C03-08／E4-03 | R199 路线后的军队地图粗剪上下文 | `[1200,2205)`；40.0–73.5 秒 | 1005 | 不把路线 ACK 推成已到站或实际 ADD。 |

上述 612＋895＋1005＝2512 帧。R204 原片是另有正常 Finish 的 23.266 秒／698 帧实机录制；早先媒体完整解码和 PTS 检查通过。Root 直接看过源帧 232／7.733 秒及 465／15.5 秒：两帧均为 CK3 客户区墨西拿战斗面板 1173 对 3717，画面相近，未见 tooltip、桌面或旧蓝面板遮挡。这只是**两张** AI 抽样；成片另抽 10、20.1、20.5、50.5 秒四张帧，确认局部剪辑画面和切点附近用途，不能代替全长 clean 或人工 1×。Review01 的 C01-01 原本已有两个封存实机视频窗口，本次没有替换 Review01。

制作从仓库[69 段双语 ProjectConfig 原件](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/production-inputs-a03/bundle-index.json)的 `project/promo-project.json` 物化，86060 B／SHA-256 `6cdc1e349826d607a9c2fe1fa17e3b50d770a3a246bd207ea323002487d48140`；run manifest 精确绑定同字节快照。三 cue 的逐段素材选择是独立运行输入，不改原 69 段配音或双语台词。[可复用选择与 composer 候选](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/three-cue-preview-a01/README.md)保留**实际构建原补丁**和**构建后同 raw 多窗口兼容修正补丁**两个身份；新补丁经只读 planner 分支对照，尚未重渲染，旧 MP4 的生产来源仍为原补丁。每台机器仍需提供并核验自己的素材根、现装工具链和容量准入。

这次先从官方 GitHub `releases/latest` 新查正式 `v0.3.0`，wheel SHA-256 `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`，与本机已装 direct URL、仓库 requirements 精确匹配。原生 `xar-promo` 完成新 run、24 个源 artifact 保全及逐个验证、只读 plan、build 退出 0、run/config 后验完整验证；RunManifest 23185 B／SHA-256 `e3695bb38f044486522cc190c173a4bdf21303d0d15fdc4b10e007c1c8fffd1c`。本片未执行原生 `audit`、`review`、`signoff` 或 `export`，不得把外置机器 QA 叫作原生审核或人工批准。

独立机器 QA 对最终 MP4 做了字节绑定 FFprobe、全部 2512 帧 PTS 30 fps 栅格检查、完整音视频严格解码（退出 0，stdout/stderr 空）；容器时长 83.754687 秒含约 21 毫秒 AAC 尾差，视频流正好 83.733333 秒。四帧有限视觉回执单独保存。最终[自动媒体检查](evidence/episode04-review02-three-cue-preview-12004/source-index.json)为 `GREEN_AUTOMATED_MEDIA_ONLY_PENDING_HUMAN_REVIEW`；下一门是完整逐帧/1×人工音画审阅、必要修剪及正式 69 段镜头资格，不因这次 partial 可播而自动授予。

本机实际 D 媒体根闭场占用 359,300,786 B（512 MiB 准入内），未来此目的新增媒体写入 0。保留 MP4、run manifest、自动 QA 和被引用源到完整 Review02 编辑审查或 2026-11-17 UTC，以先到者复核；按[通用存储策略](../storage-retention-policy.md)决定续留或回收，不能无限期默认保存。
