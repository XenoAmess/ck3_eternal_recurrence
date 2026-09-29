# E2-05 a02：骑士行与击杀通知的四帧缩区间

状态：`SPARSE_VISUAL_CANDIDATE_UNREVIEWED`。只审阅了本轮四张原生尺寸 PNG；未进行原片 1× 完整审阅，未认证 clean span，也未独立查询角色死亡状态或原生 selector 的 CharacterID。

## 冻结来源和外置回执

- 原片 SHA-256：`7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`，2,451,530,594 bytes。本轮采样器未重哈希原片，只在每次 seek 前后核对 size/mtime。
- 冻结 ffprobe SHA-256：`06A9C1FB92983390F6EE5FA48352732B09E01C4336B4D956F9CECC19F7C3A1FB`；postrun link SHA-256：`213988D4278A26EFD4AA93BD8FE8DA2A56234D9B5EC3B1AE019EB53212B0EB0C`。
- 新 append-only attempt：`D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-a02-visual-index-20260929-a04/`。`sample-index.json` SHA-256：`3D8FE95BAF71861C8B18AB45D70ACA0A5186504CF3142261F5C7570FBCAE218B`；`final-source-audit.json` SHA-256：`513A99231A958C3E4A86E3B12A701B5E95F85D09D1B8172BB41B7030839C1DAF`。四次 FFmpeg exit 均为 0，逐次 exact argv、stdout、stderr、实际 showinfo PTS 与 PNG hash 见 index 和 seek 回执。
- 目视记录：`visual-observations-02.json` SHA-256：`A18E2172FBBDC0D31671A0B20380EC87AC43E3894D4C5799ECEFB5C2A66EB4DE`。先前写入的 `visual-observations.json` 仅为误生成的 `{}` 占位，SHA-256 `CA3D163BAB055381827226140568F3BEF7EAAC187CEBD76878E0B63E9E442356`，**无效，不作画面证据**；两文件均原样保全。

四张截图均位于上述外置 attempt，原生尺寸均为 2560×1440：

| 原片实际 PTS，秒 | 原图文件 | PNG SHA-256 | 目视画面事实 |
| ---: | --- | --- | --- |
| 231.000000 | `seek-231.png` | `748F8D5A417E37FA0DFA01323081E1C74635D7E06941209D8D85BF3559B38012` | 公元 1066-12-29；兵数 11/4590；我方骑士 11、敌方法里斯 19；未见击杀通知。 |
| 232.000000 | `seek-232.png` | `E2BF0235CB71A971B5AE6FFCDA6FCC3EEC4398B7AC2F07D527044A3B2291A70F` | 同前。 |
| 233.000000 | `seek-233.png` | `E0A0B01CCC8C5F94C538A69F4CABFCC164B618D86720ECA83C680A5030E6F033` | 公元 1066-12-30；兵数 2/4573；我方骑士 10、敌方法里斯 19；击杀通知可见。 |
| 234.033000 | `seek-234.png` | `517EB41BEF6E11DD252A9801D270F573C0909D8BDFC026973C5CD1F99E5DB68E` | 同前；击杀通知仍可见。 |

PTS 233 的通知文字可读为“我方骑士图尔吉塞·德·圣塞韦里诺被阿姆鲁·阿尤布击杀！”。这一句只证明游戏录像里**显示了该 UI 文本**；不自动证明通知与骑士计数在同一源帧发生，也不证明原生 selector ID、实际死亡状态或任何未显示的战斗结算。

本轮把最后一个已观测旧状态与第一个已观测新状态缩至 **PTS 232.000000–233.000000**。这两个点还不是冻结 ffprobe 的相邻视频帧，首次变化帧仍待后续有界抽样定位。本次只使用原先允许的八帧上限中的四帧；采样于 04:59:21 UTC 完成，随后释放原片磁盘窗口，未在 d06 冷载期间继续读取 raw。
