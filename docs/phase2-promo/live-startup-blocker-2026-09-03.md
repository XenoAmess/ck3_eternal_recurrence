# 二期实机启动阻点（2026-09-03）

本记录最初记录的是冷/不完整 profile 下的 CK3 启动阻点。截至 12:55 的新实机对照已经把“CK3 完全打不开”纠正为：在显式非空 disposable `-userdir`、完整 profile 资产和 warm DX11 cache 下，CK3 本体与当前 bridge 均能到达 Frontend 并安全退出。剩余阻点属于 Phase2 runtime projection/seed 采集，不是协议授权门禁。

## 已复现事实

| 运行 | 桥接 / mod | 结果 |
|---|---|---|
| Default 桌面最小启动 | 无桥、无 mod | 约 1.3 秒后 `C0000005 @ ck3+0x1DABD89` |
| Default 桌面二期 seed runner | 无启动保护桥 | 同一 `0x1DABD89`，loader/database 尚未出现 |
| Default 桌面二期 seed runner | 四项启动保护 + Cold-Map 只读 observer | 越过上一地址后在 `ck3+0x3BE33A9`（`VFSOpen ` 冷启动错误分支）退出 |
| Sandbox 桌面二期 seed runner | 无桥 | 协议/截图门禁在启动前 typed RED；未产生素材 |
| 有效 warm profile 裸跑 | 无桥、无 mod | 42.253 秒到达 `Frontend`，`error.log=0`，exit `0`，cleanup proven |
| 有效 warm profile + 当前 Release bridge | 当前 bridge | 54.634 秒到达 `Frontend`，bridge hello，exit `0`，cleanup proven |
| 有效 warm profile + RBX guard candidate | RBX candidate | 45.582 秒到达 `Frontend`，exit `0`，cleanup proven；未替换正式 freeze |

所有运行的进程树均已清理；crash dump、exception、session cleanup 和 relay JSON 保存在
`Z:\\ck3_mod_rewrite\\_runtime\\phase2-seed-20260903\\`。当前真实 footage 仍为 `0/8`，两个目标 MP4 均不存在。

## 剩余解锁动作

1. 复用已验证的 warm profile 模板和同一 CK3 `1.19.0.6`（EXE SHA-256
   `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`）及已通过 r3 的正式 B1 generator split，继续验证 delayed-path 与后续全量 projection；未改写 full B1 的唯一 1205.343 秒 RED 继续保留。
2. delayed-path/后续全量门通过后，再原样执行 `run_zg361_phase2_seed_capture.py`，生成新的 canonical seed；旧 seed 合同禁止直接提升。
3. 新 seed 通过 paused/map-ready、PID/generation、事件和 save-checkpoint 校验后，再执行八段 clean capture 和只读 footage intake。
4. intake 完成后再次核对宣传工具 fresh clone（当前已冻结 `origin/main`=`57c42fca13ea459432c1caf76e069a1fbccf602c`），才允许启动两版 TTS、字幕、渲染、审阅和导出。

## 交付口径

两个版本仍是同等优先级的独立最终交付：人物版和制度群像版各自拥有配置、旁白、字幕、候选、审阅、导出和 SHA-256。当前不能给出“已成片”或固定日历时间；从实机启动恢复并取得 8/8 素材后，采集与 intake 约需 `20–40` 分钟，之后每版候选制作约 `45–90` 分钟，另加两轮真人审阅。

## Steam/安装路径判别（06:18）

为区分“绕过 Steam”与“游戏副本路径”两类原因，又用 Steam 库中的原始安装路径
`Z:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\ck3.exe` 做了无 mod、无 bridge、隔离
userdir 的裸启动。该副本与项目参考副本的 EXE SHA-256 相同，仍在约 1.3 秒后以
`C0000005 @ ck3+0x1DABD89` 崩溃；异常与 minidump 保存在
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\steam-library-bare-01\crashes\`。

因此当前证据已排除“仅因使用项目副本”这一解释；冷/不完整 profile 的早期崩溃仍保留为失败证据，但有效 warm profile 已证明启动链可用。不要把旧失败直接外推为当前玩家路径不可用。

## GDPR 参数判别（06:20）

又按 Steam 历史实际命令行补上 `-gdpr-compliant`，使用同一 Steam 库 EXE、`-nographics` 和全新隔离
userdir 启动。参数拼接已在第二次尝试中校正为单一 `-userdir=<path>` 参数；结果仍约 1 秒后
`C0000005 @ ck3+0x1DABD89`。对应 exception/minidump 位于
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\gdpr-bare-02\crashes\`。

这排除了“缺少 GDPR 同意参数”作为单一解释；有效 warm profile 的成功结果表明 profile 资产组合与初始化上下文必须一起记录，不能只切参数作因果结论。

## cwd 判别与转储指令（06:26）

最后做了一次工作目录对照：使用同一 Steam 库 EXE、`-gdpr-compliant`、`-nographics`，但将 cwd 从
`binaries` 改为 Steam 常规的游戏根目录。仍在约 0.8 秒后以 `C0000005 @ ck3+0x1DABD89` 退出，
证据在 `Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\rootcwd-bare-01\crashes\`。

对 minidump 的离线反汇编显示故障指令为 CK3 自身 `.text+0x1DABD89` 的
`movsxd rdi, dword ptr [r14+0x4c]`；异常线程的 `r14` 是小的无效值（本次 `0x7d8`），表明是
游戏内部早期对象/表尚未有效初始化。该证据不指向项目 bridge 或 mod 文件，也不授权修改游戏二进制。

## 图形后端判别（06:31）

使用 Steam 库原始 EXE、游戏根目录 cwd、`-gdpr-compliant`、`-renderer=opengl` 与 `-nographics` 做了最后一次图形路径对照。
结果仍约 1 秒后 `C0000005 @ ck3+0x1DABD89`；exception/minidump 保存在
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\opengl-bare-01\crashes\`。
至此冷/不完整 profile 下的 D3D11、nographics、OpenGL、cwd、GDPR 和安装副本差异均未改变故障地址；随后 warm profile A/B 已成功到 Frontend。启动参数试错收口，后续只复用有效 profile 并定位 Phase2 projection。

## Steam `-applaunch` 入口判别（06:44）

通过当前已运行的 Steam 客户端执行了一次隔离 `-applaunch 1158310`，仍使用历史用户目录的可写副本、`-gdpr-compliant` 和 `-nographics`，未加载 Mod，也未进行任何购买或商店操作。Steam launcher 正常退出，但 20 秒内没有 CK3 子进程，也没有生成新的 crash artifact；因此该入口只是 no-launch harness 结果，后续不再重复同一 Steam 入口试错。

## 历史用户目录副本判别（06:42）

为排除“空 isolated userdir 初始化”因素，将已知有历史运行记录的 `C:\Users\xenoa\Documents\Paradox Interactive\Crusader Kings III` 复制到
`Z:\ck3_mod_rewrite\_runtime\phase2-seed-20260903\userdir-cloned-history-01`，原目录未改动；随后使用 Steam 库原始 EXE、`-gdpr-compliant` 与 `-nographics` 做无 Mod 裸启动。进程约 1.16 秒后仍以
`C0000005 @ ck3+0x1DABD89` 退出，崩溃工件位于该隔离目录的 `crashes\ck3_20260903_064242\`。历史配置/缓存副本没有改变冷 profile 的故障地址，因此不能把问题单独归因于空用户目录；现已用完整 settings/account/dlc 与 warm cache 的 disposable profile 取得成功，后续不再重复同类 userdir 复制试验。

## 12:48–12:55 有效 profile 对照（最新）

- 无 Mod/无 bridge：`Z:\ck3_mod_rewrite\_runtime\bare-nomod-20260903`，42.253 秒到 `Frontend`，`error.log=0`，实际主菜单截图已保存。
- 当前 Release bridge：`Z:\ck3_mod_rewrite\_runtime\formal-currentbridge-bare-20260903\report.json`，54.634 秒，`ck3_build_match=true`，exit `0`、cleanup proven。
- RBX guard candidate：`Z:\ck3_mod_rewrite\_runtime\formal-guard-on-bare-20260903-r1\report.json`，45.582 秒，exit `0`、cleanup proven。

这三轮均没有载入存档、执行 gameplay、点击协议/通知或访问商店，也没有购买/付款动作。它们只闭合“CK3 可启动”的环境门，不代表 Phase2 seed、native evaluator、8/8 素材或双片已完成。

## 30 分钟完整投影实测（已结束；monolith control）

`formal-phase2-full-exact-1800-20260903` 已结束。实际挂载的是未拆分 monolith（264 files，15,937,535 bytes），并非 exact A+B；report SHA-256 为 `241254233107098CF5F385F1C4472D94CA3E1C8D93D6CFFF869A8C38C0F7A79A`。结果为 `timeout`，最后 marker 为 `Total of : 881`，没有 `Frontend` 或 `End loading of history`，`error.log=0`，CK3 exit `1`，cleanup 已证明。它是非拆分 control，不能作为 split 功能通过证据。

B7 workforce stub 的 300 秒轮次同样停在 `Total of : 881`，Frontend/history 均为 false，仍记为 RED。7200 秒续测已取消，不会创建对应 run。后续按 [`phase2-incremental-startup-batch-plan-2026-09-03.md`](phase2-incremental-startup-batch-plan-2026-09-03.md) 执行；第 1 批 `core-current` 已实际启动，并于 15:04:20 同时到达 `Frontend` 与 `End loading of history`。CK3 启动层记为 `STARTUP_GREEN`；整体 runner report 仍为 RED，decision 仅为 observer coverage 的 `heartbeat_not_observed`，而 `error.log` 记录 projection-missing symbols（含 `Unknown effect`/trigger 等）。因此分类为 `STARTUP_GREEN / PARSER-或-PROJECTION_RED`，不能当完整功能 GREEN。旧 `4ff` preflight RED 的 `ck3_launch_attempted=false` 仍是启动前源码配套问题，不计为 CK3 失败。

此前的 workforce 左/右半、旧 BOM 偏移切分、control-exclude 和单块 include 结果只具有负载定位价值（覆盖不完整或边界损坏），不能作为完整功能的 GREEN；BOM 修正后的完整 324-block 对照才是本轮基线。

## 15:45–16:15 修订 checkpoint 实测增量

在同一 c91a1d0、CK3 1.19.0.6、Release bridge、完整 settings/warm shadercache 和独立 userdir 条件下，修订矩阵继续按单槽执行：

- P2 `b2-closure`（64 files）到达 `Frontend` 与 `End loading of history`；首错仍是 B2 到 workforce/incident 的投影缺口。
- P3 `b1+b2-closure`（77 files）到达 history；未见原生早期崩溃，错误仍为后续依赖缺口。
- P4 `callable-core`（66 files）在 `Total of : 881` 停滞，首个明确错误为缺 `zg361_p2c_schedule_m275_runner_requisition_effect`，并伴随 appointment effect 语法块错误。
- P4 的 m275 no-op disposable shim 清除 parser error，但仍在 881 停滞；该 shim 只用于定位，不是生产修复。
- P6 `central-callable`（68 files）已纳入 m275 owner；首错收敛为 6 个 portfolio owner、旧版 `zg361_triggers.txt` 未含 B1 peer triggers，以及 `revoke_court_position` 需要 block 参数。下一轮只在 disposable 副本补这些最小闭包，再做一次 CK3 实测。

这些结果把问题进一步归类为“跨域脚本闭包/整合负载”，而不是 CK3 本体无法启动或单纯文件总大小上限。P2/P3 的 `Frontend/history` 仍只代表启动层越过，因 parser/projection 错误不能晋级为功能完成。

## B1 effect 拆分 full-entry 增量（最新）

| 候选 | 结果 | 耗时 |
|---|---|---:|
| all-stub | full-entry GREEN | 255.113 s |
| left-real | full-entry GREEN | 180.403 s |
| right-real | full-entry GREEN | 178.968 s |
| event-root closure | full-entry GREEN | 181.360 s |
| closure + excluded-A | full-entry GREEN | 193.588 s |
| closure + excluded-B | full-entry GREEN | 184.817 s |
| all-but-76（76/77 真 block） | full-entry GREEN | 171.228 s |
| balanced-files（全部 77 定义、无 stub） | full-entry GREEN | 180.396 s |

`balanced-files` 的每个定义正文与原始 B1 effect 对应 block 逐字节一致，只改变文件布局；候选为 59 files / 7,858,264 B，两份 effect 分别为 255,134 B 与 240,709 B。它证明拆文件方案具备可实施的 full-entry 候选，但未改写的 58-file 单 effect full B1 仍只有一次 1205.343 秒 RED。所有真子集及拆分候选 GREEN 不能通过集合外推变成原始 full B1 GREEN，也不能唯一证明单一根因；下一步是把拆分方案重建为可审阅候选并跑正式 B1/全量功能门，而不是直接跳到 seed。

本轮没有生成 seed 或素材，footage 仍为 `0/8`，两条目标 MP4 均不存在。G2 继续按用户要求暂停；open_kaishek 在这些候选上只提供单 effect 离线 parser smoke，真实正文 validator 仍有 `UNKNOWN_OPCODE`，IR/runtime 均 `SKIPPED`，不构成 CK3 语义或 runtime 认证。

## 正式 generator split 与 r3 收口

正式生成器现输出两个 B1 effect 文件，定义数为 `41 + 36`；完整候选为 **59 files / 7,858,254 B**。77 个定义按原顺序重组后的正文与原始未拆分 effect **exact**，formal tree SHA-256 为 `9EED00504E1AAF34F352B440CFB4DFEBF3BB1206966457834727A81BAB4FC50A`。

- r1/r2：约 0.3 秒即因 probe game-path 配置错误结束，CK3 未启动；分类为 harness/config RED，不是内容、parser 或 CK3 live RED。
- r3：**245.770 s / full-entry GREEN**；8/8 entry gates、3 个 game-state markers、material error 0、cleanup GREEN。

B1 checkpoint 现可记为 **startup/full-entry production-candidate GREEN**，而不是完整业务或 Phase2 complete。delayed-path、seed、生产 OODA、8 段素材与双片仍未完成，footage 保持 `0/8`。原始单文件 full B1 的唯一 1205.343 秒 RED 不被覆盖；正式拆分已成为可实施路径，但尚不能声称根因已被唯一证明。G2 维持 paused。
