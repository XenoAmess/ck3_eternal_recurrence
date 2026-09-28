# E2-05 a02 原片稀疏画面索引

2026-09-29。状态：`SPARSE_VISUAL_CANDIDATE_UNREVIEWED`。本记录只对 15 张原生尺寸无损 PNG 做点位目视，不是原片 1× 完整审阅、clean span 或人物死亡签核。

## 不可变来源与抽样回执

- 受管录像：`D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01/raw/e2-05-d26.mkv`，2,451,530,594 bytes，先前完整 SHA-256 `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`。本轮不重复读取整片计算 SHA。
- 冻结 ffprobe：同 recorder 的 `ffprobe.json`，12,044,180 bytes，SHA-256 `06A9C1FB92983390F6EE5FA48352732B09E01C4336B4D956F9CECC19F7C3A1FB`；身份回执 `D:/workspace/ck3_native_war_ai_promo_work/e2-05-a02-postrun-audit-20260929-a01/postrun-links.json` SHA-256 `213988D4278A26EFD4AA93BD8FE8DA2A56234D9B5EC3B1AE019EB53212B0EB0C`。
- 新成功 attempt：`D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-a02-visual-index-20260929-a02/sample-index.json` SHA-256 `28D525DBDCC73167133E19968969682C3B42584035BE25AA1234A2F3D11662C4`。15 次单线程输入 seek，各只输出 1 张 2560×1440 PNG；逐点有 `seek-NNN.intent.json`、`seek-NNN.exit.json` 和原字节 stdout/stderr，实际 `showinfo n:0` PTS 均与冻结 ffprobe 帧 PTS 在 1 ms 内匹配。`final-source-audit.json` 为 `STABLE_STAT_ONLY`，原片大小/mtime 在每 seek 前后及最终未漂移。
- 原先 `...-visual-index-20260929-a01/` 在第 0 秒按唯一 PTS 门 RED：旧滤镜处理了 `n:0` 和 `n:1`，即使只写出一张 PNG。它的 partial、日志、argv 和退出回执永久保留；未生成成功索引。修复提交 `b8c4e9e2e` 在 showinfo 前选择首帧，真实三帧小夹具和独立非零 seek 复核通过。成功 attempt 是新建 a02，未覆盖 a01。

## 目视事实与候选时间

全部 15 帧均显示同一幅墨西拿附近地图和“墨西拿之战”战斗窗，游戏处于暂停；没有在这些**取样点**看到击杀弹窗。底部战斗面板的装饰边框触及画面下沿，但本次所述日期、兵数、优势和骑士数量可读。

| 原片实际 PTS，秒 | 原生 PNG | 此帧可读事实 | PNG SHA-256 |
| ---: | --- | --- | --- |
| 0 | `seek-000.png` | 1066-12-29；兵数 11/4590；我方骑士 11、敌方法里斯 19；优势 +7 | `6686E7A97355E19A1E72DA2F7747E9A1DB15A894A5235F45CCC471E8915CAE5D` |
| 90 | `seek-090.png` | 同前，无名单 tooltip | `5F6B467C01C592B11C1103B850487B9806E6808A868A1B6721B2058AF896B64F` |
| 175 | `seek-175.png` | 同前，无名单 tooltip | `8BFF6F8F0B2FDA506B3905F08DC8DC51595A45BB0F1E199DB64F26A54A83155B` |
| 190.033 | `seek-190.png` | 同前，无名单 tooltip | `1EDFB231C0DFB27C88E7E99BCABF5490A63BEA9D496326D0D9BD55AB4441012F` |
| 210 | `seek-210.png` | 同前，无名单 tooltip | `D4CD4E6802C54A552B52349411D2E9403A0F56ABDB5AD801F35DFE3EE48F25BE` |
| 240.033 | `seek-240.png` | 1066-12-30；兵数 2/4573；我方骑士 10、敌方法里斯 19；优势 +12 | `DD4E91100B9CD01C6798C739B449D3B2DB4812BFBC19117DFF928D5D8621B1BF` |
| 265 | `seek-265.png` | 同第 27 日战斗状态 | `80318A2FF47FE3B3AC7EB70EE9818E12A62EF63CBD8E3F4BB494C554650F38C1` |
| 285.033 | `seek-285.png` | 同第 27 日战斗状态 | `805A4534615663D6C684647E9A4982362381C7869ACB9333158F69A37AC3A507` |
| 300 | `seek-300.png` | 同第 27 日战斗状态 | `7A40DB8196818081C3D69B251B0223D731348BE74AE1A2DA6DE939096ACFE9A4` |
| 315 | `seek-315.png` | 同第 27 日战斗状态 | `7567C91C7AD72C091EFD6E010E7CA7333E819983C2A67707CDBB7687EF896CB0` |
| 335 | `seek-335.png` | 同第 27 日战斗状态 | `C267589E093A79C9448166A5F08A32F2031B5D45709BF7714B9FC56953DE7150` |
| 385 | `seek-385.png` | 第 27 日我方“10 名骑士” tooltip 与十行名单可见 | `6A108AB1568B6B7636D2011A8FE3BDC889B7D5C050EF81F879AF494F63F85260` |
| 400 | `seek-400.png` | 此点仍可见我方十人 tooltip | `7E5CBCE36D5BE3C4D2AAB70B6A441B89B6313B3D877D7EBA7EFD5FC266595268` |
| 500 | `seek-500.png` | 此点仍可见我方十人 tooltip | `FE79ADAEE2CD4381C5F864B2015A7F3A65DEEEA3758E1ACA261AA3A72F72962D` |
| 580 | `seek-580.png` | 此点仍可见我方十人 tooltip | `031E734BEC8A67C78FBA8113C2C8857A32410D3EC2AEE3822BC5EE53D50F1594` |

实际日期/兵数/骑士行变化只被这轮稀疏取样夹在 **PTS 210 与 240.033 秒之间**；这个区间不是精确事件帧。先前 marks 的墙钟相对值 `190.884/304.990/388.113` 秒不是原片 PTS，不可用作剪点。第 26 日我方 11 人和敌方 19 人完整名单的截图出自录像开始前的同次 live 会话；本轮录像点位中未抽到它们，不能把独立截图冒充 raw 画面。第 27 日我方十人 tooltip 则确实进入原片；敌方 tooltip 在本轮点位未见。

## 给剪辑与事实审查的边界

可把 PTS `0–210`、`240.033–335` 和 `385–580` 作为**待连续审看的导航区间**，并优先细查 `210–240.033` 的日期变化。点位不能证明区间全程干净、是否有短暂弹窗，或名单显示的准确入出帧；最终 cut、来源标签与实际可用时长都需逐段 1× 审看后确定。眼下没有任何 `clean_span`。

画面直接支持“同一战斗窗两日数值变化”和“第 27 日我方十名骑士名单可见”。它不直接支持某位骑士死亡、被谁击杀、原生 selector 全过程或录像已拍到击杀。外部 trace 的 `knight_killed_by_enemy` 行、战报与名册差异只能各按自身证据合同叙述，不能替代画面证据或混入本次原片的视觉结论。
