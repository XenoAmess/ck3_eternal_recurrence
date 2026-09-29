# 第二期七窗 14 导航端点：独立小件回读与待真人审片重点

2026-09-30。以五条既有 raw 的七份 `PENDING_CLEAN_REVIEW` 清单为来源，对外置机器报告、14 张现存 PNG 和 14 份 `extraction-receipt.json` 做**只读小件**回核。本次没有打开、哈希或解码 GB 原片，没有启动 CK3/OBS、占屏、人工原速观看、人工审帧、`package` 或发布。七窗机器端点状态为 **14/14 `EXTRACTED_UNREVIEWED`**；人工完整 raw 1× 为 **0/5**，人工端点审阅 **0/14**，已认证 clean span **0 s**，adapter GREEN **0**。机器端点是导航坐标，不能因此成为最终剪辑边界。

## 冻结报告与核验范围

路径基准 `W = D:/workspace/ck3_native_war_ai_promo_work/`。以下每份报告均用 `certutil -hashfile ... SHA256` 重新读取，所列哈希与封存总汇／来源交接一致；三个视觉报告均为 **AI 对孤立 PNG 的预筛**，不是完整录像审阅。

| 报告 | 精确 SHA-256 |
| --- | --- |
| `W/episode02-seven-window-machine-endpoints-20260930-a01/REPORT.md`：七窗 14 端点总汇 | `CD0D3C4D4BBD170172FB3A5C2C9F1ACBD2760EFADF5AB8B20B5E4141E7DE3CFC` |
| `W/episode02-a05-a01-d27d28-endpoints-20260930-a01/REPORT.md` | `3C83AE1F8965B2DAE5CDADE7527F68EA927EED2AC0C61D42AAA5B541D82C1184` |
| [`a05-d28d29-endpoint-machine-trial-20260930.md`](a05-d28d29-endpoint-machine-trial-20260930.md) | `D47D3BF64535CD2328865C4709E75A3EA797D8532A96C5CF2BB75D656149D422` |
| `W/episode02-a05-a02-d30-endpoints-20260930-a01/REPORT.md` | `142C74E2175C96396A02AEFB9532D9CE1C5318CCF471641193AF61E769CF6985` |
| `W/episode02-a05-a02-d31-endpoints-20260930-a01/REPORT.md` | `42348BA7E6F41B5B26091AE61790B227FA0813A534AF845B50490B429DED28F7` |
| `W/episode02-k04-machine-endpoints-20260930-a01/final-machine-report.json` | `C0DE251EE7F95AC27E40C2A6EC245E605CFBA104A082941BCFEF8525F510E5DC` |
| `W/episode02-k05-a02-d26-endpoints-20260930-a01/REPORT.md` | `D2BF48C3DC11D80AD5C994E16FE5C0F854007489E6089D9BFA210D78E19E95C2` |
| `W/episode02-eight-endpoint-visual-prescreen-20260930-a01/REPORT.md`：A05-2 d28→29、K04、K05 共八帧 | `CE58E4B0460C7A246D166C846EE42106900CD468CBA9CF9C4A3B1DA1D55D12BA` |
| `W/episode02-a05-a01-endpoint-visual-prescreen-20260930-a01/REPORT.md`：A05-1 两帧 | `D2ADE3E59EBBAB6A3572A5139ACCEED6B3BCE657CC3C39F9F9ED0B4C08A8A791` |
| `W/episode02-a05-a02-d30d31-visual-prescreen-20260930-a01/REPORT.md`：d30/d31 四帧 | `EE1FABBE22E6380012C9C1EB3EB74689E096BEABCB0E76E59666731BAB2F2BDE` |

我按下表**逐文件**对 14 PNG 和 14 receipt 做 SHA-256 回读，28/28 与原机器报告／视觉预筛一致。另解析 14 份 receipt：14/14 的 `result=EXTRACTED_UNREVIEWED`、`human_review_performed=false`、声明原 raw SHA、精确 PTS、decoded index、PNG 路径与七窗冻结索引一致。回执继续绑定各自的原 FFprobe、命令、stdout/stderr；这里不把尚未重新逐项读取的 GB raw 或全部命令日志写成“本轮已重新哈希”。

| 窗口／端点目录（相对 `W`） | 精确 PTS／帧号 | PNG SHA-256 | receipt SHA-256 |
| --- | --- | --- | --- |
| A05-1 d27→28 begin：`episode02-a05-a01-d27d28-endpoints-20260930-a01/begin/` | `350.000000`／`9887` | `2F9BFD5E1D8BAAD771293F0A8730AA05553A13BDD143D0119D75FE79F8CD52CE` | `DC4DD7C332C58E76033427F2876DD6ADE4532133DFBC5C2A1B87714622F6FA06` |
| A05-1 end：同父目录 `end/` | `450.000000`／`12679` | `7963BD84DB325BC1EA95D0F5C69378AF0612F11E88911DE836EED0EFE081F8AF` | `39D322E816AD7DAD09D2A597C4E1A2821D14AF69F8EE17F8E08E82659BA45D24` |
| A05-2 d28→29 begin：`episode02-a05-a02-d28d29-endpoints-machine-20260930-a02/begin-60/` | `60.000000`／`1648` | `BBD7D80F5E4ED7251930598592189F270EBC4D420559FCDD846DDFDA3F53A407` | `5D123D6357D63CA05EBB421A00ACF4E89CB8F76BEA3F84086E4774FA0F0E29E2` |
| A05-2 d28→29 end：同父目录 `end-170/` | `170.000000`／`4726` | `A5229918971681BC8C1B8A0F8AFDEEA229DEDEF3DB215F56A821FFD6ED868C58` | `C9AD48E9C387D49B2B54E269ABCD746B5EA3C051B4E2E829C9829DC0134E1CED` |
| A05-2 d30 begin：`episode02-a05-a02-d30-endpoints-20260930-a01/begin/` | `200.000000`／`5558` | `3448E90D847ABD766E4F58E6EC8192EE2EF1F19529E75A92B829DA5C469485A2` | `83A1833C2A06D630F9F15CEE12715CA055024C07B4B0BBF6D6F6DE38807D4A32` |
| A05-2 d30 end：同父目录 `end/` | `250.000000`／`6966` | `6F14C370E8017127C6FF7F642C548BC7F2FDE27F2B5D27668E19B7ACC9CA554D` | `D5EF1BEFC971EEECAE4CF24B0A559BFBFC680B56C211F15F2592CE5B538BA1D7` |
| A05-2 d31 begin：`episode02-a05-a02-d31-endpoints-20260930-a01/begin/` | `300.000000`／`8165` | `D423EC5729443041468543C8518B9D2B97ED445C8BC9A469D46566F855ACBADB` | `C50356FEBD3C07E3449D906858136E6A4492585A77271A7F51635B6C008E93A8` |
| A05-2 d31 end：同父目录 `end/` | `349.967000`／`9573` | `E1D0A6AFF0CC919064982BE6A8AC45F6030BB94227438B84055BE21893F8A511` | `6212A923D4FDC172C1EF69C48024B01326787A279AF9FB7B574D811475C7D741` |
| K04-a07 begin：`episode02-k04-machine-endpoints-20260930-a01/k04-a07-begin-a01/` | `0.000000`／`0` | `86CBEAA5B5670279F44346EE5C6D4107A8A58B9373E112D69FB1D7F3D8DA0EA0` | `AC76B1BBD9F6F8E203179A01EA6F7ABCD1D22C8A53B08ACC1C13F3D32C3F32B0` |
| K04-a07 end：同父目录 `k04-a07-end-a01/` | `411.167000`／`9371` | `AC84E6799920C17E5FB7EF55B18E8EAA86FC3C90D429C4B4F7EC486BD9D1EC9B` | `B17765EEA69DC6BD812B01E6E5B78EC017B68CFDED1500294B9D3A55CBD98576` |
| K04-a08 begin：同父目录 `k04-a08-begin-a01/` | `8.133000`／`1` | `71872CF0E1ACD1D7ED92CFCA0D1C3FF38C181A2094B09E6CFC770D8ED7C4D264` | `94F47AA37398C676E1A8F93B404512885469B6DAB7787CC92BA95217E3AC4D35` |
| K04-a08 end：同父目录 `k04-a08-end-a01/` | `239.967000`／`4804` | `6C6F60BEAF02F6CEB80BC9E3CCF8932169B34B6B31867BB0031115FC31676F7C` | `D68BA6CB5E30BDAD631AC4F3099D26CD9186B4FA5A792D14DF79DB9878A9ADEE` |
| K05-a02 begin：`episode02-k05-a02-d26-endpoints-20260930-a01/begin/` | `0.000000`／`0` | `99AB58C06079669C1E3711050C2D9A43D068F85AF9D414819B1A93445E1CB928` | `AA08127F853C3ABF3E34DA959C4D0B7B63F31352DD3A3F6829E552EEFB4ED294` |
| K05-a02 end：同父目录 `end/` | `210.000000`／`4460` | `FCB8E3E0D424BCDB135EFB8720CE5127BB1FE05C0CA23A21CA03677554AD13B8` | `16152918B5B98429C6D75F248BFB6932FE726AFA96DDD328A05F49EF204BA49E` |

## 孤帧预筛所标真人审片问题

以下是三份外置 AI 视觉报告及本轮对重点 PNG 的只读复看所得的**孤帧观察**。它们不证明两端点之间的画面连续、运动、声音、遮挡缺席或最终故事事实。

| 窗口 | 实拍孤帧观察 | 真人完整 raw 1× 时的核对问题 |
| --- | --- | --- |
| A05-1 d27→28 | `350 s` 是暂停地图、小战斗标记，**未打开详细战斗面板**；`450 s` 面板已写 **战败**、`824 对 4575`、**撤退中／追击中**，下方地图被面板挡住。 | 找到真实面板打开与日期转换过程；不能把 `350 s` 当作已展示 d28 逐团数据的帧。A05-1 到 A05-2 是不同 recorder，需显式剪辑切口及来源标签。 |
| A05-2 d28→29 | 两帧已是暂停的 **战败／撤退中／追击中** 面板，战斗侧大数约 `824→803`、敌方 `4575`，面板遮地图。 | 核对日期、行动和 HUD 的全程变化，确认连续可用段；早期 **战败** 字样不可充作后续 d32 `normal_result`／writer／战分 `−50` 证据。 |
| A05-2 d30 与 d31 | 四帧分别在 1067-01-02／01-03，仍为暂停 **战败／撤退中／追击中** 面板；战斗侧大数 `782`／`761`，各窗首末画面近似。 | 原旁白草稿第 40 行“可比兵团当前人数不变”与观众所见大面板总数 `824→803→782→761` 有**口径观感张力**。先凭同源逐团 soft/hard 账和术语核实分母，再决定卡片说明或文案修订；不能凭孤帧认定数据矛盾或擅改原稿。确认近静止画面是否可用，d30→d31 不能跨 `271.267→278.833 s` 缺帧。 |
| K04-a07 d05 前态 | `0 s` 样本有 CK3 HUD、非黑屏；`411.167 s` 的大 **11 名骑士**悬浮卡覆盖下方战斗面板。 | 全 raw 寻找真正无遮挡入出点，不能用端点样本代替“录制起点 HUD”与全程判断；`411.167→413.300 s` 后续缺帧不得跨。 |
| K04-a08 d06 panel | `8.133 s` 样本有 CK3 HUD，`239.967 s` 仍被骑士悬浮卡挡住部分战斗面板；两端大数近似。 | **整 raw `0→8.133 s` 缺帧 RED 保留**；这与 a07 是独立冷载，须标切口。当前 V3 CharacterID／prowess／regiment 61 真数值读回仍缺，孤帧不能补证。 |
| K05-a02 d26 前态 | 两帧暂停战斗面板显示高度不对称的 **11 对 4590**，右侧海域 tooltip；`0 s` 样本非黑屏。 | 全 raw 观察是否加载、遮挡、是否有实际可用动作；不得把 d26 控制延展为 d27 死亡／selector 后态，后者仍需新 capture。 |

原 A05-2 同 raw 还有 `37.933→38.700`、`179.600→180.067`、`271.267→278.833 s` 等窗外 PTS 缺口；每个选用 span 须在自身范围重核 `≤0.2 s`，不同候选窗不因孤帧相似而拼为一段。K04-a07 的尾后缺帧、K04-a08 开头 RED 与旧 A05-2 首次 FFmpeg9 `-vsync` 失败均保留原 attempt，不被新端点覆盖。

下一门是五条独立 raw 的真实完整 1× 人审（合计理论下限 `43:59.966`），以及选定精确首末帧的实际人工检查、无外来叠层／加载、同源事实核对和逐 raw 回执。`package`、adapter 与成片签核仍按 [`existing-capture-adapter-bundle.md`](existing-capture-adapter-bundle.md) 独立执行，不因本报告放行。
