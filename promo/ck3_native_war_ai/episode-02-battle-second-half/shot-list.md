# 《战斗后半笔账》镜头与取材门

2026-09-28 镜头账更新。下表的“已录”只表示外部 recorder 已封口并保留原始媒体，**不表示**已有可剪 clean span、CK3 adapter GREEN 或人工 1× 审看。片名、文件名、请求成功、截图 mark 和自动 PTS 检查均不能代替这些门。

## 当前正式取材轨与 raw 边界

下列外置轨迹均在 `D:/workspace/ck3_native_war_ai_promo_work/`；CK3 `1.19.0.6`、玩家 `29829`、CombatID `16777218`、WarID `4`。相同源档的不同 attempt 仍是独立回放。

| 轨迹 | 精确来源与原生事实 | 已有媒体及限制 |
| --- | --- | --- |
| **A05 追击/终局** `episode02-terminal-pair-20260928-a05-live` | 从 attempt-004 **运行中生成**的第 27 日 `trace-d27-immutable.ck3`，SHA-256 `F085D8ABB89A354FA1004DBE8800505BC952AA8A68C0EA21AAB788F9875FEEB3`，配真实 `trace-d27-save.json` SHA-256 `5198123BD71842624A3FB933492F78C3BB11C65D2DED634E3965FDC79B90A012` 独立冷载。A05 第 28–31 日 control 的追击叶值与旧 004 相等，新增终局 baseline 字段不同；这是条件对拍，不能说两个 attempt 的全部字段或录像相同。A05 自身第 32 日 terminal 回执 SHA-256 `3CAC1F8F89545C299A957EB49C1B8636BB9A14C2707680A458FA8104EF9B1782` 证 `normal_result`、winner side0、玩家 ArmyID `18` 败退、writer hard-loss `53662042`、八桶分母 `996`、CB 倍率 `15000000`、WarID `4` 进攻方 row `-5000000` Q100000。 | 同一 A05 游戏会话中**相邻但非连续**的两段 1920×1080、各 600 秒 raw：`recording-e2-09-terminal-a01/raw/e2-09-terminal-a01.mkv` SHA `C2E3AB8B0E60171316DD445B999B95E91227211666FE78CCF797F733AFDA315B`，mark 涵盖第 27、28 日；`recording-e2-09-terminal-a02/raw/e2-09-terminal-a02.mkv` SHA `25A13691259215848D77EAAB8AED9C0E281AF59A8AEB126E5D726EC6FE73A9BC`，mark 涵盖第 28–31 日、第 32 日 writer 和战分面板后图。自动 PTS 审计无大于 100 ms 断档；mark 墙钟偏移与 nearest PTS **仅用于导航**。均 `ENCODED_UNREVIEWED`，没有 clean span 或 1× 审看。 |
| **A01 增援** `episode02-e2-06-d11-live-20260928-a01` | 从 attempt-004 第 11 日 `trace-d11-immutable.ck3` SHA `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`，配 `trace-d11-save.json` SHA `DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5` 独立冷载。新 attempt private trace 观察原生一天 `53146488→53146512`、ArmyID `22` 入场、full-entry `count=2`、战宽三点 `1645/1480→2467/2220→首次 side0 出伤参数 2220`，`failure_flags=0`；`production_trace_ready=false`，不能称生产观察器 GREEN。 | `recording-e2-06-d11-a01/raw/e2-06-d11.mkv` 1920×1080、600 秒，SHA `501B4C2A8557DC2EBBE88FD0485A45265FDDC9BF8EF46F7A1E968F8EB51024C7`；有第 11 日前和第 12 日后截图 mark，`ENCODED_UNREVIEWED`，无 clean span 或 1× 审看。实拍原图的战斗面板下半在 `GUI.scale=1.3` 时被裁，[只读裁切审计](e2-06-combat-panel-crop-readonly-20260928.md)列明边界；下半逐团/战宽 UI 不得以本段充当可见实证。 |
| **E2-02/03 的另一次 A01 回放** `episode02-e2-02-03-live-20260928-a01` | 同样从上述第 27 日 F085 存档和真实回执冷载，但与 A05 是**两个独立 CK3 attempt**。它的画面和 control 只能以本 run marks 配对，不能用它填补 A05 两段 raw 之间的空隙后称连续 A05。 | 两段 1920×1080、各 600 秒 raw：`recording-e2-02-03-a01/raw/e2-pursuit-d27-d32.mkv` SHA `29D11C77ABCE92B79608F5E82E66D3949C08FE30BF6219626E526ECCA5698AAB`；`recording-e2-02-03-a02/raw/e2-pursuit-d29-d32.mkv` SHA `9225EB2CCBB71CD12B5E83C2A5D788C22AE9EBC1A268A4D4611646BBF5BDE1D0`。两段均 `ENCODED_UNREVIEWED`；文件名的 d32 不等于该日拟用画面已有 clean span。 |

A05 追击控制叶值对拍原件在外置 `episode02-a05-vs-004-pursuit-20260928-a02.json`，A05 两段的自动 PTS 审计在 `episode02-terminal-pair-a05-pts-audit-20260928-a03.json`。两份回执均不是可剪画面证书。旧 004/085/024 仅为清楚标注来源的历史研究板；024 的旧 DLL 来源门仍 RED，A05 的新 writer 是本期战分数字的正式原生来源。

## 逐镜头账

| 镜头 | 需要看见的内容 | 当前拟用来源与尚缺的门 |
| --- | --- | --- |
| **E2-01 地图与身份** | 墨西拿 `2633`、WarID `4`、CombatID `16777218`、双方旗帜和战斗面板。 | 优先从 A05/A01 raw 挑同身份开场，逐 run 标记。旧 attempt-005 的 266.4 秒拼接仅是独立回放上下文候选。**缺**原始帧身份/无遮挡核验、clean span、adapter bundle、1× 审看。 |
| **E2-02 追击起算** | 第 28 日 phase、双方人数、败方 soft 池、追击/掩护与逐团预算。 | A05 a01/a02 都有第 28 日 mark 和原生 control；首选 a02 连 E2-03。A05 追击 control 已对拍旧 004，但画面数字和 PTS 边界未审。**缺**A05 专属逐团计算卡来源绑定、clean span、1× 审看。 |
| **E2-03 三日写回** | 第 28→29、29→30、30→31 日逐团 soft/hard；每日重算预算。 | A05 a02 的 control 和截图 mark 覆盖第 28–31 日；旧 004 只作历史交叉核验。**缺**逐帧可见变化与每日 control 的 clean PTS 绑定、A05 数字卡审核、1× 审看；不能把首日损失乘三。 |
| **E2-04 致残事件** | 第 5 日骑士 `34333` 致残，第 6 日有效勇武/61 号团变化，骑士仍在名册。 | 历史 039→040 只作研究。新 `episode02-e2-04-d05-live-20260928-a01` 从第 5 日精确源档冷载，但启动前请求的 `GUI.scale=1.0` 被 CK3 改回 `1.3`，postmap 回执 `PROFILE_SCALE_RED`；该次无正式 raw/clean span，**RED**。**缺**新 attempt 的事件前后人物/战报同轨画面、次帧回执、clean span、1× 审看。 |
| **E2-05 击杀抽签** | 第 26 日 14 人候选、draw/index、击杀者 `34120`、目标 `33437` 死亡脱团和第 27 日名单。 | 历史 020、070、036→038 为分开的研究轨，须分别标注。新 `episode02-e2-05-d26-live-20260928-a01` 已进入冷载流程；截至本账核对时尚无封口 raw、capture report 或 clean span，**不能预记 GREEN**。**缺**本次抽签/次帧回执、人物/名册画面、clean span、1× 审看；070 成长列表 draw 不是 020 的击杀抽签。 |
| **E2-06 增援入场** | 第 11→12 日 ArmyID `22`/13 团加入，旧双方 entry 与缓存残差、新军 starting/current、返回缓存。 | A01 新 trace 有同日 full-entry `count=2` 和 raw 前后 mark；旧 085 仅历史对照。当前 A01 面板下半被裁，尚未审出 ArmyID/13 团和细账的可见区间；内部数值可做标记来源的 A01 计算板，不能声称 UI 已拍全。**缺**完整面板补拍或只取可见上半的受限镜头、clean span、1× 审看。 |
| **E2-07 战宽到出伤** | base `1645→2467`、final `1480→2220`、首次 side0 出伤参数 `2220`。 | 三点由 **A01 自身** private trace 观测；旧 085 是独立复证，旧卡不能直接冒充 A01 同 run 卡。A01 raw 的 UI 裁切仍须逐帧核。**缺**以 A01 trace SHA 重生的来源卡、实际可见战宽 clean span 或明确标为“原生跟踪读数”的画面、1× 审看。 |
| **E2-08 正常终局** | 第 32 日 `normal_result`、winner side0、玩家 ArmyID `18` 败退，结果和 WarID `4` 面板。 | A05 a02 第 32 日 terminal 回执闭合原生结果，有 `d32-writer` 与 `d32-war4-after` 截图 mark；尚未证明结果窗口/撤退路线在 raw 中干净可见。旧 004 第 32 日截图受事件遮挡。**缺**UI clean span、同 run 前后画面审核、1× 审看；称“败后撤退”，不称 AI 主动撤退。 |
| **E2-09 战争账本** | A05 writer 分子 `53662042`、八桶 `0+675+310+0+0+0+11+0=996`、CB 倍率 `15000000`、封顶 `5000000`、进攻方 `-50`。 | **A05 自身**第 32 日 writer 给全套输入、row 与方向；a01 有 WarID `4` 前图 mark，a02 有 writer 与后图 mark，跨的是同一游戏会话的两段 raw，须显式标镜头边界。旧 [E2-09 卡](cards/e2-09-calculation.svg)仍是 024 身份，须为 A05 重生来源卡。**缺**A05 前后 UI 精确 clean PTS、画面可见战分归因审核、A05 数字卡、1× 审看。 |

**剪辑准入**：每个取用镜头登记 `attempt ID + source save/receipt SHA + game build + CombatID/WarID + 原生日期 + raw 媒体 SHA + 精确 clean span PTS + 控制回执 SHA`。跨 attempt、同 attempt 不同 raw 段都须在时间轴标边界；截图/墙钟 mark 只供定位，不能直接作媒体 PTS。每个 clean span 首尾审原始帧、HUD、日期、身份、面板和遮挡，再交 CK3 adapter 只读验证；最终成片另需实际 1× 完整观看并按精确 bytes/SHA 人工签核。非零败方掩护、主动撤退和整场条件胜率仍待研究，不能由上述局部镜头替代。
