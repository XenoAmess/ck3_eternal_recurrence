# CK3 1.20.0.3 Crozier 原生迁移

2026-10-02，目标为 Steam build **25652598**：`ck3.exe` 101,039,736 bytes，
SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`。
冻结 EXE 在 `artifacts/migrations/2026-10-02/installed-build/binaries/ck3.exe`。
本次恢复现有 production 能力；G2 策略执行及 private 行为继续暂停。

03:15 root最终验收：冻结`c0fda2a`、61 ON/4 OFF候选v2 DLL（SHA`103ebfb7ed50906ab7ffebb7f2c4e601e483ec7dd5bafb0d96e8cfae82d91898`）在真实PID82032上通过正式SDK八项typed观测，含政府三项`.3`来源、内阁候选/最终判定、法律和派系。正式计划选life-advance，真实推进一天至raw53169096，actor29829保持、最终paused；native save67,301,351 bytes/SHA`6ae968e92e4adab6109c19cc93dbff4272dc26c5737282e162c197adaeec2bc2`独立文件核验与完整进程清理GREEN。准确代码head官方CI run36912274721 SUCCESS。客户端入口已切换且真实注册SDK122工具GREEN；所有失败原件保留。[完整结果、部署/配对、边界与G2暂停](../ck3-1.20.0.3-migration.md)。这只提升已实测primitive和一次观察/推进/保存循环，不宣称全private动作或完整自动游玩完成。

## 复用依据

新版与旧 1.20.0.2 EXE 同尺寸，仅 6,355 bytes / 146 个连续区域不同。
核心 28 模块逐项比较保留原 RVA：397 unique signatures、79 vtable prefixes、
1,234 decoded instruction checks、676 source constants、82 binding RVA、57 function spans、
44 feature records 与 6 compiled define keys 全部 unchanged。
证据为 `artifacts/migrations/2026-10-02/abi-comparison/core-comparison.json`。

全 PE `.pdata` 244,435 个函数逐字节比较只有 4 个变化函数；所有 `12002` 原生
src/include 中的十六进制 RVA 引用都没有落入这些函数。
证据为同目录 `changed-functions.json`。foundation 另有一次实际新 SHA 检查，
17 signatures、7 vtables、34 instructions 通过；回执为
`artifacts/migrations/2026-10-02/foundation-preparation/foundation-comparison.json`。
这些是离线 ABI 依据，不能替代新版 paused/live 游戏结果。

永久复用账本为 `ck3_autonomous_player/native_bridge/research/ck3_1_20_0_3_abi_reuse.json`：
显式绑定新 SHA / build、旧 .2 baseline 和全部旧 manifest pins，包含 core 28、
extra 81（74 native / 7 reference）、6 metadata、4,682 个去重 frozen regions 和
41 个 BSS 虚拟布局。`verify_ck3_12003_abi_reuse.py --manifest-only` 已通过；
带 `--exe` 的默认路径验证实际新 .3 EXE，旧 SHA 门禁没有被跳过或修改。

## 接入合同

独立身份头为 `native_bridge/include/xar_bridge/ck3_12003.hpp`，独立描述符和 factory
为 `src/ck3_12003_adapter.cpp`。registry 首选 .3，同时保留 .2 和 1.19.0.6。
新版 descriptor 的 id 是 `ck3-1.20.0.3-msvc-x64`，version 与 SHA 始终为实际 .3。
未知 executable 继续得到 disabled descriptor。

新版 factory 先严格匹配 .3 SHA，才复用经证明 unchanged 的 .2 binding bundle。
`ReviewedCrozierAbiSha256` 只对完整 .3 descriptor 身份选择旧 ABI；旧 `Bind*Image`
函数没有新增 SHA 例外，仍拒绝直接传入 .3 SHA。共享 adapter 实现携带各自 descriptor，
无需复制 28 模块。拥有线程 observer、query mailbox 和 dispatcher 接受两组完整
Crozier 身份；owner thread、snapshot 和命令执行语义保持现有实现。

`RunConnectedSession` 的所有结果发送经过实际 descriptor 的版本渲染。
.3 的 typed `game_version`、`exact_build`、`version`、`build_version`、`build`、
`backend_id`、`campaign_backend_id`、`feature_backend_id`、`adapter_id`、SHA、event-indicator 标签及 `schema:ck3_12002_*`
均发布为 .3。真实实现源路径 `src/ck3_12002*.cpp` 保留，地址/RVA 保留已证明值；
不把源文件改名当作新 ABI 证据。旧版结果原样保留，escaped user text 不改写。

private compile options 默认 OFF。已有 nonwar / 宗教补充 ABI 已完成针对新 SHA 的
离线复核；随后迁移 41 个现有 private handler / mailbox / router 的 descriptor
检查和 binder 参数入口。`ReviewedCrozierAbiVersion` 与 SHA helper 在内部选择旧
已核实 ABI，保留旧 .2 guard 的意义；对外仍渲染真实 .3。独立的
`src/ck3_12003_abi_profile.cpp` 也供 standalone dispatcher/mailbox 夹具使用。
没有增加 private 行为或启用任何原来关闭的 feature。此次已迁移入口没有新增
未知 ABI 映射；既有非目标或关闭的开关仍按原合同保留。新版 private live
readiness 仍须真实 paused 查询互证，G2 策略执行继续暂停。

首轮 suspended-injection 夹具 RED 的原因是 `host.cpp` 仍期待 1.19.0.6 hello。
最小修复让 host 读取新版 shared preferred 静态 version / adapter ID / SHA；
保留 unsupported-build、capability 与进程判断，并精确核对 SHA。
原 RED 留在 `artifacts/migrations/2026-10-02/native-check-01/`。

## 必要验证

协调者统一构建 production DLL / host / attach-host / injector。新增代码与关键夹具
只需编译 `xar_ck3_adapter_registry_test`、`xar_ck3_12002_semantic_adapter_test`，再运行：

```text
ctest --test-dir <production-build> -C Release -R "^(xar_ck3_adapter_registry_test|xar_ck3_12002_semantic_adapter_test|xar_ck3_12003_semantic_worker_test)$" --output-on-failure
```

registry 夹具覆盖三版本选择、两版 factory 的 SHA 隔离、ABI 显式复用和实际版本
序列化。`.3 semantic worker` 复用原 worker 生产路径夹具的 `--patch3`，经过 observer、
mailbox、typed actor、semantic executor 和 snapshot 稳定性路径。
`open_kaishek` 对 PE/MSVC 原生线程与 ABI 无可覆盖语义，记为 not-applicable。

协调者首轮 default production 构建 394 steps GREEN；.2 worker、.3 worker、registry
及 running-attach 夹具 PASS。host 修复和 private 41 入口接入之后的最终中央构建
及新版 live 结果由协调者写入后续回执。不得据此宣称 production-live 或完整 OODA。

旧 Python 定向回归中 20 份 fixture SHA pin RED 已一次归因为基线问题：当前 20 份
bytes 与冻结 9ce5e00 源副本完全相同，此 owner 没有改写这些 fixture。
取证为 `foundation-preparation/old-fixture-pin-diagnosis.json`；没有盲目刷新旧 pins。

## 新版政府 DTO 的实机来源修复

新版 SDK attempt 03 的 campaign-root、loaded-features 与法律查询已实际成功，随后政府查询
返回 `government runtime adapter lacks its native source identities`。政府 producer 的既有
serializer 同时写出 private `backend_id`、`campaign_backend_id` 与 `feature_backend_id`；
初版 .3 renderer 只转换 `backend_id` 的 native 前缀，漏掉了这三个实际来源值。
Python normalizer 根据实际 .3 build 精确要求三个 .3 标识，因此拒绝返回的 DTO。
原始失败保留在 `artifacts/migrations/2026-10-02/live-preparation/sdk-nonwar-03/result.json`。

最小修复让 `RenderCrozierBuildIdentity` 对这三个确切 JSON 字段转换 .2 版本前缀，
同时覆盖已有 private 与 native backend。旧 .2 输出仍原样返回，真实源路径继续保留。
现有 registry 夹具读取未修改的真实 producer 记录
`research/fixtures/ck3_12002_government_adapter_available.json`，通过生产 renderer 核对
三个 .3 来源标识、实际 .3 SHA/version 及旧 .2 原样输出；没有新增 CMake target。
协调者增量 DLL / registry 构建 5 steps GREEN，该现有夹具 1/1 PASS（0.47s）；
证据在 `artifacts/migrations/2026-10-02/identity-fix-build-01/` 与
`identity-fix-test-01/`，详细诊断回执为 `foundation-preparation/government-wire-identity-fix.json`。
新版政府 paused/live 验收仍待下一次实际查询。

attempt 02 的 campaign-root 10 秒 transport timeout 保留为未查明 RED；attempt 03
相同源码的首个 campaign-root 成功返回，没有修改 timeout、重试或动作发送规则。
官方 `native_session` supervisor 在此路径只管理生命周期，不发送第二组同 pipe 查询。
