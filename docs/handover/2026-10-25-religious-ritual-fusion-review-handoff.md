# 宗教礼仪融合：人工审核整改交接（2026-10-25）

## 先读结论

用户最新指令是生成交接文档，故停止新增施工和实机尝试。八项整改已有产品代码，但**本轮尚未实机验收通过，不能发布0.2，也不能向用户报告八项全部完成**。最后一次真正进入游戏的是R0012；R0013在启动前被拒绝，没有host或CK3进程。

- 产品：`mod_religious_ritual_fusion`，Workshop **3826756673**。
- 当前公开版本仍为 **0.1.0-alpha**。0.2.0-alpha是本轮开发版本；没有上传。
- 最近产品实现提交：`1c85658bef45dbc0aff5d8216cb16f371e544ce1`，已普通推送master；[RRF官方CI成功](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40201883747)。本交接随后另作文档提交，不能把前述CI当作未来修改的CI。
- 最新完整本地Maven：**78通过、0失败、0错误、0跳过**。只证明软件检查，原生窗口、定制保存、改信与联合玩法仍待验收。
- 未完成的共享恢复工具修改已保全到外置目录，**没有留在生产源码中**。`tools/ck3_mod_acceptance_unrun.py`已恢复到上述提交。

本机观察：`machine_id: 4-8e1c2f1861`，**2026-10-25T14:43:34Z / 北京时间22:43:34**，仓库`C:/workspace/ck3_eternal_recurrence`。没有CK3、公共验收、screen keeper或Maven进程。Steam后台原生查询为`offline=true`；这是当时状态，恢复工作时仍须重新取新鲜凭据。显示模式已恢复原 **1024×768**，没有遗留2560×1440测试模式。最后屏幕租约已精确CAS释放：**13877→13878，task `ck3-acceptance-a15`**。

现场身份与状态原件：`C:/workspace/rrf-development-20261024/review-fixes-a01/zh-live-a01/shared-prelaunch-recovery-a01/HANDOFF-STATE.actual.json`；相邻`HANDOFF-STEAM-OFFLINE.actual.json`为2436 B，SHA-256 `1b75bc95fe32b85ec3db65b667aa273ee0ddab329c2d566a3b1db96b1819358d`。原始release、显示恢复和实际进程wait仍单独保留，不用“进程消失”替代退出码。

## 用户八项要求与现状

完整方案及逐场记录见[人工审核修订](../../mod_religious_ritual_fusion/docs/manual-review-followup-2026-10-25.md)。恢复时以用户最后一条八项要求为准。

| 要求 | 已提交实现 | 尚需真实证明 |
| --- | --- | --- |
| 仿照礼仪改革美化界面 | 来源卡片、分页、右侧结果与费用；后置定制改为真正原生礼仪改革窗口 | 实际布局、滚动、长文字、窗口尺寸及可读性 |
| 创建提示清晰、列出禁用原因 | 按钮提示与可见阻断区消费同一SGUI校验 | 真正悬停与非法组合是否给对原因 |
| 独立决议组及顺序 | 上“融合同宗教的礼仪”，下“融合其他礼仪”；保留ID | 独立组、精确文案、上下顺序的实机图 |
| 决议总是灰色 | 补默认候选与可行性合同、显式AI间隔0 | 合法状态正常亮、非法状态灰且原因正确；尚未确认修复 |
| 删除“检查选项” | 已删，选择后自动校验，提交前重验 | 实际界面没有旧按钮 |
| 四名称、图标、颜色、改信预览、美德罪恶 | 原生四名称/图标/颜色/动态教义/美德罪恶；原版至亲级联预览、可选封臣邀请与结果读回 | 同一结果ID保存、0追加编辑费、实际改信及冷载一致 |
| 兼容Steam3182367229 | More Tenets Slots(XA) v11身份研究；RRF在下；实际核心上限镜像3–100，过滤空白/内部占位 | 实际超过3项的结果完整保留，原版无MTS仍3项；不能以单元测试冒充百项实机通过 |
| DES可选、通用改革扩展 | 中立Doctrine默认注册；DES默认非宗族化，原生动态教义列表可选宗族化 | 联合加载下新增组出现、两种选择及DES后续维护行为 |

通用兼容的实际边界：标准类别中的新教义组由原生数据模型枚举；任意第三方自定义GUI和附加脚本副作用**不会自动合并**。全新第三方信条类型仍受来源目录与投影守卫限制，不能宣称任意mod自动兼容。唯一新增同名GUI覆盖是`gui/window_rite_creation.gui`；已保留MTS v11相对于原版的滚动布局差异，其他改同一窗口的模组仍须适配。

## 实现要点与禁止误判

1. 创建只走一次既有`create_dynamic_rite`；实际所选3–100核心进行完整集合对齐。单次费用同宗教礼仪500、另一模式1000虔诚，十年冷却。来源A/B不得修改。
2. 创建后针对**同一新结果**打开原生`EditRite`草案。会话有一年期限，临时编辑豁免只供当前玩家的这次定制使用。创建/编辑规则、目标SGUI及最终贡献守卫已实现。
3. 原生`can_edit_rite`规则只有actor，没有requested Rite。因此自有界面能核对目标，不能称为底层命令级目标安全。原生报价非0时专用保存按钮应拒绝。
4. 专用保存先标记请求，再调用原生`EditRite`；**ACK、窗口关闭、确认取消均不是保存成功**。必须观察真实延迟`on_rite_updated`与token、结果ID和最终集合/双方贡献守卫通过，才结束会话。
5. “保留默认”只在尚未请求原生保存时可用；请求后关闭为延期，恢复入口必须回到同一对象。原生无修改时不能保存，须至少修改一项。
6. 至亲按原版规则自动级联，不提供虚假的关闭开关。封臣邀请是最终配置完成后的可选操作，须按实际可用性、接受度和原生报价逐人重验；未知提交不可重放。**基线500费用验收结束前不要混入额外收费的封臣互动**。
7. 九份本地化134键有格式检查；中文/英文已写，其他七语部分新增键仍为英文占位，不能声称完整翻译。

生产清单当前 **89文件（35显式+54生成）**。历史75、89、90文件记录有各自来源，不做全局替换。新GUI49575 B，SHA-256 `75e20058a7ff422eee5083d547d2a0986367d2423b78b1cd6276dd300607cda5`；删除了旧`rrf_native_setup_window.gui`及其单独scripted-widget注册。

## 软件与实机证据

下列路径以外置工作根`C:/workspace/rrf-development-20261024/review-fixes-a01`为基准，scene为其`zh-live-a01`。这些机器事实仅属于`4-8e1c2f1861`。

| 证据 | 真实结果与用途 |
| --- | --- |
| `JAVA-VERIFY.a09.actual.json` | 80840 B；SHA `f9ad3ed67d64ec48254c96249e99e34ed698c50e1c09c768cfdf77bc954daf3b`；14:14:37Z，78/0/0/0，原wait0，152输入前后相同。执行起点e88加当时局部修改，不能追认为后来的clean提交 |
| `zh-live-a01/qualification-a05.HANDOFF.actual.json` | 13948 B；SHA `616f554146f42ebdb4307440c35e970e2e3953b934bdbac48d94a8e09f6d2c4b`；1c856 clean，1097路径、GAP0、Java producer0、六条实际消费者均0；仅`SOURCE_BOUND_NOT_LIVE` |
| R0011 / keeper a13 | 12:26–12:32Z进入游戏，fixture聚合READY失败；发现非法GUI转义、事件文件内inline trigger跨文件误用、决议AI间隔缺失，已修。未进入融合界面；原生/保留OS handle/host/keeper0，公共run2，CAS13857释放 |
| R0012 / keeper a14 | e88 clean，fixture READY实际PASS、27项DIAG全YES。A核心6→3、两个B各4→3；不是100项。未融合前旧独立编辑窗口就空白弹出，原生查询确认；Root14项GUI断言全false。公共run2、原生/保留OS/host/keeper/allocator0，CAS13872释放 |
| R0013 / keeper a15 | 1c856 clean，分配后首run因离线TTL过期在launch-intent前拒绝；第二run因不可覆写purpose已存在拒绝。两次原wait2，host/CK3均未启动。keeper/allocator0，CAS13878释放。没有业务通过或原生退出0可声称 |

R0012具体核心计数原件：`scene/R0012-fixture-diagnostics-a01/ACTUAL-CORE-COUNTS.actual.json`，12285 B，SHA `592b67405ec359492ba91b5886c1f4f914dd30a2657db456244ec21c3413305e`。它只证明本场准备修整有效，不追认R0011缺失的内部失败原因。

R0012截图`scene/screenshots/R0012/02-decision-group.png`虽然文件名如此，实际是**错误空白窗口诊断图**，4184906 B，SHA `e10c26ca9c12015ae84eaead6d02c16df17ce56807238f6d561c6dbe194858c5`。不是决议组通过图，不可作为本轮商店素材。旧0.1的六张正式实机图保留；本轮还没有合格0.2商店图。

## 当前阻断：启动前拒绝后的正规恢复

应先读`tools/ck3_mod_acceptance_unrun.py`与`tools/ck3_mod_acceptance_allocate.py`的`pre-intent-background-offline-ttl-refused`分支。不得直接调用底层launcher绕过公共run：那会缺少`CaseClient`、业务adapter和正常关闭消费链。

R0013原件全部在`scene/root-execution-a15`及`scene/live/4-8e1c2f1861--religious-ritual-fusion--R0013`：

- 第一run：`PUBLIC-RUN.started.actual.json`、`PUBLIC-RUN.original-wait.actual.json`、stdout/stderr。第二run使用`PUBLIC-RUN.a02.*`。
- 原allocator：`ALLOCATE.*`，原wait0。keeper的`report.json`与live的`keeper-actual-parent-exit.json`均保留。
- `SCREEN-RELEASE.actual.json`为真实CAS包；`DISPLAY-RESTORED.actual.json`为恢复模式读回。
- `keepers/a15/STOP`是**原始普通文本**，结尾有实际UTC；byteexact副本`root-execution-a15/STOP.original.actual.txt`。不要改为补写的“当时JSON”。
- `UNRUN.a01.*`：原closure实际child wait1，拒绝真实Root回执仅有`original_wait_returncode`而旧合同要求`exit_code`。
- `shared-prelaunch-recovery-a01/UNRUN.a02.*`：候选closure实际child wait1，时间排序过严；allocator进程出生1792938472.469847，Root开始记录14:27:52.468631Z，比出生早约1.216ms。Popen前记开始时间是合法记录，不能伪造时间来满足校验。

候选仅保全，**未做完整测试/严格类型检查，未产合格closure**：

`scene/shared-prelaunch-recovery-a01/HANDOFF-CANDIDATE/`

| 文件 | 字节与SHA-256 |
| --- | --- |
| `ck3_mod_acceptance_unrun.candidate.py` | 77849 B，`8454c5b7b6b82159a12dd2507544bfdf02fbdef519a1e9e5f228718a756a2738` |
| `unrun.candidate.patch` | 10998 B，`7a3d3fdbd375b002b9780778caf96115025694d1ffd0b77826b6523241f9124c` |
| `INDEX.actual.json` | 记录当时HEAD、保全时间、未完成范围和两次失败 |

候选98增/6删，不是可直接应用的完成品。生产`unrun.py`已恢复，当前SHA `00c2ef112969052f2b4e95c66b759686b5fe59b7fcf8f227a2ccc91f78d43900`。

还有未走到的真实来源障碍：R0013 frozen输入图有629项，包含旧`unrun.py`。closure终段会完整校验它们；修改共享reader后会出现旧冻结源漂移。**不能热改旧freeze、忽略脏树或放宽全局来源守卫**。须明确解决恢复reader演进与旧冻结证据的来源绑定，保留原始图及失败，验证闭环后才能分配下一场。不要假设只校验launcher/gate。

## 继续工作的顺序

1. 先读根AGENTS与存储策略；核当前机器、路径、时钟、Git和任务总线，不从旧状态外推。当前普通任务ID`ck3-rrf-review-fixes-20261025`会在交接完成时关闭；后继重新登记。所有子线程已写闭，无待消费测试进程。
2. 解决上面的共享恢复实际故障，保留候选作参考。此旧Python模块不在一期接管名单内，可按实际范围维护；新模块仍Java+Maven+Quarkus。回归须执行真实原始回执→closure producer→allocate消费者，包含错误时间/字段/来源；跑实际修改模块的完整检查及严格类型检查。不能补造wait、STOP或原生退出。
3. 将完成修复提交并普通推送，fetch/rebase禁止merge/force。新clean HEAD重新freeze/Q；复用未变的a09、registry、faith实际证明，新增共享修复的真实证明，不为无变化输入重跑Maven或全量native build。
4. 原89文件stage和紧凑fixture可作输入来源参考，按新revision重新正式构建。新独立state使用准入后的`review-zh-core-a04/state`，不得复用已经消费purpose的R0013/state-a03。目前a04还未创建。
5. 创建新的case-inputs、runtime、prepared；新allocate预计attempt **a16**，以实际返回run ID为准。前置应指向R0013/a15、CAS13878及**合格的新previous-failure-close**。若无中间其他屏幕epoch，省略`--latest-screen-release`；把同一previous-release再次当latest会被拒绝。
6. keeper就绪后用实际支持模式临时2560×1440，保存原模式；关闭时恢复。Root reviewed-context须明确`reviewer=/root`和本场新鲜Steam离线receipt。**后台probe和公共run放在同一个顺序调用中立即执行**，不要在30秒TTL内穿插解释、读文件或其他慢调用。公共run本身仍会preflight；绝不复用过期凭据。
7. 等实际hold与fixture READY后，先确认空白提前弹窗已消失、决议组/亮灰正确，再进入自有选择器。不要把ACK当后态，按本场实际原生快照和保存核对。
8. 完成三核心基线、原生定制保存/恢复/取消、默认非宗族化与可选宗族化、图标/颜色/四名/美德罪恶、改信预览与实际对象对照。再做超过三核心和无MTS的独立代表场景。最后独立冷载保存结果。按实际合同逐项交付，失败如实回false并正常退出，不能为“通过”改证据。
9. 截取多张原始实机图，分别记录机器、run、时间、源与SHA；界面图、结果图、图标颜色、四名、改信和新增教义尽量覆盖。诊断图与可上架图分别标用途。
10. 如用户继续要求更新Workshop，所有新版必要业务验收完成后再发布同一条目；当前交接不授权把未验收0.2视为完成。发布只传正式staging；`remote_file_id`仅用户目录外层.mod，上传后重建无ID staging。缓存验收只做正式文件匹配与CK3实际加载，不重跑业务。

## 选择、MCP与原生定制操作要点

- 所有实机从`tools/ck3_mod_acceptance.py plan/prepare/allocate/preflight/run/verify`公共入口；共享host/native不另复制，不启动旧独立runner。
- 下一场队列沿`tools/ck3_mod_acceptance_queue.py --live <实际live> --plan <新plan> --name <唯一名>`。旧plan可读，不能原样重放旧widget身份。
- 当前草案**默认选中A全部核心**。fixture A=`esotericism,legalism,astrology`；B=`esotericism,legalism,communal_identity`。三项基线选`esotericism,astrology,communal_identity`，即从默认A去掉legalism、加入communal。教义选B的`doctrine_divorce_allowed`。以本场实际顺序核对按钮，不能照旧R8“点前三项”。
- 原生查询参数化决议时，SDK尚未资格化非空selected_terms。可用本场generic native widget selector，须真实读回目标B；不可盲猜参数。
- 真正原生编辑根名：**`rite_creation_window`**。专用按钮`rrf_native_apply`、`rrf_native_keep_defaults`、`rrf_native_defer`；四输入框`faith_name_edit`、`faith_adjective_edit`、`faith_adherent_edit`、`faith_adherent_plural_edit`，每项30字符。
- Widget只能使用最近一次query的`query_generation`和`widget_id`，均为十进制字符串。query另一根会使旧generation失效。每次activate后重新query；`fresh_revision:true`交给原host补revision。
- 事件必须先读真实实例及显示选项。`option_number=native_option_index+1`；原生EditRite若弹普通确认窗，查询该实际根，不要虚构事件。
- 原生没有输入框setter时，按仓库桌面合同取得原始截图、真实尺寸与预览内容矩形，用`desktop_coordinate_map.py --receipt`定位；确认英文LANGID0409与控件焦点，粘贴后全文读回。ACK不证明输入或保存。
- 原core人工阶段有14项必选断言及原hold截止前90秒保留；以本场awaiting文件为准。三核心合同不能因选择4项而把`exactly_three`置true。
- 保留public run与allocator原Popen wait；原生正常关闭和独立OS handle、host、keeper分别读回，恢复显示后STOP keeper并等其原wait，再精确CAS释放。lease冻结clean树期间不改tracked源码或文档。

## 四核心测试的未实施设计

本段仅只读分析，**未编码**。现core夹具与`core.json`固定三项；不能在同一旧合同里创建4项并声称通过。生产保存解析器`SaveInspector/SaveContracts`本身不限制3项，无需新造平行oracle。

最小后继为单一强类型`ExpectedSelection<List<TenetKey>>`：验证3–100、唯一、真实Kind.TENET及来源可达；默认recipes显式3，代表4选上述A/B并集。由同一对象生成结果核心与`rrf_origin_core_tenets`精确谓词，并提供pinned JSON给既有prepare/独立savedAST消费者；同步公共requirement、序列化和测试。涉及`FixtureContracts.Request`、`FixtureEmitter`、`rrfa_observation_triggers.txt`、recipes及`AcceptanceFixtureTest`和`core.json`。

当前夹具来源并集只有4项；5–100不可达时须明确拒绝，不能声称现夹具覆盖了100项。四核心冷载使用本场真实after-save新reference，不能套用旧R8固定Rite153。

## 外置输入与命令锚点

scene=`C:/workspace/rrf-development-20261024/review-fixes-a01/zh-live-a01`；以下均为**历史可读输入，不授予下一场资格**。

| 路径 | 用途/状态 |
| --- | --- |
| `source-freeze-a04/source-delta.actual.json` | 1c856 clean冻结；257714 B，SHA `106daa5833bce7051617d73d4cca3e3b947daa9de50b6589e78c067cd5073aea` |
| `qualification-a05/` | 最新六链实际来源资格；a04失败保留，a05仅移除零独占coverage且引用退役GUI的旧139项证明 |
| `native-source-binding-a03` | 2721 B，SHA `44e975ee9f0c5b86dc3342bc59070cd2b1c6c89ed0a1f425ef51ec63e6da3eb1` |
| `runtime-a03/runtime.local.json` | 12638 B，SHA `1386ddb676db17def29337c482c2e8d74aca50f5915723c26887fac7a0408649` |
| `prepared-a03/prepared-case.json` | R0013已消费的准备输入；不是新场次输出 |
| `inputs/staging-rrf-a05` | 89文件；sibling manifest SHA `a385c844e3d4265dc79b74635ee20644b3fb9eed321aee3f6d9260805ad6f534`；本地review5 tag绑定1c856，未作为新公开发布 |
| `../fixture-core-rite-a04.fixture.json` | 紧凑日志夹具；7287 B，SHA `84a1906d01da9c27566001edac6c479edab38dbb06a32744c8f99324ce2cb1be` |
| `inputs/core-joint-a03.case-inputs.json` | slots→DES→RRF→fixture；当前绑定旧a04存储准入及state-a03，下一场必须换新 |
| `FREEZE.a04.command.actual.json` | 原freeze精确argv、原wait0 |
| `BUILD-RUNTIME.a03.command.actual.json` | 公共runtime精确argv；六qualification、gzip-members、case输入/原生绑定 |
| `PREPARE.a03.command.actual.json` | 公共prepare原argv与wait0；ENTRY默认prepared-a01需显式改为新目录 |
| `root-execution-a15/ALLOCATE.started.actual.json` | 原allocate精确参数；不要重用a15 |

可复用原生DLL：`C:/workspace/rrf-development-20261024/build/native-qualified-a01/build/xar_ck3_bridge.dll`，15711744 B，SHA `ff6916d2ff3cff737803c910ac28452ad1d141fe540b7a0994e05197f91a74af`；原qualification在同级`native-a01/PUBLIC-RUNTIME-QUALIFICATION.actual.json`。未改native时不重复whole build，但新source绑定必须实际消费。

MTS输入在工作根`compatibility-inputs/mts-v11/more_tenets_slots_xa_dev`，上游commit `fae5b3bfda87f872f42052c5ab4d729efb3b4d19`，48文件；`release-manifest-v11.json`9159 B，SHA `2d9c319293b2bce98c2cc041c759b0d6400aa22ce1d9216ba620b8f194823172`。是固定源码联合输入，**不是Steam缓存下载验收**。DES输入为`staging-des-a01`，18文件；descriptor由builder渲染，不能声称与源码字节完全相同。

## 容量、期限和保护

继续遵守[统一策略](../storage-retention-policy.md)与其JSON，不因为剩余磁盘较多就越过任务分项预算。机器相关只对`4-8e1c2f1861`有效。

最新已观察账本head146，准入：`scene/ADMISSION.zh-core768MiB-a06.Q6-M88-W80.state-a04.actual.json`，19734 B，SHA `85232396f876d2df8d64aa52f5e9fbea5e3c3e440b6150b4ef1b85caf849921f`。**2026-10-25T16:30Z到期**，不是交接后长期授权；恢复已过期则先重新审计/准入。总额768MiB：wire80、PNG80、cache160、四份native save288、before瞬时72、metadata88；Q6、support2、共享恢复4均含在metadata内。Java额外52MiB已于head143关闭，不能继续沿用。

head146观察scene141891336 B，metadata剩24422648 B（含共享恢复预留4MiB），wire剩36007936 B；随后少量交接文件增加，**这些不是最终闭场清点值**。wire已有47878144 B，预计下一基线增加24MiB仍在80MiB内；没有授权连续再跑三场，后继每场先按实际检查。原R0012 metadata40MiB曾超额14220744 B，保留RED；后来前向调拨不追认旧预算通过。

R0011/R0012 shader cache各155353904 B已按精确身份清理，闭场小回执在各自`closure-R001*-cache-a01`；mod-content/gfx保留。R8/R10、旧正式75文件与六张照片等历史保护至2026-11-01T04:00Z，按原记录到期复核，不自行延为永久。候选、当前源码输入、原STOP/失败/退出及恢复所需证据是未解决问题当前输入，不得清理；续工先补用途复核期限。用户过往允许清理CK3 Workshop下载不等于现在可删除任意个人/任务目录。

## 交接后的发布限制与运行规范

- 默认Steam离线，普通开发/验收不转在线；新启动前重新后台probe，不能用本交接离线事实或截图作准入。联网发布后立即恢复离线；在线时先核其他机器账号占用。
- 不使用PowerShell；命令shell为`cmd.exe`。长/复杂命令优先结构化argv，避免cmd引用拆词及8191字符上限。Python操作片段仅为既有现场工具调用，不能新增Python生产模块。
- 默认`mvn`最低3.10.0；本机已观察3.10.0、home `C:/apache-maven-3.9.16`、Java25.0.4.1，路径名称不是版本承诺，也不要在构建配置锁该绝对路径。
- 不提交或推送本地review tags作为正式发布；不移动已公开`religious-ritual-fusion-v0.1.0-alpha-publish1`。公开版本未变，不写新版本“已发布”changelog。

接手后的第一个交付应是**真实原件可消费的R0013恢复闭环**，随后是**新原生上下文界面的实际融合与保存**，而不是继续增加静态设计或重跑已经通过的无变化检查。
