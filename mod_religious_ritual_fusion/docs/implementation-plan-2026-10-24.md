# 宗教礼仪融合：编码方案

日期：2026-10-24；依据：[可行性报告](feasibility-2026-10-24.md)。用户已授权先写编码与验收方案，再开始实现。本文的功能规则是首期实现默认值，集中配置，后续可调整；不把静态完成写成实机通过。

## 产品范围

首期实现两个入口：**礼仪融合**从玩家当前 Rite 与同 Faith 的另一 Rite 创建第三个 Rite；**宗教融合**从玩家当前 Rite 与另一 Rite 创建独立 Faith，原生 Religion 归属以玩家当前 Religion 为基础。允许研究跨 Religion 的内容选择，但保留实际知识、DLC、教义限定和互斥条件。两来源原对象保持各自身份；不迁移或改写它们。

采用独立决策目标选择器和融合窗口。按文化融合方式对照两来源，从双方核心信条池选三个不重复的最终核心；按教义组选择 A 或 B 的现有值。预览显示来源、最终选择、Rite／Faith 模式、费用及采用范围。双方至少各贡献一个独有的最终内容，公共项不能伪造双方贡献。

默认礼仪融合费用 500 虔诚，宗教融合费用 1000 虔诚，每角色成功后十年冷却；成年、有地、和平、未被囚禁且无未决提交时可进行。以上是本产品费用与规则，不称为原生创建器报价。默认由创始者采用；原版改宗钩子的近亲连带仍需实测，不强制改变双方全部信徒或封臣。

不动态创建 Religion／Religious Family，不伪造原生双父关系，不宣称双方自动视融合结果为正信。两个来源 Rite、创建时 Faith、所选核心／教义及创始者作为模组历史保存。动态名字与图标先复用原生生成，名称编辑及更大传播范围在主链通过后扩展。

## 模块与单一合同

- CK3 原生层：`common/decisions` 选择目标；`gui` 独立窗口；`common/scripted_guis` 执行选择、取消、确认；`common/scripted_triggers` 与 `scripted_effects` 负责共享规则和唯一创建路径；`localization` 提供简中、英文。
- Java 工具层：`tools/` 为 Java 21 + Maven + Quarkus 命令行宿主，提供 `generate`、`validate`、`build`／`verify`。纯解析、合同、生成、发布保持普通 Java 类，不启动 HTTP 服务，玩家运行不依赖 Java。
- 共享产品合同统一规定 `rrf_` 前缀、变量、状态、模式、费用和文件清单。结构化数据使用 record／enum，JSON 严格检查字段、类型、版本与重复键。生成器是目录、候选规则与生成文件的唯一生产者；修改生成文件必须回改生成器再生成。
- 构建只读取显式清单，输出 staging 与逐文件 SHA 清单；拒绝内部 `remote_file_id`，不上传源码、工具、docs、fixture 或 target。仅当前源树业务通过后才具备发布资格，本次不发布 Workshop。

草稿存在玩家 Character 上：`rrf_source_a`、`rrf_source_b` 为真实 Rite scope，`rrf_source_a_faith`／`rrf_source_b_faith` 为打开时 Faith，`rrf_mode` 为 `flag:rite`／`flag:faith`，`rrf_selected_tenets` 为 Tenet scope 列表，`rrf_selected_doctrines` 为 Doctrine scope 列表。候选、最终选项与规则版本使用同一合同，不在 GUI 和提交端各维护一套拼写。

草稿状态为 editing → committing → succeeded／unresolved；取消只清草稿。成功结果保存为 `rrf_last_result_rite`／`rrf_last_result_faith`；真实生成对象与双来源历史另存在结果 Rite 上。未知或部分结果保留实际对象引用和诊断，禁止自动重发创建或扣款。

## 原生接口与合法性

来源二使用已存在的 `select_scope_object` Rite 决策 widget；枚举使用实际 `every_religion_global → every_faith → every_faith_rite`。独立窗口通过 `gui/scripted_widgets` 注册，不编造 native GameView。scope 变量与列表经 `MakeScope.Var/GetList` 送入 GUI，选择通过 scripted GUI 的 root actor 和有类型的 item scope 进入共享路径。

当前已找到 `rite_can_choose_tenet`／`rite_can_choose_doctrine` 原生触发器，但它们以既存 Rite 和该 Rite 的 head 为上下文，**单项通过不代表融合草稿全部合法**。实现必须再验证当前发起人知识、三核心唯一性、双方贡献，以及最终 `selected_tenets/selected_doctrines` 组合。读取原版 `is_shown/can_pick/requires_dlc_flag` 的源绑定目录并生成候选规则时，必须保留 actor 与 Faith／Rite 上下文；遇到不能正确投影的规则明确禁用该候选并显示原因，不能省略或默许通过。不得先创建临时礼仪来获取预览，再把取消产生的对象留在游戏里。

教义每组单选；创建新 Rite／Faith 后的 rite／faith／religion 锁按真实引擎处理，预览明确标记，最终核对不可省略。当前版本核心上限为三，`target_divergence=0`，不随机补齐。原核心未选中后可能保留为 permitted，预览及验收区分状态，不称彻底删除。

## 唯一提交流程

1. 重验 actor、两来源仍存在、玩家仍为来源 A、当前 Faith 仍与草稿一致、两来源实际内容仍覆盖候选、资格、费用、冷却及最终组合；GUI 的 enabled 与 effect 内检查共用触发器。
2. 写 committing，执行一次 `create_dynamic_rite`，三个目标核心通过 scope 参数传入；同组教义通过实际覆盖／修改接口统一应用。先 `convert=no`，保存新 Rite。
3. 宗教融合模式仅对这个新 Rite 执行 `detach_rite_to_new_faith`，保存实际 Faith，不迁移来源 Rite。
4. 读回新 Rite、Faith、核心状态与选定教义。缺失或未知进入 unresolved，保留生成对象，不重复创建，不虚报成功。
5. 结果符合当前合同后，记录双来源和选项，扣一次产品费用、设冷却，再让创始者采用实际结果。只调用已满足前提的原版 helper，不补发整个 `on_rite_created`。
6. 清理草稿显示，保留成功记录。取消、重复点击、提交期间失效、保存后重开均执行同一状态规则。

CK3 脚本不是数据库事务；无法保证异常时自动回滚新对象，因此预验前移，部分结果如实保留。该限制必须纳入验收，不能用自动重试或还原源宗教掩盖。

## 编码顺序与完成定义

先提交本文与[验收方案](test-acceptance-plan-2026-10-24.md)，随后并行实现 Java 合同／生成／构建、GUI／本地化、共享脚本及 CI。第一工作包形成可构建的两模式主链和离线回归；接着按公共验收入口进行原生解析、真实操作及存读档。每个工作包记录实际完成与未执行范围，默认 commit + push，线性 rebase，不 merge。

发布和缓存验收不属于本次编码交付；用户后续授权发布时复用正式 staging、来源业务通过与永久 changelog 流程。完成编码不等于全部玩法已通过。
