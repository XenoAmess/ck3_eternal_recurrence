# Crown pending publication：补齐原始 hot/cold 身份字段

观察于 **2026-10-19T04:06:47.929504Z**，`machine_id: xenoamess-full-tower-eb9d2c1186`；机器身份来自 `tools/ck3_live_run_id.py`。本次只读已闭 AUTO130 小回执及 SDK063 源码，未访问 Game、桌面、RPC、活 Driver/SAVE 或修改冻结运行源。[证据](evidence/crown-pending-publication-context-2026-10-19.json)保留原件 SHA、实际身份核对、源码 pins 和单次合同回归命令。

AUTO130 原件为 **46,540 bytes，SHA-256 `ce6cc323f7be1c6c2aac637a0c53ca173d0fa2146f6acdff56fd16dc1d3c1ea5`**。旧 classifier 报 `receipt original ID/target/source/frame mismatch` 的原因是 plan 缺少 `crown_cold_recovery`，而旧合同要求它严格为 `False`。本次核对未发现该回执的 action/target/source tuple 过期：

| 字段 | AUTO130 实际值 |
| --- | --- |
| pending / ACK / receipt 原始 ID | 三者均为 `crown-formal-2215f5b0b90d415cb7d19ab7b2592f3d` |
| requested / effective law | 均为 `crown_authority_1` |
| actor / episode / owner | `31254` / `native-31254-6271ac8cd441` / bridge PID `214568`，planning connection `4` |
| source_context | 恰好两项 `{bridge_pid:214568, episode_run_id:上述episode}`，完整等于普通 consumer 的 `_context` |
| 原始来源 | readback queriedNative、pending preNative、ACK pre-public/native/proof 均 `54` |
| 独立后验 | receipt post-public/native/proof 与 planning Native 均 `55`；publication `ready/same_process=true`、`54→55` |
| 日期 | 原始 readback、pending、ACK、receipt、planning 均 `53145048` |
| 已有物质回执 | `enacted/material_result=true`，law/resources/succession verified 三项 true；prestige `220250260−22000000=198250260` |

`pending_material.pending` 与 `crown_pending_action` 全文相同。planning 的应用层 public revision 为 `19`；Crown transport 的 `post_public_revision` 按其既有合同与 `before.native_revision` 比较，因此这里 `55` 与 Native `55` 属于同一计数语义，不能拿应用层 `19` 当作另一处 mismatch。ACK 中的 post balance 仍是未验证占位，物质扣费来自独立 receipt。本审计没有重复提交或新增业务信用。

来源差异位于 SDK063 `service.py` 的 `pending_material_independent_receipt` 提前返回：它保留 pending record，却省略普通 `crown_authority_formal_consumer_v1.py` 原来会输出的 cold 标志。publication 的 `ready` 只查 source 的 PID/episode 两项；普通 consumer 采用**完整 dict 等值**。因此额外 context key 虽可得到 `ready`，原 consumer 仍会走 cold，不能把所有 `ready` 统一补成 hot。

本次 canonical [Service](../../ck3_autonomous_player/src/xar_autoplayer/bridge/service.py)只在该提前返回的 Crown plan 增加：

```python
crown_cold_recovery = (
    pending.get("source_context")
    != private_crown_source_context_v1(self.driver, planning_snapshot)
)
```

`private_crown_source_context_v1` 是原 consumer `_context` 的直接导入别名。完整原 context 相等才得到 false；异 PID、额外 key 或缺 source 得到 true，沿原有 cold/current-law 读取语义，不制造旧 Native receipt。construction 分支不增加该字段；策略、频率、动作、receipt 校验及优先级均保持原逻辑，没有新增 query。

[合同回归](../../ck3_autonomous_player/tests/unit/test_material_publication_portable.py)只运行一个新 Service test node，包含完整 hot、异 PID、额外 context key、缺 context 四个场景，**1 passed in 1.29s，exit0**。它调用真实公共 Service planning 分支，确认原 pending ID/内容和 receipt route 保留、cold 标志符合原 helper、无新机会 planner 或 publication 等待；Native/游戏输入为 synthetic。原 AUTO130 的当前零 RPC classifier 适配由独立 harness owner 维护，本补丁不改旧证据或放宽未知材料守卫。

当前 SDK063 未热换。后继 canonical 合批采用与实际运行资格分别记录。本包使用 storage01 已登记 `m4-crown-contract01` 小叶，预计256KiB、硬1MiB，单次测试关闭 pycache/cacheprovider/plugin autoload，临时与日志均在该叶；精确闭账包含 manifest 自身逻辑量、allocated unknown、future0/process0。无删除、无新全局预留或物理释放信用。
