# R10 独立 A 的公共入口

`tools/ck3_mod_acceptance_r10_arm_products.json` 新增 `war-episode04-r10 / r10-independent-a`，使用明确的 `xar.e04.r10-independent-a-case.v1`。原 `r10-common-arm` 与联合 PLAN 的 B/C、两站和费用门槛保持原语义。这里复用现有 `strategy_a.admit/update/report`，不创建第二个 host、SDK 或时钟。

本机来源记录为 `desktop-3fevhd2-1c74096080`；实际源小索引见 [source-spec](acceptance/2026-10-18-r10-independent-a/actual-source-spec.json)。R206 早期正常 S0 是 72,572,514 B、SHA `aaf7cfc4fef4f22d28ae7d174ffc6642bc586449a3fae9d51b0ba6a45ddb65da`，actor33388、Army0/CArmy0、raw53147376、1506、route[]；历史记录不授新机器安装、容量或实机资格。Army ID 0 合法。目标 1513 仍须本次原生 preview 完整可达，不能据历史目标补一条路线。

## 两个显式阶段

`arm.phase=collect-baseline` 只允许 `baseline`、`finish`。它在同一帧采完整 Army/DATA、统帅、现金、loaded features 和原生 preview，记录完整原 cohort。0 Move、0自然日；终场沿原 CommonArmIO 的一次正常 Save，再由公共 runner 等 Root GUI Quit。采集状态不算正式臂。未采完整基线时不填合成 wallet、统帅、特征或路径。

`tools/ck3_r10_a_inputs.py freeze` 仅读实际 capture/原 pins，冻结 T0、cohort、直达路线、到场状态、事件政策和90日上界。随后必须新分配、独立冷载同一正常 S0；`arm.phase=execute` 比较完整 cold observable baseline，实际进程出生须晚于 freeze，再调用原 A-only admission。原采集 PID 中不能转成执行臂。

执行阶段为 `baseline → Move-once → Move-post → advance（每次一个精确自然日）→ finish`。Move 有 durable once claim，未知结果不重投；独立 post 才能证明完整 target/route。每天保留真实 +24/1tick/overshoot0 与 full 原件。到场须省份、允许状态、route[]、targetnull同时满足；事前固定 `follow_after_arrival_to_day90=false` 时实际到场可结束，只有真实第90日未到才可 budget-censored。中断仍沿原 `ObservationIO.handle_modals` 和原 generation 续行。

## 真实调用

先由公共 runtime/native scope review 与 Root 容量 owner 产生本场实际 runtime/capacity。该来源 spec 不是游戏容量采用。以下 CLI 只绑定元数据或写 Root stage mailbox，不调用 SDK：

```text
python -B tools/ck3_r10_a_inputs.py bind --spec <本机actual-source-spec.json> --runtime <本场runtime.local.json> --capacity <Root实际cap.json> --scene <全新scene> --output <全新C绑定目录>
```

生成的 `PUBLIC-PREPARE-ARGV.json` 内有完整公共 `prepare`、`plan` argv，产品和新 case 已写定。后续仍用原 `allocate → actual READY → fresh Steam review → preflight → run`，每一步带该次 `--prepared-case`。不猜 run 编号；不把旧 launcher ACK 或 readiness pilot 当成新冷场。

采集完成的小状态在 actual run 的 `case-output/r10-A/arm-a-0000/baseline.actual.json`（若 Root 先做了其它合法阶段，以实际 stage-result pin 为准）。冻结与新执行绑定：

```text
python -B tools/ck3_r10_a_inputs.py freeze --capture <actual baseline.actual.json> --evidence-root <同一实际证据根> --output <新A.frozen.json>
python -B tools/ck3_r10_a_inputs.py bind --spec <同一actual-source-spec.json> --runtime <新独立场runtime> --capacity <新场Rootcap> --scene <新scene> --frozen-plan <A.frozen.json> --output <新绑定目录>
```

每个 `r10-A-stage-NNNN-awaiting.json` 出现后，Root 可先预览再写一次响应：

```text
python -B tools/ck3_r10_a_inputs.py stage --awaiting <actual awaiting.json> --stage baseline
python -B tools/ck3_r10_a_inputs.py stage --awaiting <同一actual awaiting.json> --stage baseline --write
```

该工具从原 awaiting 复制实际 run、machine、reviewer，不注册新通道。响应一旦存在不覆写。B/C 的 `stage` 也仅写原公共邮箱，B role Move 必须另给实际 `--army-id`，recovery 必须给原 `--day-start-raw`，不重新 Arm。B/C `bind --label B|C` 仍要求完整冻结联合 PLAN；没有两份真实正库存站点时立即拒绝，不制造可执行 B fixture。

## 结果与预算边界

独立 A 默认不比较费用，也不授 joint ABC、winner 或 causal ledger 资格；`A_only_report` 保留原 A 的实际抵达/未到场状态。R206→1513 的 A 不能充作另一个 Mar31 S0 的 A。联合比较仍需同 S0/source/DLL 的三独立冷场、完整 B两站/Cwaypoints/费用和物理归因原件。

Root 需在 `min(original hold, capacity deadline)` 前至少预留 normal-close900+cleanup120秒；现有 stage mailbox300/IO guard180不是这1020秒的替代。`maximum_stages=96` 足以 baseline、一次Move及post、90日与finish，未知事件/额外策略决定须保留真实测量停止。每整军日显式请求至少16条/2份full，额外 wait/modal/rebound另计；90日 A 下界1468条/183份full，wire/normalized/envelope多副本和正常保存/录像独立预算。容量不足即保原件正常退出，不以sourcepool授游戏写入。

一个 compound 用 native-shaped synthetic fixture 实际调用生产 baseline 和原 A admission，同时确认采集阶段拒Move、stale preview拒绝、B0联合PLAN仍拒绝。它证明 Python 合同，不证明新实机正式 A 成功。实际源/测试边界见 [intake](acceptance/2026-10-18-r10-independent-a/input-intake.actual.json) 与 [compound](acceptance/2026-10-18-r10-independent-a/source-compound.actual.json)。
