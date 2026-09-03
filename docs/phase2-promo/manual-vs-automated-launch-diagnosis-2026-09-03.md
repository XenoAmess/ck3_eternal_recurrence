# CK3 手动启动与自动采集启动差异诊断（2026-09-03）

## 结论先行

此前把“CK3 能打开”与“Phase2 自动采集链能达到 loader/native readiness”混成了同一件事，表述不准确。到本记录时间为止，最可靠的结论是：

- **正常玩家启动链仍然可用。** 2026-09-03 08:19–08:22（Asia/Shanghai）从 Steam → Dowser → Paradox Launcher → CK3 启动，CK3 到达 Frontend，Steam 记录进程退出码 `0`，`system.log` 记录了完整图形初始化和数据库启动。
- **自动采集链失败的是另一条路径。** 它直接创建 `ck3.exe`，使用隔离 `-userdir`，经常带 `-loadsave`/`-continuelastsave`，并在部分运行中使用挂起创建、bridge/observer/guard 和受控桌面。昨晚多数运行其实到过 `Frontend`/`In Game`，失败发生在 bridge/采集器收尾；今晨另有无 mod/无 bridge 裸跑在 CK3 pre-loader 崩溃。无论哪一种，都尚未产生可用的 Phase2 seed/footage。
- **“昨晚突然坏了”不是已证实的游戏更新或 mod 损坏。** Steam 的 CK3 `buildid=23530548`、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，以及 Steam 安装目录与项目参考副本的文件树均未发生对应变化。
- **单一根因尚未闭合。** 当前最有证据的类别是“启动链/执行上下文不同”：完整 Launcher handoff、session token、真实 Documents profile、图形初始化、窗口站/桌面和受控进程创建时序，与自动化的 direct/isolated/suspended 路径同时发生变化。不能把其中任一项单独宣布为根因。

## 时间线与证据

| 时间（Asia/Shanghai） | 路径 | 结果 | 解释边界 |
|---|---|---|---|
| 9 月 2 日 16:40–18:29 | 轻量 direct `ck3.exe` 探针；多为无存档参数 | 多次进程级 exit `0` | 证明探针能启动并被 runner 收尾，不等于完整玩家前端或 native readiness |
| 9 月 2 日 18:32–9 月 3 日 01:41 | 实际 evaluator/capture；隔离 profile，常带 `-loadsave`/`-continuelastsave`，部分带 bridge/debug | runner 多记为 exit `1`，但多份 per-run `debug.log` 已到 `Frontend`/`In Game`；异常落在 `xar_ck3_bridge.dll!XarCk3BridgeStop` 收尾路径 | 这是日志里第一个清楚的“工作形态切换”点；**不能把这些 exit `1` 直接解释成 CK3 没启动**。它们主要说明采集/bridge 收尾失败；参数相关性不是因果证明 |
| 9 月 3 日约 05:46 | 无 mod、无 bridge 的裸 direct 启动 | 在 CK3 早期 pre-loader 以 `C0000005 @ ck3+0x1DABD89` 退出 | 这是目前最早有明确证据的“真正未到 Frontend”失败；它与昨晚多数 capture 的 cleanup RED 是两个层次的问题 |
| 9 月 3 日 08:19–08:22 | Steam → Dowser → Paradox Launcher → CK3；无自定义 `-userdir`、无 bridge | 到 Frontend，exit `0` | 这是当前“玩家可玩启动”正证据 |

9 月 3 日 08:19 左右 Paradox Launcher 从 `2026.11-rc` 更新到 `2026.11-rc.1`，随后正常 Launcher 链成功启动 CK3。因此该更新发生在失败尝试之后且紧接着成功，不能作为“导致 CK3 不能打开”的证据。9 月 2 日的 Steam 客户端更新也同时覆盖了成功和失败运行，不能单独归因。

## 为什么先前会看起来“可以打开”

先前的成功记录混合了三种不同强度的结果：

1. **真正的玩家路径成功**：完整 Steam/Paradox handoff、普通交互桌面和真实用户目录，确实能到主界面。
2. **自动 runner 的进程级成功**：runner 观察到足够的启动进展后主动收尾，Steam 因而记为 exit `0`；这不是“视频所需的 8 段 clean span 已可采集”。
3. **较早 exact-build managed 成功边界**：某些旧 freeze 在同一 EXE 上曾到过 `database_init` 或 producer 回调，但仍未达到完整 native readiness；不能直接外推到当前 freeze/当前桌面。

昨晚 Phase2 从“探针/研究”切换为“加载 checkpoint、注入只读观测、等待 seed/事件/业务后置条件和视频素材”的生产采集链后，所需条件明显更严格，runner 的失败状态也更容易被看见。更准确地说，昨晚相当一部分运行已经打开了 CK3，只是 bridge/采集器在停止阶段失败；真正的早期裸启动崩溃是在今晨约 05:46 才被单独复现。这个时间点解释了观感上的突变，但不证明某个单独参数把游戏弄坏了。

### 对“昨晚打不开”的更正

我之前把 runner 的 exit `1` 和“CK3 没有打开”画了等号，这是一次过度概括。判断“打开”至少要分成三层：进程是否创建、是否到达 Frontend/In Game、以及 Phase2 是否完成 native readiness 和可录制素材。昨晚的 capture 多数通过了第二层但没有通过采集链收尾；今晨 05:46 的裸跑才是第一层之后、Frontend 之前的崩溃。反过来，历史上也有少量 direct managed run 在同一 RVA 失败，所以“之前一直能开”同样不是所有自动化形态都成功，而是不同启动路径和验收层级被混在了一句话里。

## 已排除与仍未排除

### 已有证据排除

- CK3 depot 在昨夜没有更新；两个安装树的文件数、关键二进制和 EXE SHA 一致。
- 失败并不需要 Phase2 mod 或 bridge：无 mod、无 bridge 的 direct probe 也在同一早期 CK3 RVA `0x1DABD89` 复现过。
- `-noWorkshop`、`-gdpr-compliant`、不同 CWD、`-nographics`/OpenGL，以及两种 `userdir` 参数形式都没有单独解除故障。

### 尚未唯一定位

- 完整 Steam/Paradox session handoff（包括 Launcher 传给 CK3 的会话上下文）与 direct `ck3.exe` 的差异；
- 普通 `WinSta0\\Default` 与 Codex sandbox desktop 的差异；
- 真实 Documents profile、隔离 profile、图形/窗口初始化和挂起注入时序的组合差异；
- 当前 exact source/freeze 与旧成功 freeze 的启动前状态差异。

## 下一项最小验证

不再重复同一 sandbox 形态的启动。下一次 CK3 串行实验应在真实交互 `xenoa / WinSta0\\Default` 环境中，固定 EXE、source、profile、CWD 和参数，先做无 mod/无 bridge 的 A/B；随后才做带 bridge 的 Phase2 seed。若需要保留完整 Steam/Paradox handoff，则另做 launcher-aware capture，并把 session 参数视为输入证据而不是隐式假设。

在上述 A/B 之前，Phase2 的真实素材计数保持 `0/8`，两条最终视频保持未生成；这不是因为玩家无法启动 CK3，而是因为自动采集链尚未通过其生产级启动门。
