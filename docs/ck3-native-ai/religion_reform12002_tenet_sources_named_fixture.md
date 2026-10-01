# CK3 1.20.0.2 Tenet 来源专用队列槽验收

2026-10-01 新专用槽 `permitted_executor_religion_draft_tenet_choices12002` 的实际库路径通过 **1 场景、8 检查、1 完整 command_result**，MSVC `/O2 /W4 /WX`。readiness 为 **static-ready named queue fixture**。使用真实提供器、key copier、队列及序列化源码，native helper 使用受检查的 fixture stub；本验收不声称 paused live 或宗教动作能力。

前序来源、原生调用树与原通用包装证明分别见 [Tenet 来源](religion_reform12002_tenet_sources.md) 和 [完整队列返回包](religion_reform12002_tenet_sources_mailbox_fixture.md)。这些源码与旧矩阵保持冻结。

新增测试从旧通用 case 的 artifact 副本复用实际 Fixture、FrameAdapter 和 Pump。副本只将通用 case 外层 `main` 改名，原提供器 `main` 仍使用原有改名；两个旧入口都不调用。输入仍为实际 DB 8 来源、草案 2 个 `0x70` 字节槽，槽 ID 7 和 11，以及各自独立的 source main Rite、actor Faith、category `+888`、TopScope `+D0`。

fresh mailbox 先把通用 `permitted_executor` 清空，只赋值新专用字段为 `ExecutePlayerReligionDraftTenetChoicesMailbox12002`。runner 从当前真实 `MainThreadQueryMailboxV1` 声明提取全部 `permitted_*` 字段，生成 artifact helper 检查其余字段全部为 `nullptr`。随后实际 `TrySubmit` → owning `ObserveMainThreadPumpAndDrainV1` → 原 observer/copier → `FinishQueryMailbox` → `Wait/Reclaim` → 原完整序列化器成功执行；终态回到 `idle`，captured pump epoch、owner thread 与 exact callback 均符合预期。

只重编中央变动的 `main_thread_query_mailbox_v1.cpp`、`ck3_12002_query_mailbox.cpp` 及新 case；提供器四 object、通用包装中的 protocol 与 Tenet mailbox 两 object 直接复用。没有重跑提供器或通用 case 矩阵，没有手填 DTO、拼接返回 metadata、创建窗口/item 或发宗教 command。

唯一 named 完整包与原通用完整包逐字节相同，SHA-256 均为 `9f0adadd05c0b94a5b32043efc6ba5bb7f9fca32fe1664899f3fc68b32ba0a86`。来源过滤与 final gate 字段继续独立保留，当前 popup cache 的空列表不能替代 DB 全来源。

证据：[query-tenet-sources-named/attempt-001/result.json](Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-reform/query-tenet-sources-named/attempt-001/result.json)，SHA-256 `ff6f96dee576fc321d3df8c5a3f0a8b9243c26a7e90bf21d524a0c716109cc44`。其中记录所有 source/header pins、复用 object、完整实际 permit 字段清单、生成 helper、编译/运行日志及原包路径。该场景直接配置库 mailbox；production install environment 的复制与注册由中央集成另行记录，本场景未运行真实 IAT installation 或 worker dispatcher。

需要复现时使用新 artifact 目录：

```python
import subprocess

subprocess.run(
    [
        r"Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe",
        "ck3_autonomous_player/native_bridge/research/religion_reform12002_tenet_sources_named_tests.py",
        "--artifacts", "<new-attempt>",
        "--generic-objects", r"Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\query-tenet-sources-mailbox\attempt-001",
    ],
    check=True,
)
```

日/周报告字段：2026-10-01 / 2026-W40；新增专用槽的实际 admission 与完整 owner 查询通过，解除通用 fixture permit 与 production named permit 之间的验证缺口。readiness 为 static-ready named fixture，无本轮 RED；仅本次单例运行，旧矩阵未重复，没有 CK3 或 Git 操作。下一项由 root 完成中央构建/默认 OFF 注册、Python 官方 SDK 单例与 paused 实机等价性验证；本包不包含宗教选择、创建、编辑或完整 OODA。commit/push 由 root 统一执行。
