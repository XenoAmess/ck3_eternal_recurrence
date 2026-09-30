# 第二期 a04：逐句机制证据与优先补证

本页只记录战争视频的机制证据工作，不把 H3937 等整局自动游玩接口研究计入视频补证。工作树为 `C:/w/e2gold1001`，独立分支 `codex/war-series-brown-gold-20261001`，固定底座 `d81b91be1ae6bf818f38c3c5af0d595dd4ea4752`。遵守用户隔离指令，没有接收新的 master 内容，也没有合入、推送 master。

目标实物为完整六章 a04：`CK3-War-AI-Episode02-Review-20260930-a04.mp4`，240710781 字节，SHA-256 `CB141C63966D86BDC8E267B4D958A79C1BB06A8EF69814DC0D6788F0345B8C7E`。它包含 167 句：开场 10、追击 30、骑士 38、增援 42、终局 37、收束 10。核对实际 timeline 中的每句话、事实引用、原版静态来源、原始回执和实际画面；静态调用链、公式复算、历史实机和本次画面保持不同证据层级。

## 两个优先缺口

| 顺序 | 未闭合部分 | 最小补证与验收 |
| --- | --- | --- |
| 1 | 当前 a02 的骑士 33437 次日状态。最终 trace 失败，没有 d27 该人物生命行、抽选行或冻结存档；旧 020 的死亡标记及存档、036→038 的名单移除不能替代当前 a02。 | 从已冻结 d26 检查点开新 run，前态与次日暂停原生帧绑定 actor/date/revision；推进恰一天后只保存一次 checkpoint，复制成不可变 d27 保存态，严格核对人物 33437 的 alive/dead/death_date/death_reason/killer。保存态证据与 live targeted query 分开报告；旧 a02 UNKNOWN 保持。 |
| 2 | 增援 A01 的原图只与同 run、对应日期相符；缺战宽 tooltip 和 UI 到 hook 瞬间的精确帧绑定。 | 新 run 推进前后两组暂停原图、人数及战宽 tooltip、snapshot/control，绑定同 run/date/native frame/revision/CombatID/参与军队。新读数现场记录，不强迫复现旧 A01。暂停后逐团 current 可能已承受伤亡，不能冒充 join 返回时刻的值。 |

这里 d26/d27 是案例日编号，分别是 **1066-12-30 / 1066-12-31**（raw `53146848 / 53146872`），不是 12 月 26、27 日。现有死亡通告片段从 raw PTS 233 秒起，画面日期为 12 月 30 日，不能充作次日生命状态。

增援旧证据中的 join 入口、返回及首次出伤已齐：同 CombatID `16777218`、ArmyID `22`、日期 raw `53146512`、thread `20844`，旧 side0 27 行及 side1 24 行九字段不变，缓存残差归零；incoming current 合计 2560，战宽 `1480→2220`，首次出伤参数 2220。原图是前日 `893/1603`、后日 `827/4106`；这些事实不证明图像已锁定到 hook 的同一瞬间。

原版 UI 悬停入口已找到：`game/gui/window_combat.gui:646` 使用 `CV_TT_RELATIVE_SOLDIERS`，简中文案 `combat_window_l_simp_chinese.yml:65` 含双方人数及 `GetCombatWidthBreakdown`。现场仍须审阅原始图，并以当前真实尺寸、预览内容矩形和 mapper 回执完成悬停；不能把军队小计数当战宽。

## 当次补采停止事实

2026-10-01 02:38–02:49（Asia/Shanghai）在本机取得独占屏幕任务 `war-evidence-screen-20261001-a01`，claim sequence `3141`。当前本地 MCP `operator_get_capabilities`、`operator_get_status` 实际返回用户 `1`、桌面 `WinSta0\Default`、机器 `DESKTOP-3FEVHD2` 且身份匹配；CK3、injector、录制器进程门为空。

Steam 主窗口当时隐藏，按当前 HWND/PID 语义显示后，原始 1024×768 截图显示 Steam 内容全黑，桌面时钟停在 `23:40 / 2026/9/30`。第一次恢复选区碰到移动窗口，被拒绝且原件保留；第二次正确选区确认 stale，显式 ToDesk 恢复尝试的 `sc stop ToDesk_Service` 返回错误码 5。随后当前随机挑战码可以产生新 GDI 像素，但 Steam 原图仍全黑；窗口可响应、截图新哈希或挑战码变化均不能替代可见的新鲜“离线模式”。

因此没有分配新 live run ID、没有调用游戏 job handoff、没有启动 CK3、没有推进日期或取得新原生/游戏画面。Steam 模式未修改，ToDesk 服务保持原 PID `4792`。屏幕已用 exact CAS `3141→3142` 释放。两项优先缺口仍未关闭，不能写“已补拍”。

当次停止回执永久保留于 `C:/Users/1/ck3-a04-mechanism-evidence-20261001/root-attempt-01/capture-stop.json`，SHA-256 `19D63F862E08DD0696933DC1F69F3F93AC966FA01108668B6F0A30EA2B37E87A`；该文件索引所有恢复失败、原始截图、挑战码、窗口复位及当前 MCP 原件。恢复桌面后先重新取得屏幕租约与当次新鲜 Steam 离线原图，再运行新 operator profile 的实际 capabilities/status/preflight/handoff；禁止复用旧 GO 或旧离线回执。

## 可直接修的制作与引用问题

- `reinforcement-r038` 主图是 12 月 15 日 `827/4106`，旧图注却写前日 `893/1603`；旁边前日图的标签正确，保持。
- `pursuit-p028` 图卡四个 `↔` 在最终视频中显示为空方框；改为字体支持的“对应”，不改机制文案。
- `knights-k035` 旁白说“放大这条中文通告”，旧成片只是整帧实录。新版本给同一 raw 前 2.5 秒加入动态通告放大，保留原始日期、人数和名单；2.5 秒是保守的包装窗口，不是已测通告消失时刻。后段关闭局部放大，不制造冻结帧同当前画面的假绑定。
- 终局六处 facts locator 指向汇总 JSON 不存在的 `terminal/ui_anchors` 根字段，原件实际在 targeted pursuit verification 中；开场 `snapshot.body.active_wars` 的根定位也有笔误。修精确路径，不改口播或数值。

包装配色沿用前两期棕金；配色中间版 a05 已独立媒体审计通过且永久保全，最终制作修订使用新 a06 run。旧 a04/a05、失败 attempt、原始画面及音轨全部保留。任何抽帧、机器检查或 OneDrive 客户端 InSync 均不是完整真人 1× 审片或 signoff。

逐句 JSON、补证输入与实际入口统一落在 [a04 证据目录](../../promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/README.md)。制作与引用修复不提前声称取证闭合。

七处引用已经修正，两个 checked-in catalog 每份都只改 `source_path/source_field_or_line`，回退这两个字段即可还原原对象。对应 key 为 `opening-o002` 第二项 facts 和 `terminal-t003/t004/t005/t014/t015/t037` 第一项 facts；原件各 JSON pointer 已实际解析并核对值。开场 native War4 的实际字段为 `war_objective_province_ids=[2638]`、`primary_opponent_character_id=31549`，旧文案中的字段别名不作为实际键使用。可核验修改明细见 [locator-corrections.json](../../promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/locator-corrections.json)。它修引用，不增加原生观测，也不修改旧 a04/a05 run。

## 实际制作与传输回件

a06 已完成：30:18.633、239659692 字节、SHA-256 `F716D9F4FA79F3471941FF7FC4860A2D8F3D8EA103B73502D5C724609DB598D2`。三处画面修订、七处 catalog 引用和棕金包装分别有精确差异；三块重编、21 块逐字节复用，24 份字幕及 85284 个 AAC packet 保持原 a04 内容与时码。独立全片解码、媒体及有限帧检查通过。

2026-10-01 03:37:37，本次唯一 MP4 的 OneDrive 客户端 InSync=1，目标精确 SHA、全字节 validated 与九项元数据核对通过；没有独立远端回读。新 native manifest 最终包含 272 项素材、1 份自动审计、0 个人工 signoff，文件绑定复验通过。详见 [a06 成片与单文件同步](../../promo/ck3_native_war_ai/episode-02-battle-second-half/series-color-a06-20261001.md)。这些结果只完成制作与客户端同步，不关闭两项实采缺口，也不代替完整真人审片。

## 全 167 句核对完成

[完整索引](../../promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/audit-index.json)已与实际旧a04 timeline核对：167/167，六章分别10/30/38/42/37/10，无漏句、无重复，中文逐字相同，218项主张。索引 SHA-256 `68ADEDC0040666A45CC7873556CA28DE79C5DA94700A53F606DB49E276BC8992`。骑士38/增援42由各自审计表汇入；其余87句由根接手逐句落盘，并核对sameA05原始writer的八桶、动态系数、signed row，追击原始输入pin、静态两遍顺序及原图引用。

164句在其声明的边界内支持；另3句机制有据但存在旧a04制作问题，已在新a06修复。此分母是审计覆盖，不是全部机制能力完成率。两项优先实采仍0次新增观测。

此外，逐句表保留以下范围缺口：每次追击一项hard unavailable（共3），UI内部取数公式未证，非零败方screen无自然同帧逐团实机，分子与硬账差10人当量的成因未闭合；其他CB/特殊部队/资格与枚举生命周期、普通AI主动撤退及完整概率尚未覆盖。本片没有据此作完成声明，后续扩展须分别取证。
