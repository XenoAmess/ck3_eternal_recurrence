# 补正预览检查器的已声明 AST 逆投影

`574c015bd7e6e37eb6cbb3f5b88bdd868b1a4bab` 的实际 Li Yu CI [run37702997797/job113070638610](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37702997797/job/113070638610) 在 `test_c3_i3b_preview_scope.py:135` 拒绝制度 trigger：检查器只撤销旧 optional-target guard，没有撤销本次有实际 R26 反例依据的 `NOT{AND{四条原条件}}` 修复。旧检查器失败及原始日志完整保留于 [CI 证据](574c-exact-ci/REPORT.md)。

本次只修改该检查器。在唯一 ready→NOT→any_in_list(rites,dormant0)→NOT→AND 的完整已声明 AST 形状中撤销一层 AND，再核原 C3/I3 两个 SHA 指纹；四个条件、次序、operator 与其余表达式均继续严格核对，不刷新 baseline 指纹。原脚本 50 案例和 19 个去 guard 反例只执行一次；新增 11 个错误变更检查也通过。[源码验证报告](source-checker/REPORT.md)为 SOURCE_ONLY，不能推断游戏业务通过。ROOT 应用后精确 bytes/SHA 与该已测候选相同，复用结果，未重跑旧测试。

同一 574c 的 Linear History CI 成功，Official Runner CI [run37702997764/job113070638653](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37702997764/job/113070638653) 在无关 RMTM 第579行继续失败：计数3、预期2，20测试/1失败/2跳过。两项 RED 分开记录；本次不修改 RMTM，不把 CLA bypass 或旧198 CI投影为本次成功。后继提交的 CI 状态以其实际新 run 为准。

正式产品 staging 在 clean574 上已实际构建 71 文件，manifest SHA-256 `103bd5e6fcc2ba7646a9987f43b0b4ba28893b6ac7f89bc45d5a4d0311dae133`，其 `git_sha=574c…` 来源不改。新提交只变检查器和文档，下一 clean export 仍必须以实际新 HEAD 完整核对这71行，不能把 reviewed anchor 的旧 HEAD 当作新 native/source 资格。资产 helper 为唯一新增产品 key；旧69业务比较宇宙及87/88保护不删减。

R0027 尚未分配、启动。新 native 构建、metadata、profile、宗主保护、冷重载、争统与修习实机均未取得；整体 NOT_GREEN。
