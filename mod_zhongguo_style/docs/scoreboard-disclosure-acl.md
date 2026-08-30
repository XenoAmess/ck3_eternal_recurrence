# 考核榜 received-self 字段 ACL（#013）

状态：2026-08-31，`ck3-static-ready / live-unverified`。

本专题只定义并实现现有考核榜“我受评的榜”中的本人案卷字段权限。它不新增 HUD 按钮、顶层窗口、team 页或 MCP 能力，也不改变 manager 的 managed 案卷。当前结论来自生成器与 L0 静态测试，尚无 CK3/MCP 实机证据，不得写成 fixture-live 或 complete。

## 冻结输入 ABI

发布榜单时，subject 上的以下六个 B1 字段是唯一策略输入：

- `zg361_b1_disclosure_policy_available`
- `zg361_b1_disclosure_policy_id`
- `zg361_b1_disclosure_self_mode`
- `zg361_b1_disclosure_team_mode`
- `zg361_b1_disclosure_evaluator_identity_mode`
- `zg361_b1_disclosure_blackbox_risk`

`tools/gen_scoreboard_snapshot.py` 只在榜单发布瞬间读取这些字段，将存在的值冻结为 `zg361_sb_self_disclosure_*`；旧存档缺失的 metadata 在 mirror 内归一为 `0`，但不会反写 B1 产品状态。GUI 和后续案卷选择只读取冻结 mirror，不回读人物的 live `zg361_b1_*` 或 `zg361_result_*`；因此发布后更换政策、换上司或进入下一周期不会改写旧案卷 ACL。

## A / B / C

| 路线 | 冻结判定 | 本人案卷可见字段 | 明确不可见 |
|---|---|---|---|
| A | `available=1`、`policy_id=B1 case_serial`、`self_mode=3`，且六字段齐全 | final grade、grade reason、冻结 KPI/价值观、八项 evidence、appeal open/outcome | evaluator/peer identity、原话/comment、recusal identity、内部 quota/calibration trade |
| B | `available=1`、`policy_id=B1 case_serial`、`self_mode=1`，且六字段齐全 | 仅 final grade | 除 final grade 外的所有详情字段；GUI 不显示“不可用”占位行 |
| C | `available=0` | 回退 #013 落地前的 received-self allowlist | 仍执行原 allowlist 对 evaluator identity/comment/recusal identity 的排除 |
| 旧存档 | `available` 不存在 | 与 C 相同，保留旧榜兼容性 | 同 C |

`available=1` 但 policy tuple 不完整、`policy_id` 不匹配或 `self_mode` 未知时 fail closed：团队公示行仍可存在，但不生成本人详情按钮。该路径不能偷偷回退成 C，因为那会把损坏的已配置策略解释为更宽权限。

## 案例绑定与后续更新

生成本人案卷前必须同时满足：

1. result 的 owner/cycle/case 三元组完整；
2. B1 的 owner/cycle/case 三元组完整，其中 owner/cycle 分别等于 result owner/cycle；
3. result owner 等于榜单 source manager；
4. result cycle 等于 source manager 已发布的 scoreboard cycle；
5. A/B 的 `policy_id` 等于同一 B1 case。

`result_case_serial` 与 `zg361_b1_case_serial` 来自两个独立 cursor，绝不互相比较；例如 B1 case `41` 与 result case `903` 是合法组合。A/B 的 `disclosure_policy_id` 只绑定 B1 case `41`，不能错误绑定 result case `903`。

满足后，result tuple、B1 tuple、policy metadata 与选定 ACL mode 一起分别冻结。3.25 送达或申诉改判的 mutable 更新继续要求冻结 result owner/cycle/case 相等，并按原 ACL 更新：A 只刷新 final/appeal，B 只刷新 final，C 才沿用旧 mutable allowlist。B1 owner/cycle 仍与冻结 result owner/cycle 对齐，但 B1 case 只作为独立 audit/policy identity 保存，不参与 result-case mutable guard。旧事件、旧 result case 或新周期 live 字段不能污染当前详情 buffer。

manager managed view 仍使用原 `CASE_FIELDS` 全量冻结 schema；本次没有添加 `m_XX_disclosure_*` 字段，也没有改变 managed 行和详情语义。

## GUI availability

现有唯一 `zg361_sb_self_select_gui` 根据冻结 ACL 将允许字段复制到唯一 `zg361_sb_detail_*` buffer。详情行的显示规则为：

- managed 详情保持原行为，字段缺失时显示“不可用”；
- received 详情只显示实际被 ACL 复制的字段；B 因而只显示 final grade，不渲染其余字段标签或占位值；
- 隐藏的 binding owner/cycle/case 只用于 selector 和 mutable update，不作为 A/B 可见案卷字段。

本实现没有构造不存在的 team UI。`team_mode=2` 仅作为冻结 ABI metadata；团队 aggregate 展示和 MCP 返回同一 ACL 仍是后续产品入口，当前 readiness 为 `partial / not implemented`。

## 静态验收

```powershell
py -B mod_zhongguo_style/tools/gen_scoreboard_snapshot.py --check
py -B mod_zhongguo_style/tools/test_scoreboard_snapshot.py
py -B mod_zhongguo_style/tools/validate_local.py
```

测试覆盖生成可复现、UTF-8 BOM、六字段 ABI、A/B 精确 presence/absence、C/旧存档 fallback、损坏策略 fail closed、B1 case `41` + result case `903` 正例、stale owner/cycle/policy ID、详情行 availability、敏感字段排除、后续 mutable 更新不扩权及 managed view 不新增策略字段。
