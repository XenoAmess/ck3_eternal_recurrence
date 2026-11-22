# 债务危机20剧情的软件验证

2026-11-23（北京时间），machine_id: `4-8e1c2f1861`。

现有 `CrisisAssetsScriptTest` 实际12项全部通过，0失败、0错误、0跳过；原7项保留，新增5项。测试执行生产脚本的AST，逐一覆盖20种上下文下的剧情分支、加权选择边界、缺少作用域或字段、技能阈值，以及21种禁止进入终局的情况。选择剧情不改变角色存活、现金、债务和资产。

玩家、未成年、尚有可用资产、仍有持仓或挂单、未达到逾期与复核条件等情况，执行真实终局入口的外层条件后均没有剧情选择或写入。两种语言各20组标题和描述只检查结构与唯一性，英文未作语义或实机验收。

本次复用单模块Maven与已有缓存，`mvn.cmd -o -T1 --batch-mode --no-transfer-progress -f mod_financial_markets/tools/pom.xml -Dtest=org.xar.ck3.markets.debt.CrisisAssetsScriptTest test`。Maven原始wait为0／28.336183秒，测试12项耗时0.560秒；本次实际重新编译53份测试源码，产品源码在整个测试窗口保持不变。未执行游戏、死亡或新闻派发，不能据此宣称20剧情的引擎实测、全游戏气泡送达或完整Mod验收通过。

[实际JUnit、源码窗口和退出码](../../docs/maintenance/evidence/2026-11-23-financial-markets-crisis-scenes20-software.json)。
