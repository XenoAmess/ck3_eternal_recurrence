# R90：道学普通提名已提交，制度后验未验收

2026-10-14（北京时间跨至 10-15）。R90 使用独立 A63 有限容量预约、新鲜 Steam 离线画面与屏幕独占，从 R79 的不可变原儒家存档启动 CK3 1.20.0.4。实际 host 是[修复后的冻结包装器](R90-HOST-BINDING.md)，不是 R89 的旧 `C:/csr19` 宿主；正式候选83文件与 staging 逐件一致。原 `confucian_faith` Faith31、主礼仪道学33、玩家白沙礼仪174、玩家31254、道学推荐候选31763及没有宗主头衔均重新读回。基线和准备两个 cell 为 `complete/qualified=true`。

ROOT 通过正式“议建共同体宗主制度”决议发起本轮，`lyd.430` 选实际原生 index2“待诸方答复”；“封定制度条款、征询诸儒”随后灰显并显示条件不足。通过正式“明确提名自己参与本派代表推举”决议进入 `lyd.410`，选实际原生 index0“我明确赞成所示条款”，白沙自提名后决议灰显。道学31763的一次性普通互动由修复宿主实际进入原生提交路径：返回 `accepted=true`、`dispatch_invoked=true`、`native_queue_result=submitted`，提名回执状态仍为 `pending`、`business_postcondition_verified=false`。这证明 R89 的参数桥接错误已越过，**不证明道学 NPC 接受**，也不能以缓存的名册资格代替接受后验。

随后 ROOT 在制度检查点错误提交了 `request_full_readiness=true`。`lyd_release012_headship_adapter.py` 只允许准备阶段的显式 `observe` 请求此重读；制度阶段的 `ROOT_optional_full_readiness_request` 实际为 `null`。公共 case 因 `ValueError: Full readiness request must be an explicit preparation observe` 保存 RED，未执行后续后验查询、封定、两派三分之二表决、活人同意、签署、建制或36项效果验收。该错误属于本次操作，**不得重试 R90 的一次性提名，也不得给 0.1.2 发布信用**。下一场新准入从 R79 原存档重做，制度检查点仅用合法 `observe` 与实际 G2/G3、原生状态证据确认提交后结果；可请求完整 readiness 的操作只在准备阶段。

退出与资源回收独立合格。ROOT 审阅原始 1920×1080 退出对话框，取消 `autosave_exit`，经带回执的坐标映射单次点击“退出到桌面”；CK3 原进程和宿主退出码均为0，原生 `GREEN/cleanup_ok=true`、公共 `normal_close_qualified=true`，业务仍为 RED。keeper 停止，显示器恢复1024×768，屏幕任务序号5918→5919释放且无资源占用；Steam 末次新截图仍显示离线。只删除与保留来源大小和 SHA-256 均相同的三个存档副本，并将三份原生 JSONL 日志分别无损压缩、校验解压哈希后删除原流；六原件共512,585,239 B，压缩包共5,126,577 B。R90 唯一议案前存档、R79 源存档、原生报告和错误原件保留。四根逻辑量499,909,103 B；加32 MiB余量后的保守 carry 为141,378,882,266 B，低于142,400,773,035 B上限。A63 1.25 GiB 预约于原17:21:44Z期限前闭账、余额归零，容量协调任务序号5920完成。

外置证据根：`A63=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-r90-admission-20261014-063`，`R90=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0090`，`CASE041=C:/workspace/ck3-common-runtime/cases/lyd-release012-headship-resume-20261014-041`。R90 的 `xar_checkpoint.ck3` 为91,608,339 B / SHA-256 `7003b52b1b69602cd1b1520ffaa3403743300114027729699ced80f7a2769f62`；它是议案前保存，不能替代代表接受后的存档。

| 关键回执 | SHA-256 |
| --- | --- |
| `R90/case-output/baseline-cell-result.json` | `39eaf26fb884167214a1e2c574745484e960f20ad18721a4df00ec50f716c198` |
| `R90/case-output/preparation-cell-result.json` | `3bca3ce2c6b5022130cdcd0a690d829971e86f757163d938b114cc81d7044a93` |
| `R90/case-output/release012-institution-0006-nomination-receipt.json` | `13662675b09baa81ca99a900a4fa7345cc551349b6ce34e6b02b4ae9da2b2e85` |
| `R90/case-output/case-error-preserved.json` | `8f9c9ce8183fdc29b073c98878e0d9fef4f840c547a38fc09ef0bef878602366` |
| `R90/case-output/normal-close-result.json` | `651cb63123a63f59733e1b566555e8a1ee0b3fbd48129577dbc7fb0f8261bc07` |
| `R90/native-report.json` | `ee4fba828f1e741563f89a50f55c5960b1f5cd816615191976beb601ed035418` |
| `A63/R90-SCREEN-RELEASE.actual.json` | `19b73b570ac57bb8ad14b21de689a50de7edb83326e628d5c12cb7c850c0b31b` |
| `A63/R90-EXACT-RECLAIM.actual.json` | `2d6a03091681529950a8ff849850f9e89e36cf1ea94776477d50e27d088def4d` |
| `A63/CLOSED-RESERVATION.actual.json` | `6a8e53dfad5baf77e807cff4165800ac144d47485a34e9306f9eb12cea8f0445` |
