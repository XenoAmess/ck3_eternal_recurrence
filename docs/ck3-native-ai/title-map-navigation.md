# 原生 landed-title 地图定位：Python/MCP 对接状态

## 当前结论

截至 2026-08-30，`center-map-on-landed-title-v1` 的 typed Python/MCP facade、native
stable-key resolver、owning-thread dispatch、相机原始状态回读和 settled gate 均已落地，
并在冻结 CK3 `1.19.0.6` 的最终 ZhongGuo 合批实机中达到 **`fixture-live`**。能力仍只由
exact-build adapter 广告；能力未广告时，调用明确返回
`UnsupportedStepError: capability_not_available`。

`fixture-live` 只证明显式调用的 title-map presentation primitive 及其失败合同，不等于跨版本
支持、通用 gameplay consumer 或完整 OODA。静态 fixture 和 transport ACK 也仍不能单独证明
镜头完成。

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
相机中心真值：county 必须经过原生 title-bounds resolver。某局中 county 与其 capital barony
可以得到数值相同的 bounds/center；身份仍由独立 stable key、tier 与 full-generation TitleID
证明，不能反过来用数值相同把二者合并。

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

## Fixture-live 证据与剩余边界

2026-08-30 最终合批 attempt
`Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\zga_20260830_0930_clean_2fa2ac8_mcp`
在同一受管 CK3 PID `39576`、同一 connection generation 和同一暂停 binding 中完成正式 typed
矩阵。权威 `cell/report.json` SHA-256 为
`7D240300754BE5F1FAE8D1B131B3443F95CF20532F09AA17FA2B62DBC1B20665`。

实机结果包括：从广州移到 `c_bianzhou`、再次移出后定位 `b_kaifeng`、重复调用得到
`already_centered`、不存在 key 得到 `title_key_not_found` 且相机不变、最后回到
`c_bianzhou`。县与男爵领分别返回 TitleID `13948` / `13949` 和正确 tier；本局二者原生
bounds 数值恰好同为 `[6836,2619,6836,2619]`，不作为身份失败。7 次成功调用均满足完整
binding、bit-exact current/target、runtime zoom、
`settled=true` 和 `target_write_blocked=false`；正式路径的 OCR、屏幕/像素判断、窗口激活、
键盘、鼠标和剪贴板计数全为 0。production 没有安全可逆的 inhibit 控件，因此该正向分支明确
记录为 `skipped / executed=false / live_claim=false`，没有改内存制造测试状态。

当前 readiness 因而是 `fixture-live`。该 tool 仍保持 explicit-only、planner 隔离和 exact-build
绑定；在真实通用 gameplay consumer 与独立 production 证据出现前，不提升为
`production-live primitive` 或 `production-live loop`。
