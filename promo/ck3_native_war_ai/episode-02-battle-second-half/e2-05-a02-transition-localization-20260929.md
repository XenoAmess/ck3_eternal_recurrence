# E2-05 a02 骑士行变化定位：五帧粗区间

状态：`SPARSE_VISUAL_CANDIDATE_UNREVIEWED`。此文只记录已完成的五帧原片点位审阅。未做原片 1× 完整审片、未登记 clean span、未证明原生 selector 的 CharacterID 或实际死亡状态。

## 冻结输入与外置回执

原片先前完整 SHA-256 `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`；冻结 ffprobe SHA-256 `06A9C1FB92983390F6EE5FA48352732B09E01C4336B4D956F9CECC19F7C3A1FB`；postrun link SHA-256 `213988D4278A26EFD4AA93BD8FE8DA2A56234D9B5EC3B1AE019EB53212B0EB0C`。读帧器使用提交 `f6067d45b`、`eb3d705a9` 的小数秒 seek 门；邻帧工具使用 `29a8b49ec`、`05d014d00` 的严格全帧 PTS 读取门，独立复审已通过。

新外置 attempt 为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-a02-visual-index-20260929-a03/`。`sample-index.json` SHA-256 `134AECFC3E2D3B6799482D4AD2C5FEF038619D3E732D54F9BB1149A9AC6DBE3F`，逐帧记录原片身份、FFmpeg exact argv/stdout/stderr、退出码、实际 PTS、PNG 2560×1440 尺寸和 PNG SHA。`visual-observations.json` SHA-256 `7D465842D5150A95EFC79A7475C2F5155DF8EC469857C48D8C6010E5600ECA2` 是只读目视记录，其 `observed_at_utc` 误填，已在**新文件** `visual-observations-correction-01.json` SHA-256 `7F54C1D2F85AB57CC19435022B332218D963EB5D0D0A96178C7B2114ED38BF8D` 标明无效；原文件未覆盖。

| 原片实际 PTS，秒 | PNG SHA-256 | 目视状态 |
| ---: | --- | --- |
| 215 | `0EFB96BC89237E1DB62B1CCC07FF1633A040390ADF560A126FEF3237357E1DD0` | 1066-12-29；兵数 11/4590；我方骑士 11、敌方法里斯 19。 |
| 220 | `D9499212FB30AAAC66EFB08A69A2EC7E43E6E442ED103B418EB948D183BB7DE0` | 同前。 |
| 225 | `0989DB51ECCD7AF93AA972056A2110F0E54A43F6B6CB91ABB912DFBACBE36107` | 同前。 |
| 230.033 | `3FB140DD5978E405675DA1013A1ECEBE4CCFC766976EAA901B8F721398667746` | 同前；此取样点未见击杀通知。 |
| 235 | `688DB15AAC2E64D1DC5F7D7C9551ADCD9439638B3A374BCE14888983607174F7` | 1066-12-30；兵数 2/4573；我方骑士 10、敌方法里斯 19；画面出现一条击杀通知。 |

PTS 235 的原生 PNG 上，通知逐字可读为：**“我方骑士图尔吉塞·德·圣塞韦里诺被阿姆鲁·阿尤布击杀！”**。这是录像中可见的游戏 UI 文本，可用作待审镜头线索；不能由此推出原生 selector 的候选集合、随机索引、两人的 CharacterID，或角色死亡状态已经由独立原生查询证实。

据这五帧，11→10 骑士行变化、日期变化和通知出现都只能夹在 **PTS 230.033–235**。它们是否同一帧发生尚未定位。第二个短磁盘窗口来到时 a08 冷载已排队，故未启动新 seek；该窗口第二轮新增帧 **0**，原片读取权已归还。下一次需在新外置 attempt 有界抽 PTS 231/232/233/234，再按画面状态与冻结 ffprobe 邻帧序号缩至最后一个 11 帧和首个 10 帧；每轮需由屏幕/磁盘负责人明确排程。
