# 《CK3：信仰与权力》第一期 V7 本地审阅交付

`machine_id: 4-8e1c2f1861`；原生产进程于`2026-10-19T13:44:11.792039+00:00`实际wait0，`2026-10-19T13:44:22.262495+00:00`封存本地交付。技术与所列画面抽查通过；完整人工1倍速听看片和签收未完成。当前研究及演示版本为**CK3 1.20.0.4**。

## 可直接打开的文件

| 文件 | 本机交付 |
| --- | --- |
| 视频 | [episode01-review.mp4](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/episode01-review.mp4) |
| 中文字幕 | [episode01.zh.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01.zh.srt) |
| 英文字幕 | [episode01.en.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01.en.srt) |
| 双语字幕 | [episode01.bilingual.srt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01.bilingual.srt) |
| 中英讲稿 | [episode01-script.md](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01-script.md) |
| 17章时间点 | [episode01.chapters.txt](C:/workspace/ck3-faith-and-power-20261017/episode01/production-candidate/value-v7-production-a01/full-final-a04/native-run/derived/direct/text/episode01.chapters.txt) |
| 本地交付索引 | [LOCAL-DELIVERY-a04.json](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v7-20261019/LOCAL-DELIVERY-a04.json) |

视频149,978,004B，生产者SHA-256 `befe1a2293741c76dd5fcbbf64cd58a5889c9da4f63c88a5007551fdc89cabad`。2560×1440／30fps，48kHz双声道；136段旁白、467组中英字幕、17章、79,024帧，帧跨度**43:54.133**。实际容器2634.154687秒，首视频PTS 0.021354秒；字幕及章节沿最终实际PTS生成。只继承生产者视频SHA并核当前大小，没有另存媒体副本。

## 本轮修改

原钩子之后新增完整口播免责声明，明确只解释游戏机制，不对现实宗教、历史、文化、政治表达评价和立场，请勿将游戏取舍套用现实；同段明确研究版本。具体全文见[修订说明](../../promo/ck3_faith_and_power/docs/episode01-revision-v7.md)与[冻结稿](../../promo/ck3_faith_and_power/docs/episode01-narration-v7.zh.md)。

连续审读实际V6的135段中英文本及画面标题、图注、标签，按1.20.0.4官方中文区分**信仰领袖**（整个信仰）与**礼仪领袖**（一支礼仪）。坎特伯雷例子的人物确实兼任两职，分别说明采用圣地与修改礼仪使用的身份；天主教页“你的总主教”不再代称已核实的礼仪领袖或宫廷司祭。完整来源与逐段判断在[永久审校记录](../../promo/ck3_faith_and_power/docs/evidence/episode01-v7-textual-audit-20261019.json)。官方名称、复杂条件的前提、费用比较、指代和转场已随新旁白同步修订。

13段新声音（12段修改、1段新免责声明）与123段精确旧音频组成新声钟；最后一轮只重制XB01／XB04两处画面，其余134个完整片段精确复用。没有重拍或启动游戏。战争系列原配乐仍经既有路径混入，旁白0dB／配乐−17dB，循环、淡入2秒／淡出8秒，不另做normalize或duck。

## 实际检查与边界

正式链严格整片AV解码、格式、全部79,024帧PTS／CFR、逐段映射、字幕、章节、音频信号与配乐存在性检查通过。首版V7抽查16张画面发现两处布局问题；最终两段使用同场真实界面并列说明身份与采用条件，另抽查新画面确认修复。其余正面样帧仅在完整片段内容精确不变的范围继承，旧首版两问题回执保留；抽帧不取得全片人工听看信用。

两次失败分别保留：a02官方版本查询真实403／原wait1，只有容量元数据；a03目标框奇数高度导致FFmpeg pad失败／原wait1，部分媒体按实际容量闭场。后继a04改正该高度并使用新输出和新准入。限流备用分支只有8项测试、15个子例的模拟证据，实际a03版本查询走匿名200，不能写成真实gh回退成功。最终媒体状态由本次原wait0和输出检查决定。

源码修复的定向测试与仓库全CI分别记录。[CI实际观察](evidence/faith-power-v7-ci-observation-20261019.json)保留父提交00a9的三个相机夹具失败、新3ac官方CI当时仍运行及两个Linear成功；本次未修改相机生产代码或其夹具。媒体通过不等于仓库全CI GREEN。

[永久交付小索引](evidence/faith-power-v7-local-delivery-20261019.json)绑定原wait、成片完成记录、最终输入、像素检查和容量闭场。项目保守上界47,862,210,085B，低于配额51,177,672,294B；本轮future／writers均0，未删除文件，未把取消预留计作物理回收。本审阅版及必要来源于10月26日前复核；可重建过程件按通用策略48小时复核，不重置历史期限。

这是已生成的本地审阅版，尚未上传、完整人工听看片或签收。既有原生能力缺口保留[V6交付](faith-and-power-episode01-value-v6-delivery.md)所述范围，不因这次剪辑扩授业务资格。
