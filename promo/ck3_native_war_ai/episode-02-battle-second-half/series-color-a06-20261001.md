# 第二期 a06：棕金配色与证据呈现修订

这是新 run 的成片与实测回执记录。旧 a04/a05、失败 attempt、原始录像和过程素材保持原样。独立分支 `codex/war-series-brown-gold-20261001`，固定底座 `d81b91be1ae6bf818f38c3c5af0d595dd4ea4752`；没有拉取、合入或接收新的 master 内容。

## 实物

| 项目 | 实际值 |
| --- | --- |
| 文件 | `CK3-War-AI-Episode02-BrownGold-Evidence-20261001-a06.mp4` |
| 新 run | `C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-evidence-20261001-a01/` |
| 字节数 | 239659692 |
| SHA-256 | `F716D9F4FA79F3471941FF7FC4860A2D8F3D8EA103B73502D5C724609DB598D2` |
| 时长 | 1818.633333 秒，30:18.633 |
| 内容 | 六章、167 句、13 原速实录、24 编码块 |

包装沿用前两期的棕金色：背景 `#211813`、面板 `#35291F`、正文 `#F0E5CF`、次要字 `#BBA98D`、金色 `#CBA56A`、分隔线 `#61503C`。原始游戏 UI 不做调色。来源与 a05 配色中间版见 [前两期配色及 a05 记录](series-color-a05-20261001.md)。

## 已修正

- `reinforcement-r038` 主图标签改为实际 12 月 15 日、827/4106；前日小图 893/1603 保持。
- `pursuit-p028` 四个字体缺字箭头改成“对应”。
- `knights-k035` 在同一 raw 前 2.5 秒加入动态通告放大，履行旁白的画面承诺。放大取同源同帧，原图日期、人数及骑士名单保留。2.5 秒是包装窗口，不能用来推断通告寿命，更不能证明次日生命状态。
- 七处事实引用仅修路径及原始字段定位，精确修订 catalog 单独冻结为 `claim-catalog.json`；旧 timeline 只作原音轨与字幕时码输入。明细见 [locator-corrections.json](evidence-a04-audit-20261001/locator-corrections.json)。

三块重编，另外 21 块逐字节复用 a05。机器审计确认 24 份字幕完全一致；85284 个 AAC packet 的内容及时间戳与原 a04 相同；两张卡只改文字区域，原 UI 像素保持。k035 放大区域有实际成片帧与同帧原图比对。全片音视频解码退出码 0，共 54559 帧。

独立报告：[媒体检查](C:/Users/1/ck3-a06-evidence-media-audit-20261001/attempt-01/report.json)、[有限画面审阅](C:/Users/1/ck3-a06-evidence-media-audit-20261001/attempt-01/quality-report.json)、[代码审阅](C:/Users/1/ck3-a06-evidence-media-audit-20261001/attempt-01/code-review.json)。状态为 `PASS_PENDING_HUMAN_REVIEW`，不等于真人完整 1× 观看、听审、clean-span 认证或 signoff。

## 单视频客户端同步

2026-10-01 **03:37:37（Asia/Shanghai）**，仅该 MP4 放入既有授权目录 [OneDrive 成片](C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-War-AI-Episode02-BrownGold-Evidence-20261001-a06.mp4)。复制流与目标 SHA 相同，客户端 InSync=1，validated=239659692、modified=0，九项元数据核对全部成立。

精确状态是 `CLIENT_METADATA_IN_SYNC_REMOTE_UNVERIFIED`；没有独立远端回读。没有下载其他云端文件、调整同步设置，未把源码或素材目录放入 OneDrive。实际回执：[final-delivery.json](C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-evidence-20261001-a01/delivery/final-delivery.json)。a05 中间版没有传输。

媒体报告、有限帧审阅和实际同步证据已追加进本 run 的 native manifest，不修改旧记录。文件绑定复验通过，人工 signoffs=0。[finish-receipt.json](C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-evidence-20261001-a01/finish-receipt.json) 的 SHA-256 为 `64BEB460CB28C0E88CEE04404D7A71C101AC42CE3BE62C3C140FF505F1797F3D`。

## 机制证据边界

本次制作修订没有生成新的游戏证据。当前 a02 骑士 33437 次日状态、增援同帧战宽 tooltip 与原生帧绑定仍待实采。桌面恢复失败原件及优先配方见 [逐句机制审计](../../../docs/ck3-native-ai/a04-mechanism-evidence-audit-2026-10-01.md)。不能把修图、路径修复或客户端同步算作这两项取证闭合。
