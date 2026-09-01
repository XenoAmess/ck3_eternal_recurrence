# 考核榜 named-widget MCP action 单元

状态：**exact dispatcher + provider-owned observed revision 已静态接线；production capability 与实机 PASS 仍为 RED**。本轮没有启动 CK3，也没有使用 OCR 或坐标。

## 1. 动作面

能力名为 `game.command.activate-zhongguo-scoreboard-v1`，step 为 `activate-zhongguo-scoreboard-v1`。外层原子动作只有五个：

| action | provider-owned 目标 | 后置条件 |
|---|---|---|
| `open` | 关闭态唯一可见的 managed/received/system 入口 | modal 打开，对应 list page 唯一可见 |
| `switch-managed` | `zg361_scoreboard_tab_managed` | managed page 唯一可见 |
| `switch-received` | `zg361_scoreboard_tab_received` | received page 唯一可见 |
| `switch-system` | `zg361_scoreboard_tab_system` | system page 唯一可见 |
| `close` | `zg361_scoreboard_header_close` | modal 与三页均不可见 |

`reopen` 不是一次原子 callback。它必须严格拆为：`close ACK → 独立 closed query → open ACK → 独立 open query`。直接提交 `reopen` 会得到 `reopen_requires_two_phase_sequence`。

已在目标页时切到同一页属于 `action_noop`，不会伪造一次变化。

## 2. exact dispatcher

冻结基线为 CK3 `1.19.0.6`、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

安全入口是 `CPdxGuiShortcutManager` binder RVA `0x36E1C40`，不是旧的 slot 36。旧 `0x36C6A90` 已证明属于 hover/oversound，永久禁止调用。

静态闭合链路：

```text
target +0xD8 -> GUI context
context +0x3E0 -> shortcut manager; manager +0 == context
bridge-owned 0x50 pimpl stub; +0x48 == target
empty 0x20 CString SSO; length 0, capacity 0xF
RVA 0x36E1C40
  -> CPdxGuiShortcutEvent (0x40, type 0x1D)
  -> DeliverGuiEvent RVA 0x36CB4A0
  -> context prehandlers, then target prehandlers
  -> ButtonBase slot13 RVA 0x36C69A0
  -> selected onclick callback group
  -> target slot10
```

dispatch 前精确检查：

- target `+0xD0` 的 `0x01/0x02/0x08` 均清零；其中 `0x08` 是 cached effective-hidden，`0x02` 是 cached effective-disabled；
- target vslot13 必须为 `0x36C69A0`，vslot10 与选择到的 callback vslot2 必须可调用；
- flags=0 时先选 `target+0x3F8` group0；为空才退到 `target+0x338` group0；选择到的组必须至少有一个 callback；
- modal vector 位于 context `+0x290/+0x29C`，count 限制为 0–256；若存在任何有效可见 modal，target 必须是绝对最后一项 `vector[count-1]` 的严格后代，helper 为 `0x369E620`。

传入 `{shortcut id=0, name=""}` 只能称为 bridge-owned native semantic activation，不能宣称触发了真实注册快捷键。

原生返回值只记录为 `native_handled`。prehandler 可以短路或修改 event `+0x14`，ButtonBase 即使没有 callback 也可能返回 true；反过来 callback 已执行时 raw bool 也可能为 false。因此 raw bool 无论真假都不证明动作发生，ACK 始终是 `acknowledged_verification_pending`。

## 3. provider-owned observation revision

没有找到可诚实命名为 engine/canonical scoreboard revision 的字段。provider 因而发布五个顶层字段：

- `provider_session_id`：DLL 生命周期内稳定的 128 bit CSPRNG 值，固定 32 个大写十六进制字符；
- `observation_sequence`：每次成功的 application-main 同帧双读 query 增加 1；
- `observed_state_revision`：只有完整 TREE 或 SEMANTIC canonical bytes 相对上一条成功观测变化时增加 1；
- `tree_fingerprint_v1`：稳定 GUI 树身份的 SHA-256 诊断值；
- `semantic_fingerprint_v1`：可见、enabled、modal、活动页与 ACL/case tuple 的 SHA-256 诊断值。

revision 判定比较 provider 内部保存的完整 canonical bytes，不拿 SHA-256 相等代替逐字节相等。查询使用 `publish_observation`；动作 source reread 使用 `validate_without_advancing`，必须与最后一次已发布观测的 session、connection、player、date、build、allowlist、tree bytes 和 semantic bytes 全部一致，而且 ACK 不推进 sequence/revision。

未采样的 A→B→A，以及同地址 destroy/recreate，仍无法排除；本合同不作 ABA-proof 或 engine revision 声明。

## 4. 请求与 ACK

请求固定绑定：

- nonce、allowlisted action；
- public/native revision、connection generation、player；
- provider session、observation sequence、observed state revision；
- tree/semantic fingerprint；
- window instance、target instance 与 target vtable。

caller 不能提交任意 widget 名、角色 scope、坐标、变量名或 callback 地址。

ACK 回显上述 source binding 和 provider-owned target，并给出：

- `minimum_observation_sequence = source + 1`；
- `minimum_observed_state_revision = source + 1`；
- provider session 不变；
- tree fingerprint 不变；
- 预期 modal、active tab、list view 与 window instance。

暂停状态下的纯 GUI 动作通常不会推动世界 public/native revision，因此 later query 必须与 source 的 public/native revision相等，而不是错误地要求 `+1`。

## 5. 独立 later query

验证 PASS 必须同时满足：

1. nonce 独立；provider session、connection、player、date、build 与 public/native paused frame 不变；
2. observation sequence 至少为 source+1；observed state revision 至少为 source+1；
3. tree fingerprint 完全相同；semantic fingerprint 与 source 不同；
4. modal 与目标页面的逐项 typed postcondition 成立；
5. window instance 保持相同。

shared helper 固定执行 `source query → action result/ACK → independent later query`，保存到 `07c_phase2_scoreboard_named_widget_action_cell.json`。当前即使收到结构正确的 exact ACK，只要 `production_capability_advertised=false`，cell 仍输出 RED `provider_owned_revision_verification_unavailable`，不会生成 verified PASS。

## 6. shared wiring 与 readiness

- state 使用 application-main 第 18 固定槽；action 使用独立第 22 固定槽 `permitted_executor_duovigintary`；
- adapter 只广告运输合同 `game.contract.zhongguo-scoreboard-action-v1-fail-closed`，不广告 production action；
- bridge、native driver、service、MCP 已严格传递 provider binding；内部 state query wire 另带当前 `expected_connection_generation`；
- normal、`python -O`、native Release fixture 与 runner static RED gate 均须通过；
- `full_widget_gate_ready=false`、`production_live_ready=false` 保持不变。

当前真正剩余 blocker 只有：在冻结 build 上取得真实 paused source→ACK→later artifact，确认五个原子动作的可见后置状态，并据此另行决定是否广告 production capability。内页选择、back、scroll、geometry 不属于本轮外层六动作范围。
