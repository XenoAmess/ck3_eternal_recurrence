# E2-05 a02：原片相邻帧上的骑士 11→10

状态：`SPARSE_VISUAL_CANDIDATE_UNREVIEWED`。本次仅对五张原生尺寸 PNG 做离线点位目视；未进行原片 1× 完整审阅，未认证 clean span，也未独立证明原生角色 ID、selector 或角色死亡状态。

## 来源和回执

冻结原片 `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-d26-live-20260929-a02/recording-e2-05-d26-a01/raw/e2-05-d26.mkv` 为 2,451,530,594 bytes，先前完整 SHA-256 `7FC3D614C50AD958DA57359248A196A230BD2B0B5B511EF242596837042C1C0F`。本轮采样器未重哈希大原片，而是按已审 postrun link SHA `213988D4278A26EFD4AA93BD8FE8DA2A56234D9B5EC3B1AE019EB53212B0EB0C` 锁定来源，并在每次 seek 前后核对 size/mtime。冻结 ffprobe SHA `06A9C1FB92983390F6EE5FA48352732B09E01C4336B4D956F9CECC19F7C3A1FB`；严格 PTS helper 检查全部 12,656 个视频帧均有可用时间戳，以下索引用其原始视频帧顺序。

五次单帧 FFmpeg 均 exit 0。每次使用独立外置 append-only attempt，内含 exact argv、seek 前 intent、exit、原始 stdout/stderr、source audit、actual showinfo PTS、冻结 ffprobe PTS、2560×1440 PNG 及其 SHA。汇总目视回执为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-a02-adjacent-visual-20260929-a01/transition-observations.json`，SHA-256 `916AE44DAAA244DEBA3B6B9BD7F72ED8527C070AE143E3D6D883AC77D54F10E7`。

各 attempt 位于 `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-05-a02-visual-index-20260929-aNN/`；表中 index SHA 对应其中的 `sample-index.json`，PNG 文件名位于同一目录：

| Attempt | 冻结帧序号 | 实际 PTS | PNG 文件 / SHA-256 | index SHA-256 | 原生画面目视 |
| --- | ---: | ---: | --- | --- | --- |
| a09 | 4913 | 232.233000 | `seek-232p233.png` / `8C57A7CC76F1B82F6452AA7F9F7515082A62428380F6C1D05D462D66837782D8` | `A27981D6A7E845DC410F8FF6D35971757C87ADD31F7B1F43FA2070153CCDE4C8` | 12 月 29 日；兵数 11/4590；我方骑士 11、敌方法里斯 19；未见通知。 |
| a05 | **4918** | **232.533000** | `seek-232p533.png` / `A2DD883306EFF9B6D925A0F68E21819EEBE0544A9A91CD9CA936E129701A349B` | `3A10ECE940F9A9BD7F435ABD8CAE889A2F89A24D07818A5EE7AA775146F5FAB3` | 12 月 30 日；兵数 11/4590；我方骑士 **11**、敌方法里斯 19；未见通知。 |
| a08 | **4919** | **232.567000** | `seek-232p567.png` / `5438CC4210EFE071C38ABD5854EFE87E39F091A9ABDF8DA5FE84E5C8C64F9F27` | `0A973A94AB8A2F245B7A77FFDF2262C43074B475A3F08CE00EAF81B589303C33` | 12 月 30 日；兵数 2/4573；我方骑士 **10**、敌方法里斯 19；通知开始半透明淡入，文字**不可读**。 |
| a07 | 4921 | 232.667000 | `seek-232p667.png` / `31CF2D1251BEA29E0C70818F5364C1175A33D1DBC53CDAF9788C3D181D571A86` | `2786F83FD751B740743305E3D9BC6A25116ABF2FA36078ED60FCFC8D81F614A5` | 12 月 30 日；兵数 2/4573；骑士 10/19；通知继续淡入。 |
| a06 | 4924 | 232.800000 | `seek-232p8.png` / `3E0703E62CE049BF8741B7A1951C9EEAAD2705034AEE265FC79C0874292A73B0` | `5AA4A7B31345551BBAB00FADF41E021EBA257BB872F349A5281EE411DE2808CB` | 12 月 30 日；兵数 2/4573；骑士 10/19；通知比前帧更清楚。 |

冻结 ffprobe 中帧 **4918 与 4919 相邻**，两帧间没有第三个视频帧。因此骑士行的可见 **11→10** 变化已定位在 **PTS 232.533000→232.567000**；同一对帧中通知从未见变成半透明淡入，但后一帧文字不可读。通知中姓名和“击杀”的完整文本仅在较晚的 a04 PTS 233.000000 原图可读，不可回填为 232.567 帧已读清文字。项目主代理另行直接查看了 4918/4919 两张原图，确认骑士数及半透明通知边界；这仍非 1× 完整录像签核。

日期变化比骑士行更早：帧 4913（PTS 232.233000）仍显示 12 月 29 日，帧 4918（PTS 232.533000）已显示 12 月 30 日。日期转换目前只有这个**非相邻帧**区间；未在五帧限额外继续抽样。下一次若需精确日期切换，按冻结帧序号在 4914–4917 内有界复核。
