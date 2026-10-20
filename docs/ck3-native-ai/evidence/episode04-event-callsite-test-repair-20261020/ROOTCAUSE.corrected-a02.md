# ec7649 step94：旧公共单日测试夹具漂移

machine_id: desktop-3fevhd2-1c74096080。只读 GitHub诊断与离线测试时间：2026-10-20 16:17Z起；首封包实际时间16:26:03Z；新P总4MiB中的本lane≤192KiB，hard17:15。D仍bc63851081462413d0cc6ebe62e37490707ee6a9 clean，W未写。

官方run39450418160/job118723432377，exact head ec7649fca7e211a5b09423379935539e645158d9，step94 Test shared CK3 acceptance without installed CK3 实际 failure。Clock比较段已经过去不等于全CI成功；本包不重跑远端CI或旧矩阵。

## 实际错误

16:07:40原log末尾，test_ck3_mod_acceptance_event_callsite.py 的8methods/4errors，全部在真实advance_day第481行报 NameError: need is not defined。四个事件观察测试已通过。保留的完整step94段没有其他FAILED/ERROR/Traceback。

根因是测试使用AST只摘CaseClient.advance_day函数体，namespace仅有require。真实client模块第8行正确import native_day的need/obj/integer等；新advance_day又要求guard(90)、execute_plan(...reserve=90)。旧fixture缺这套实际公共调用合同。因此不能只补一个假的need来遮住下一层缺失。

首次候选切到真实完整CaseClient方法后，9methods/2fail：原assertIs要求返回相同Python对象；真实native_day.obj第56–59行按合同构造完整dict副本。a02将这两处改为全值assertEqual，保留全部事件/间隔/flags/单次提交断言，不mock obj、不改生产代码。

## 最小候选

仅tools/test_ck3_mod_acceptance_event_callsite.py：直接绑定CaseClient.advance_day；DayClient提供明确无native能力的guard报告，并检查原reserve90；两个同对象断言改为完整JSON值相等；增一method/6子例验证bool/multiday/无效timeout/非bool flags在报告与提交前拒绝。原AST helper仍仅用于既有_business.observe/require，不再截断正在演进的公共单日方法模块依赖。

最终patch：EVENT-CALLSITE-REAL-METHOD.candidate-a02.patch，3259B，SHA256 951930b8876c7e24e07fec205393d1d15cdd13c20917b8c1dcd1a17fc232b5d6。
真实focused：Popen33892原wait0，9methods PASS（6 invalid-control子例），见FOCUSED-ORIGINAL-WAIT.actual-a02.json及原stderr。第一候选Popen9272原wait1/两identity failures完整保留。所有assertions保留语义检查；没有SDK/CK3/原生请求。

测试从exact ec7649的client/native_day Git blobs在新Python子进程内存加载完整模块；不把bc旧模块当作ec（bc尚无native_day.py且client blob不同）。仅_business精确7108B作为原测试AST数据夹具落盘。source OID/SHA在CANDIDATE-SOURCES.prepared-a02.json。

本地Python3.14.7 -B -O -X utf8；实际CI为3.13.16。本地9methods通过及只读git apply --check/whitespace通过，不代表新head远端全suite通过；需publisher实际合入并由新exacthead CI裁定。

## 日志与保真

gh2.100首次因终端escape guard拒绝stdout（Popen25708/wait1，0B）；FIRST-GH-GUARD-REFUSAL.from-terminal.json明确是由原工具异常输出整理的派生记录，不伪装该原进程当时已写回执。随后同exact job用官方allow-escape-sequences读取一次可消费响应：501506B SHA256 1e3a9d301f771b07f3ebd4d713317cbb32019a8b91b44254c9df0f69e5deac65；未保存全log。

仅保存原response byte[411007,499340)的完整step94段88333B，SHA256 454d8b094f6b6e23f48c07f60e485c066e88f2108c3c40cc15148c1f68e4c502；offset/fullhash在LOG-EXTRACTION.actual.json，原Popenwait在ORIGINAL-WAIT.actual.json。没有整log下载落盘或其他head日志查询。候选/首轮失败/实际终态均分列，旧记录不覆写。
