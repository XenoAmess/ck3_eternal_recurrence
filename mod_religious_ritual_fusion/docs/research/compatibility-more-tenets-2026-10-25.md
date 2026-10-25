# More Tenets Slots(XA) 兼容研究

观察时间：2026-10-25T09:37:19Z；`machine_id: 4-8e1c2f1861`（本次运行 `tools/ck3_live_run_id.py machine` 实际读回）。本文件记录只读研究和拟定方案，未把静态结论写成组合实机通过。

## 用户要求与适配目标

目标是 [More Tenets Slots(XA)，Workshop 3182367229](https://steamcommunity.com/sharedfiles/filedetails/?id=3182367229)。加载列表中先放该 mod，再放“宗教礼仪融合”。按照用户本轮补充：未加载该 mod 时恰好三个核心信条；加载时允许选择 **3–100 个真实核心信条**，不显示空白占位。容量是上限，不要求填满 100 槽。

不能把“100 个槽位”误读为“存在 100 个必须采用的空白信条”，也不能截断来源礼仪已有的核心集合。最终产物需要保留用户实际选择的完整集合，并继续满足双方独有贡献、知识、DLC、最终组合限制以及每个普通教义组至多选择一项等要求。

## 来源与实际可读取范围

本轮通过已连接 GitHub 读取 [上游仓库](https://github.com/XenoAmess/ck3_mod_more_tenant_slots)，固定研究提交为 `fae5b3bfda87f872f42052c5ab4d729efb3b4d19`，不是未固定的后续 master。该提交 README 将正式产品标为 v11、CK3 1.20.0.4；其历史验收属于原记录中的机器，不能外推为本机组合验收。

本机 `C:/Program Files (x86)/Steam/steamapps/workshop/content/1158310/3182367229` 仅剩 `common`、`gui`、`localization` 目录，正式 `descriptor.mod` 和上限定义文件均不存在。这是前轮用户授权清理后的目录骨架，不能当成已安装可加载的完整来源。本轮未启动 Steam 下载、游戏、Maven，也未更改订阅、ACL 或 Git 历史。

| 上游固定提交内的文件 | Git blob SHA | 核对结果 |
| --- | --- | --- |
| `more_tenets_slots_xa_dev/common/defines/more_tenets_slots.txt` | `9e31a984834e8fc6557f9219ed745347fd018828` | `NReligion.FAITH_CORE_TENETS_CAP = 100` |
| `more_tenets_slots_xa_dev/common/script_values/zz_mts_core_tenets_cap.txt` | `c7a1acbabfd09fc62755868c9908aefb259cd337` | `pam_faith_core_tenets_cap_value = { value = 100 }` |
| `dev_tools/selector_padding.py` | `811d800f0837ee3e40cdfb43a7ae0b2bc0843149` | 明确生成的是惰性普通教义元数据，`tenet_placeholders = 0`；原生空槽继续为空 |
| `more_tenets_slots_xa_dev/common/religion/doctrine_group_types/mts_selector_00.txt` | `193a61097182a667fce25f4386e9dbc4edf51208` | `mts_selector_group_001..010` 均为 `category = not_creatable` |
| `more_tenets_slots_xa_dev/common/religion/doctrine_types/mts_selector_00.txt` | `bf8348b1997ca89b9d34c573392f114a2a7fe3d5` | 对应普通教义 `visible = no`、零费用和零分歧 |
| `more_tenets_slots_xa_dev/common/scripted_effects/mts_selector.txt` | `2de45a0a38fc5e087faa5463a0e5b079ec925f87` | 添加 100 项 `mts_selector_doctrine_001..100` 元数据，不添加核心信条 |
| `more_tenets_slots_xa_dev/common/scripted_triggers/mts_selector.txt` | `384dc97f156f739ba502e562da1fb185f42ff0f9` | 将这 100 个 doctrine 识别为内部元数据，过滤纯元数据更新通知 |

可复查的固定源：[上限定义](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/fae5b3bfda87f872f42052c5ab4d729efb3b4d19/more_tenets_slots_xa_dev/common/defines/more_tenets_slots.txt)、[脚本上限镜像](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/fae5b3bfda87f872f42052c5ab4d729efb3b4d19/more_tenets_slots_xa_dev/common/script_values/zz_mts_core_tenets_cap.txt)、[元数据生成器](https://github.com/XenoAmess/ck3_mod_more_tenant_slots/blob/fae5b3bfda87f872f42052c5ab4d729efb3b4d19/dev_tools/selector_padding.py)。

## 当前 RRF 的具体问题

1. `rrf_ready_trigger` 要求 `rrf_core_count = 3`；`rrf_toggle_tenet_effect` 仅在数量小于 3 时添加；提交后的 `rrf_check_created_result_effect` 再次要求数量恰为 3。这三处共同拒绝 4–100 个实际选择。
2. `rrf_capture_core_scopes_effect` 只保存三个 scope，`create_dynamic_rite` 只传三个 `core_tenet_override_entry`。即使只放宽界面上限，提交路径也仍然丢失第四项以后的选择意图。
3. 草稿初始只收集两个来源的候选，并不默认勾选来源 A 的全部核心。面对很多核心时需要重新逐项选择，也增加误删既有核心的风险。
4. 本产品当前 catalog 实际包含 97 项 `Kind.TENET`，且这 97 项均无 `blockedReasons`。MTS v11 本身没有新增真实 tenet 定义；它扩展槽位并添加普通教义元数据。因此 100 是容量上限，不意味着当前组合必定能凑齐 100 个互相兼容的真实信条。
5. 普通教义是由 `CatalogReader` 读取已来源绑定的定义，再由 `CatalogGenerator` 按组生成替换、可用性和最终组合校验。当前原版 catalog 根本不包含 MTS 元数据；即使将来用合并源重建 catalog，`visible = no` 和 `category = not_creatable` 也会分别生成阻断原因。不能通过遍历全部 `rite_doctrines` 取代该合同，否则内部元数据会进入选择、贡献或美德罪恶预览。

## 最小实现边界

### 数量与真实内容

- 增加本产品统一容量值：正常为 3；在已核对的 MTS 脚本上限接口为 100 时取 100，且本产品不超出 100。原版 `common/script_values/pam_values.txt:2645` 明确说脚本不能直接读 native define，必须使用 `pam_faith_core_tenets_cap_value` 镜像；RRF 不覆盖该全局镜像或原生 define。运行时镜像只能证明有效上限接口，正式组合资格仍须核对精确 MTS staging 和实际加载顺序。
- 提交要求 `3 <= selected_count <= effective_cap`；普通模式自然退化为恰好 3。禁用提示应显示当前数量、最少 3 和当前容量。
- 候选仅来自两个来源 `every_rite_tenet` 的去重并集，并通过由 catalog 生成的“真实 TENET”识别器。当前 MTS 没有真实 tenet 新定义，这可以同时拒绝旧 `tenet_zz_empty_`、未知占位、doctrine 元数据与重复项；不能靠 UI 文本是否为空来判断身份。
- 来源展示、默认勾选、候选、选择、双方独有贡献、预览、提交以及结果后验必须使用同一真实内容定义。来源 A 的全部真实核心默认选中；不能用前三项补齐或截断方式初始化。若将来加入其他宗教内容 mod，需要扩展来源绑定 catalog，而不是静默接受未知定义。
- 空槽不加入变量列表，不生成虚构 TENET 对象，也不在美德罪恶或来源卡片展示占位图标。

### 创建与完整结果核对

`create_dynamic_rite` 的帮助明确说 override 替换创立者最不喜欢的核心，最多原生容量项；它不是任意完整集合 setter。三项 override 不能代表 100 项结果。

最小可行路径是只创建一次新 Rite，在新 Rite 上用原生 `remove_rite_tenet` / `add_rite_tenet` 将实际集合精确对齐已校验的选择集合，保持两个源 Rite 不变。可用原版示例为 `11_dlc_pam_scripted_effects.txt:904–905` 的 scope 参数，以及 `religion_on_actions.txt:811/815` 的遍历项 scope 参数。移除旧项时先快照到本地列表，再遍历快照修改新 Rite，避免原地迭代失效。新增真实核心前仍受容量和最终组合守卫；失败要保留 unresolved，不能扣费并伪装成功。

该路径的自动图标／自动名字生成发生在内容对齐之前，因此本轮新增的自定义四名称和颜色应用须在最终内容确定之后执行；不能把旧内容生成的自动名字声称为对最终新组合重新生成。另一条更复杂路径是 Java 生成 3–100 数量的完整 override 分支，它可在自动生成之前传入全部核心，但会增加几千项重复脚本；若采用，仍须做最终完整集合核对。

后验至少比较：实际真实核心数等于选择数；每个选择项均存在；每个实际项均在选择中；没有空白／未知核心；所选普通教义每组唯一、最终状态正确；两个来源核心和普通教义集合保持不变；只生成一个新对象、只收一次费用。不能仅检查“前三项存在”或总数不超过 100。

### 贡献、普通教义和加载顺序

双方独有贡献继续以真实核心或可编辑普通教义计算；共同核心、隐藏 MTS 元数据、占位项均不算贡献。同组普通教义仍须移除该组已选兄弟项再加入新项，不得因为扩展核心容量而放宽。

RRF 继续使用自己命名空间的窗口，不打包覆盖 `gui/window_rite_creation.gui` 或 `gui/window_faith.gui`，保留 MTS 的滚动网格及其 native selector 修补。避免覆盖 MTS 的 `on_rite_updated`，也不复制其 100 个惰性元数据定义；对新 Rite 内容修改产生的通知要在有限实机窗核对，不能直接屏蔽真实宗教变更通知。

## 拟修改文件与验收

拟修改 `common/script_values/rrf_values.txt`、`common/scripted_effects/rrf_draft_effects.txt`、`rrf_selection_effects.txt`、`rrf_commit_effects.txt`、`common/scripted_triggers/rrf_draft_triggers.txt`；Java 端由 `CatalogGenerator.java` 生成统一真实 TENET 识别器并补专用兼容回归。GUI、语言文案、自定义名称／颜色与亲属封臣预览由本轮对应实现统一接入，避免多处另造识别规则。生成文件必须经生产生成器更新，不能手改。

静态验收覆盖原版 2/3/4 项、MTS 2/3/4/100/101 项，初始化保留超过三项、去重、双方独有贡献、元数据与旧空白占位拒绝、普通教义同组替换、结果完整集合拒绝，以及双方源集合不变。97 项 catalog 的事实意味着真实 100 项组合需要额外合法测试输入；不能为凑到 100 在正式产品添加假信条。

组合实机必须分别核对无 MTS 与有精确 MTS 的实际加载顺序，观察四项以上真实核心创建、UI 滚动且无空项、普通教义替换、美德罪恶预览、完整后态、一次计费及保存／独立冷载。该 mod 的上游历史 100 槽验收不抵扣本产品组合验收。本轮只读研究未执行这些实机步骤。

## 最小外部来源获取清单

2026-10-25T09:49:02Z，`machine_id: 4-8e1c2f1861`，已通过 GitHub connector 读取上游正式 `release-manifest-v11.json` 和正式提交 `d1c9deee5c0214f9418c8df821a8ac9f3f97d334` 的树，逐项比较研究提交与正式提交的 Git blob 身份：**全部 48 个正式载荷文件均一致**，路径大小也与正式 manifest 相符，总载荷 **1,015,384 B**（约 0.97 MiB），另取 manifest 为 9,159 B。

完整路径、每项大小、SHA-256、Git blob 和固定 raw URL 在[最小来源清单](compatibility-more-tenets-2026-10-25.allowlist.json)。这份清单只记录已读取的元数据；`payloads_downloaded=false`，本轮未下载正式载荷。按该清单逐文件取回并逐项核 SHA，可在 4 MiB HTTP 总预算内获得精确载荷，不需要克隆仓库、整仓 ZIP、Steam 库下载或历史截图原片。必须将它作为独立 MTS 来源挂载，RRF 位于加载顺序下方；这不是 Steam 实际下载验收，也不能据此声称缓存下载已通过。

正式构建入口是上游 `dev_tools/validate_and_build.py`，`RELEASE_FILES` 为显式 48 项清单；它调用来源投影 `dev_tools/migrate_to_ck3_1_20.py`、元数据生成器 `dev_tools/selector_padding.py` 和共享框架构建器，核原版 SHA、双构建及 tag。本轮未执行该存量 Python 构建入口，也未在本产品增加 Python 构建模块。对于当前只需精确联合加载的适配研究，优先直接复用已发布 manifest 所 pin 的相同载荷并核全部字节；不得把文档元数据比较冒充重新构建或实机已通过。

## 本轮实现交接

Root 授权后，上述五份 CK3 脚本与 `CatalogGenerator.java` 已按方案修改，并增加 `MoreTenetsCompatibilityTest.java` 的七项生产脚本 AST 回归。真实内容识别器由同一生成器输出到 `common/scripted_triggers/rrf_catalog_membership_00.txt`；`rrf_real_tenet_trigger` 在 Tenet scope 使用，`rrf_real_doctrine_trigger` 在 Doctrine scope 使用。此新增生成文件仍待 Root 用更新后的 JAR 统一生成。

`rrf_core_limit_value` 采用已核对的 MTS 镜像值恰为 100 时上限 100，其余为 3；每次刷新同步角色变量 `rrf_core_limit`，供界面读取。数量仍是 `rrf_core_count`。提交守卫使用 `RRF_REQUIRE_CORE_RANGE`，新增选项达到容量时使用 `RRF_REQUIRE_CORE_CAPACITY`；本地化由 Root 统一维护。初始化、清理和提交依次调用 Root 提供的 `rrf_initialize_creation_options_effect`、`rrf_clear_creation_options_effect`、`rrf_apply_creation_options_effect`。最后一项位于完整核心与普通教义对齐、可选新 Faith 分离之后，完整结果核对之前。

这次实现保留三项合法 scope 作为原生创建种子，随后在新 Rite 上移除所有未选择的核心、补入全部选择核心；先核新对象不等于两个源对象，再允许修改。完整后验同时检查两方向成员关系和数量，不以“三项种子”代表最终集合。只读 `git diff --check` 实际退出 0，五份 CK3 文件保有 UTF-8 BOM，括号计数配平；这些检查不代表引擎解析或 Java 回归已通过。按照 Root 的统一构建安排，子任务未运行 Maven、编译 JAR、生成 runtime 文件或启动游戏，正式构建、完整回归与实机状态由 Root 后续单独记录。

## 第三方新增核心的当前限制

当前核心选择路径仍按固定 catalog 投影 `can_pick`、互斥及来源规则，并对未登记的核心 fail closed；因此第三方自行新增的真实 Tenet 尚不能自动获得本产品的组合创建资格，不能宣称兼容所有礼仪内容 mod。MTS v11 仅扩展容量及增加隐藏 Doctrine 元数据，不新增真实 Tenet，不受这项范围限制。`every_rite_tenet` 本身是实际 Tenet 的核心迭代，MTS 的 Doctrine 元数据不会进入其中；97 项白名单属于本产品静态规则的资格边界，并非引擎的 Tenet 类型边界。后续若要自动支持新增真实核心，应消费实际原生 TenetItem 与当前草稿的 `CanPick` 及最终组合校验，并在初始化、选择、预览、提交和后验一并迁移；只放开白名单、跳过未知核心规则或仅在 GUI 隐藏空项，都不能据此授予完整兼容资格。
