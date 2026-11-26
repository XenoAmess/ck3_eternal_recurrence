# CK3 模组开发、验收与发布手册

本手册覆盖模组脚本、Pages、测试、正式 staging 和 Workshop。操作实机前读[实机与机器授权](ck3-operating-authority.md)。当前产品版本、canonical ID、来源和发布证据优先查产品自己的文档与[发布日志](../release-changelogs/)；[旧产品索引](agents-history-through-2026-11-25.md)保留旧版。代码路径以仓库根为基准。

## 持续排程与产品边界

- 按 11 月 20 日和 22 日用户要求，推进现有宗族化密教与宗教礼仪融合事项，再排经来源核实的白绮接管组和其他未完成产品。AUB、DJC、CHT 为已核组成员，CCC 归组取决于来源证据。礼与道（LYD）固定倒数第二，天朝361（用户原称天朝365，catalog `zhongguo-361`，canonical `3792585972`）最后。已通过的独立交付沿原证据使用，按真实后续需要安排。
- 金融市场 `mod_financial_markets/` 的玩家及所有合格 AI 发行、买卖和债务流程是该独立产品的明确例外。预算、冷却、分批及市场容量约束按产品文档。其他授权的 AI/NPC 例外见下文硬性约束。跨模组可复用合同和夹具按[知识沉淀规则](autoplayer-workflow.md#知识沉淀)复用。
- 已发生的 HTTP 429、部分公开核验、失败提交与 UNKNOWN 按原收据处置。特定旧发布的停止自动 GET 或禁止重传决定见各自发布记录，保持原结果、素材、工坊条目和原媒体顺序。
- 生成器及软件验证入口见[开发手册](repository-development-workflow.md)。需要真实 CK3 时走下文统一验收入口，使用任务实际 owner、机器、fixture 和独立 profile。

## 2026-11-02 宗教礼仪融合实机开发、测试与发布恢复授权

- 用户最新明确：“现在开始你可以使用ck3.开发，测试，然后发布。”本次宗教礼仪融合窗口修复可继续CK3开发、实机验收及同一Workshop条目更新；覆盖下方本次任务的暂停约束。其他任务不据此自动恢复其自动游玩或重放未知动作。
- 继续核执行机器、当前Game/Steam、共享资源和存储；普通实机保持Steam离线，正式发布与缓存下载所必需的在线操作沿既有权限执行并恢复离线。用户已授权开发→测试→发布，不再次要求发布确认；保留真实失败，修复后画面通过与源码／软件通过分别记录。

## 家徽编辑器 GitHub Pages

- `coat_of_arms_editer_of_ck3/` 的 `master` 更新必须由 `.github/workflows/coat-of-arms-editor-pages.yml` 自动构建并部署到本项目 GitHub Pages；禁止手工提交 `dist/` 或维护 `gh-pages` 分支。
- 正式 Pages 门禁必须包含静态 DDS pack 逐文件校验、Vitest、无 CK3/无后端 Playwright E2E、production build 与构建后 pack 复验；任一 RED 不得部署。
- 项目所有者已于 2026-09-15 明确将当前原版 CK3 1.19.0.6 DDS pack 视为本仓库版本管理与 GitHub Pages 发布所授权的素材。其他 build、DLC 或 mod 素材不能由此自动外推为已授权。
- 正式站点必须保持纯前端：不得安装、启动、查看或连接 CK3，不得要求 MCP、Quarkus 或 Java；开发期研究夹具不得进入线上运行路径。完整合同见 `docs/ck3-coat-of-arms-github-pages.md`。

## Steam 创意工坊发布 Changelog

### 缓存验收范围（2026-10-07 用户永久指令）

- 本仓库现在及后续全部 mod 发布的缓存验收，只要求：Steam 实际下载到本机的已发布文件与正式构建一致，以及 CK3 实际加载这份缓存。完整当前规则见 [缓存验收](../workshop-cache-acceptance.md)。
- 不得在缓存验收中重复功能、事件、按钮、特质、数值、冷却期、任命或其他游戏内业务测试，也不得为了缓存验收挂载业务测试 fixture、重跑代表业务 cell 或完整矩阵。实际启动日志能证明目标缓存已挂载/加载时即可结束，不要求另开新游戏、进入地图或进行 native 业务查询。
- 发布前源码与正式 staging 的功能验收仍按各产品合同执行。缓存核对不得把仓库/staging 内容复制覆盖真实 Steam 下载目录。历史失败和当时的旧门槛原样保留；本条覆盖旧文档、操作卡中的缓存业务复验要求。正常关闭 CK3、保持 Steam 离线和释放现场资源继续按已有操作规则执行。

- 本仓库内每个独立 mod 产品，每次正式发布或更新到 Steam 创意工坊成功后，都必须编写一份**相对上一公开版本**的 changelog，
  永久保存为仓库跟踪文件并提交、推送到 `master`。统一路径为
  `docs/release-changelogs/<product-key>/<version>.md`；首次发布没有上一版本时，必须明确标为 initial baseline。
- 每份 changelog 至少记录：产品与 Workshop item ID、当前/上一版本、发布日期、当前/上一 tag 与 commit、玩家可见新增/变更/修复、
  兼容或存档迁移、已知限制，以及正式构建和实机验收证据链接。草稿可以在发布前准备，但只有实际上传成功后才能写入最终发布事实。
- Workshop 上传、订阅缓存复核和对应 changelog 的 `master` commit/push 缺一不可；没有永久入库的 changelog，不得把该次 release
  标为完成。历史 changelog 不得覆盖删除；勘误必须追加带日期的更正记录。
- **Steam Change Notes 是独立交付物**，不能用仓库 changelog、Workshop 主描述或一句摘要代替。每次正式发布都必须把完整的
  玩家可见更新说明写入目标版本条目，并在提交前冻结待发布文本及其字符数、行数和 SHA-256。
- `CreateItem` / `SubmitItemUpdate` 的 `EResult=1` 只证明调用返回成功，**不证明 Change Notes 已公开**。完成发布前必须匿名读取
  `https://steamcommunity.com/sharedfiles/filedetails/changelog/<item-id>`，对目标条目的 entry ID、HTML 解码及换行归一化后的全文、
  字符数、行数和 SHA-256 做精确核对并保存证据。更新既有条目时必须证明该条目正文确实被替换；如果原生 `change_note` 提交没有
  改变公开页面，应通过登录态 owner page 编辑既有条目后重新匿名回读。缺少这项公开回读时，不得把 release 标为完成。

## Steam Workshop Compatible Version

- 完整规范见 [Compatible Version 自动维护](../workshop-compatible-version.md)，全部14个玩家产品的目录、canonical ID、禁止上游ID及构建参数见 [产品清单](../../workshop/products.json)。清单不存会过时的当前公开版本；无ID的开发版不得猜目标。
- 从CK3 1.20开始，兼容标签唯一取自正式发布 `descriptor.mod` 的 `supported_version` major.minor，再查 `ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py` 的单一registry；当前精确普通Steam tag为 `1.20 'Crozier'`，通过SetItemTags维护。未来minor须先确认实际分类值，只更新此registry一次，各builder和native发布自动使用；未知1.20+ minor拒绝构建／发布。旧1.19不预标1.20。
- `tools/workshop_compatibility_tags.py`及14产品builder只渲染descriptor标签，不改变业务字节；native从实际staging再次派生。完整待提交tags须保留非版本tag的原字符串和顺序，包括 `"Balance "` 末尾空格，禁止strip／排序／只提交版本tag覆盖原分类。
- 已验收公开release允许仅tags回补：从该release固定commit提取原始published descriptor到新外置metadata-anchor，不传content；仅StartItemUpdate＋SetItemTags完整列表＋SubmitItemUpdate(NULL notes)。这是metadata修订，不是新内容release，不新增Notes、不需相同业务重验；完整正式发布继续遵守上节所有门禁。
- tags-only必须核owner/app/item，冻结anchor及前后tags，保存实际SDK回执、匿名完整tags与Compatible Version右栏及requiredtags链接exact核对、最终Steam离线证据；成功后追加 `docs/workshop-metadata-revisions/<product-key>/<date>-compatible-version.md` 并实际commit/push master。原发布版本／日期和旧失败记录保留；回调成功或源码标签不能替代公开回读，缺证据标METADATA_PENDING。

## 文案人格（琉焰卿）

所有琉焰卿的台词/事件文案必须贴合此设定：

- **风格**：中二 + 奇幻，具有诱惑力、诱导性；从容不迫，永远像在等一笔迟早成交的生意
- **设定**：以人类的情感为食的咒间仲魔；**不会刻意告诉玩家自己的恶劣性**——恶意只藏在措辞的阴影里，表面永远温柔有礼
- 称玩家"旅人"，第一人称"我"；自称"琉焰卿"；把分数说成"分量/余烬"，把交易说成"典当/垂青/咒痕"
- 祝福诅咒奖池的权威定义在 `docs/blessing-curse-pools.md`，改池必须五处同步（表内列明）

## 本地化开发策略

- **日常功能修改只创作、修改简体中文与英文文案；语义与术语审阅只针对简体中文，英文仅检查格式**。不要主动翻译或润色法、德、日、韩、波、俄、西七种语言；生成结构必须包含九语言时，可暂用英文占位以保持文件可加载，但不得把占位称为已完成翻译。
- 只有用户明确表示“要发布了”或给出等价发布指令后，才补齐其他语言。其他语言只做 key、占位符、格式、编码和加载结构等基本规格检查，不做多语言实机验收。
- **实机验收统一使用简体中文**（2026-10-03 用户再次明确）。英文及其他语言不得成为实机验收矩阵或发布门禁；已有非中文实机记录保留为过程证据，不能计作中文验收通过。
- **普通开发 push/PR 的 CI 不得强制运行七语发布格式检查，也不得因为 release audit snapshot 暂时落后而阻塞功能开发。**非中文发布检查只核对 key、文件头、编码、占位符、引擎标记和可解析格式，不得要求语义、术语、翻译完整度、母语审阅、实机显示或截断签核。正式格式检查只在用户明确进入发布阶段后，由对应发布 tag 或人工 release workflow dispatch 触发；发版前必须补跑并通过。
- 发布翻译优先让 `MiniMax-M3` 承担低风险、机械性的字符串翻译。开始任何翻译修改前只检查 `MINIMAX_API_KEY` 是否存在；若不存在，立即停止且不得修改项目，严禁输出、记录或暗示 Key 内容。
- MiniMax 只能接收最小必要的 key-value、语境和保护 token，并只返回合法 JSON；不得让它分析项目、决定 key/文件、编写或审查代码、操作文件或判断验收结果。所有修改、审计和验证由当前执行者亲自完成。
- 完整调用边界、提示词、审计清单和交付格式见 `docs/localization-workflow.md`，执行发布国际化前必须先读。

## 硬性约束（血泪教训，详见 docs/）

- **一切内容只对玩家生效，AI 永远不得触发**。现有屏障：开局走 `every_player`（不含 AI）；死亡链要求
  `has_character_flag = xa_enabled`（该 flag 只能由玩家点契约获得）**且** `is_ai = no` 双闸门；GUI 桥走
  `GetPlayer`。今后新增任何事件/决议/互动/钩子，都必须挂在上述玩家限定链上（或自带等价闸门），
  禁止给 AI 留入口；新增 on_action 钩子时注意其本身对全场角色触发，effect 必须包 limit
- 一个已授权例外是独立 `ox_here/` mod：AI 可以低意愿使用“牛来”，所有层级每 12 个月检查一次，执行后冷却
  **恰好 1 年且永远不得提高到 1 年以上**。该例外不得外推到主 mod 或白绮独立版；权威权重与实机边界见
  `docs/court-position-mechanics.md`。
- 第二个已授权例外是独立 `mod_zhongguo_style/`：有地、在世、天朝制公爵及以上 AI 管理者可静默运行 361 后台考核；
  伯爵和男爵只能被考核，不能建立 cohort、分配配额或校准别人。该例外只覆盖此 mod，不能外推到主 mod、白绮版或其他政府。
- 用户于 2026-10-04 明确授权独立 `mod_superman_qiang/` 对每个合格角色记录性经验：年满 18 岁、在世的 AI 与玩家使用相同计数及属性转移规则；查看交互由玩家发起。此例外只覆盖本产品两个原版性行为效果接入点，不外推到其他产品。
- 用户于 2026-10-22 明确授权独立 `mod_living_artifacts/` 的 AI/NPC 正常获取、装备、培养活武器，与玩家使用同一觉醒、自动成长、喂养、压制及反噬规则；包括原版允许持有装备的无地 NPC，不能在 NPC 手中休眠。卸下可免费停止成长，同时失去活武器加成；继续装备时仅可付费暂时压制。喂养按原版四档稀有度且无 CD，不提供手动升级许可、免费锁级或六路线加点。此例外仅覆盖本独立产品，当前仍为设计阶段；详见 `mod_living_artifacts/docs/design.md`。
- 用户于2026-10-24明确授权独立 `mod_dynastic_esotericism/` 对全部存活信徒实施宗族归属与背离规则，含AI、无地者与儿童，按同一礼仪／宗族绑定处理。玩家限定不适用于该产品后台同步；监禁、放逐、处决只提供相应犯罪理由，不自动执行处罚。范围与恢复、赦免规则见该产品 `docs/requirements.md`。
- 所有脚本文件 **UTF-8 BOM**；yml 缺 BOM 直接不加载
- script values 目录是 `common/script_values`（**不是** scripted_values）
- `is_tutorial_lesson_completed` 是 interface trigger，只能用于 customizable_localization / GUI，游戏状态脚本禁用
- on_action 同名键**覆盖不合并**，扩展用 `on_actions = { 自定义钩子 }` 模式
- 自定义顶层窗口必须在 `gui/scripted_widgets/` 注册才会实例化
- `Tutorial` 数据上下文只存在于 tutorial_window 本体
- 教程课程自动完成用 `trigger_transition`（课程文件内），不要试图从外部点按钮
- 游戏语言非英语时，customizable_localization 的 key 必须在**当前语言**的 yml 里存在（不吃英文回退）；
  用于事件选项名时该 key 本身也要有静态 yml 条目，否则运行期显示 raw key

## 全部未来mod验收的公共入口（2026-10-08永久规则）

- 所有未来mod acceptance只从`tools/ck3_mod_acceptance.py`的`plan / prepare / allocate / preflight / run / verify`公共入口选用一份全局common runtime manifest及其本机路径映射。产品仅提供fixture、business case data与adapter，不自行选用或复制host/source/native版本；共享问题在共享层修一次。既有产品builder及发布前源码业务合同保持，旧runner/frozen仅保留底层实现和历史证据，不能作为未来新run分叉版本的入口。
- 旧冻结输入、失败attempt与原证据按通用存储策略到期复核和回收；当前必要基线、活跃输入及关键未解决问题原件须有用途明确且有期限的保护，不再默认永久保留。回收不改写历史GREEN/RED/UNKNOWN，引用须准确标明现有原件可用性。新run使用公共manifest绑定的版本；共同host/native对必要既有capability的实际qualification只做一次并复用，不按产品重复whole build/full matrix，也不因公共GREEN减少原产品业务要求。plan或adapter数据可消费不证明实际adapter可运行，pending能力如实保留。
- 公共入口记录各phase实际elapsed，区分共享资格、产品业务、GUI-only真实业务及退出/cleanup；导航ACK、正常退出、host GREEN、静态/plan不得授业务PASS。原预算与case合同按真实绑定记录，未来参数不追认旧失败。缓存继续只验实际Steam已发布cache文件exact formal match及CK3实际mounted/loaded，不重复缓存业务。实施边界见[mod升级提速与公共验收](../ck3-mod-upgrade-fast-validation.md)。
