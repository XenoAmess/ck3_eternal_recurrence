# 正常前驱的原写锁重验（2026-10-27）

machine_id: `4-8e1c2f1861`；观察时间 `2026-10-27T12:06:49.729686+00:00`。来源为下列外置原始回执，不代表其他机器。

正常 `previous-shared-managed-session` 原先只在分配前检查原生清理；原 `chain.lock` 内没有重跑正常前驱 reducer。现在锁内重新消费真实 native-cleanup/projection、`previous_session_closure`、keeper、原释放 Pin、新鲜屏幕状态及进程清单，并核 run、machine、路径和 latest chain。任一变化都在新场次 intent、ID、SCREEN 注册及 keeper 启动前拒绝。已有 projection 路线保持不读取大 native-report body。

`claim_machine_admission` 对原 writer 使用窄 Protocol 和真实同目录模块，Prepared 路径先验证再封包；未另造 attempt 状态转换实现。此时没有启动新游戏或实际本机 allocator，锁内实机消费仍待后续公共运行。

## 实际验证范围

执行身份为基于 `32b9db8717a42e0acbb219cf7d1f1c38eebcc612` 的 `SCOPED_WORKING_TREE`，两维护文件执行前后相同；不能追认为本说明未来提交的 clean 执行。

- 四个完整模块 adapters、bootstrap、native_projection、pre_identity：51 tests，失败0、错误0、跳过0。
- 完整新增 evidence Protocol/helper 与完整修改的 claim/writer Protocol：分别严格类型检查通过。导入的旧 callee body 不因此获得严格检查信用。
- 额外完整 allocator 非严格检查仍有20处存量错误，位于本次修改以外。其原退出1单独保留；未列入六条 PASS 资格命令，没有整个模块、完整 CI 或游戏通过结论。
- 回归在真实 `allocate_and_keep` 和原机器写锁入口改变 native、keeper、释放、run/machine、屏幕、进程及 projection，验证拒绝且不创建新 intent/ID/注册/keeper。

首轮 tamper 夹具误用只许新建的写函数造成6个错误，后续 typed writer 错选白名单 peer 又造成原入口错误；修复为测试临时文件覆盖和原 keeper import 后重跑完整模块。所有失败保留。首轮 bootstrap 子进程21848的原 wait 未取得，保持 UNKNOWN/null；stdout 与进程已消失不能授予退出0。

## 原件

外置根 `C:/workspace/rrf-development-20261024/review-fixes-a01/review-validation-a17`，已关闭未来写入，不再续写。

| 原件 | 字节 / SHA-256 |
| --- | --- |
| `metadata/qualification-a01/COMMAND_VALIDATION.actual.json` | 10148 / `f155f10d6e3d48b91f5f1d30eaaaa1a0d7eaf6bbd3556bd49a7963c08d855c10` |
| `metadata/validation-a04/EXECUTION.actual.json` | 3483 / `5a0579abb3084968b732c1a0f7f58f4d2b008633f1becba5657ed219706cd6ba` |
| `metadata/validation-a01/CLOSED.actual.json` | 11395 / `b6108c515895f2472e86d9b5b3dd6df724350d4924acdd075ba81ada47f9e6f2` |

最终累计占用851968B，容量采样峰1093632B；后者不是连续峰值。旧 C4 的准备包、15Z期限和全部历史实耗保留，新来源须另建 P2、六链资格与 Prepared，不能修改原冻结包追认修复。
