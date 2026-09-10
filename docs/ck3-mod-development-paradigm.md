# CK3 Mod 开发、维护与发布行为范式

状态：现行总纲。适用于本仓库当前与后续所有 CK3 Mod 产品；产品文档可以增加更严格的要求，但不得降低本规范的完成标准。

本规范回答三个问题：开始一个 Mod 时先做什么，维护已有 Mod 时如何控制变化，以及满足什么条件才可以称为已经发布完成。
具体命令、游戏版本和产品文件数量以各产品的 `AGENTS.md`、构建脚本及验收计划为准。

## 一、核心定义

CK3 Mod 不是若干脚本文件的集合，而是一份部署到 CK3 版本敏感脚本运行时中的玩家行为合同。

统一工作循环为：

```text
定义玩家体验
  → 查明原版与作用域合同
  → 建立最小可加载骨架
  → 完成一条玩家可见垂直闭环
  → 扩展内容并保持单一权威来源
  → 按风险分层验收
  → 从干净 staging 发布
  → 用玩家实际下载到的 fresh cache 复核
  → 保存 changelog、证据并广播完成
```

不得以“脚本能解析”“CI 通过”“上传器显示成功”分别冒充功能完成、实机完成或发布完成。

本文中的：

- “必须”表示完成门；不满足就不能把对应工作包标为完成。
- “应该”表示默认做法；偏离时要记录具体原因。
- “可以”表示按产品风险选择的能力。

## 二、生命周期与退出条件

| 阶段 | 主要行为 | 阶段产物 | 退出条件 |
|---|---|---|---|
| 0. 立项 | 定义玩家价值、边界和验收句 | 产品合同 | 每项需求都能转换为可观察结果 |
| 1. 原版研究 | 检查 exact-build 原版定义、调用链和 scope | 原版依据与作用域合同 | 不再依赖字段名猜测行为 |
| 2. 骨架 | 建目录、descriptor、命名空间和本地加载入口 | 最小可加载 Mod | 启动器识别，CK3 能加载，无项目解析错误 |
| 3. 垂直切片 | 贯通一个入口、选择、状态变化和反馈 | 第一条可玩闭环 | 玩家能在真实 CK3 中完成完整路径 |
| 4. 扩展 | 增加内容、生成器、UI、资产与兼容边界 | 功能候选 | 单一权威来源成立，边缘状态有明确合同 |
| 5. 验收 | 执行 L0–L3 中与风险相称的层级 | GREEN 或可复现 RED | 结论与实际运行证据匹配 |
| 6. 发布候选 | 翻译、构建 production projection、冻结 tag | staging、manifest、ZIP | 候选可复现且不含测试内容 |
| 7. 发布 | 上传、远端回读、fresh-cache 校验与实机复核 | 公开 Workshop 版本 | 玩家下载字节、页面信息和产品行为均正确 |
| 8. 维护 | 以相对上一公开版的增量合同修复或扩展 | 新版本与 changelog | 旧 ID、存档和兼容承诺得到处理 |

阶段可以在小型 Mod 中快速连续完成，但不能靠跳过退出条件缩短流程。

## 三、立项：先写玩家行为合同

新 Mod 开工前必须写清：

1. 产品 key、中文名、英文名和一句话玩家价值。
2. 玩家从哪里进入功能：决议、事件、角色互动、GUI、on_action 或其他入口。
3. 玩家执行什么操作，会看到什么反馈，游戏状态发生什么变化。
4. 状态属于角色、头衔、信仰、文化、全局还是存档外通道；何时创建、读取、迁移和清理。
5. 玩家与 AI 是否都能使用；若只有玩家可用，AI 闸门必须显式存在。
6. 目标 CK3 版本、所需 DLC、依赖 Mod、已知冲突和加载顺序要求。
7. 是否兼容旧存档；不兼容时玩家会遇到什么，以及是否提供迁移。
8. 明确非目标，防止功能和验收无限扩张。

需求必须写成可证伪的句子，例如：

> 玩家执行决议并选择第二项后获得指定特质；保存并重载后特质仍存在；AI 不会执行该决议。

“增加一个有趣系统”“优化体验”不是验收合同。它们必须继续拆成入口、动作、状态和可见结果。

### 立项最小模板

```text
产品：
玩家价值：
入口：
前置条件：
玩家动作：
成功后置条件：
失败/取消后置条件：
状态所有者与生命周期：
玩家/AI 边界：
版本、DLC、依赖与冲突：
旧存档策略：
非目标：
最低实机验收场景：
```

## 四、原版优先：先证明 CK3 怎样工作

实现任何新机制前，应该先检查当前 exact build 中最接近的原版实现：

- 同类型的 decision、event、interaction、on_action、scripted effect、scripted trigger 或 GUI。
- 调用者提供的 `root`、`scope:*`、saved scope、目标对象类型和可能为空的对象。
- 可见条件、可用条件、AI 条件、成本、取消路径和执行时机。
- 同名条目跨文件的覆盖/合并规则，以及是否真的需要覆盖原版。
- 原版本地化、图像格式和 GUI provider 怎样绑定运行时对象。

应复制“最小结构和语义”，不应复制整份原版文件。能够追加新条目时，不使用 `replace_path`；确需覆盖时，必须记录覆盖原因、原版
文件身份、升级风险和兼容对象。

每个高风险调用链至少记录：

```text
入口 → 当前 scope → scope 转换 → trigger/effect → 写入对象 → 玩家可见后置条件
```

未经原版源码、运行日志或实机行为支持，不得仅凭字段名称推断语义。相关语法和已实测陷阱见
[`grammar/`](grammar/README.md)、[`on_actions-events.md`](on_actions-events.md) 和
[`gui-system.md`](gui-system.md)。

## 五、骨架、命名与加载真值

新产品推荐至少建立：

```text
mod_<product_key>/
├─ descriptor.mod
├─ common/
├─ events/
├─ localization/
├─ gui/                    # 有 UI 时
├─ gfx/                    # 有运行时素材时
└─ thumbnail.png           # 需要 Workshop 预览时

tools/build_<product_key>_release.py
tools/test_build_<product_key>_release.py
workshop/<product_key>_description.bbcode
docs/<product_key>-test-plan.md
docs/<product_key>-acceptance.md
docs/release-changelogs/<product_key>/
```

具体目录按产品裁剪，但必须满足：

- 自定义 event、decision、effect、trigger、variable、GUI 和 localization key 使用唯一、稳定的产品命名空间。
- 仓库内层 `descriptor.mod` 不携带 Workshop `remote_file_id`。
- 用户目录外层 `.mod` 明确指向当前要测试的源目录或 staging。
- 首次游戏验证先证明实际加载路径；不能默认认为播放集加载的是仓库源码，因为启动器可能合并为 Workshop 缓存。
- 开发树、测试夹具、release staging 和 Workshop cache 是四个不同身份，不得混称或互相覆盖。

骨架的退出条件不是“启动器里看得见”，而是 CK3 实际加载该产品后进入预定界面，且项目相关日志没有解析错误。

## 六、架构：一个规则只能有一个权威来源

推荐按职责拆分：

| 层 | 责任 | 禁止事项 |
|---|---|---|
| 产品数据 | 数值表、奖池、文案 schema、稳定 ID | 同一参数在多处手工复制 |
| 生成器 | 从权威数据生成重复脚本、本地化或图像投影 | 手改标记为 GENERATED 的文件 |
| 运行时 | CK3 trigger、effect、event、decision、GUI | 混入测试专用入口和证据逻辑 |
| 展示 | 本地化、tooltip、图标、事件图和 Workshop 素材 | 展示数值与真实计算各自维护 |
| 验收 | 外部夹具、测试事件、日志 marker、runner | 把 acceptance-only 内容发布给玩家 |
| 发布投影 | allowlist、测试剥离、production-only 替换 | 直接上传开发源目录 |
| 证据 | report、日志、截图、hash、失败 artifact | 覆盖失败尝试或事后改写为 GREEN |

若真实效果和 tooltip 都需要同一计算，二者必须读取同一 schema 或由同一生成器产出。稳定 ID 一旦公开或写入存档，默认只增不改；
如必须迁移，应提供显式版本和迁移效果。

## 七、先完成一条垂直闭环

第一项实现必须尽快形成一条完整路径：

```text
入口可见
  → 条件正确
  → 玩家操作
  → effect 执行
  → 状态改变
  → UI/本地化反馈
  → 保存、重载或后续触发仍符合合同
```

垂直切片期间：

- 只实现证明核心玩法所需的最少内容，不先铺开大量相似条目。
- 同时实现成功、取消和不可用条件，避免只测试理想路径。
- 使用正式运行路径；测试入口只能帮助到达状态，不能替代对产品入口和后置条件的验证。
- 先让一条链在真实 CK3 中成立，再批量生成内容和制作完整视觉资产。

## 八、实现时必须明确的运行时合同

每个机制至少审阅以下边界：

### 作用域与对象生命周期

- 当前 scope 的类型是什么，切换后是否仍是预期对象。
- `root`、saved scope、event target 和 iterator 内 scope 是否被混用。
- 对象是否可能死亡、失去头衔、被销毁或在延迟事件到达前失效。
- 同帧写入是否会立即被 GUI、tooltip 或另一个 effect 观察到。

### 条件与副作用

- 可见条件、可用条件和真正执行 effect 的业务前置必须一致。
- 取消、资金不足、对象缺失和重复点击不得产生部分副作用。
- 扣费、创建对象和授予状态应该形成一个可验证的原子业务结果。
- 玩家与 AI 路径必须显式区分，不能把 UI 不可见当作 AI 不可执行。

### 持久化和迁移

- 写入者、读取者和清理者必须明确。
- 保存/重载、角色死亡、继承、切换玩家、跨局或版本升级是否改变状态所有者。
- 新变量加入旧存档时，要处理“不存在”而不是假定为已初始化。
- 任何迁移都要可重复执行或有完成标记，避免重复发放、重复扣除和重复转换。

### UI 和展示

- tooltip 展示必须与执行时真实 trigger/effect 一致。
- GUI provider、data context 和 scripted GUI 的调用链必须完整。
- 原始 localization key、fallback 文本或 acceptance marker 不得出现在玩家画面。

## 九、本地化与资产

日常功能开发只创作、修改和审阅简体中文与英文；只有用户明确进入发布阶段后，才补齐产品承诺支持的其他语言并执行发布级审计。
完整规则见 [`localization-workflow.md`](localization-workflow.md)。

所有玩家可见对象都要检查名称、描述、tooltip、事件正文、选项、确认文本和不可用原因。验证至少覆盖：

- UTF-8 BOM、文件头、key 完整性和重复 key。
- `$KEY$`、`[scope.GetName]`、格式标签、换行和动态 token 未被翻译破坏。
- 真实 UI 中没有 raw key、fallback、截断或越出安全区。
- 图片源文件、生成投影、运行时格式和引用路径一一对应。
- Workshop thumbnail、正文图片和 media strip 是不同交付物，不混入 Mod staging。

图片来源、DDS 投影和静态 parity 见 [`image-assets.md`](image-assets.md)；宣传素材还必须保留来源与授权记录，见
[`asset-provenance.md`](asset-provenance.md)。

## 十、分层验收

### L0：静态与可复现构建

证明文件结构、语法、编码、生成器 parity、本地化引用、稳定 ID、release allowlist 和 deterministic build。L0 可以在 CI 完成，
但不能证明 Paradox 运行时语义或 UI。

### L1：真实加载

使用 production projection 在本地启动 CK3，证明 Mod 被实际挂载、能进入目标界面、引擎完成解析，且项目日志没有阻塞性错误。

### L2：单项机制

真实执行决议、事件、互动、on_action、GUI 或状态转换，断言输入、分支、成本、效果和失败路径。

### L3：玩家闭环与高风险生命周期

沿玩家真实路径完成入口、动作、反馈和后续状态；按产品风险覆盖保存/重载、死亡/继承、玩家切换、跨周期、跨存档或兼容加载。

### P：发布与 fresh-cache 复核

针对 Steam 实际下载到的全新订阅缓存，验证 manifest 允许的 descriptor 规范化、其余文件精确一致，并对公开候选执行必要的 L1–L3
复核。P 层通过之前不能把 Workshop 上传标为发布完成。

详细 runner、证据边界和 L0/L1/L2/L3 定义见 [`testing-workflow.md`](testing-workflow.md)。

### 按风险选择验证

| 变更 | 最低验证 |
|---|---|
| 纯文档 | 链接/格式检查 |
| 不影响布局的文案 | L0 本地化检查 |
| tooltip、动态文本或图片 | L0 + 对应 UI 切片 |
| 数值表、奖池或生成器 | L0 parity + 相关 L2 |
| event、decision、interaction、scope、on_action | L0 + 对应 L2 |
| GUI 注入、持久化、死亡、继承、跨存档 | L0 + L1 + 风险对应的 L2/L3 |
| 正式发布 | 发布计划要求的 L0–L3 + P |

同一结论只做一次与风险相称的验证。已有可核验 GREEN 或可复现 RED 时，不为理论风险重复运行相同检查。

### CK3 启动与离线预验

- 开始任何 CK3 验收前，先判断 `open_kaishek` 是否覆盖该步骤的确定性子集；有覆盖就先运行并记录版本、fixture、命令、结果和不支持项，
  无覆盖则记录 `not-applicable`。离线结果不能替代 CK3 实机 GREEN。
- 所有实机启动必须发生在本地机器，不使用 Remote Play。
- 本机可能需要较长加载时间；自动化默认允许最多 30 分钟启动窗口，并以真实 frontend/HUD/目标界面状态判断是否完成，而不是仅按短超时判 RED。
- CK3 是排他运行资源；使用前登记，退出后证明进程树清理并释放资源。

## 十一、证据与 RED 处理

每个实机结果至少绑定：

- Git commit、实际 runtime tree hash、CK3 版本和 EXE SHA-256。
- 场景、输入、预期后置条件和实际结果。
- `error.log`、`debug.log` 及产品需要的其他增量日志。
- JSON/JUnit、截图、存档或 MCP response 等实际证据路径与 hash。
- 进程清理、受保护用户数据和源/staging 未被意外修改的结果。

失败必须分类为：

1. `product RED`：产品行为违反合同。
2. `fixture/harness RED`：测试夹具、坐标、时序或断言错误。
3. `environment RED`：解释器、依赖、桌面、Steam 或 CK3 环境不满足前提。
4. `tool-coverage RED`：离线 parser、validator、MCP 或 adapter 尚不支持该语义。

不同类别不得互相冒充。失败 attempt 永久保留，不覆盖、不删除、不改写为 GREEN。修复应针对已有实证做最小变化，然后只重跑受影响边界；
ACK、schema 通过、窗口出现或日志无错都只能证明各自声明的条件。

## 十二、日常维护范式

每个维护工作包执行：

```text
读取现有产品合同和最新公开 changelog
  → 复现真实问题或写出新增行为合同
  → 查当前 exact-build 原版与既有权威数据
  → 做最小修改
  → 运行一次相称验证
  → 保存结果与遗留边界
  → fetch + rebase
  → commit + 普通 fast-forward push
```

维护时还必须：

- 保持公开 event/key/variable/稳定 ID 的兼容性；更名或删除前先设计迁移。
- 明确本次变化是否影响旧存档、DLC、依赖、加载顺序和其他产品。
- 修改权威数据后运行生成器并审阅输入、生成文件和文档三者的差异。
- 不顺手扩展与本次需求无关的门禁、安全研究或大规模重构。
- 不因一个外部阻点让不冲突的文档、静态检查或发布准备停滞。
- 工作包验证完成或形成可复现 RED 后立即交付，不积压成大批未提交修改。

Git 只允许线性历史：从最新 `origin/master` 工作，远端移动时 fetch 后 rebase，禁止 merge commit、force-push 和覆盖其他任务的修改。
完整规则见 [`branch-management.md`](branch-management.md)。

## 十三、正式发布范式

正式发布必须形成以下闭环：

1. 确认发布产品、版本、目标 Workshop item 和相对上一公开版的变化。
2. `fetch + rebase` 到最新主线，完成发布级国际化与资产审阅。
3. 完成要求的 L0–L3；云端 L0 不替代本地 CK3 实机。
4. 在 clean exact commit 上建立与 descriptor 匹配的产品 tag。
5. 只通过产品 release builder 生成 production staging、manifest 和 deterministic ZIP。
6. 检查 staging 不含测试标识、开发工具、过程素材或预存的内层 `remote_file_id`。
7. 本地外层 `.mod` 指向正式 staging，经 Steam 初始化成功的 PDX Launcher 上传；不直接上传仓库源目录。
8. 若出现新的 Workshop Legal Agreement，停止并等待物品所有者亲自处理。
9. 回读匿名 API/公开页面，核对 item ID、标题、描述、标签、DLC、可见性、preview 和 media strip。
10. 从空路径下载 fresh Workshop cache，执行严格 manifest 校验及产品要求的实机复核。
11. 上传后从 exact tag 重建 canonical staging，清除 Launcher 临时注入的内层 `remote_file_id`；外层 `.mod` 保留正确 item ID。
12. 创建或更新 GitHub Release，核对远端附件与本地冻结产物 hash。
13. 写入 `docs/release-changelogs/<product-key>/<version>.md`，记录版本、tag、commit、玩家变化、兼容性、限制和证据。
14. 提交发布记录并推送 `master`；核对远端 SHA 后，广播 `done` 并释放 Git、CK3、Steam/Workshop 等共享资源。

启动器、descriptor、缩略图和 fresh-cache 的具体规则见 [`workshop-publishing.md`](workshop-publishing.md)。

## 十四、Definition of Done

### 新 Mod 首个可玩版本

- 产品合同、非目标、状态所有者和玩家/AI 边界已写明。
- 原版依据和 scope 调用链已确认。
- 命名空间、descriptor、本地加载路径和日志基线正确。
- 至少一条玩家可见垂直闭环在真实 CK3 中通过。
- 权威数据、生成器、运行时、展示、测试与发布投影边界明确。
- 版本、DLC、旧存档和兼容限制已记录。

### 维护工作包

- 变化相对当前行为合同清晰且范围有限。
- 最小修改已完成，没有无关扩张。
- 与风险相称的一次验证已经 GREEN，或形成可复现、正确分类的 RED。
- 生成结果、文档和兼容说明同步更新。
- 提交已经 rebase 并普通推送到最新主线。

### Steam 正式发布

- 正式 tag、staging、manifest、ZIP 和 SHA-256 可互相回链。
- 发布所需 L0–L3 已在精确候选上完成。
- Workshop 页面与远端内容正确。
- fresh-cache 严格校验及要求的实机复核通过。
- canonical staging 已恢复，内层 descriptor 无 `remote_file_id`。
- GitHub Release、永久 changelog 和发布验收记录已推送。
- 发布任务已广播完成并释放共享资源。

上述任一项缺失时，应明确写“尚未完成”及缺口，不能用预计、计划或局部成功代替。

## 十五、文档路由

- 知识库入口：[`README.md`](README.md)
- CK3 脚本与作用域：[`grammar/`](grammar/README.md)
- on_action 与事件：[`on_actions-events.md`](on_actions-events.md)
- GUI：[`gui-system.md`](gui-system.md)
- 变量与 script value：[`variables-scriptvalues.md`](variables-scriptvalues.md)
- 本地化：[`localization-workflow.md`](localization-workflow.md)
- 图片资产：[`image-assets.md`](image-assets.md)
- 测试与实机验收：[`testing-workflow.md`](testing-workflow.md)
- Workshop 发布：[`workshop-publishing.md`](workshop-publishing.md)
- Git 与冻结证据：[`branch-management.md`](branch-management.md)
- 多任务通知：[`codex-task-bus.md`](codex-task-bus.md)

产品自己的测试计划、验收报告、发布交接和 changelog 是本总纲在该产品上的具体实例；出现差异时，保留实际证据并更新总纲或专题文档，
不要让新结论只停留在一次会话中。
