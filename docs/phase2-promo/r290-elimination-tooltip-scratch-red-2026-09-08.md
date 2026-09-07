# R290 elimination tooltip scratch RED（2026-09-08）

## 结论

R290 从提交 `82064f6` 构建的 fresh product 成功完成 loader、晚期存档恢复与同 PID reconnect。generation 2 已实机验证动态贪墨者 interrupt 合同；generation 3 随后暴露 `zg361.5` 描述/tooltip 推演会读取尚未提交的 elimination scratch variable，属于真实产品 RED。修复 `12038bd` 已通过静态、回归与可复现发布构建，但必须由 fresh R291 才能升级为 live。

## Fresh product 与启动证据

- 产品投影：`phase2-full-release-r290-82064f6`，共 `1,031` files；product tree / projection manifest / release manifest / ZIP SHA-256 分别为 `813be9e74963988633d2f9f6f11f06e87324db011f51715e83c6b827bcc59b7f` / `480ffc80ccae897b8aba6523a4a31876b9428093ba3c98487d6429f7743be6bf` / `a59795acb16d1d7af55f424c7ac44341ad24762e7871219c151d8d1362740cb6` / `ab6909ac7d1106f927d9d277e8335cae207d073abd602daeaa059ad15a12b7fc`；逐文件 verify GREEN。
- no-launch preflight 位于 `_runtime/p2r290relay/preflight.json`，SHA-256 `E874507AEA337A3140745324B04B4BE20E5DDDB9F42CDD957705C4D0D66E08D5`，状态 `READY_TO_RUN`，未创建 child process。
- warmup PID `53832` 在 `11.057s` 到达 authenticated Frontend 后完整回收。唯一 final PID `165204` 达到 loader `303/303`、fatal `0`、paused/map/mailbox/bridge/player `32904`，restart `0`。

## Generation 2：动态贪墨者合同 live GREEN

- generation 2 在同 PID/restart 下关闭 EP3 决议、debate、chancellor task 与 tribute mission，增量 runtime scan `76` 条、blocking/warning 均为 `0`。
- `secrets.0122` 的 exact-build source 证明 `embezzler` 与 `local_secret_owner` 均来自动态 `secret_owner`，不能冻结为历史角色 ID。合同现只冻结 player-bound aliases；动态 owner 三元组彼此相等且非玩家，exposer 只要求为可选的唯一 Character。全部 identity/type/postcondition 门实机通过并选择 authored/native `3/2`。
- 合同修复已以 `c0e583a` 推送；generation 2 report / diagnostics SHA-256 为 `1A62EF799468BA522BA74FD0FEADF6B222C296A8A2F408DC6B65DF36032F042A` / `433ED3249FC2EE8C3525247E33175F3BB14A288FA33A8534ACCA68825AD9ACFA`。

## Generation 3：`zg361.5` tooltip scratch 产品 RED

- generation 3 exact 关闭贪墨事件与 `epidemic_events.1100` 后，产品在构建 `zg361.5` tooltip/description 时产生 12 条 blocking diagnostics：`zg361_tmp_elim_n` 未设置 3 条，`zg361_purge_score` 未设置或比较无效 9 条。
- 根因是 CK3 对 delayed target event 与 option effect 做推演时会遍历 elimination 逻辑，但不会提交前置 `set_variable`。因此后续 scratch 读取在 tooltip 上下文中不可用；这不是 harness 误报。
- 最小修复把触发 `zg361.5` 的 delayed event 和 option A 内的 AI elimination effect 包入 `hidden_effect`，只隐藏预览推演，不改变实际执行、玩家闸门或淘汰语义。新增 B2 回归后，normal/`-O` 各 `47/47`、local/static validation、release tests `9/9` 与 1,031-file reproducible build 全部 GREEN；release manifest / ZIP SHA-256 为 `7e30721ae0327ccc2616e4e352de75b985e1066d1dbd34369c94da767b29ad6b` / `7b741c885d7bf0cbe41123ffc64cdda9473610c5fe736bedd3469766e8cc709d`。修复已以 `12038bd` 推送。
- generation 3 report / diagnostics SHA-256 为 `333B96B789174E766ACE6AB21A93AF95D80A24EFBF711FA08D4AB156BF056707` / `2F00C38ADF785BFD1CBE1EB4DC47E3E6DBA4B4DDCD5549BA0CBE2AB8BCA69D60`。

## 边界与下一门槛

R290 已通过 session queue 受控停止，final PID 与 injector 槽均归零。B1 新配额 reconciliation 已装载并进入 performance season，但被 `.5` 产品 RED 阻断，尚未到达 calibration，所以 `d4f5120` 仍是 live-pending。T0 `50%`、strict `4/361`、definitions `106/626`、stage `8/11`、T1 `90%`、T2 current horizon `100%`、总体 `67.5%` 及宣传 registry/footage/MP4 `0/4`、`0/8`、`0/2` 均不变。下一门槛是 fresh R291 同时验证 tooltip diagnostics 归零与 B1 calibration 闭环。
