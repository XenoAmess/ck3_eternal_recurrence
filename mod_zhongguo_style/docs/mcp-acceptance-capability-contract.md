# ZhongGuo 361 二期 MCP 验收能力合同

状态：需求合同与 provider 施工账本。**合同、native bridge/provider 实现和 exact-build 实机验收均已获授权**；不再存在
“只写能力边界、不实现 provider”的限制。天朝二期完全完成前保持全局最高优先级，G2 次之；MCP 施工按下文真实 blocker
逐项闭合，不扩成无关的平台重构，也不得中断正在运行的有效 CK3 长局。二期测试优先 MCP；OCR 仅允许在 native 状态已经闭合后
制作最终截图，不参与导航、状态真值或 GREEN 判定。

## 当前实现盘点（2026-08-31，exact repository source）

当前 `ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py` 已注册并可供既有 G1/G2 runner 使用的相关语义入口包括：

- `ck3_take_snapshot`、`ck3_wait_for_change`；
- `ck3_save_checkpoint`、`ck3_restore_checkpoint`；
- `ck3_query_campaign_root_context_v1`、`ck3_query_loaded_feature_manifest_v1`；
- `ck3_query_current_event_window_context_v1`、`ck3_select_event_option`、`ck3_resolve_active_event`；
- `ck3_center_map_on_landed_title_v1`。

本轮又加入了首个窄域 source/fixture provider：
`ck3_query_zhongguo_case_snapshot_v1(case_kind, request_nonce, expected_revision, subject_character_id?, owner_character_id?)`。
V1 只允许玩家持有的 `case_kind=zhongguo.b1.performance`，不接受变量名；实际 owner 与 paused player 不同会返回
`player_binding_mismatch`，不会借此读取 AI-owned case。它把 request nonce、exact build/DLL consumer、connection generation、
paused date/player、public/native revision、subject 与实际 owner 绑定到同一响应，并返回 B1 案卷身份、`mechanism_039`/`roster_lock`
操作及 receipt、pending milestone deadline。`open_date_raw` 只读产品的 `zg361_b1_pending_open_date`，期限长度只读
`zg361_b1_pending_deadline_days`；当前产品没有显式 due-date 变量，因此 `due_date_raw` 固定为 typed
`due_date_not_persisted_by_product`、`deadline_due_date_ready=false`，绝不以 open date + days 推算 due date。
当前 exact-build ABI 还没有证明 `set_variable = current_date` 的 event-target kind/payload 转换；原始 open-date 变量存在时，
`open_date_raw` 必须返回 `value_type_mismatch`，不得把不明 payload 冒充 CK3 `date_raw`。
`not_scheduled` 是完整的 typed negative observation，故其 identity/due 两个 gate 都为 true；pending/expired 则只有在显式
`due_date_raw` 可用时才打开 due gate，`open_date_raw` 不参与推算或替代。

该切片目前只有 Python contract/schema、native/provider source 与离线 fixture 证据，状态为 **static/fixture-ready**；尚未在 exact-build CK3
中取得 paused response artifact，因此不能写 production-live，也不能解除正式 runner 的 capability RED。上述既有能力与本轮窄切片足以在
不使用 OCR 的情况下识别/操作当前原生事件、绑定玩家与构建、等待独立 revision，并保存或恢复测试现场；它们**不能**因此被扩写成
二期领域验收已经可用。对照下文合同，当前 MCP 注册面仍没有或尚未 live 闭合：

- B1 之外的 allowlisted ZhongGuo case/receipt/deadline snapshot，以及 B1 provider 的 exact-build paused 实机证据；
- 产品 decision 枚举与 stable-key 执行；
- 任意受评者的个人金币、直属上司国库、modifier、opinion pair 与来源快照；
- named scripted widget 查询、activate/close/reopen 与 scoreboard ACL 数据投影；
- AI-owned ZhongGuo case snapshot；
- B4–B8 的 vacancy/position/project/incident/workforce/cross-cycle domain-object 查询。

因此当前可先复用 native event context 做“看到哪张产品事件、选择了哪个真实选项、是否产生新 revision”的部分闭环，并用新 provider 的
离线 fixture 固定 B1 案卷/receipt/deadline ABI；但凡验收条件涉及实机案卷五元组、双付款守恒、hidden deadline、考核榜内页/ACL、
AI 后台案或跨周期 lineage，仍是 **MCP capability RED**。这些 RED 必须交由
MCP/native bridge 层按下文 allowlist 实现，mod runner 不得用坐标/OCR、测试决议或任意变量写入伪造 GREEN。

## 一、B1 前置能力

### 1. Allowlisted mod case snapshot

输入：产品命名空间内的 allowlisted case kind、可选 subject/owner ID。输出必须来自同一 paused revision，并包含：

- exact owner、subject、cycle serial、case serial、state；
- policy ID/choice、operation key、hook、pre/post state；
- evidence/grade/quota/feedback 引用 ID；
- deadline target/case/expected-state token；
- source revision、connection generation、paused/date/player identity 和 readiness gate。

它是只读查询，不允许任意枚举或改写 mod 变量。未实现字段返回 typed unavailable reason，不能长期用 `null` 冒充完成。

首个实现切片只覆盖 `zhongguo.b1.performance` 的案卷五元组、revision/timeline/feedback、固定 roster-lock policy/operation/receipt，
以及 pending milestone deadline 的 target/owner/cycle/case/expected-state/open/due/on-due-operation。它不声称已覆盖 evidence/grade/quota
引用，也不外推到 B4–B8、AI-owned case 或 arbitrary variable reader。离线 contract/schema/native fixture 通过只把状态推进到
**static/fixture-ready**；必须在 pinned 1.19.0.6 DLL 上取得同一 paused revision 的真实响应后，才允许单独提升这个窄切片。

### 2. 产品 decision 枚举、执行与独立 ACK

提供当前可见/可用产品决议的 stable key、可用性、阻塞理由和执行入口。执行必须：

- 只接受 allowlisted product decision；
- 绑定请求 revision、player、paused session 与 nonce；
- 返回独立 ACK；
- ACK 后必须等待新 revision，再由查询证明后置；
- acceptance-only 决议不得作为正式二期动作路径，更不得靠 OCR 找按钮。

### 3. 资源、modifier 与 opinion 前后快照

同一 revision 返回角色个人金币、领主国库/可用预算、贤能/能力资源、目标 modifier、目标 opinion pair 及来源 identity。必须区分
个人金币与国库，不得只给合计。查询只读；业务扣款仍由产品脚本执行。

### 4. Hidden deadline target/case binding

隐藏期限必须查询到 exact target、owner、cycle、case、expected state、due date 和 on-due operation。只有 generic marker 而不能证明
target/case 绑定时不得判 GREEN；这正是首纵切 `.52` 尚未闭合的缺口。

### 5. Named scripted-window/widget contract

建议能力名为 `get_named_scripted_widget_state_v1` 与 `activate_named_scripted_widget_v1`（最终命名由 MCP 层决定）。对 allowlisted
scripted window/widget 返回：stable widget identity、存在、visible、focus、modal/blocking、screen rect、outer/inner active tab、
close/reopen ability、selected source/slot/cycle/case 与 revision。提供 activate/close/reopen 的 typed action 和独立 ACK；动作参数只允许
stable identity，不接受坐标。

考核榜 B1 最小 allowlist 必须覆盖：toggle、modal、panel、managed/received/system 外层页、list/detail、facts/peer/quota/audit、
back/close、`m_01`、`m_80` 与当前玩家 received-self 案卷按钮。状态查询还要证明：

- 详情来自冻结 scoreboard/case snapshot，不是人物 live variable；
- 公爵及以上管理者可选 managed case，伯爵/男爵只能选 received-self；
- 非本人 received 行不能取得 evaluator identity、raw comment、recusal identity 或内部 quota trade；
- X/Escape/backdrop/切页/新榜发布清理 selection，关闭后重开回到 list/facts；
- 原生右窗、自动事件、决议窗、pause、struggle、outliner、barbershop 与 scoreboard 的 visible/blocking 互斥可查询；
- 100/125/150% UI scale 与三档分辨率下 rect 仍在安全区。

另需 bounded scoreboard/case snapshot 返回 ACL 后的 facts/peer/quota/audit 冻结字段；GUI state 与数据查询必须来自同一 paused revision。
它用于考核榜内页、告身、申诉/PIP、职业/HC、项目/运营和制度审计，不得退化为坐标点击或 OCR 找按钮。本条先冻结 typed 合同，
随后由 native bridge/provider、MCP facade、fixture 和 exact-build 实机矩阵依次实现并验收；在最后一项通过前仍保持 capability RED。

### 6. AI-owned case snapshot

只读查询授权 AI 天朝制公爵及以上持有的案卷，不切换玩家、不向 AI 注入任意动作。输出与玩家 case schema 相同，并带 AI route、
manager rank/government/direct-subject eligibility。

## 二、后续批次能力

- B4/B5：真实 vacancy、candidate、court position、title relation、任命/空缺/占用状态查询；
- B6：项目、贡献签名、指标版本、矩阵权重和重组映射的 domain-object 查询；
- B7：incident、维护/积弊、共享官署、工时、外包、招聘漏斗与真实角色/职位 binding 查询；
- B8：跨周期 case lineage、政策版本和宪章 future-default 查询。

动作层仍只允许产品 decision/event/interaction。MCP 不提供“写任意变量、设任意后置、直接给资源”的调试后门。

## 三、统一 response/ACK 约束

所有查询/动作至少绑定：schema version、exact CK3 build、DLL/consumer identity、connection generation、request nonce、source revision、
paused/date/player identity。动作 ACK 只能证明命令被产品路径接受；最终 PASS 必须由 ACK 后新 revision 的独立状态查询、资源守恒和
可见反馈共同证明。

## 四、测试使用规则

1. runner 全程保持 US English HKL；
2. fixture 只造真实角色、cohort、资源和期限前置，不写后置；
3. 动作前 snapshot，动作后 ACK，再等新 revision 查询；
4. OCR 只在所有字段已闭合后生成最终截图，不参与导航和断言；
5. RED artifact、request/response、ACK、revision 和 cleanup 证据全部保留；
6. MCP 缺能力时更新本合同并交给 MCP 层施工，mod 侧不得用 OCR 或 acceptance-only 后门永久绕过。

## 五、启动门与合批拓扑

正式二期 runner 在进入昂贵的长局前必须先读取 runtime `ck3_get_capabilities`，逐项核对本合同的 allowlisted case、产品动作、
资源/关系、hidden deadline、named widget、AI case 与 B4–B8 domain-object 能力。源码中注册过工具不等于当前 exact-build DLL/consumer
已经提供；缺任一必需能力时应立即产出 `MCP capability RED`，不得启动旧 OCR/坐标/测试决议路径继续跑完整 CK3 长局。

现有 `ck3_restore_checkpoint` 的合同与实现语义是重启受管 pure-native CK3 session，而不是在原 PID 内载入。因此“真实存读档证明”与
“整份验收严格单 PID”不能同时作为门禁。最低成本且诚实的正式拓扑是：

1. 一份 acceptance attempt 下启动第一个 CK3 进程，冻结真实角色、案卷、资源、期限和 GUI digest，只保存一次；
2. 调用一次受控 restore，要求 connection generation 与 PID 改变，同时逐字段证明 date/player/case/deadline/receipt/policy 恢复一致；
3. 在第二个 CK3 进程内连续完成 D+7/30/90/180/300/365、三周期、权限、AI 与主 GUI 批次，除此之外不再重启；
4. 主长局只跑一个代表性显示配置；若 provider 不能可靠热切分辨率/UI scale，则 3×3 几何矩阵拆为九个短 GUI cell，不能重复九次
   完整三周期链，也不能声称一次 PID 覆盖了未切换的配置。

361 项不应逐项重启或逐卡点击。逐号证明由 allowlisted case/query 批量核对；A/B/C 与 typed negative 按 38 个共享领域 recipe 合批。
每个动作统一遵守：paused snapshot → stable product action + nonce/expected revision → 独立 ACK → 等待新 revision →
case/resource/widget/visible-feedback 独立查询。最终 artifact 至少保存 capability manifest、真实角色 roster、action journal、
001–361 case matrix、38 域 A/B/C matrix、资源/期限账、save/restore proof、scoreboard ACL、widget blocking、三周期 lineage、守恒与清理证明。
