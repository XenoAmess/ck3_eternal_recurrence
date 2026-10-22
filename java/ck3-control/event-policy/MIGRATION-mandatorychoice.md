# Mandatory native choice：Java 纯规则迁移

边界：`org.xar.ck3.control.events.mandatorychoice`，Java 21，作为 `event-policy` 的进程内叶；不独立启动 Quarkus 或 JVM。入口是 `MandatoryChoiceCodec.decode/select` 与强类型 `MandatoryChoicePolicy.selectUnknownMandatory/selectExistingNative`。

迁移源为 `ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_policy_v1.py`。当前实际生产调用者只有 `mandatory_choice_planning_v1.py:235`；`select_existing_native_choice_v1` 目前仅由旧单测调用。`pending_interaction_fallback.py` 与 `vanilla_events/unhandled_fallback.py` 的专用流程并未通过这个旧函数，本叶不接管它们。全局 planner 的 typed event/interaction 优先、独立顶层 modal 关系验证、同一窗口 pending 禁止再提交仍属于既有调用者。

保留规则：过滤不可见、禁用和非选项控件，去除内容相同的 identity 重复、拒绝冲突重复；多项先按原生 top/left，再 rendered_index 和原 Python Unicode/code-point identity 顺序。单个合法选项不依赖几何。generic 路径必须有 blocking proof 和完整目录；只有已有 event 授权路径可使用明确来源的 rendered-order proof。选择保留 native index 与 public number 的 +1 转换，不依据陌生标签猜偏好。

普通 `pending_character_interaction` 始终交还专用 left-reply policy，左右两项中左项禁用时不能通过本叶改选右侧接受。旧 selector 曾开放这种 domain，但没有生产调用；旧 `test_mandatory_choice_policy.py` 的历史 right-accept 期待与当前共享专用实现和用户左侧规范冲突，不继承为 Java 规则。本叶为此有明确拒绝回归。

所有结果只提出选择，不执行 MCP、窗口、文件、HTTP、ledger 或 native transport。`Decision` 中 dispatch、ACK、原窗口消失、物质效果和 replay 信用均为 false；实际 ACK 与同一窗口消失只能由外层执行证据分别确认。来源、query ID、window instance、episode 和完整原始选择目录保存在不可变模型/证据中。未知结果不得因重新调用本叶而获得重放资格。

JSON 边界集中在 codec，拒绝重复/未知核心字段、尾随内容、无效 UTF-8、bool/float/string 整数替代、错误布尔类型与身份越界，区分 missing/null/empty。完整 8 字段 frame 是该 Java 边界必需条件；旧 selector 的任意非空 frame 宽松行为不保留。非负序号/正身份沿原 native frame 检查，整数不经 JS Number，保留 signed64/uint64 的精确整数域。原生边界几何仍使用 binary64，与旧 `float` 排序一致；它不承载金额或 ID。`source_identity`、`typed_window_relation` 和原生证明中的来源扩展作为 opaque evidence 保留，不被此排序叶授予来源/准入资格。

`src/test/resources/mandatorychoice/producer-golden-v1.json` 来自实际调用未修改旧 Python producer 的 17 组输入/输出，记录 producer/fixture SHA 和捕获时间。主输入来自已跟踪的 `tests/fixtures/mandatory_choice_v1/native-query.json`：它是 **offline native wire fixture**，不是本轮实机资格或保存进度。golden 为 JSON 类型域差分，几何浮点的文字形式不作旧字节来源替代。默认 JUnit 只读已提交 golden，不调用未跟踪 Python。

JUnit 另覆盖完整 frame 缺/错字段、整数 token、uint64 最大值、来源/episode 保留、missing/null/empty、只读集合、序列化往返及 Unicode tie 顺序。持久 Maven/CI 由 Root 的唯一构建 writer 集中执行；本叶交付时未自行运行 Maven、未接入旧生产 planner、未执行 Game/RPC/ledger，不能写成实际接管或实机通过。切换需宿主批量接入同一全 Game 动作权威，再跑完整 producer→planner→原执行/证据消费者链；禁止每个选项另启 HTTP/JVM 或静默 Python fallback。

本机捕获事实仅绑定 `machine_id: xenoamess-full-tower-eb9d2c1186`，身份由 `tools/ck3_live_run_id.py machine` 本轮实读；精确观察时间见 golden provenance。源码/小型 fixture 总量限 192 KiB，构建与 scratch 仅使用 Root 的 D 盘工作包。
