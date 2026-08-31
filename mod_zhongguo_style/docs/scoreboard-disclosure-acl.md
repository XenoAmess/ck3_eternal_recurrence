# 考核榜 received-self 字段 ACL（#013）

状态：2026-08-31，`ck3-static-ready / live-unverified`。

本专题定义并实现现有考核榜的本人案卷字段权限，以及 #141–#145 冻结对象的独立只读投影。它不新增 HUD 按钮、顶层窗口、team 页或 MCP 能力。当前结论来自生成器与 L0 静态测试，尚无 CK3/MCP 实机证据，不得写成 fixture-live 或 complete。

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

manager managed view 仍使用原 `CASE_FIELDS`，并从 owner 为该 manager、subject/cycle/case/state 五元组完整且处于允许终态的 #141–#145 对象，额外冻结独立的 `B1_OBJECT_FIELDS`。新对象 schema 不属于 `RECEIVED_CASE_FIELDS`，因此增加 B1 字段不会自动扩宽旧 C 路。最终档仍只读取不可变的 `zg361_result_grade`，不从任一 B1 对象另造 grade。

## #141–#145 独立对象 ACL

- managed：仅复制当前已发布 manager 自己拥有、且 owner/subject/cycle/case/state 严格匹配的安全字段。
- received-self：先通过同一五元组，再与已冻结 #013 ACL 取交集；只有 A（`acl_mode=3`）可获得 B1 安全字段，B 与 C/旧存档均不因本批新增字段扩权。
- team/public：本批为空；不生成 `r_XX_b1_*`，伯爵和男爵只能看到自己的 self 投影。
- 所有 owner/subject/cycle/case/state binding 只作为 selector/更新 guard，不生成详情行；evaluator、reviewer、raw、recusal、swap identity 和薪酬/奖励字段均不进入安全 schema。

#143 A/B 使用各自 subject-local 投影五元组。A 只公开 `reopen_result/reason_code`，B 只公开 `next_cycle_evidence/target_cycle`；batch、probe、severity、其他 cohort identity 与 next-cycle 业务对象内部字段不直接绑定 GUI。

榜单主体仍在淘汰前发布。由于 #141 的最终判断结果只能在 `zg361_b1_mark_published_effect` 把案卷推进 state 8 时产生，紧随 mark 的一次性 `zg361_patch_scoreboard_b1_post_mark_effect` 只给 owner/cycle/case 完全匹配的既有 slot 补冻结 B1 字段；patch serial 防止同轮重复，且不重排、增删或重写 80 个榜单行。

## GUI availability

现有唯一 `zg361_sb_self_select_gui` 根据冻结 ACL 将允许字段复制到唯一 `zg361_sb_detail_*` buffer。详情行的显示规则为：

- managed 详情保持原行为，字段缺失时显示“不可用”；
- received 详情只显示实际被 ACL 复制的字段；B 因而只显示 final grade，不渲染其余字段标签或占位值；
- managed 槽和 self mirror 各自保留 result/B1 case tuple；选中后的唯一 detail buffer 只保留 canonical `binding_owner/binding_cycle_serial/binding_case_serial`，不再生成从未写入的 `detail_case_*` 或 `detail_b1_case_*` 重复字段。`b1_case_state` 只在源记录五元组门禁中使用，不复制到 detail；clear effect 也只清理真实 selector 或 mutable update 可写的字段。

本实现没有构造不存在的 team UI。`team_mode=2` 仅作为冻结 ABI metadata；团队 aggregate 展示和 MCP 返回同一 ACL 仍是后续产品入口，当前 readiness 为 `partial / not implemented`。

## 静态验收

```powershell
py -B mod_zhongguo_style/tools/gen_scoreboard_snapshot.py --check
py -B mod_zhongguo_style/tools/test_scoreboard_snapshot.py
py -B mod_zhongguo_style/tools/validate_local.py
```

测试覆盖生成可复现、UTF-8 BOM、六字段 ABI、A/B 精确 presence/absence、C/旧存档 fallback、损坏策略 fail closed、B1 case `41` + result case `903` 正例、stale owner/cycle/policy ID、详情行 availability、detail surface 七个 remove-only 重复 binding 不再生成、#141–#145 独立 schema/五元组/ACL、post-mark 一次性补丁、敏感字段排除、后续 mutable 更新不扩权及 80 槽/四内页/七滚动面/3×3 geometry/332 按钮不回退。

简体中文与英文为本批原创文案；法、德、日、韩、波、俄、西七语由英文结构占位生成，仅保证 key 可加载，**不是发布翻译**。
