# 0f548显示contract sibling-import CI修复与有限验证

machine_id: `desktop-3fevhd2-1c74096080`。来源为2026-10-20的实际CI/候选回执；所有原件按字节归档，未覆盖旧e37成功或0f548失败历史。

精确原source `0f548b643782c479bc3eebd3ffef14d710c13d06` 的Official Runner CI run39469117380/job118788198935在step55“Test losing-war cash allocation and ordinary mercenary decisions without CK3”失败。`decision_observation_feed.py:11`导入`decision_display_contract_v1`时，原测试的specfile加载未提供该真实sibling。该组1failed、165passed、62subtests；Linear history run39469117468成功。

窄日志为HTTP206原bytes308330–316521/316522，共8192B；既非整job日志，也不证明失败前所有未选步骤。[实际尾段与原请求回执](ci-0f548/FAILED-LOG-DIRECT-RANGE.actual.json)保留范围和SHA；SAS只在取证时内存使用，原件不含SAS。

上游`870f66155`已修复同根因，当前baseline为`6022a3d`。本批保留上游test原字节，不应用或stage我方candidate test；我方1972B候选只作为相同根因的独立历史证据归档。该候选从同目录加载真实contract，临时注册canonical sys.modules，退出时恢复；formatter及typed projection生产源码未改，全部原assertion AST保持。[精确补丁](candidate/SIBLING-CONTRACT-IMPORT.candidate.patch)。

原Popen12524/Python3.14实际wait0。真实镜像上的原失败方法AST复现缺sibling；candidate在canonical模块不存在/已有sentinel两种状态均保所有原断言PASS、完整还原sys.modules/sys.path，每次调用真实project_plan2/project_card1/reason_text3。[有限验证](candidate/FOCUSED-ORIGINAL-WAIT.actual.json)。这只是单方法AST seam，绕过无关heavy imports；不是全类、完整exact checkout、Python3.13或新head整个CI绿色。

两个CLOSED原件列原lane的全部外置文件。本精选未复制BUS、镜像fixture/tools或所有helper；未选文件仅保留原source refs，不因manifest中有条目而声称其已入库。fixture/tools原source可从原0f548 Gitblob取回；[原source与真实绑定pins](candidate/SOURCE-AND-PREPARATION.actual.json)明确D整体src与0f有26文件差异，实际只验证函数所需三个global的来源。

本次归档不授游戏、SDK、native hook或业务资格。当前新head的自动workflow必须另行按exacthead读回；不得沿用e37成功追认0f或本次提交GREEN。
