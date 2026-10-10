# LYD 本机：共享着色器缓存准备

本包修复新隔离 profile 不继承着色器缓存的准备路径。只授源码、来源校验及复制结果；是否改善启动、是否完成事务诊断及一期业务，仍须新公共入口实机。原 R44/R45 startup RED、根因 UNKNOWN 和一期 NOT_GREEN 不变。

## 源码与实际冻结

公共实现由原作者 `dbbb73de0` 正常 rebase 为 `c22d56141ca5d29a050dbc040fa048e233a2e295` 后推送。16 项针对性测试及真实 R44 来源 key 检查通过；该测试并未验证后续冻结树的完整依赖。

本机 Source06 冻结 `0628e97c09f38687c494f0b2d90db0f0b1d71d8f`，仅对 Source05 增加四个公共 Python 路径，7,906 文件，原 native/host 字节保持。首次快照于05:28:55至05:28:58 UTC实际 exit1、3.662秒：冻结 allocator 缺少 helper 导入的 `previous_session_closure`。错误发生在复制循环之前，seed目录未创建；producer原 `cache_body_read_started=true` 是调用前预设标记，不能当作正文已读的证据。原 RESULT、stderr 和勘误保留在 [execution-001](C:/workspace/ck3_lyd_runtime_20261004/r46-shader-cache-snapshot-execution-20261010-001/RESULT.actual.json)。

最小 Source07 `e8562cc04fae188f73c59ed33215126bb8bca7ac` 以 Source06 为唯一父提交，只带入主仓现有 allocator 的完整闭场守卫及调用，38行新增/3行删除，不改 host/native或业务。该 allocator 精确取自 c22 blob：33,215 B / SHA-256 `2763c2a8721f8ec6b38e4966c10987395cd1458ee889d699c20347abbde18d31`。其余7,905文件copy2并核大小、SHA继承Source06已验证清单；没有新全量ZIP、native编译或全树正文重hash。恢复配方为Source06已验ZIP加该单文件，见 [SOURCE07-BIND](C:/workspace/ck3-common-runtime/20261010-006/SOURCE07-BIND.actual.json)。

本机选定 `C:/csr7` 与 `20261010-006/runtime.local.json`：runtime 2,011 B / `418bb8c97eb27a4e71845c26ddf66a9672a03f79df6cfbb36b460f16c40c5f48`；manifest 5,221 B / `ee5f7821fd66f6729193017bef32c56d9e810d5d996159ec11693aeae8e39bdb`。debug、saved-load后注入、succession只读开关及本机既有Cbr2 native不变。Source06/07是机器输入版本，不是业务验收批次或正式release。

## 实际缓存快照

来源为实际已闭场 R0044，绑定原 frozen argv、prepared、runtime、native-report、host-started、原 host Popen退出、keeper report及CAS4340释放八项原件。失败启动闭场证据不追认为正常退出0。匹配键要求同一游戏EXE、host/native、共同源码核心、77业务文件、配置和已核外层descriptor；只规范化当前profile路径。

修正后的producer002于05:36:24.050492至05:37:17.623736 UTC单次执行成功，53.716秒、exit0。实际3,687文件/143,124,020 B，与选定元数据及cache key `9d57912e010a1dd2a9e1e4abd53ee9fc892912d501e7a3d1eb310ca0bc176a47`一致；源缓存保持只读。快照为派生数据，`startup_qualified=false`、`business_pass=false`。

- [seed manifest](C:/workspace/ck3_lyd_runtime_20261004/r46-shader-cache-seed-20261010-001/manifest.json)：678,234 B / `8d5122c79cf1295c9a22939c143eca3102b50655c56bedf14a64d71094c47c91`。
- [实际结果](C:/workspace/ck3_lyd_runtime_20261004/r46-shader-cache-snapshot-execution-20261010-002/RESULT.actual.json)：4,158 B / `5eb50c97398ae736e289bb1f8a630768ff86c76e35a4e094b0b0c692588caef9`。
- [期限记录](C:/workspace/ck3_lyd_runtime_20261004/r46-shader-cache-snapshot-execution-20261010-002/RETENTION.actual.json)：2,584 B / `ef7f5c08ddf0f01f1e14c559865d85b0fd62b251961ffcd27e9319682d10c72e`。

七天期限继承R44实际闭场，复核到期为2026-10-17T03:03:44.013573Z，复制不续龄。快照、profile和allocator三份副本都计入[本轮唯一4 GiB写入预算](../maintenance/storage-cleanup-2026-10-10.md)，没有新增大型ETW导出。

## 公共准备实际通过

公共 prepare、plan、无 run-context preflight 于05:41:20 UTC前各单次实际exit0；预检为 `READY_FOR_EXISTING_REVIEWED_LAUNCH`、blockers为空，见[三阶段实际回执](C:/workspace/ck3_lyd_runtime_20261004/r46-public-prepare-execution-20261010-003/RESULT.actual.json)。此前wrapper002在公共调用前被额外的MAIN/frozen四文件全等检查拒绝，公共prepare调用次数为0；移除该错误包装层检查后才执行首次公共准备，原拒绝记录保留，未修改公共准入。

C8 `prepared-case.json` 为1,291,909 B / `2f228e9e440cacd05dbbef587d1f9be70d3195c78d303739ef1b566ac6b41e80`，实际缓存准备报告为1,217,508 B / `3b5b7ca74c508a7f828f448fbd77daa32c3e57e3bc12be3d3655d0ea1a7372a1`，3,687文件及上述key保持。业务输入除新增精确 `shader_cache_seed` 引用外，与原draft逐JSON一致：原D2a seed、actor31254、77业务文件、45项有序继承缓存、7个政治字段、事务option和900秒readiness均未改变。

下一步由公共 allocate、审阅后preflight、run、verify消费同一选定版本。尚未启动R46；准备成功不能代替缓存命中、启动改善、加载或业务验收。
