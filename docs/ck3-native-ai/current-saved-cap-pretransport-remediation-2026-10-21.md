# CurrentSaved CAP 提交前门禁整改（2026-10-21）

`machine_id: xenoamess-full-tower-eb9d2c1186`。证据截至 UTC `2026-10-21T13:52:50.450482Z`；闭场观察为 `13:46:29.382952Z`，basis 资格观察为 `13:47:25.462208Z`。来源为本轮真实 A28 请求、闭场及 Driver/SAVE 小型取证回执。

## 实际失败与闭场

A28 的 SEM `11375` 实际返回，postcheck 通过。CAP `11376` 随后在本地门禁中，把原 Queue 写出的 flat 六字段 `INFLIGHT` 误按嵌套 `request` 读取，因而在 transport 前 HALT。CAP 未进入原生调用，没有 FULL、新游戏天数、普通周期或 checkpoint；原请求未重放。

实际闭场为 SDK 退出码 `[1, 0]`、Game forced exit `1`、Game Job 活跃数 `0`、录制 worker `0`；supervisor/display Tasks 已不存在，screen126 于游标8023释放。R0016 为 completed-red，不能作为业务验收通过。累计仍为5143周期、5622天，Driver history5896，下一序号11377。

## 整改与验收

`current_saved_campaign_preflight_v1.py` 采用原 Queue 的单一 flat 六字段 DTO；入口校验必填字段、类型、来源和实际请求文件，再构造内部类型。持久化读取及消费者采用同一合同，无嵌套格式兼容别名。未知结果不得重发的守卫保留。

回归通过真实原 Queue 的 `call`、atomic 写入和 session 路径执行 SEM→CAP→BOUND。完整16项通过、0 skip，其中24个错字段、错类型、错路径及重放条件负例没有新增 transport 调用。basis 15项、cold consumer 9项也通过，合计40项、0 skip。离线消费者修复已经通过，下一场原生 CAP 仍须实机读回。

`current_saved_basis_v1.py` 为本次失败增加独立 v2 epoch；原 v1 业务 basis、失败回执与原始字节保留。实际18个 ref 的消费者校验通过，绑定闭场后的 Driver、原 checkpoint 和 business seed。多个 restore bookkeeping 行按实际 lineage 校验，不把失败记为业务进度。

Root 对实际 Driver 完整读取2次，共85540610字节，包含第一次错误比较后失败的读取。SAVE 正文读取及完整哈希次数均为0：复用旧 canonical 来源 SHA，核对当前 SAVE 的 FileID、大小及 mtime 未变。本轮未重新执行 canonical API，未声称重新校验 SAVE 正文。

八个 Python 文件联合检查 `--strict --strict-equality --explicit-package-bases --follow-imports=silent --no-incremental --cache-dir=NUL` 实际通过，输入前后稳定。扩大到11叶的检查失败，52条诊断位于未修改的 `tools/ck3_live_run_id.py` 和 `root_saved_campaign_preflight.py`；失败回执保留，未压掉诊断。八叶通过不代表全仓库严格类型通过。

修改范围为 basis/testbasis、owner、core/testcore、testcold 六个源码叶；producer、feeder 参加联合类型检查但源码未改。现有 CI 已运行相同八叶类型检查和整个 preflight 测试模块，新测试随本次源码进入。新提交远程 CI 按精确 SHA 另行记录，不预写成功。

G2 仍为6/8，30年仍为5622/10950天；A20 实测活动 FULL 为2.62388555秒/日，含 HOLD 连续墙钟为4.632秒/日，1秒/日目标未完成。Source32 scoped clock 优化已离线资格化，实际吞吐须由后续完整批次验证。A29 使用新 v2 basis 从11377开始，保持同一30年目标和原墙钟起点；本记录不预记 A29 启动或推进成功。

## 证据

下列回执均属于上述机器。根目录 R：

```text
D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/current-saved-cap-pretransport-fix01
```

| R 内文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| ROOT-A28-ACTUAL-CLOSED-NO-BUSINESS-INDEX01.json | 9870 | ff6a1ca415a7e007baa6b5986be8800e3245f61febd958b60bb91d2883a73764 |
| ROOT-A28-CLOSED-DRIVER-SAVE-REVIEW01.json | 4113 | 8a1710900331aabb748db34de074edb0ee08177f33da8a208e364cd298bd3f58 |
| ROOT-A28-CANONICAL-SAVE-IDENTITY-REUSE01.json | 3127 | f6939cdb862af4600dbceb608046ebf18abdaf9a61df60d0cf5e28f088b4465a |
| CURRENT-SAVED-CAP-PRETRANSPORT-FAILURE-EPOCH01.json | 6397 | 716ef3ed10d62380dd458608bc2f1511f8b98fc27505fcb9f7e3aba16cf3f574 |
| CANONICAL-SAVED-BASIS-QUALIFICATION01.json | 2944 | da10ddaee3dcbb97aac9305b6f56bd1b2cfdc6dc8844bb355a875e4fc5e623a5 |
| ROOT-CAPFIX-FINAL-STRICT8-QUALIFICATION01.json | 2771 | 36658cb549e41342715687884804f20d6a8fca75c311ff153fb3fe9c87bf3d2c |
| ROOT-CAPFIX-FINAL-STRICT11-QUALIFICATION01.json | 11243 | bffd8102e446fe0604f2948c4c27847859648e4c2a09980b92d91028d22ee022 |

回归结果来源为本轮实际执行 stdout；上述回执继续绑定原生请求、失败 traceback、原 frozen guard、闭场与 basis 原件。
