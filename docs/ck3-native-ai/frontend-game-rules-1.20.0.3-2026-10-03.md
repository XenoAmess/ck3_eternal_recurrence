# `.3` 前端规则原生读取与兼容验收入口

本包为[兼容任务接续](../ck3-upgrade-resume-2026-10-03.md)补充规则页观察。默认构建开关保持 OFF，产品实机和 Apply 均未完成。原361 R0002的13张规则截图显示12次滚轮没有改变可见列表；它证明旧驱动未完成导航，不能证明三个规则已选择或B1已运行。原始回放、首个失败尝试及后续修订保留于 `C:/workspace/ck3-upgrade-20261003/zhongguo-agent-01/`。

## 真实来源与新增接口

只针对 CK3 1.20.0.3 / build25652598 / EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。`AccessGameRules` RVA `0xA98990` 从 application slot `0x5CB87F8` 读 application+`0xA38` 的 `CJominiGameRulesGui`；当前选项集合在 owner+`0x98`，count+`0xA4`，每项16 bytes，分别指向真实 `CGameRule` 与已选 `CGameRuleSetting`。两类构造函数确认脚本key为+`0x18`的CString，setting+`0x40`回指规则。完整反汇编、RTTI与来源绑定在 `native-rule-access-bindings-12003.json`、`native-rule-selection-bindings-12003.json`；这些是本机EXE研究，未借旧OCR生成规则值。

新 `XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1=ON` 要求已有MODEL与SELECTED_START开关ON；`.3` descriptor只在开关启用时发布两项能力。通用MCP接口无输入pointer、路径、脚本key或任意回调：

| 工具 | 真实读取或动作 | 结果边界 |
| --- | --- | --- |
| `ck3_query_frontend_game_rule_selections_v1` | 应用主线程读取当前可见 `game_rules` 窗口的真实选项对 | `ready=false`保留原因；不填默认、不证明Apply |
| `ck3_activate_frontend_game_rules_v1` | 仅从Bookmarks调用真实已命名`game_rules_button`，随后独立查询窗口/controller | 已可见时不重复调用；一次调用后未读到真实模型则拒绝，不以ACK算成功 |

原生读取核对exact GUI ABI、application/owner/rule/setting的实际类型、owner与真实窗口root、数据库对象marker、setting→rule关系、集合边界与唯一规则key。它在同一应用主线程连续读取两次，指针或值变更即拒绝，不对选项作猜测。结果恒为 `applied_settings_proven=false`；当前窗口选项不能替代实际已提交规则或战役存档。

## 验证与冻结

原始query/open接线补丁 `frontend-game-rules-query-candidate.patch` SHA `de0efd3aa0c8b45c10ba34cfc54754bf3bb4cc0066c80c173f05acf26005bb47`。10个MSVC `/W4 /WX` synthetic-memory检查PASS：包括实际off保持off、错误owner/root/type、越界集合、错误setting父规则、重复key、两次读之间变更。Python合同8个拒绝分支、unavailable保持及实际driver方法AST执行PASS；四个接线C++的 `/Zs` PASS。报告为 `native-query-focused-attempt-05/report.json`、`query-integration-focused-report.json`、`native-query-integration-syntax-attempt-02/report.json`。均为离线检查，不是实机。

已经通过的测试并入原native/单位测试入口，未重跑。CMake为使用assert的native测试显式 `/UNDEBUG`，保证Release不会编译掉断言；原已跑测试字节与结果保留。后续接线把规则分支放到现有route分支之后，去掉空`if(false)`起始分支；语义未增加。此三行整理及测试接线未包含在下面已完成的旧冻结DLL中，不能说二者全部源bytes相同。

组合构建使用外置 `courtier-agent-01/source-f4e-frontend-caps-rules-01`，4555文件复核无漂移，源freeze SHA `c3664c8492e7410c283ba8946ed84d388a2f547c0a28cc8d8f5f5d62edd40535`。编译输入fingerprint `6F1B666F306BF4E746B5869D1E6E4AE26403969030836D59E7A975EEFA785698`只标识native输入，不能替代Python/runtime/save指纹。组合构建与已有descriptor聚焦项均PASS，收据 `native-frontend-caps-rules-attempt-01/result.json`。DLL4560384bytes，SHA `fa03664f79fc5c37c6eee74c279fcfc6849a8414affef8efebf12bda20912794`；injector SHA `bd9e1f47b58e101ead5eac863a42360b7a1c748c82fd9c58153f77b48d0c4743`。caps-only及更早产物未覆盖。

永久harness仅增加窄`--frontend-rules-diagnostic`，须与bootstrap和diagnostic-only同时使用：保全实际route/tree，实际Bookmarks时直接调用上述typed打开/查询，再有限hold；没有NewGame、角色选择、Apply、Start或产品测试。前端诊断不使用需要地图snapshot的PlanClient逐行执行器；全局结束仍明确diagnostic-only RED，单项规则观察须按真实结果另行判断，不把预期结束当产品RED或GREEN。外置v3 SHA `7a19371d8e9db3ef13f3d169cd6ee748a73f06b70effb0cdeac16d2eea24ee8f`；CLI负例实际拒绝、help成功，原3项harness测试没有重复。

## 后续仍需真实观察

R0003的实际诊断没有达到controller：加载中一次route=`bookmarks`之后，树是截断的 `_root_`且窗口不可见，下一route不可用；Python opener在原生打开命令派发前拒绝。具体原始报告与后续一致等待修复见[启动接续](../ck3-upgrade-native-startup-2026-10-03.md#r0003瞬态路由不能证明可操作窗口)。不能据此次query的unavailable判断真实规则模型不可用。

下一独立run必须重新领取屏幕、审阅当次Steam离线原图、核对准确二进制/源/用户目录与本机能力，然后读取真实85项默认值或361三个规则。准备文件中的`LastAppliedRules`、原生调用ACK、synthetic数据及schema通过都不等于实际选择。尚缺选择目标规则、Apply/Hide按钮资格及应用后规则读回；这些后续候选不修改现已冻结的DLL或旧证据。

原版Apply/Close按钮没有name，不能伪造名字来走fixedInvoke。后续需实际规则scope树、原生child_path与可见/可用状态，或同等真实资格读回；已找到Apply/Hide函数RVA也不授权绕过原版IsHost/NotGameStarted条件。该工作包没有派生出新的Workshop发布、B1成绩或主/白绮七cell通过。

## 选择、提交与实际实例读取：源码已接入，实机待验

后续候选复用同一个默认OFF的私有开关；没有新增生产默认动作。三键选择输入为 `rule_key`、`expected_current_setting_key`、`desired_setting_key`，从实际rule的选项集合计算有界Next次数，不写原始指针。原版Next方法为 `0x21DD6F0(record*)`；每次调用前后核对同owner/root、选项集合与全部选中对，只允许目标项按真实顺序变化。原版Apply `0x21DBD20(owner*)` 后再Hide `0xBE9CF0(owner*)`；调用前读取实际主机与未启动资格，Apply后owner/model改变即拒绝Hide。主机条件来自 `byte[base+0x5CC14D0]&0xFD==0`；首次启动条件来自 `state_slot0x5C68C50` 和state+`0xC3`。未绕过原版按钮条件。

| 新工具 | 合同 |
| --- | --- |
| `ck3_query_frontend_game_rules_window_v1` | 真实owner/root与可见、enabled、主机、首次启动状态；独立隐藏读回才证明关闭 |
| `ck3_select_frontend_game_rule_v1` | 实际选项有界Next，独立query验证目标与其余全部规则 |
| `ck3_apply_and_hide_frontend_game_rules_v1` | 单次原版Apply→Hide；ACK不证明设置已应用 |
| `ck3_hide_frontend_game_rules_v1` | 单次原版Hide与独立关闭观察，不调用Apply |
| `ck3_query_frontend_applied_game_rules_v1` | 真实 `CGameRuleInstance.selected_settings`，不读取GUI默认值或准备文件 |

actual实例入口 `0x5CB3D78` 是已安装getter的std::function holder；核对holder RTTI、VT和getter `0x27F82F0`后，只读其等价纯getter链：state存在取state+`0xF0`，否则取application+`0x268`。再核对 `CGameRuleInstance` 类型与真实setting数组、setting→rule、数据库marker、唯一key及两次稳定读取。GUI选中值与动作ACK继续恒为 `applied_settings_proven=false`；只有这个实际实例读取ready时才给true，仍须和当次目标完整比对才能证明该次提交结果。

选择/Apply原补丁SHA `1d882f6e4825330d1e2e470412c19325d6f7b7d5c908ea0ce3a93ed97cab33e0`，actual实例补丁SHA `08e0e9789b127cb4f6cf3b12bb410151e6dad8ebd144f42ea45033b76cbdf9cb`。26项动作native synthetic与10项actual实例synthetic、10+3项Python合同检查通过；真实调用接线分别4个C++ `/Zs`通过，均非实机。没有重复运行已通过的规则读取检查。完整来源/报告索引在 `zhongguo-agent-01/typed-rules-delivery-v1.json`。

永久harness新增可选 `--frontend-rules-plan`，仅用于普通Robert bootstrap的pre-Start阶段；checked-in意图只允许显式rule/desired key，current必须由当次query取出。它绕开需要地图snapshot的通用逐行plan执行器，仅调用六个已定义typed规则接口。每个动作在调用前写journal；丢失ACK就停止，禁止重发。ApplyHide之后另一次window query及later actual-instance query必须证明关闭和完整pair一致，再复用既有一致等待取得新Bookmarks/picker证明，随后才交还既有Robert Start。原默认路径不变；诊断、冷checkpoint、SDK/server模式拒绝该参数。14项新聚焦协议检查通过，输入bytes快照、binding/query sequence、无关规则不变、未ready观察、三种丢ACK与不重试均覆盖。源码补丁SHA `09063595effc58e920fa9f6b6306a5bb16d349b9df161e6b1189fcc1ca219724`；外置361意图与来源在 `zhongguo-agent-01/rules-plan-package-01/`，没有把准备配置当actual信用。

## 有界窗口树组合

R0005真实Bookmarks超过512节点，旧截断拒绝保持。新预算为2048行，遍历队列4096/depth64/child4096界限不变；行和pending队列改为惰性heap容器，避免扩大应用主线程栈。完整command_result序列化逐行核对最终bytes（含结尾），超过既有2MiB协议上限返回typed rejection。MSVC实测row88bytes、tree result45104→72、frontend context96064→6256；EXE PE stack reserve4MiB/commit4096。这里只是布局/PE检查，未声称实际stack高水位或Bookmarks完整总数。新native/Python预算边界与实际root-name拒绝检查已通过；新组合f4与pinned master2c28的6个C++接线语法均通过，旧include来源错误保留为单独环境context RED。

组合还提供 `ck3_inspect_gui_window_tree_v1(window_kind)`，只允许decisions、decision_detail、courtier、vivhite_courtier四个固定root；当前root row必须唯一且名字匹配，隐藏root不算modal打开。它复用已迁移named-GUI读取，不进入旧ingame11906分支，没有决议动作、选中状态、文本或hover能力。game_rules可见时，原frontend树接口返回该局部scope；隐藏后回Bookmarks。新能力只提供观察，不证明AUB策略默认值或廷臣tab选择。

最终24文件源码组合补丁SHA `e6eb225f4fc4175041761681215a48fe8a841ad9d3fbafe125083f38b0600ed5`。新外置f4组合为 `courtier-agent-02/source-f4e-frontend-actions-applied-window-budget-rootguard-01`，4567文件，freeze SHA `c2a5fb367e6d78bc432d8c265dda47f6d84f339b2f3915bf27094bfe705dc0d6`。它与当前master有明确基底/接线差异，不能宣称全部bytes相同。新独立DLL构建已开始，尚待产物和实机；旧source、512预算DLL与全部失败attempt未覆盖。新的Python等待默认轮询间隔1秒，只减少完整树写入量，ready仍靠两次真实一致观察。

23:53:58（Asia/Shanghai）唯一jobs2 Release构建完成，346 steps、exit0；新native预算聚焦项执行一次PASS。DLL4,613,120bytes，SHA `bac25eb4de967bd9be9603c8983ab672052dabbd74ec8d8e42cef1e97a501065`；injector39,936bytes，SHA `45383f0700dc6660c7182cd812390ae96a84fe8bfe3d248d98d8add642b28e46`。MODEL、SELECTED_START、TARGET_ROBERT、GAME_RULES为ON，旧死亡modal为OFF。最终[产物包](C:/workspace/ck3-upgrade-20261003/courtier-agent-02/frontend-native-final-combo-packet-01.json) SHA `4474b5d6ac06b215df1cb3eaeb93f4ce39fd743a5a29f1c5ff0dce252f0234b5`，4567源文件复验通过；完整源差异表仍保留。

原 `result.json` 的Release断言收据筛选只识别 `/c`，实际CMake MSVC命令使用 `-c`，故原收据RED保留。单独脚本只重新读取同一冻结raw log（SHA `2624cdbb86f48aea8bc085c9a8a1d2cc8562e32aed3e9490eac348a549608f45`），另存 `result.checked-release-flags.json`：四个测试目标10条实际compile argv均在 `/DNDEBUG` 后有 `/UNDEBUG`。没有重建、替换二进制或重跑测试；纠正只属于收据解析。实机与七cell仍0/7。主仓Python-only检查通过。

10-04 00:09 [R0006实际观察](../ck3-upgrade-native-startup-2026-10-03.md#r0006完整书签树与实际规则选中值)已完成一次typed NewGame、完整1846行Bookmarks、规则打开及三次独立86对GUI选中值读取，283行规则scope完整。85项准备默认值一致，额外安装规则单列来源。Apply/actual-instance/Start仍未运行；可选第四只读control工具名错误导致全局RED保留，不影响之前原语的独立证据，亦不提升产品通过口径。

10-04 00:30 [R0007](../ck3-upgrade-native-startup-2026-10-03.md#r0007实际规则提交与普通罗贝尔地图)实际完成一次Apply→Hide、独立窗口关闭与actual-instance86对完整比对，再以新Bookmarks证明进入stockRobert暂停地图。默认难度Select是实读验证的no-op，Next次数0。实际playerID31254只属于该run；未来业务ROOT动态绑定。启动原语报告GREEN，产品/七cell仍未增；死亡modal关闭、正常quit缺口不变。
