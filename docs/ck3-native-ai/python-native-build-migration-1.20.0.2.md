# CK3 1.20.0.2 的 Python 原生协议迁移

本包只做后台离线迁移。没有附加玩家的 CK3 进程，没有调用游戏、输入、存档、暂停或重启。状态为 `static-ready`；新增版本接受能力仍以 native adapter 的 `hello.capabilities` 和实际实现为准，Python 认识一个来源身份不等于发布该能力。

## 确定的接口变化

`bridge/version_identity.py` 将以下两组身份绑定为整体，未知版本、混搭版本与 SHA、不同版本 backend 名均拒绝：

| 游戏版本 | EXE SHA-256 |
|---|---|
| 1.19.0.6 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| 1.20.0.2 | `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D` |

旧版常量和 fixture 保持可用。campaign root、loaded feature manifest、pending interaction context、war-entry assessment、claim termination terms 各自保留旧 provenance，同时验证独立的新 RVA、字段布局或脚本指纹。title-map 的 native driver 与 service 根据完整新旧身份进行前置校验，并要求命令结果来源与 hello 的同一组身份一致。

事件 scope 的消费者同时保留旧正式构建的 5 项 readiness、`root_scope/saved_scopes=null` 格式，并支持旧开发树已扩展的 7 项 readiness 格式；新版明确要求 7 项和已物化 scope。迁移所需的 scope schema 没有连带提交旧版的策略或动作改动。新版测试直接读冻结 wire fixture，不依赖未提交的事件测试 helper。

这里存在两处真实的协议内容变化，不能只替换版本文本：

- loaded feature registry 仍是 44 项，但原 `barter_troops` 的 index 36 被删除，后续项目向前移动，末项变成 `cstring_id=0x4169`、`key=by_god_alone`。这里只发布原生 feature 的 opaque identity，没有展开宗教领域。旧 44 行即使数量相同，也不能用于新版。
- 事件窗原生 indicator 枚举变成 `0=trait`、`1=stress`、`2=fulfillment`、`3=stress_and_fulfillment`、`4=death`、`5=scheme`。新版 combined 行增加 `secondary_direction`，保留主 stress 与副 fulfillment 的不同增减方向；magnitude 仍是 unavailable。原 1.19 的已知 raw kind 集合继续是 0–3。新版事件窗 locator 使用 `CIngameInterfaceIdlerGfx` 的 `0x44BC408`，不是同名 nongfx idler 的 `0x44D6048`。

所有上述内容均来自本轮 native 逐版本模块和新 EXE 的静态证据。对应 ABI 账本为 [campaign/feature manifest](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_2_campaign.json)、[war-entry](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_2_war_entry.json)、[claim terms](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_2_claim_terms.json)，事件窗与 pending 的独立原生模块保持同一来源约定。

## 验证与边界

新增 [离线协议回放](../../ck3_autonomous_player/tests/unit/test_native_build_contracts.py) 复用现有合法 payload，整体换成独立的新来源身份；确认游戏语义字段保持原值，混用旧 RVA、旧 SHA、旧 registry 或旧 coverage 会失败。title-map 同时经过真实 Python native driver 和 service 的 fake transport 请求链。

[pending 原生静态 wire fixture](../../ck3_autonomous_player/tests/fixtures/ck3_12002_pending_context_native.json) 来自编译后的新版 C++ reader 与 serializer 的 `--emit-json` 夹具模式，SHA-256 为 `157459ba623bc481357e9727a987ea3a4647aa68ba2c3fc2fcfc44e3dd8b77d6`，由 Python contract 直接读取验证。它证明静态 producer → wire → consumer 一致，属于内存夹具，不是 live 游戏证据。

[事件窗原生静态 wire fixture](../../ck3_autonomous_player/tests/fixtures/ck3_12002_event_window_native.json) 同样来自新版 C++ 夹具与 serializer，SHA-256 为 `5f2a3dc5e04dda2e650eec4c337e9c6062849572cf1e4d8d35fd1c9db0ecd230`。Python 直接读取其 fulfillment 行，以及主方向 `increase`、副方向 `decrease` 的 combined 行，验证两个方向和 trait/critical 标识都被保留。

`prewar_scope` 保持研究候选和 `advertised=False`，本轮只迁移已经闭合的 Unit 观测来源。`war_exit_terms_v2` 保持旧实机崩溃后的 production-disabled 状态，本轮没有重新开启该域。UI/OCR 的 1.19 baseline、旧 simulator manifest 和历史策略说明也没有被简单改名成新版本。

最终测试记录维护在 `artifacts/migrations/2026-09-30/post-update-1.20.0.2/python-identity/`；协调者将本包结果合并进当天日报、周报及总迁移记录。是否能在新版地图上真实完成操作，仍须之后取得用户允许的 paused live artifact 才能判定。

最终工作树离线回归包含 126 项测试，其中 17 项为本轮迁移回放；另外用 HEAD 的旧 event tests/strategy、仅加入迁移身份改动的 native driver/service 验证了可提交组合，120 项全部通过。两组均未跳过。组合 patch 的 `git apply --cached --check` 也已通过。开发时一次新增测试的放置错误产生 `NameError`，已记录为 harness RED 并修复，没有将其归因于游戏能力。
