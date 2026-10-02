# A05-2 d28→29 单窗首末帧机器试跑

2026-09-30；只对七窗审阅计划的 A 组 `A05-2 d28→29` 导航窗试跑项目 wrapper `extract-frame`。来源清单为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-a02-d28d29-adapter-pending-20260929-a01/source-manifest.json`，`13924 bytes`，SHA-256 `8115562E7924F5C6C6A2E76AB886563AB16FD1188449930D72484716FD2AC043`。它绑定原 raw `840210967 bytes` / SHA `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC` 与 FFprobe `15730950 bytes` / SHA `1EA5CCC3C36500DFE62AA42409FC6725237C03DCAB9B5BD2AA3D7176EF1BA5E0`。原 raw 和来源清单均未改写。本窗已有的轻量 PTS 导航范围为真实帧 `60.000000–170.000000`、索引 `1648–4726`，窗内最大相邻 PTS gap `0.067 s`；这些范围仍只是未审剪辑候选。

三个 `extract-frame` 命令前分别重新查询 [正式 Latest Release](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest)，均为 `v0.2.1`；独立工作树无相对 `.venv`，显式使用 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，实际 `-m xar_promo --version` 为 `0.2.1`，wheel pin SHA `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`，已核顶层和 wrapper `extract-frame --help`。本机 FFmpeg 为 `9.0.1-full_build-www.gyan.dev`。任务没有启动 CK3/OBS 或占用受管屏幕。

## 保留的第一次 RED

首次在源码 HEAD `343545fc87db04d58bd9273103b17e54a61a282a` 用原 wrapper `-vsync 0` 抽 `60.000000`，前置来源重核通过，FFmpeg 命令返回 Windows code `2880417800`，原 stderr 明确为 `Unrecognized option 'vsync'`。外置失败目录 `D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-a02-d28d29-endpoints-machine-20260930-a01/begin-60/` 保留 `command.json` SHA `79460D83C71288BCD6A2D6A247DC016BA5F8C904DA05704B351C99586F62375D`、`stderr.txt` SHA `8A773BBD6A1B3809C7242E7C3655DD84A0231A1C1CF328063C0C218ECBF9172C`、零字节 `stdout.bin`、`failure.json` SHA `6F9122C61BEE5D5FA41E39EA348CF65F6C02841F5C1E1F453E3B415E618F4DDC`。没有 PNG 或 `extraction-receipt.json`。此 RED 不被覆盖或改称通过。

源码 HEAD `f87d5e0e5` 起将新提帧命令改为 [FFmpeg 官方文档](https://ffmpeg.org/ffmpeg.html)中的 `-fps_mode passthrough`，而 `select=eq(n\\,INDEX),showinfo`、完整来源重核和实际 PTS 比对不变；普通和 `-O` fixture 各 `15/15`。随后为防旧成功 `-vsync 0` 回执在未来封装时被新模板拒绝，`package` verifier 仅额外接受旧的精确 argv 模板，仍强制原件／PNG／command／FFmpeg `showinfo` SHA、PTS、时间及真人 1× 门；三个兼容反例后 fixture 普通和 `-O` 各 `18/18`。这只影响后续 verifier 的只读判定，旧 RED 文件不修改。

## 新 attempt：机器提帧成功，但仍未审画面

新外置父目录为 `D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-a02-d28d29-endpoints-machine-20260930-a02/`。两端点各用独立新子目录；wrapper 对整条原 raw 重新哈希，并按原 FFprobe 索引解码，再核 FFmpeg `showinfo` 实际 PTS。以下 SHA 经 `certutil` 对现存文件回读；两份回执均 `EXTRACTED_UNREVIEWED`、`human_review_performed=false`。

| 端点／约墙钟耗时 | 精确 FFprobe PTS／decoded index | PNG bytes／SHA-256 | `extraction-receipt.json` SHA-256 | command／stderr SHA-256 |
| --- | --- | --- | --- | --- |
| `begin-60/`，`20.85 s` | `60.000000`／`1648`；showinfo `pts_time:60` | `2559864`／`BBD7D80F5E4ED7251930598592189F270EBC4D420559FCDD846DDFDA3F53A407` | `5D123D6357D63CA05EBB421A00ACF4E89CB8F76BEA3F84086E4774FA0F0E29E2` | `88D27FBD523A1807B6360842F0EF695BF9FBB221A07C55465AF366B99DF2F8C2`／`B57DFEBD92F8BC2B32C87DF1F34BE233AA9AB91109B8E31DA2864AAF6446C2CA` |
| `end-170/`，`32.49 s` | `170.000000`／`4726`；showinfo `pts_time:170` | `2566386`／`A5229918971681BC8C1B8A0F8AFDEEA229DEDEF3DB215F56A821FFD6ED868C58` | `C9AD48E9C387D49B2B54E269ABCD746B5EA3C051B4E2E829C9829DC0134E1CED` | `E2DB87F9B5089A762702FA73D4D0702AAA152B9305184950C1E2D8EDEF5AC161`／`8BE6AB9282FF98C31BCA59A4586BA1521F5AA174BE48B9CFD1894DFC3246555A` |

本单窗两次成功命令合计约 `53.34 s` 墙钟；每次会重读 GB 级来源，其他窗耗时需实测，不能据此推定全部端点的固定速度。两份 PNG 和整个原 raw **尚未由真人按 1× 完整审看**，原始导航边界也未缩为经人确认的 clean span。没有 `human-review.json`、`package`、adapter GREEN、成片签核；已认证 clean span 仍 `0 s`。后续按 [`seven-window-human-review-plan-20260930.md`](seven-window-human-review-plan-20260930.md) 在真实审阅后才判断画面首尾、HUD、日期、遮挡、加载和可用区间。
