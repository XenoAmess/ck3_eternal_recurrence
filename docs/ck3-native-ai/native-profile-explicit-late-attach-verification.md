# 原生 Profile 首次加载超时后的显式 attach 晚验证

R0019 首次 attach 在原生状态尚不可用时返回 RED，但 injector 已 exit0，完整进程树回收已证明，原 Python driver、pipe 和 DLL 连接仍保留。后续只读 snapshot 在同 PID/session/gen1 上读到真实暂停地图；旧服务仍缓存首次 RED，导致普通业务不能进入。这两项实际回执分别保留，后续可用状态不改变首次失败事实。

## 生产入口与范围

入口沿用 `ck3_attach_profile_bridge_v1`，参数仍为 `{}`；没有新增工具或自动重试。显式再次调用只在原 RED 的原因精确为 `BridgeUnavailableError: native game state is not available yet; CK3 may still be loading or may not have entered a map`、原 injector `returncode=0` 且 `complete_process_tree_proven=true`、原 driver 仍存在且 profile 为 1.20.0.3 时进入晚验证。其他缓存结果沿原路径返回。

晚验证读取当前 guard 和原生时钟，核原失败回执/attach claim、injector 的原 pipe/PID/DLL 参数和冻结产物 SHA。原 driver/state/endpoint 必须仍属该 pipe，连接须为原 generation1；snapshot 仍调用已有身份校验，要求精确 .3 adapter/build、地图 ready、暂停、date/speed 与前后新鲜时钟一致。该路径不调用 injector、factory、reconnect 或游戏 action，也不等待循环。未知、漂移或不同连接返回新的 RED，原失败缓存和文件保留。

成功只追加新的 `attach-late-verification` 回执，沿用既有状态 `attached_snapshot_verified`。回执包含原 RED 的 path/bytes/SHA、前后实际 guard/clock、真实 snapshot、generation1，以及 `reinjected=false`/`reconnected=false`；服务随后缓存这个新结果。原失败回执、claim 和历史 SDK 结果不改。进程重启后的 resume 合同未由此修订。

实现见 [生产服务](../../tools/ck3_native_profile_mcp.py) 与 [服务测试](../../tools/test_ck3_native_profile_mcp.py)。两个新增 focused case 覆盖初始缺状态超时后晚验证成功且不再注入，以及 unknown/different clock/unpaused/speed unknown 继续 RED；本次服务类共 11 tests exit0。另以模拟对象验证 class replacement 不改变实例字典、原 driver/state/endpoint 或注入次数。测试均使用模拟 backend，没有 CK3、SDK 或 debugger 操作。测试夹具的两次先行失败分别保留；没有改写为通过。

## R0019 实际截止：2026-10-07 04:48:31 UTC

- 原运行来源为 clean HEAD `465595b67efa8f72dfc97bc0de218302c75e3bfd`，export `C:/lr19s1`。晚验证生产候选在独立工作树 `C:/lci18w1` 的文档合并 HEAD `2bcd5e4e34a958ffbb2166b4dbf067fc3de158e0` 上准备；两项生产源码 preimage 与 465 逐字节一致。该 Python overlay 与原 compiled native/source qualification 分列，不冒充原 build 的源码。
- ROOT 通过标准 Microsoft debugpy/DAP 仅连接原 Python MCP server `10744`，在 `04:48:14.982560Z` 显式替换 service 类。service/driver/state/endpoint/lock/原 `_attach_result` 六项对象 ID 全部保持，原 cache 仍为 RED，SDK/native calls 均为 0。候选 SHA 为 `7abbe35ac90dd5cc9af35d95198eee2400a4dbabd8a5d1d0c310ad93dfcb7364`。这是已加载的代码 overlay 事实，尚不是 attach 晚验证成功。
- ROOT 随后把一次显式既有 attach 入队；Client 的旧 `attach_requested` 门禁在 MCP 派发前以 `ERROR_NO_RETRY` 拒绝，SDK result 为 null、native copies 为空。原队列一次记录、claim 和失败保留；没有重置 flag、重连或改成成功侧证。
- 下一次真正晚验证回执仍 **NULL**。正式 baseline/投票/factory 新 T/C3/I4 信用不从 source、overlay 加载或 snapshot 推导；整个 mod 仍 **NOT_GREEN**。

本次小型永久原件索引：[INDEX](acceptance/2026-10-07-r0019-late-attach-repair/INDEX.json)。关键原件：[首次 attach RED](acceptance/2026-10-07-r0019-late-attach-repair/INITIAL-ATTACH-RED.native.json)、[同连接只读 snapshot](acceptance/2026-10-07-r0019-late-attach-repair/SAME-CONNECTION-SNAPSHOT.native.json)、[ROOT 实际 source overlay](acceptance/2026-10-07-r0019-late-attach-repair/PYTHON-SOURCE-OVERLAY.actual.json)、[队列04拒绝](acceptance/2026-10-07-r0019-late-attach-repair/QUEUE-04-RESULT.actual.json)、[测试](acceptance/2026-10-07-r0019-late-attach-repair/SERVICE-TESTS.actual.json)。后续恢复与业务实证只能追加新截止记录。


## R0019 后续实际恢复：2026-10-07 04:52:05 UTC

ROOT 经标准 debugpy/DAP 接入原 Python Client，在其原 event loop 上对原官方 `client.call_tool("ck3_attach_profile_bridge_v1", {})` 发起一次显式请求。原队列 `attach_requested` 前后均为 true；没有重置该 flag、改 claim、创建新的 Client/server/transport 或重连。服务已加载的生产候选由这个真实 MCP 请求执行晚验证，而不是通过调试器手改 `_attach_result`。

实际官方 SDK 原件为 51943 B、SHA `c07515af6048e742e5c6a0218c58dfc57eab00292377e0179203fb2edf9ec9ec`；实际 native 原件 `0003-attach-late-verification.json` 为 24459 B、SHA `86f5c118a24a6a3200a91086ed7a0739ee2b8bf30471ae50e293ff08ca947605`，在 `04:52:05.224249Z` 返回 `attached_snapshot_verified`。原 CK3 PID19980、原 Native SID `172caf27cc8b44549ea94ed2f306cfe0`、原 Client SID `5b11bc8186974854aa695cf2704e8866` 与 generation1 保持；实际 snapshot 为 date53144712、paused/map_ready true、actor31254，钱包为 gold1043/prestige2200/piety3150。新回执引用初始 RED2167 B/SHA75d41e…，已逐字节读回仍相同，`reinjected=false`、`reconnected=false`。

新的实际 attached binding790 B/SHA `a70e27c99d46ff43843d718948b8bdecf6a4e7d0299d879297e0ab8c625671dc` 已创建。至此只授予“原会话 Python 晚验证恢复”这一 live primitive 信用；此前 RED、队列04拒绝和04:48 source-only/loaded-overlay截止仍保留。原官方 SDK 的实际字段为 `isError=false`；ROOT response 的 `is_error` 字段原样为 null，不修写该 harness 字段。实际 native status 与原官方 SDK 全文分别保全。baseline SAVE、完整政治 control、正式投票、factory 新 T/C3/I4 不由此获得信用，whole mod 仍 **NOT_GREEN**。

04:52 独立增量索引：[INDEX](acceptance/2026-10-07-r0019-late-attach-repair/late-recovery-045205/INDEX.json)，包含[官方 SDK 全文](acceptance/2026-10-07-r0019-late-attach-repair/late-recovery-045205/OFFICIAL-SDK-LATE-ATTACH.actual.json)、[原 native 晚验证](acceptance/2026-10-07-r0019-late-attach-repair/late-recovery-045205/ORIGINAL-NATIVE-LATE-ATTACH.actual.json)、[原 Client 显式调用/flag](acceptance/2026-10-07-r0019-late-attach-repair/late-recovery-045205/ORIGINAL-CLIENT-EXPLICIT-CALL.actual.json)及[实际 attached binding](acceptance/2026-10-07-r0019-late-attach-repair/late-recovery-045205/ROOT-ATTACHED-BINDING.actual.json)。旧大 raw/save/log 继续留原外置目录；本次不扫描 checkpoint body。
