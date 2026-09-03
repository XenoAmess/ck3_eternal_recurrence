# CK3 启动恢复实机证据（2026-09-03）

本记录只收录本日隔离 userdir 的启动边界证据。所有运行均使用 Steam 的 CK3 1.19.0.6（buildid 23530548），没有载入存档、没有执行 gameplay、没有点击协议或通知，也没有访问商店、购买或付款。

## 固定输入

- 可执行文件：`Z:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\ck3.exe`
- EXE SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- bridge：`_runtime/bridge-fresh-release-freeze165b-20260903/xar_ck3_bridge.dll`，SHA-256 `1FBA822831F52D161FD4EEF6A657E48FA11AF98B9CAA706C236C5F41FF184E96`
- 每轮使用独立 profile、完整 `pdx_settings.txt`/account/dlc 与已验证的 DX11 warm shadercache；CK3 启动槽严格串行。早期失败 profile 缺少这些资产，不能与本矩阵的有效启动条件混为一谈。

## 结果矩阵

| 变体 | 实测结果 | 关键证据 | 退出/清理 |
| --- | --- | --- | --- |
| 无 Mod / `-noWorkshop`（冷/不完整 profile 的历史探针） | RED | 在 `ck3+0x1DABD89` 以 `C0000005` 退出；与昨日基线一致 | 隔离进程已清空 |
| 无 Mod / 无 bridge（完整有效 profile） | GREEN | `formal-bare-nomod-20260903`；42.253 秒到达 `Frontend`，`error.log=0` | WM_CLOSE、exit 0、cleanup proven |
| 无 Mod + 当前 Release bridge（完整有效 profile） | GREEN | `formal-currentbridge-bare-20260903`；54.634 秒到达 `Frontend`，bridge hello，`ck3_build_match=true` | WM_CLOSE、exit 0、cleanup proven |
| 无 Mod + RBX guard candidate（完整有效 profile） | GREEN | `formal-guard-on-bare-20260903-r1`；45.582 秒到达 `Frontend`；candidate build 444/444 | WM_CLOSE、exit 0、cleanup proven；未替换 freeze165b |
| 历史 51-file core + 当前 Release bridge | GREEN | `Frontend` 窗口与日志标记，正常进入主菜单边界 | WM_CLOSE、exit 0、cleanup proven |
| core + b1（62 files，7,736,083 bytes） | GREEN | run `formal-phase2-b1-20260903`；PID 58824；12:12:14 `End loading of history`，12:12:18 `Setting idler 'Frontend'`，startup 60.124510s | 12:12:19 WM_CLOSE；exit 0；进程树/控制文件均清空 |
| core + b1 + case-kernel（64 files，7,905,151 bytes） | GREEN | run `formal-phase2-casekernel-20260903`；PID 10072；12:15:30 on_action 881，12:15:35 Frontend，startup 51.023986s；bridge hello | 12:15:41 WM_CLOSE；exit 0；`cleanup_proven=true` |
| core + workforce（152 files，12,906,558 bytes） | RED/未闭合 | run `formal-phase2-workforce-20260903`；12:05:28 到 `Total of : 881` 后约 5 分钟没有 Frontend；缺 shared case-kernel 时出现未知 trigger/effect 级联 | observer 中断后安全回收；原 interim report 无最终字段，独立 evidence 已记录 |
| broad product（279 files，29,351,046 bytes） | RED/未闭合 | 约 350k 脚本行；在 on_action 880/881 后高内存长时间停滞；`error.log` 未见可归因的基础 parse 错误 | 已安全关闭并证明清理 |
| event-core + localization augmentation（162 files，15,060,079 bytes；loc fan-out 仍不完整） | RED/未闭合 | 窗口与 `frontend_main.gui` 曾出现，但没有 `End loading of history`；`Total of : 881` 后静止；error.log 68 行均为 B1/B2/incident/manager 缺失 loc | runner 已 WM_CLOSE、安全清理；不是 CK3 原生 crash |
| event-core + 完整 localization fan-out（261 files，15,924,897 bytes） | RED/未闭合 | `error.log=0`、parser=0，但仍在 `Total of : 881` 后无 database-init/history 进展 | runner 已 WM_CLOSE、安全清理；缺失 loc 已排除 |
| workforce blocks 0–161 + full localization（264 files，12,932,133 bytes） | **启动边界 GREEN / 功能不完整** | 100.574 秒出现 `frontend_main.gui`、`End loading of history`；截断右半导致约 40 行 unknown/missing-bracket 级联错误，不能作为完整功能树 | WM_CLOSE、exit 0、cleanup proven；仅用于负载二分 |
| workforce blocks 162–323 + full localization（264 files，14,282,642 bytes） | **启动边界 GREEN / 功能不完整** | 59.541 秒出现 `frontend_main.gui`、`End loading of history`；截断左半导致缺定义级联错误，不能作为完整功能树 | WM_CLOSE、exit 0、cleanup proven；仅用于负载二分 |

## 当前判断

CK3 本体、Steam 路径、Release bridge、完整 settings/cache 和 Frontend 检测链已经被独立实机证据证明可用；“完全打不开”并非仍然成立。当前剩余 blocker 是 Phase2 broad projection 的完整 workforce 合并（两半同时存在时的体量/跨块组合）与依赖闭包，而不是协议授权门禁或缺失 localization。b1、case-kernel 以及 workforce 左/右半截断闭包均已越过 Frontend，说明可按块级增量合并定位。event-core/full-loc 的停滞发生在 `Total 881` 后且无原生 crash，需继续区分总量阈值与特定大块组合。

下一轮在同一完整 loc/central 基线下验证左右半区的最小组合与四个最大块（3、4、317、318），再按 16-block chunks 二分；每轮只启动一个 CK3，先保存日志、Frontend/history、退出码和清理证据，再释放槽位。任何一轮出现 parser/syntax 错误，只记录可复现的具体符号，不做未经证据支持的全局删改。

## 相关 artifact

- `Z:\ck3_mod_rewrite\_runtime\formal-phase2-b1-20260903\report.json`
- `Z:\ck3_mod_rewrite\_runtime\formal-phase2-casekernel-20260903\report.json`
- `Z:\ck3_mod_rewrite\_runtime\formal-phase2-workforce-20260903\profile\logs\debug.log`
- `Z:\ck3_mod_rewrite\_runtime\formal-phase2-workforce-20260903\profile\logs\error.log`
- `Z:\ck3_mod_rewrite\_runtime\formal-bare-nomod-20260903\report.json`
- `Z:\ck3_mod_rewrite\_runtime\formal-currentbridge-bare-20260903\report.json`
- `Z:\ck3_mod_rewrite\_runtime\formal-guard-on-bare-20260903-r1\report.json`
- `Z:\ck3_mod_rewrite\_runtime\formal-phase2-event-locaug-20260903\report.json`
- `Z:\ck3_mod_rewrite\_runtime\formal-phase2-event-locfull-20260903\report.json`
- `docs/phase2-promo/phase2-group-dependency-scan-2026-09-03.md`

## 30 分钟完整投影轮次（进行中，13:49 起）

应要求将这一轮的 runner watchdog 设为 `1800` 秒（30 分钟）。这只是观测窗口，不是 CK3、Steam 或 Windows 的限制，也没有设置 11 GB 内存上限。轮次使用完整 direct-union-v2、完整 localization fan-out、264 files/15,937,535 bytes，与前面的短超时实验保持相同 EXE、profile、CWD 和单槽规则；不载入存档、不执行 gameplay、不点击协议/通知、不访问商店。

截至 13:52，PID 46160 仍在运行：debug 日志最后一行是 `Total of : 881`（13:49:47），尚未出现 `Frontend` 或 `End loading of history`，`error.log=0`，工作集约 11.0 GB、私有内存约 14.3 GB。runner 每 60 秒记录 marker、内存、退出码和清理状态；若同时观察到 Frontend 与 history 完成，则提前安全收尾，否则保留到 1800 秒并保存最终 report/hash。当前结论仍为 **PENDING**，不能把中途状态称为成功或失败。

### 用户追加：120 分钟续测安排（14:03）

本轮 runner 在进程启动时读取了 `1800` 秒，deadline 不能安全热改；因此不篡改当前 run 的语义。它会先按原定 1800 秒自然收尾并保存证据，随后立即用同一 EXE、source/tree SHA、warm profile、bridge 和参数创建独立的 `formal-phase2-full-exact-7200-20260903` run，`timeout_seconds=7200.0`。续测报告会记录 `parent_run` 指向本轮，便于连续审计；两轮之间不插入其他 CK3 启动。

## 最终收口（2026-09-04 00:04；取代上述 PENDING/续测安排）

- 30 分钟 monolith control 最终 timeout，停在 `Total of : 881`，无 Frontend/history，
  `error.log=0`、exit 1、cleanup proven；report SHA
  `241254233107098CF5F385F1C4472D94CA3E1C8D93D6CFFF869A8C38C0F7A79A`。
  用户随后取消了 7200 秒续测，因此没有创建对应 run。上面的 `PENDING` 与续测文字只保留为当时记录。
- 后续 53-file case-kernel 与 55-file safe-core 均完成 full-entry GREEN；未拆的 58-file B1
  保留一次 1205.343 秒 pre-menu OCR RED。七个 stub 子集和保留 77/77 正文的双文件诊断候选
  均 full-entry GREEN，但不用于认证业务语义。
- 正式 generator 最终按 41/36 个完整定义拆分 B1；两份生成文件重组后与旧 495,777 B monolith
  逐字节一致。正式 59-file / 7,858,254 B 候选 r3 在 exact CK3 1.19.0.6 上以 245.770 秒
  通过 8 个 entry gate、三条 game-state marker、exact mount、material-error 0 与 cleanup。
  formal tree 为 `9EED00504E1AAF34F352B440CFB4DFEBF3BB1206966457834727A81BAB4FC50A`，
  report SHA 为 `22C7ECA8D071812381FC753DF8E6E29CEFB435C6ACFE0EE3D42D3647A1DA3980`。
- 因而 B1 当前是 **startup/full-entry production-candidate GREEN**；这不唯一证明旧 RED 是
  “文件过大”，也不认证 delayed-path、seed、native bridge、完整 Phase2 或 OODA。真实素材仍 0/8，
  两版 MP4 均未生成；G2 按 owner 要求继续暂停。
