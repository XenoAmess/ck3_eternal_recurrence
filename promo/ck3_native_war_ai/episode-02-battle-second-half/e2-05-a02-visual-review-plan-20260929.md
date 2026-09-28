# E2-05 a02 原片视觉索引计划与审查门

2026-09-29。**本版只读小型回执与既有原始截图，未读取或 seek 2.45 GB 录像。** 现金侧 R0266 正占 CK3 屏幕并准备冷启动；待其明确允许短时磁盘读取或释放资源后，另起外置 append-only 取样 attempt。此计划不登记 clean span 或人工 1× 签核。

## 本次来源身份

E2-05 a02 受管 run 为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/`，从第 26 日原档 SHA-256 `C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B` 冷载。原生帧为 WarID `4`、CombatID `16777218`、ArmyID `18`、玩家 `29829`、省份 `2633`，日期由 raw `53146848→53146872`，同 run 单次 +24 小时。原片 `recording-e2-05-d26-a01/raw/e2-05-d26.mkv` 为 2560×1440、600 秒、2,451,530,594 bytes，SHA-256 `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`。后审 `e2-05-a02-postrun-audit-20260929-a01/` 证明 12,656 帧从 `0.000–599.967 s`，无缺失/倒退/>0.2 秒间隙，状态 `MEDIA_PTS_CANDIDATE_UNREVIEWED`。

墙钟 mark：`d26-before` 约录制器起后 `190.884 s`，`d27-after` 约 `304.990 s`，`d27-player-knights` 约 `388.113 s`。**这些是导航锚点，不能当媒体 PTS 或实际日期跳变的切点。** 截图回执分别 SHA-256 `E3AE1941A92E59DC7EFA8A790D3C10269C0AAF4147D5C2020A5FC7E07988F292`、`6811BCEDBB8B6A7C8EAAD10658CAE2A1C9931A20BEB4C0ACF293DA510040F3D6`、`5DE5F25D72DA10D93A6129B37FF2EFE3A5F29101D59511AC65DC5889CA7E7F62`；corresponding `marks.jsonl` SHA-256 `3266390257DAEFF91114FF1E7D017192ECF50D836776D1BC5E8191643C9C5337`。

## 无 raw 的可见性预判

已直接查看 2560×1440 原始截图：录制前干净战斗窗中墨西拿地图、日期、双方兵数 `11/4590`、战斗优势 `+7`、双方骑士数量 `11/19` 均在画面内；录制后 d27 战斗窗见 `2/4573`、优势 `+12`，玩家骑士数 `10`。对应截图及 SHA 分别为 `episode02-e2-05-a02-screen-lease-20260929-a01/battle-panel-cursor-clear-a01.png` `54F5DF803ED2E15AE400E0098AD1ED39F54A6EAADE56936CF132CE0AEBC5AEF7`、上段 d27 截图 SHA `6811...F3D6`。100% GUI 下只有装饰边框延伸出屏幕；数字与骑士行清晰。

录制前另有己方 11 骑士 tooltip 截图 `knight-label-after-a01.png` SHA `32D222DCCDA4C5A1FAC64AD1225B5C6B1F6EFF5E131F1D56432B51EFF975F4CA`，敌方 19 骑士 tooltip 截图 `enemy-knights-list-a01.png` SHA `90A1BC28E9E2BFBDDDA5F3401DCB7137451EA09A718BE038401B24A1A188E619`；d27 录制中的己方 10 骑士 tooltip 截图 SHA `5DE5...E7F62`。**前两张在 recorder 启动之前取得，只能证明同次 live 会话的 UI 能拍清，不能证明对应名单已进入 raw。** 姓名到 CharacterID 的对应关系也不能只靠相似拼写推定。

## 获磁盘许可后的低负载取样顺序

取样使用单线程 FFmpeg、输入 seek、每点一张原生尺寸**无损 PNG**，不做全片解码、转码或循环抽帧。细小 CK3 字符只凭原始 PNG 判读；如另制 JPEG，最多作导航缩略图。输出只能是外置 `ck3_native_war_ai_promo_work` 根目录下**新建的平级专用 attempt**，不能落在 raw、live、audit 或仓库源树中，也不覆盖 `a01/a02` 旧索引及本次 recorder。E2-05 专用脚本硬绑定既审 `postrun-links.json` SHA `213988D4278A26EFD4AA93BD8FE8DA2A56234D9B5EC3B1AE019EB53212B0EB0C`、原片 SHA `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F` 和 ffprobe SHA `06A9C1FB92983390F6EE5FA48352732B09E01C4336B4D956F9CECC19F7C3A1FB`，不能让调用者自报另一 run。每次 seek 启动前写精确 argv/意图，完成或 RED 后保全原样 stdout/stderr、退出码与 PNG partial；每次前后以及最终重核源原片 size/mtime。逐张记录原片的先前完整 SHA 来源、请求 seek、实际解码帧 PTS、PNG 宽高、PNG bytes/SHA-256；实际 PTS 只接受唯一 `showinfo n:0` 并与已冻结的完整 `ffprobe.json` 交叉核对，多帧或无法核准保持 `PTS_UNRESOLVED`，不得生成成功索引。

| 目标 | 首轮 seek 秒点 | 要验证的画面事实 |
| --- | --- | --- |
| 第 26 日无提示框战斗窗 | `0,30,90,150,185` | 窗口是否从录制首帧即完整；日期 1066-12-29、`11/4590`、骑士 `11/19`、优势 `+7` 是否同屏清晰。 |
| 第 26 日双方名单 | `175,190,205,220`，并根据截图再向前后各细化 | raw 中到底有没有己方 11 人、敌方 19 人完整 tooltip；不得用录制前截图代替视频。 |
| 唯一日推进及可见事件 | `240,265,285,300,315`，发现状态切换后再以 5 秒级细化 | 找到视频中实际日期/兵数/骑士数跳变的相邻帧；若无游戏弹窗，明确记 `no_visible_popup_in_samples`，不能写作“看见击杀”。 |
| 第 27 日战斗窗与名单 | `335,365,385,400,430,500,580` | `2/4573`、优势 `+12`、己方骑士 `10`、完整名单是否留在 raw；确认 tooltip、鼠标和边框不遮住关键行。 |

每个候选窗口须至少在起、中、末抽样，精确 PTS 后再提出待 1× 审片的入出点；若画面中有日期改变、hover 覆盖、输入焦点或弹窗，拆分窗口。只对独立原速素材计一次时长，不能把静止暂停画面循环计时。完整原片审阅之前，输出状态固定为 `SPARSE_VISUAL_CANDIDATE_UNREVIEWED`。

## 论断门

1. **战斗窗可见**：同一原片的日期、墨西拿、完整双方兵数/骑士行/优势在具体 PTS 均可读，且有对应原生 control SHA。第 26/27 日分别绑定 `e2-05-d26-control.json` SHA `D41E384CE022C261E15E3761980A0A78E26BA0B21C9FCF3F2393F062F03CEC1F` 与 `e2-05-d26-post-snapshot.json` SHA `062907DC73AAD127C766F45E754BEC7457E8C6B956D842A87DB2BF35B6030249`。
2. **名单变化可见**：raw 中分别看见标题 11 与 10、完整行列表；如名单只在独立截图而不在 raw，仅可给静态对照卡。名单差异是“有人离开战斗骑士行”，单凭 UI 不证明死亡、击杀者或抽签。
3. **击杀事实与视觉分离**：`e2-05-d26-trace-finish.json` SHA `BFF0A9CFCE858C88B9FEA67D0FB646CDB7175BA7DC957898769BE02D5479C7D0` 的快速读取只报告 `knight_killed_by_enemy` 一行；完整 selector、CharacterID `34120/33437`、死亡/脱团须由同 run 原生事实审计单独确证。没有 `event-fire` mark 或可见事件弹窗，不能把 trace 行写成已经拍到击杀，也不能把历史 `020/070/036→038` 的 RNG/名单接到本 run 画面。
4. **clean span 与使用门**：机器 PTS GREEN + 稀疏 PNG 只产生剪辑候选。精确 cut 要有全段 1× 原速审看、字幕/来源标签可读性、同 run raw/report/timeline/evidence-index 精确哈希、无遮挡和 CK3 adapter 校验后，才可登记 `clean_span`。任何重新编码后都需绑定新 bytes 并重审。
