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
- `ck3_center_map_on_landed_title_v1`；
- `ck3_query_zhongguo_scoreboard_state_v1`。

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

本轮同时新增了与上述 B1 manager-owned provider **完全独立**的收件结果查询：
`ck3_query_zhongguo_result_case_snapshot_v1(request_nonce, expected_revision, owner_character_id)`，capability 为
`game.command.query-zhongguo-result-case-snapshot-v1`，固定 `case_kind=zhongguo.result.received-self`。它不接受
`subject_character_id`、`case_kind`、变量名或其他未知字段；subject 永远是同一 paused frame 的 played character。
必填 `owner_character_id` 只是 expected filter，实际 owner 只能从玩家 scope 的 `zg361_result_case_owner` kind-4 character target
解码；实际 owner 必须等于 filter 且不得等于玩家。错 owner 返回 `owner_filter_mismatch`，owner 为玩家返回
`not_received_self`，两者以及其他顶层 unavailable 都必须把 case/notice/delivery 语义字段全量清成 typed unavailable。

该 provider 只双读以下 13 项固定 allowlist，且前后 frame、行集合必须一致：
`zg361_result_case_owner`、`zg361_result_cycle_serial`、`zg361_result_case_serial`、
`zg361_result_case_state`、`zg361_result_grade`、`zg361_result_absolute_grade`、
`zg361_result_kpi_frozen`、`zg361_result_rank_frozen`、`zg361_result_cohort_n_frozen`、
`zg361_result_delivery_method`、`zg361_result_objection_recorded`、
`zg361_result_settlement_posted_serial`、`zg361_result_appeal_open`。其中 KPI 保留原始 Q100000；
`objection_recorded` 缺失按产品语义解释为 false，其他缺失仍是 typed unavailable。产品状态矩阵冻结为：open
`state=1/method=0/settlement=0/appeal=false/objection=false`；A 签收
`3/1/case_serial/true/false`；B 签收 `3/2/case_serial/true/true`；C 拒签
`2/3/0/false/false`。`rank_frozen > cohort_n_frozen` 只关闭 notice/aggregate readiness，不伪造新名次。

`.50` 同帧调用时 expected owner 来自现有 event-window saved scope `zg361_notice_prompt_owner`，event root 为玩家；
result provider 仍独立读取 current result owner 并核对二者。B1 case serial 与 result case serial **不得比较**，例如
`41/903` 可以同时合法。本查询不证明 owner 的 AI 身份或考核资格，不证明 scoreboard #013 ACL，也不暴露 evaluator、peer、
raw comment、recusal、quota、calibration 或 compensation。native application-main mailbox 使用固定第十五槽
`permitted_executor_quindenary`；当前仅为 **static/fixture-ready**，取得 exact-build paused artifact 前不得写 production-live。

`fd0682e` 又提交了独立的考核榜只读查询
`ck3_query_zhongguo_scoreboard_state_v1(request_nonce, expected_revision)`，capability 为
`game.command.query-zhongguo-scoreboard-state-v1`。caller 只能提交 nonce 与 expected revision，不能提交 widget/变量名、角色 scope、
屏幕坐标或动作。provider 在同一 application-main paused revision 内固定查询四个真实 runtime instance：
`zg361_open_scoreboard -> zg361_scoreboard_toggle`、`zg361_scoreboard_window`、`zg361_scoreboard_modal`、
`zg361_scoreboard_panel`；并只从 played character 双读以下 20-key ACL allowlist：
`zg361_sb_m_01_char`、`zg361_scoreboard_managed_owner`、`zg361_sb_r_01_char`、`zg361_sb_self_char`、
`zg361_scoreboard_received_owner`、`zg361_scoreboard_received_cycle_serial`、`zg361_scoreboard_received_case_serial`、
`zg361_sb_self_case_owner`、`zg361_sb_self_cycle_serial`、`zg361_sb_self_case_serial`、
`zg361_sb_self_b1_case_owner`、`zg361_sb_self_b1_cycle_serial`、`zg361_sb_self_b1_case_serial`、
`zg361_sb_self_disclosure_acl_mode`、`zg361_sb_self_disclosure_policy_available`、
`zg361_sb_self_disclosure_policy_id`、`zg361_sb_self_disclosure_self_mode`、`zg361_sb_self_disclosure_team_mode`、
`zg361_sb_self_disclosure_evaluator_identity_mode`、`zg361_sb_self_disclosure_blackbox_risk`。managed ACL 只能由真实 materialized
managed surface 推导，不按爵位猜权限；received-self 必须与当前玩家、result tuple 和独立 B1 policy tuple 完整 join。

该 v1 只冻结 instance exists 与 local/effective visibility，以及上述 current-player ACL。`enabled`、`focused`、
`modal_blocking`、`screen_x/y/width/height`、`scroll_min/max/value` 均固定返回 typed unavailable；`activate`、`close`、
`reopen` 也固定为 `read_only_provider_action_not_exposed`，不暴露写动作。`full_widget_gate_ready=false` 与
`production_live_ready=false` 是当前 schema 的固定不变量。native/serializer/mailbox、Python contract/service/MCP、schema 与离线 fixture
已通过 fresh MSVC/Ninja 和正常/`-O` 测试，但尚无真实 CK3 paused response artifact，因此能力只能记为
**static exact-build / live-unverified**。下一步晋级门是在真实 managed 与 received-only 角色各保存同一 paused revision 的 MCP response，
核对四实例、20-key ACL、player/date/revision/connection binding；在此之前不得解除 runner 的 scoreboard live RED。enabled/focus/
blocking/rect/scroll 与 activate/close/reopen 还必须分别冻结 exact-build ABI、实现 typed query/action 并取得动作后新 revision 证据，
不能由这个只读切片外推。

二期 runner 已把该 capability 与 `zhongguo_scoreboard_state_v1_query_supported` 纳入强制 preflight；原先笼统的
“scoreboard state/action/ACL 全部未冻结”RED 已缩窄为 action、enabled/focus/blocking、geometry 与 scroll 的真实剩余缺口。
这只证明当前代码不会漏装只读 provider，不会把尚未执行过的 paused query 或尚不存在的动作写成 GREEN。

该切片目前只有 Python contract/schema、native/provider source 与离线 fixture 证据，状态为 **static/fixture-ready**；尚未在 exact-build CK3
中取得 paused response artifact，因此不能写 production-live，也不能解除正式 runner 的 capability RED。上述既有能力与本轮窄切片足以在
不使用 OCR 的情况下识别/操作当前原生事件、绑定玩家与构建、等待独立 revision，并保存或恢复测试现场；它们**不能**因此被扩写成
二期领域验收已经可用。对照下文合同，当前 MCP 注册面仍没有或尚未 live 闭合：

- B1 之外的 allowlisted ZhongGuo case/receipt/deadline snapshot，以及 B1 provider 的 exact-build paused 实机证据；
- 产品 decision 枚举与 stable-key 执行；
- 任意受评者的个人金币、直属上司国库、modifier、opinion pair 与来源快照；
- scoreboard 四固定实例/current-player ACL 已有 static read-only provider，但尚无 paused artifact；完整 enabled/focus/blocking/rect/scroll
  查询、activate/close/reopen 和内页数据/动作仍未 live 闭合；
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

当前 `fd0682e` 已冻结的 `game.command.query-zhongguo-scoreboard-state-v1` 只是本节的最小只读前缀：四个固定 runtime instance 的
exists/local/effective visibility 加 played-character 20-key ACL。它不等价于上述完整 named-widget/action 合同；所有未冻结 widget 字段
与三个动作必须 typed unavailable，`full_widget_gate_ready`、`production_live_ready` 必须保持 false。只有 managed 与 received-only
真实角色的 exact-build paused artifact 通过四实例、ACL 和同帧 binding 核对后，才允许把这个最小 read-only primitive 单独提升为 live；
其余完整 GUI gate 继续 RED。

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

### Runner P0 落地边界（2026-08-31）

`tools/run_zhongguo_acceptance.py --phase2-live-batch` 已从一期场景分流为独立的 MCP-only 路由：预检设置
`require_visual_tools=false`，`run_phase2_live_scenario` 不调用旧 `run_scenario`、OCR、`ImageGrab`、坐标输入、lobby 导航或
acceptance-only 测试决议；失败清理也不截图。普通 `--loader-smoke` 仍只运行通用 native readiness、error.log 和 mount gate，
不会继承二期能力门。

二期能力门在 error.log 扫描、mount inventory 和任何游戏导航前读取一次 runtime capabilities，并把完整矩阵写入
`02_phase2_mcp_capabilities.json`。当前已冻结且逐项 fail-fast 的要求为：paused/map-ready/player/active-event snapshot，
pause/resume/speed-1 timeline，event option action+ACK capability，save-checkpoint，current-event context，loaded-feature manifest，
B2 PIP snapshot、Incident snapshot，以及相应 query support flag、materialized action step、pure-native/无视觉 fallback、连接 PID/
generation、checkpoint materialization 与 managed restore lifecycle 配置。

Workforce collective + 三周期、AI-owned case、scoreboard 完整 named-widget/action gate 的正式 ABI 尚未冻结。scoreboard 的
四实例/current-player ACL 只读 ABI 与 capability 名虽已由 `fd0682e` 冻结并实现，但尚无 paused artifact，且 enabled/focus/blocking/
rect/scroll/action 仍为 typed unavailable。runner 不把该最小 static primitive 冒充完整 GUI gate；其余未冻结项仍记录为
`abi_not_frozen` requirement，所以当前完整二期启动门必然产出
`MCP capability RED`，且总报告强制 `gameplay_green_claimed=false`。即使测试替身伪造 cell `result=GREEN`，只要缺少完整的
MCP-only scenario proof，总结果也会降为 RED。

二期 map-entry runner 已改为固定存档的 MCP-only native frontend start，不再保留 `runner_not_wired`。权威 seed 合同固定 save
hash/size/mtime/header、exact game/EXE、相同 mod IDs、source report/index 与真实角色绑定；`native_session` 只走
`continue_last_save`，不进入主菜单、lobby、OCR、坐标或测试决议。来源 product/fixture tree 只作 provenance，不要求与每次开发后的
当前代码逐字节相等；否则任意正常 mod 更新都会无实证地永久废弃存档。当前 runtime 由新 bootstrap tree、mount inventory、
loaded-feature manifest 与首次 paused MCP snapshot 共同验证，后者还必须精确匹配 `date_raw` 和 CharacterID。安装失败发生在 native
driver/supervisor/CK3 创建以前，并写 `00_phase2_seed_install.json` RED；加载身份写 `04_phase2_seed_loaded.json`。

save/restore helper 已冻结一次保存、保存后动态出现 `restore-checkpoint`、一次 restore 和两 PID lineage 的静态合同：第一 PID/
generation 在保存期间不变，restore lifecycle 的 previous/new PID 必须分别等于前后 snapshot，第二 PID 必须不同，generation 必须
恰好增长一代，checkpoint size/SHA、date 与 player identity 必须恢复一致。该 helper 目前只有 focused fake-service 正负测试，不是
live 证据。

### Runner P1 lifecycle ownership（2026-08-31）

phase2 launch ownership 已迁到生产 `native_session` supervisor：pipe driver 先创建，非 daemon supervisor thread 自己持有 launch/state
锁并消费 restore lifecycle queue；停止顺序固定为 stop event → 等 supervisor 完整退出并取得 session report → 验证旧/新 PID cleanup →
关闭 driver。普通 acceptance、loader-smoke 与 promo 仍沿用原 direct-launch/`stop_tracked` 路径，未改变。

通用 `native_session` 的 `verify_prepared_profile` 新参数默认严格保持 `True`；只有 ZhongGuo phase2 显式传 `False`。原因不是跳过验证，
而是通用 `verify_profile()` 的 schema 固定绑定 Eternal Recurrence singleton descriptor/production manifest，无法表达 zg361 的双 mount
隔离 profile；zg361 runner 已在启动前独立验证 bootstrap tree、runtime/workshop identity，启动后再验证 MCP exact binary、error.log 和
mount inventory。restore relaunch 原本就固定使用 `verify_prepared_profile=False`，此改动没有放宽其他 caller。

`09_phase2_native_session_cleanup.json` 现在要求 session kind/mode/pipe、save ACK 推导出的 restore 必要性、`restart_count=1`、唯一旧 PID
shutdown、恰好两个不同 PID、generation 恰加一、restore source/intent/request ID、restore 后 raw capability binding，以及旧 PID 与最终
PID 各自的 Job/tree/global inventory/watchdog/control-file/contract-error 清理合取。若在 save ACK 前因 capability/paused/manifest RED
退出，则允许并严格证明单 PID、零 restart 的清理；不能由“进入 scenario”这个手工布尔值伪造两 PID 预期。上述 P1 仍只有
fake-supervisor/static 证据；seed installer 虽已 static-ready，但在取得 current-tree exact-build load artifact 且领域 provider RED 解除前，
不得写 production-live。

### Scoreboard stable-target paused-probe prerequisite (2026-08-31)

The generated scoreboard GUI now assigns unique scoreboard-only names to the
managed, received-self, and system entry buttons, the modal backdrop close
button, and the header close button. The fixed read-only scoreboard provider
queries those five targets together with the existing window/container/modal/
panel instances. For each of the nine fixed targets it returns the stable
identity, same-query instance pointer, vtable pointer, existence, and local/
effective visibility. Pointer values are diagnostic uppercase hexadecimal
strings bound to the same paused revision; they are not durable identities and
must never be reused after the query.

This closes only the static prerequisite for one bounded MCP paused probe. It
does not expose `activate`, `close`, `reopen`, a generic widget-name argument,
or any click path. Enabled/focus/modal-blocking/geometry/scroll remain typed
unavailable, `full_widget_gate_ready=false`, and
`production_live_ready=false`. The five names still require exact-build paused
proof that CK3 materializes them on the intended PushButton instances before
the callback candidate can be investigated. No action readiness or live claim
is implied by this contract expansion.
