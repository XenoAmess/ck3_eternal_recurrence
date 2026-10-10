# Root / bundle 查询的 history 导出优化

`query_campaign_root_context_v1` 的前后两次 snapshot，以及 `query_turn_bundle_v1` 汇总前的一次 snapshot，显式使用已有 `include_native_command_history=False` 入口。前后边界仍独立读取；现有 finite provider、legacy fallback、校验、RPC、修订号和返回结构沿用。

2026-10-11 的唯一新 synthetic compound 实际通过四组、60 项检查。真实旧新 service 方法与现有 NativeHeadless driver snapshot/history 方法连接小型 fake native transport；root / bundle 完整输出、RPC 及修订号一致。root 独立读取两次，bundle 三次；旧 history deepcopy 次数为 2 / 3，优化入口均为 0。拒绝 deepcopy 的 opaque history 在旧入口校准失败，在新入口不可达。完整小型 Driver 对象、opaque 扩展、对象身份和 synthetic 文件字节保持不变；root 修订漂移仍被拒绝。

此次执行显式注入固定旧新 service module。测试文件的默认仓库入口及其 previous-call control 已提供源码，未在本次 compound 中另行运行。可复用命令和边界见 [recipe](../../ck3_autonomous_player/tests/recipes/service_query_history79.json)，测试见 [test_service_query_history79.py](../../ck3_autonomous_player/tests/unit/test_service_query_history79.py)。不依赖保存的外置 baseline 文件来复用默认入口。

实际 FIRST RESULT SHA-256：`19eba54188ba73a85f23e4cf24478085e7962ef3d9a693151a612c107b1541d8`；recipe02：`25154bbd69e73c1248d9119816d3a6ee29b290d48ab4326c3231a09103690918`；执行测试源码：`a1b7dabb81e9346c498dce8029b98e23e8507d337635b77c3a5ca8762cf1815c`；10 的 exact GO：`d54a65586060ea839e82109866b6b7f6d20057c4b37a8bee407a851b689b68ca`。

旧 service 源码 pin：`410320ccd6757ca7be54111296333cc36c215ca5317d7385219a67b1b23399e3`；候选：`c5bea2e72758edc3fc64ea676b7904db7cd886b47980c5563f18efe48afb412d`。原外置 actual 输入与 RESULT 留在逻辑包 `continuation-32/service-query-history79`，按统一存储策略复核；哈希证明历史身份，不能代替已回收原件。

此结果只授予上述 synthetic 功能与 clone 可达性证据。没有读取或哈希真实大 Driver，没有重播旧 QA，也未修改当前 SDK78/R94、Git 或游戏。实机耗时改善与未来 SDK79 接收由后续实际回执分别确认。
