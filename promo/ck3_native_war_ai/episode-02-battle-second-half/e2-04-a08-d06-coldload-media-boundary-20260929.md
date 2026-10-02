# E2-04 a08：独立 d06 冷载镜头与媒体门

2026-09-29。第二会话从第一会话保存的 d06 不变源档独立冷载。两次会话不是一条连续原始录像；第一会话 600 秒 raw 只含 d05 前态，唯一 d05→d06 推进发生在 FFmpeg 录制停止后，该 raw 没拍到推进。不得把两段画面剪成未经标注的同一次连续推进。

外置完整回执为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-v3-media-audit-20260929-a01/facts-a01.md`，SHA-256 `35091B80A2D52742AA2EBA0F64494C78E19A6A8BEB9B4EA5F366D5EEF9DF090D`；机器 PTS JSON 与原始抽帧在同一外置目录。第二会话源码 HEAD 为 `e4957f17eb2c36aaf8e9e4c4afeaaf16d100b44a`，源档 SHA-256 `F05A48A0839E76DD05D053FACBA524405FD547DD0A6CA07396ADB8ABE42A0B5A`，原生保存 sidecar SHA-256 `85C226E247AF4D32E246DCCF9F4C7323106D3A6BD0F12FCB883ABE843D3B785B`。

受管冷载后，同帧 snapshot/control 证明暂停的 d06、actor 29829、War 4、Combat 16777218、Army 18、province 2633，wrapper revision 4、native revision 3、snapshot ID `native:3`。V3 查询使用的入场省份仅是 Army 路径候选，实际战斗引擎入场值未读到；请求超时后保全 RED，没有重发。第二次只读 snapshot 仍证明相同暂停身份。此会话没有推进日期。

| 独立原片 | 自动 PTS 结果 | 画面与使用边界 |
| --- | --- | --- |
| d06 战斗面板 240 秒，SHA-256 `44EC9EE794658C13B6CBAE5B13D9A0105CC0C4DB04F7918D51FEDB4DA43C15D9` | 4,805 帧；0.000→8.133 秒有 **8.133 秒缺帧**，故整片 `RED_PRESERVED`。8.133–239.967 秒仅是机器连续候选。 | 同 run 原生战斗窗有单独 mark，约在开录后 208 秒；该时间是墙钟估算，不是视频 PTS。不能跨缺帧做 clean span。 |
| d06 骑士名单 90 秒，SHA-256 `ED26DACABA0BF082663C0AB663273406D3CB38ADD8DE9D4417C487DCD0487C4B` | 1,884 帧、0.000–89.967 秒，无缺失 PTS、倒序或大于 0.2 秒的间隙；该门不证明每个标称 30 fps 帧都存在，状态 `PTS_CONTINUOUS_UNREVIEWED`。 | 从**这条原片**请求 seek 10 秒抽出的原尺寸 2560×1440 PNG SHA-256 `D20B4F3D1B99126C6D985873018E2FEBD1467D7162EC4074722E898CD51369B2`，可见己方 11 人名单第 5 行 **7 勇武**。名单原片只有 start/end mark；自然封口后的新 mark 被拒，未补假锚点。 |

原始像素没有显示角色 ID 34333。a08 第一会话同源原生 trace 记录角色 34333 致残，第一会话保存的 d06 存档由严格离线 reader 查到角色存活和 `one_legged+wounded_1` 候选；这些证据不能替代第二会话缺失的 V3 当前数值。名单第 5 行 7 勇武可以作为可见后态镜头，但 34333→7 的身份对应应标为跨证据推断，61 号团当前攻击/防御值保持 **UNKNOWN**。历史 039→040 计算卡只可显式作为独立研究轨呈现。

两条原片均未获得 clean span 或人工 1× 签核。受管会话清理 CK3 成功、FFmpeg/OBS 进程清零，显示恢复 1920×1080，`ck3-screen` 于 06:51:07 UTC 以 task-bus seq 2379 正式释放。后续如剪用 90 秒片，先从原片定位精确 PTS、逐帧确认无遮挡文字，再作人工原速审阅和精确 bytes 签核。
