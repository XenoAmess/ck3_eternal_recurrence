# R289 B1 calibration 前配额漂移

状态：**产品 RED 已定位；最小修复 `d4f5120` 已推送并达到 `static-ready`；等待 fresh R290 实机验证。**

## 现场与结论

- R289 generation 18 从不可变 episode seed `0d1095…dbcb1c` 继续运行，在 5,000 个产品观测日上限内始终保持 `b1_active=true`、`review_now=false`，没有抵达 `.146/.147`。
- `ZG361B1: exact quota bank closed` 后，冻结配额仍为 top/middle/bottom `8/16/2`，合计 `26`；进入 calibration 闭环时，满足当前 manager/cycle/case、state `5`、active、roster、grade 与 calibration score 的 durable rows 只有 `8/15/2`，合计 `25`。
- `zg361_b1_prune_unavailable_subjects_effect` 没有记录弱引用清理；因此这不是仅靠延长 harness 观察窗或再次清理 dead weak scope 能解决的问题。旧逻辑没有在 calibration 第一个消费者之前复核“有效 exact tuples 与冻结配额相等”，导致 conservation gate 永久等待不存在的第 26 行。

关键 live 标记位于保留 profile 的 `logs/debug.log`：performance season opened、facts frozen、quota bank closed、D340 watchdog recovered，随后 closure gate 持续为 `closure=0 / calibration_finalized=0 / quota_valid=0`，并稳定显示实际 `8/15/2` 对目标 `8/16/2`。

## 修复边界

新增 `zg361_b1_reconcile_pre_calibration_quota_effect`，并在 `zg361_b1_open_calibration_effect` 的 conflict/consumer 链之前调用：

1. 先执行既有 unavailable subject prune。
2. 只计数当前 manager/cycle/case 的完整 state-5 live tuples，并分别核对 top/middle/bottom 与合计数。
3. 配额完全一致时不改变既有 local 或 pooled book。
4. 仅在任一精确计数不一致时记录 mismatch/fallback receipt，放弃本 manager 的陈旧 pool membership，并调用既有 canonical local allocator 重建当前 book。

此修复不放宽 B1 conservation、identity、case-state 或 closure 条件，也不通过延长 5,000-day 产品观察窗隐藏 liveness RED。

## 证据

- generation 18 retained runtime diagnostics：1,911 bytes，SHA-256 `29101A380CED7D0FE392736F9BC5BD4FD89F9F596744E336B39F956C18F6DC38`
- product entry evidence：25,308 bytes，SHA-256 `3EBC54E66A63CD2534290B8D02E25FC382D32947A85EB96169742B3C89A7C656`
- report：36,098 bytes，SHA-256 `9A7C686E680E97D5436EB3B114DCAAB6AFD4FCA924A3C36376132661096ED005`
- B1 generator `--check` GREEN；normal/`-O` 各 `75/75` GREEN；`validate_local.py` 与 `validate_static.py` GREEN。
- release tests `9/9` GREEN；1,031-file reproducible build manifest/ZIP 为 `583AD54E…05D8` / `AB6909AC…B7FC`。
- 修复提交：`d4f5120`，已推送 `origin/master`。

## Readiness 与下一门槛

当前只标记为 `static-ready`。R289 PID `122132` 加载的是旧产品树，且已经耗尽该 seed 的产品观察边界，不能作为本修复的 live 证据。必须受控回收 R289，在进程槽清空后以 `d4f5120` 或更新 HEAD 物化 fresh R290，并验证：reconciliation 标记只在实际漂移时出现、配额变为 exact、closure/finalization 完成、`.146/.147` 可达且 runtime blocking diagnostic 为零。

本轮没有增加 strict scene、full-tree stage 或宣传素材计数：T0 `50%`、strict `4/361`、definitions `106/626`、stage `8/11`、T1 `90%`、T2 current horizon `100%`、总体 `67.5%`；T0-P2 继续 `LOCKED`。
