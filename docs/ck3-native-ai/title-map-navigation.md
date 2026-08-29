# 原生 landed-title 地图定位：Python/MCP 对接状态

## 当前结论

截至 2026-08-29，`center-map-on-landed-title-v1` 的 **Python/MCP 路径达到
`static-ready`**：typed facade、service、named-pipe client、严格结果解析、错误分层、
planner 排除、官方 MCP SDK 调用测试和静态 fixture 均已落地。

这不代表 native camera ABI 已闭合，也不代表 CK3 实机通过。exact-build DLL 只有在
stable-key resolver、owning-thread dispatch、相机原始状态回读和 settled gate 全部可用时，
才可广告 `game.command.center-map-on-landed-title-v1`。能力未广告时，调用明确返回
`UnsupportedStepError: capability_not_available`。

权威需求与实机门见
[`../ck3-native-title-map-navigation-contract.md`](../ck3-native-title-map-navigation-contract.md)。
本页只记录已落地的 Python 边界，避免把 transport ACK 或 schema fixture 写成镜头完成。

## 公开接口

MCP 只公开一个参数化工具：

```text
ck3_center_map_on_landed_title_v1(
    title_key: str,
    expected_revision: int
) -> object
```

- 固定 semantic step：`center-map-on-landed-title-v1`。
- `title_key` 是独立 named-pipe request field，不拼进 step 字符串。
- stable key 必须使用 `e_` / `k_` / `d_` / `c_` / `b_` 前缀、小写 ASCII
  canonical spelling，UTF-8 编码不超过 1024 bytes；中文显示名等本地化文本在 Python
  preflight 即被拒绝。
- `expected_revision` 必填，是 non-negative uint64，必须等于当前 backend-neutral paused
  snapshot revision。
- `ck3_execute_step("center-map-on-landed-title-v1")` 被 service 和 native driver 双重拒绝。

原生 transport request 固定为：

```json
{
  "type": "execute_step",
  "protocol_version": 1,
  "request_id": "...",
  "step": "center-map-on-landed-title-v1",
  "expected_revision": 17,
  "title_key": "c_bianzhou"
}
```

这里的 transport `expected_revision` 是 Python 从公开 revision 绑定到的 native revision。
native 不得伪造只有 Python 才知道的 public revision、episode 或 connection generation。

## 绑定投影

native raw result 只返回它真实知道的四个绑定字段：

```text
snapshot_id / revision(native) / native_revision / date_raw
```

Python 在提交前后读取同一 paused、map-ready snapshot，验证玩家、日期、snapshot、native
revision、episode 与连接代次均未漂移，才将公开 `binding` 投影为：

```text
snapshot_id / revision(public) / native_revision / date_raw /
episode_run_id / connection_generation
```

任一字段缺失或变化都抛 `BridgeUnavailableError`，不会对新状态重放旧 title intent。
`native-headless` 与配置化 hybrid-fallback 都只允许 native 后端承接该工具；data Mod 与视觉
fallback 不会接管。

## 完成语义与相机原始回读

`native_action_ack.status=dispatched` 只表示原生提交被接收，不是成功。Python 只接受两个最终
状态：

- `centered`：必须有 positive native sequence，并通过下述完整原生相机 gate。
- `already_centered`：调用前已由同一 gate 确认；sequence 必须为 `null`，ACK 必须为
  `not_needed`，没有额外 camera mutation。

两种成功都必须返回已解析的 `title.key`、full-generation `title_id`、tier pair、
`anchor_kind=title_bounds_center`、原生
`bounds_extent=[min_x,min_z,max_x,max_z]` 与 `map_x_adjustment`。bounds 和 adjustment 都是
signed int32 native map-grid units；bounds 顺序固定为 X/Z 两轴的最小值和最大值。
`capital_province_id` 可以是 positive int32 或 `null`，但它只记录 provenance，绝不能充当
相机中心真值：county 的官方右键语义是所有 de-jure child map anchors 的 bounds center，
并不等于首府省份。

`camera_center` 必须精确包含：

```text
expected_position_xyz : [position_x, position_y, position_z]，3 个 finite f32
current_state         : [position_x, position_y, position_z, zoom,
                         camera_param_4, camera_param_5]，6 个 finite f32
target_state          : 与 current_state 相同的固定顺序，6 个 finite f32
zoom_index            : non-negative int32
expected_zoom_value   : finite f32，从 runtime zoom table 独立回读
settled               : true
target_write_blocked  : false
```

`camera_param_4` / `camera_param_5` 只命名为 exact-build opaque camera parameters；现有证据不支持
把它们猜成 rotation、pitch 或其他高层概念。

parser 按 IEEE-754 f32 raw bits 强制 `current_state == target_state`、
`target_state[:3] == expected_position_xyz`。bounds 到 expected X/Z 的关系也不是普通 float 平均，
而是复现 A79C70/A79B10 的 exact-build 运算：先把 `min+max` 逐步按 uint32 wrap 并重解释为
signed int32，再对 wrapped sum 作 toward-zero `/2`；X 继续按 int32 wrap 减
`map_x_adjustment`；最后用 `cvtdq2ps` 一次转成 f32。expected Y 必须为 `+0.0f`。此外还要求
`postcondition_verified == true`、completion predicate 精确为
`exact-build-native-camera-settled-v1`。`target_write_blocked` 是 exact-build 的 `+0x777`
gate；证据只支持“目标写入被阻止”的命名，不把它过度解释为 pointer drag 状态。
`zoom_index` 是 camera `+0x744` 的独立索引；它不等于 state 的任何分量。native 必须从
camera `+0x7B0` runtime zoom table 的该索引独立取得 `expected_zoom_value` 并做 bit-exact
核对；Python 再要求 `current_state[3] == target_state[3] == expected_zoom_value`（f32 raw
bits）。不能把 target state 的分量原样复制成“expected”绕过此 gate。

named-pipe 写入、command result `ok=true`、revision 增长、窗口像素变化，乃至单独一个
`postcondition_verified=true`，均不能替代这些原始向量与 gate。

native typed RED 保留下列机器可区分 reason：

```text
unsupported_build / requires_owning_thread / requires_paused / map_not_ready /
title_key_not_found / title_generation_mismatch / title_not_centerable /
camera_state_unavailable / state_changed / submission_failed / internal_error
```

未知 rejection string 视为 malformed transport，不会伪装成合法业务 RED。

## Planner 隔离

capability 保留在 `bridge_capabilities`，但 native capability projector 明确不把固定 step 加入
`action_steps`。因此 `choose_one_life_turn`、`plan_turn` 与 `auto_turn` 看不到该命令；只有显式
typed MCP 调用能到达它。即使错误 backend 把 step 塞进 `action_steps`，公开
`ck3_execute_step` 仍 fail closed。

## 静态证据

实现入口：

- `src/xar_autoplayer/bridge/title_map_navigation_contract.py`
- `src/xar_autoplayer/bridge/service.py`
- `src/xar_autoplayer/bridge/native_driver.py`
- `src/xar_autoplayer/bridge/mcp_server.py`
- `tests/fixtures/title_map_navigation_v1_static.json`
- `tests/unit/test_title_map_navigation_v1_bridge.py`

测试覆盖 `centered`、`already_centered`、canonical key/UTF-8/1024-byte 边界、typed IPC
字段、planner/generic-step 隔离、缺 capability、stale revision、paused/map-ready、exact-build
mirror、已知与未知 native rejection、timeout、malformed envelope、相机原始向量和 settled/
write-blocked gate、session drift，以及官方 MCP SDK 的 list/call/error 路径。

```powershell
& tools\.venv\Scripts\python.exe -m unittest `
  ck3_autonomous_player.tests.unit.test_title_map_navigation_v1_bridge
```

当前静态 fixture 明示 `evidence_level=static-ready`、`live_claim=false`；其中 TitleID 和相机
向量都只是 schema shape，不是汴州/开封的实机 golden。

## 尚未解除的实机门

native 必须继续在真实 capability 尚未闭合时保持不广告。闭合后仍须按权威合同，在同一受管
CK3 session 跑 `c_bianzhou`、`b_kaifeng`、重复 already-centered、不存在 key、不可定位 key、
零 UI/键鼠/OCR 调用和 cleanup 矩阵；通过前不得写成 `fixture-live`。
