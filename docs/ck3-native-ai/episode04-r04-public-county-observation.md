# R04 公共县进入观察接口

`tools/ck3_mod_acceptance.py` 仍是唯一启动入口。`war-episode04-r10 / r10-common-preparation` 默认只收集零日 readiness；显式提供 `case_inputs.r04_county_entry` 时，随后在同一个公共 `CaseClient` 上执行一次 Move、至多七个精确日和一个末日观察窗口。它不新建 host、SDK、游戏或录制器。正常退出归公共 `Selection.run()`，失败也进入原有正常闭场流程。

该实现将 [R219 交接](../handover/2026-10-20-war-episode04-vacation-handover.md) 中的现有县观察业务和 direct-v2 消费者收敛进仓库。旧外置 wrapper、旧 READY、旧 PID、旧容量及相机信号不作为新场输入。

## 输入与公共调用

保留 readiness 所需的 `plain_configuration`、正常存档来源回执、军队/战争/目标和公共 budgets；在同一个 `case_inputs` 对象内追加：

```json
"r04_county_entry": {
  "scene_root": "<新场景目录>",
  "capacity_admission": {"path": "<新 Root 容量回执>", "bytes": 1234, "sha256": "<实际 SHA-256>"},
  "expected_source_save_sha256": "<实际正常 S0 SHA-256>",
  "expected_start_date_raw": 53147376,
  "origin_province": 1506,
  "target_province": 1513,
  "actor_id": 33388,
  "army_id": 0,
  "native_carmy_id": 0,
  "capture_after_days": 6,
  "max_days": 7,
  "driver_limit_bytes": 1073741824,
  "profile_limit_bytes": 805306368,
  "deadline_utc": "<新 Root 时限>",
  "camera_timeout_seconds": 900,
  "prefix": "<本场唯一命名空间>"
}
```

数值展示 R219 同类七日场的形状；真实 S0、ID、限额、时限及路径必须来自当次绑定。源码不固定机器、盘符或某次存档。`max_days` 必须等于 `capture_after_days + 1`，且不超过 7。默认正常退出预留 900 秒、清理保存 120 秒、单日超时 120 秒；可选预算字段直接沿用已有 ObservationIO 合同。

```text
<runtime-python> -B -X utf8 tools/ck3_mod_acceptance.py prepare --runtime <runtime.json> --products tools/ck3_mod_acceptance_r10_products.json --product war-episode04-r10 --case r10-common-preparation --case-inputs <新 inputs.json> --prepare-output <新 prepared>
<runtime-python> -B -X utf8 tools/ck3_mod_acceptance.py plan --runtime <runtime.json> --products tools/ck3_mod_acceptance_r10_products.json --product war-episode04-r10 --case r10-common-preparation --prepared-case <新 prepared/prepared-case.json>
```

实际 `allocate` 取得新 `ready-context.json` 后，再用相同参数加 `--run-context <当次已审阅 context>` 执行公共 `preflight / run / verify`。按 [公共消费顺序](../ck3-mod-upgrade-fast-validation.md#当前公共cli与本机共同版本) 补齐 keeper、离线画面和 launcher 绑定；本接口没有另一份 county CLI。

## 分盘、相机与失败后验

已分配场的公共 preflight 校验新 Root cap 的机器、run、source、scene、profile、Driver、限额与有效期；运行时再核实际 retained OS handle、PID、创建时间、原 hold、控制文件和原正常 S0 启动链。精确 cap 可以授权不同卷上的根目录；路径位于同一场景父目录不单独授予权限。

profile 用量包含 `component_additional_roots.profile`。嵌套及重复根先合并，再按文件路径去重；它与 Driver 分别受各自上限约束。计量只读取目录元数据，不读取存档等大文件正文，也不遍历共同父目录。

正式录制配置必须在推进前绑定这组固定路径：

```text
camera_output_name = case-output
camera_awaiting = <LIVE>/case-output/before-action-camera-awaiting.json
camera_signal = <LIVE>/case-output/before-action-camera-started.json
observer_result = <LIVE>/case-output/R04-BAYEUX-TERMINAL.json
```

公共 `window_take.TakeSpec` 在构造期拒绝 `before-entry-window-*` 等别名。相机仍由既有 `window_take_actor.py` 准备原始帧、直接审图和唯一 Start；它必须绑定同一新现场。六个准备日与 Move 不录制。末日完整 baseline 和自然采样 ON 的原生读回完成后，actor 发布 awaiting；只有真实 canonical Start 回执及 process-ready 精确 pin 被消费后才允许第七日。Start ACK 不授予画面质量或业务资格。

每个精确日通过时立即更新 `actual_days` 与逐日证据，然后才进入下一次可能失败的准备。第七日前相机超时因此保留已完成六日；未知单日结果不补计、不重 Arm。公共 `verify` 独立读取同机器、同 run 的 terminal，失败也呈现已完成天数；原件缺失时显示 `actual_days=null`。Move 只提交一次，未知结果只做独立后验。观察的 finally 保留暂停/原时钟收束、采样 OFF/clear 和一次正常 Save；公共入口继续负责正常退出。摘要与窗口事实分别保留，单个 direct-owner 阳性也不授予整军总损耗或 R04 整卡完成。

## 本轮离线验证

`machine_id: desktop-3fevhd2-1c74096080`；观察时间 2026-10-20T02:18–02:22Z。来源为主树 `python -B -X utf8 tools/test_r04_county_entry.py` 的实际执行回执：六项 focused synthetic 回归通过，覆盖公共 hook/七日合同、终端回读保留六日及缺失/跨 run 拒绝、六日后超时、不重投未知单日、额外 profile 去重/独立上限、分盘精确身份及旧 marker/路径逃逸拒绝。`open_kaishek: not-applicable`，因为本次修改为 Python 路径/元数据/调用顺序，没有可由 CK3 脚本 parser 或有限运行时覆盖的脚本语义。该离线结果不代表新实机、录像或正常退出通过。
