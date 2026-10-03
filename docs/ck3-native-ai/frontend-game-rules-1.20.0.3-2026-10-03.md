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
