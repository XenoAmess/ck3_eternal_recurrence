# R0037 启动前失败与共享恢复

观察时间：2026-10-28T14:08:02Z；`machine_id: 4-8e1c2f1861`。这是 RRF 续工记录，不授予游戏业务或发布资格。

## 真实失败

R0037／keeper a44 已分配，但启动前容量检查发现 Root 尚未关闭验证登记：`all_shared_regression_writers_closed=false`，独立验证 future 仍为 96 MiB。检查正确拒绝；没有 public run、Steam probe、显示模式变更或 CK3 启动。原 Root wait1、allocator wait0、两 guard wait1／1、keeper wait0 全部已消费，SCREEN 在 sequence 14442 实际释放。

原件位于 `C:/workspace/rrf-development-20261024/review-fixes-a01/retry-cold-R0033-a01`（下称 C7）。原释放为 `metadata/normal-close-a01/R37-resource-close-a01/SCREEN-RELEASE.stdout.json`，1427 B，SHA `6e5a6d9d6b6c491cf62b9e1b5726b1e209857a5e872c1e03e2dc5594dbe40a49`。不把这个约 20 秒的已知退出过程写成 600 秒 idle，不将原始 wait 改成 UNKNOWN。

## 共享修复与实际消费

在既有 `tools/ck3_mod_acceptance_unrun.py` 中，为原 PRELAUNCH 终态增加 `root-serial-prepublic-original-waits-v1` 回执格式。生产者消费原 intent、PID、十进制 FILETIME、argv、退出码、keeper STOP、失败检查及原释放，进入原 reducer 和机器 writer 锁重验路径。历史 Root 外层回执缺少 FILETIME，模型保留 `None`；不从已经退出的 PID 补造身份。此维护属于现存共享验收恢复工具，不新增 Python 生产模块。

真实 R0037 的公共 producer→完整 reducer 预演 a03 原 wait0：

- `C7/metadata/normal-close-a01/R37-unrun/a03/ALLOCATED-UNRUN.actual.json`，13728 B，SHA `ad9973f001646469094993947f0c29422d9fe11be3631579f4f372f4ead7dd46`。
- 返回的 `admin_done.canonical.json`，2660 B，SHA `184ec1de06d59ca0c485786b637cd4396e2276b5e1e2edf1de9a02027eb3164b`，绑定实际 14442 事件。后继消费该返回 Pin；原 raw release 单独保留。

预演不等于后继实际锁内准入。`normal_close_qualified`、`business_pass`、发布资格均为 false。a01 缺少显式 SDK PYTHONPATH、a02 错把完整启动代码 SHA 当正文 SHA 的真实失败均保留；修正实际比较与夹具后才得到 a03。

## 验证范围

`C:/workspace/rrf-development-20261024/recovery-v22` 下新 a02 运行完整原 CI 命令组：

- 共享验收原 92 命令全部执行，946 项测试；89 个命令退出 0，36／48／92 退出 1。原件 `acceptance92/attempt-a02/EXECUTION.actual.json`，24818 B，SHA `73c9b241f7a72cbe3c94c854f7a64aa50300990de10c2f29f067ecaa335320f6`。36、48 为未改的 prepare 历史 Pin（31816/e53b 对实际 37759/6d29），92 为旧 SimpleNamespace 夹具缺少 `prepared_path`；保留基线 RED，不伪称全组通过。
- 本次对应命令 15–18 原 wait 全 0：unrun 47、prelaunch 48、offline 8 项，以及严格类型检查。新增六项回归覆盖真实 producer→完整 consumer→原 OS writer 锁、字段类型、身份与锁内漂移。
- 公共导入原 10 命令及 RRF 五消费者的原命令共 11 个，254 项测试、零 skip、四项静态命令，全部原 wait0。`case10-and-rrf5/attempt-a02/EXECUTION.actual.json`，4391 B，SHA `cdbbdc5d5ed078b4ed095cc6df8df5389edfe01f43184ccc4f6e7bccddceb583`。

静态生产范围为 13 个新增完整 AST 节点，另检查整个修改回归模块；未宣称整个旧 unrun 模块 strict。两叶在整组执行前后字节相同。此前被取消的 a01 前缀保留实际原 wait1，不计作完整命令组。

后继必须先关闭全部实际验证 writer/future，保留 C7 累计花费与原期限，完成新 clean source、state a05、完整容量检查和公共准备，再实际进行冷载及五日业务验证。R0037 没有新增实机截图，也没有更新公开二进制版本。
