# Robert h2743 防守战争退战：同帧观测合同

## 当前证据边界

跨机请求 [`WAR-ROBERT-H2743-EXIT-20260928`](../autonomous-agent-progress/coordination/war-requests/requests/WAR-ROBERT-H2743-EXIT-20260928.json) 的 R0263 摘录只证明：正式 Robert 存档 h2743、raw date 53217264、WarID 16777231 仍在、玩家相对战争分数 -12、军队 83886367 在一次有界路线推进后仍存在。它没有这一帧的 CB、原生退战选项、接受状态、条款或整场继续作战风险输入。R0197/R0221 的投降是另一份精确输入的一次性、已用尽授权；其结果不能替代 h2743 的选择或授权。

现有 `strategy.py` 已能调用 `query-war-termination-options-N`，并可在保持同一战争签名、角色、连接及有限期限时复用已证明的负面查询；它也有进攻方 Raiktor 三路退战决策和进攻方原生法理郡无安全路线处置。缺口是**防守方**同帧选项进入正式结论时，没有一份明确区分“原生可执行”和“实际代价已知”的独立观测结果。

## 本次交付

`formal_defender_exit_observation.py` 作为 `choose_one_life_turn` 的只读附注，对恰有一场玩家为主防守方且分数为负的战争工作：

1. 没有本帧的原生 options 时返回 `current_native_options_required` 和精确查询 literal；现有战术规划器仍负责实际选择下一步。
2. 拒绝跨 snapshot、public/native revision、连接 generation 或 episode 的缓存行，以及非原生、战争侧/分数不符的行。确认 CB 是原版 `individual_county_de_jure_cb`、数据库索引 17 后，逐项记录胜利、白和平、投降的原生可执行性、对方是否现在接受以及条款是否可见。
3. 领地及封臣、双方有符号资源、定向停战、继续作战风险只要没在当前输入出现，均为 `null`。结果始终 `recommended_outcome: null`、`action_literal: null`；其存在不能作为提交退出动作的授权，也不能释放 ECON 和建设门禁。

这个 observer 被正式单步策略调用并附在原战术计划的 `formal_defender_exit_observation` 字段，不改变原计划的 `selected_step`。它使下一次原生查询后的事实与未知项能被下游读取，并防止从“可执行”偷换到“值得投降”。

## H2743 下一次复验

先只传输并核对请求中的 h2743 save、driver、完整 family sidecar、对应 DLL 四类文件及各自 SHA-256；不要让 OneDrive 同步无关文件。由本机正式配对、Steam 离线新鲜画面和本机独占资源门禁后，恢复原存档并只读取得当前 `query-war-termination-options-16777231`。这是目前**第一个缺少的原生观测**；不能把 R0221 在 -15 分时的可用性和条款状态投射到 h2743 的 -12 分帧。

拿到当前 options 后，若白和平不可用而投降可用，下一缺口是该 CB 的实际领地/封臣和资源代价及继续作战风险区间；不能把未知代价按零处理。若白和平可用，先比同帧接受与其条款，再结合已有战斗/路线预测。只读结论可以交接“继续作战并复观测”或“当前仍无法排序”；任何退战动作都必须由独立正式 typed consumer、当前帧门禁和全套后置/冷恢复证据处理。单次 R0197 授权不可重用。

## 验证

`test_formal_defender_exit_observation.py` 使用仓库保存的真实 R0221 原生 options 证据作为历史样本，另用**合成的** h2743 形状帧验证缺失查询、跨帧拒绝、可执行但条款未知时不产生命令，以及正式策略确实附加只读结果。合成帧不是 h2743 的实机观测。Python-only 静态校验通过；精确 h2743 复验在四类原始资产抵达前未做。
