# R0030：分阶段 factory 诊断在 D2 首现政治继承差异，终局保护 RED

源码 `fa0f5e1ee098ab6fab4635bedce939eab857610a`，clean export `C:/lr30s2`，native build `C:/lr30b2`。本轮以 R29 已签署 B3 保存为历史种子，执行专用诊断 D0–D6；没有重演当前正式四callback链。历史R29正式PASS保持历史，本轮 formal B3/B4/B5、成功newT cold、C3/I4信用均 **NULL/NOT_RUN**，whole mod **NOT_GREEN**。

| 实际诊断阶段 | actor完整缓存 | 主要实际观察 |
|---|---:|---|
| D0 新cold控制 | native45=saved45 | 六项diagnostic conditions TRUE，原87保护TRUE；政治7与signed seed完整AST相同 |
| D1 doctrines | 45 | cache/政治7不变；原87仅1项tenet/doctrine projection FALSE，原值保留 |
| D2 create/holder/resolve | 40 | **首次差异已在SAVE前原生cache出现**；saved40一致，五政治Title heir改变；新domain Title18373；realm四laws不变，same_faith law前后均不存在，Faith107 head仍NULL，尚未SetHoF |
| D3 SetHoF | 40 | Faith head变为T18373/holder31254，四propsTRUE、title law count0；无新增政治/cache差异 |
| D4 cleanup | 40 | 无新增政治/cache差异；不能据此声称所有actor AST行均未变 |
| D5 law95 | 40 | law95加入T；无新增政治/cache差异 |
| D6 result/terminal | 40 | result1；终局原保护82/88 TRUE，保存43/48 TRUE；五政治及actor保护仍RED |

D2 actor缓存移除38561/39045/39171/39352/39527，无新增ID。Title2230/2231/2235/2262/2264仅heir字段变化；2232/2263完整AST相同。完整顺序及唯一字段投影已保存到 [FACTS.actual.json](FACTS.actual.json)。原生before/after缓存、当前stage event context、SAVE/G2/G3及唯一存档解析严格各用对应阶段原receipt和frame；D2变化先于其SAVE而被观测，且先于D3 SetHoF。该边界定位不推断 D2 内部 create、holder、resolve 哪条native指令产生变化，也不推导realm laws丢失。

D1原87的预期doctrine差异没有降级或抹去；D2以后诊断raw original87继续保留全部FALSE。D6另保留标准终局模型独立载体 `D6-TERMINAL-STATE.observed.json` 与 `D6-TERMINAL-TYPED-PROTECTION.observed.json`，分别43/48和82/88；不把诊断STATE的空checks当通过。T18373真实typed/native实体、holder31254、四项propertiesTRUE、完整law95=`temporal_head_of_faith_succession_law`仅为局部终局事实，不能替代政治保护成功或用作成功cold/C3/I4输入。

七个阶段作者各唯一body read1且原exec实际完成，合计7次已保全正文解析；本报告/比较/归档不新增正文读取。局部每阶段native cache與saved完整顺序相等，不等于全mod或正式授权PASS。原SDK、native、request、frame、STATE/TYPED与完整stdout/stderr保存，不重跑reader/比较器/测试。

原生编译8targets与focused6实际PASS分别保留；Defender WMI登记7项失败导致outer exit1，不能把outer1改作编译失败或抹为整体GREEN。FA0官方CI的Official step41仍因三项obsolete fixture tests失败；LiYu/Linear成功分列。单独修补candidate的三项focused0属于新source candidate验证，不能追改FA0官方CI。两个CI包原完整log/index及既有ZIP元数据单独保留，不重复扫描旧ZIP或重新运行CI。

失败cold BOM001/002、attach preadmit001、CAS lowercase001、typed freezer把.py源当JSON的001及后续source003修正均完整保全；各originalexec/stdout/stderr与后继成功分列，没有静默覆盖。游戏、Client、game holder、keeper原过程均最终0；新鲜Steam离线已由ROOT实际审阅，CAS3950与无owners/census[]、typed check/create0由最终闭合ref绑定。正常闭合不补业务信用；autosave只按原typed observer字段保留，不能凭退出补成功保存。

本包复用R29原字节collector，闭合后才冻结实际报告、有限R30 packroots和完整原JSON，ROOT执行一次ZIP原字节验证。存档、EXE/DLL/LIB、source tar、截图和旧ZIP仅采集原件path/bytes/SHA外置引用，永久保留但不读取。主仓写入/import/commit/push由ROOT负责。未创建归档时，ZIP与导入状态仍pending；本报告不声称发布或整体验收完成。

ROOT在真实typedclose后已实际导入CI/BOM修补13files（actual import002原回执另存）。import001因错误preimage在写入前拒绝；002按当前MAIN原001builder精确preimage导入。该后续源码变化不改加载FA0的旧官方CI失败或R30诊断RED，也不补新HEAD/新编译/新实机信用。

本包另绑定 ROOT 已验证的闭合原件状态：`ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY`。没有传入时仍为 NULL；归档不执行 verifier、不追认 typed/业务资格，也不代替原 HANDLE 或原执行过程事实。
