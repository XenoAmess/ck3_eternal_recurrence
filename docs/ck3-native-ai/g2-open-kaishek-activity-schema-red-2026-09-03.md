# G2 / open_kaishek 活动类型语义边界（2026-09-03）

## 当前证据

最近一次同步版本的离线 preflight 仍是 parser `GREEN`、validator `RED`：76 个文件、23,919,626 bytes，validator 报告 172,255 个诊断；样例全部落在 `common/activities/activity_types/zg361_jingcha.txt:UNKNOWN_OPCODE`。回执为
`_runtime/phase2-seed-20260903/artifacts-preflight-open-kaishek-sync/open_kaishek-preflight.json`，其 corpus SHA-256 为
`28e681358558f5e975fae911bf5ddf54eacb3c95dac3133852eaaeca6425c284`。

`Ck3Profile11906` 当前是有意收窄的 Phase 0 语法表，未声明 CK3 activity-type 顶层键或其嵌套 trigger/effect 的完整 schema。`zg361_jingcha.txt` 的活动定义包含 `province_filter`、`phases`、`on_start`、`on_complete`、`ai_will_do`、`guest_invite_rules` 等活动专用结构；把这些键猜测成通用 opcode 会掩盖真实语义，不能作为 validator 修复。

## 判定

- 这是 open_kaishek 的 schema coverage RED，不是 parser 故障：同一 corpus parser diagnostics 为 0，IR/runtime synthetic fixture 仍为 GREEN。
- 当前没有 exact-build activity validator/evaluator 证据，也没有合法依据把活动 UI 语义提升为 G2 native/live capability。
- 本次不修改 profile、不把未知键加入 allow-list，也不把离线 parser/runtime 结果写成活动已经可执行。

## 下一项最小施工

先冻结 CK3 `1.19.0.6` 与对应 EXE SHA，在原版 activity-type 数据和 exact-build 调用链中分别确认上述顶层键的归属、作用域和求值时机；随后增加只读 schema fixture 与差分证据。只有证据闭合后，才考虑更新 `Ck3Profile11906` 并重跑完整 corpus validator。该工作与当前两条宣传片的素材采集不冲突，但不能解除 CK3 启动崩溃。
