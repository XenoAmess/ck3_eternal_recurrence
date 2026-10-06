# 《礼与道》恢复：SDK 同帧转换器源码接入

2026-10-06，用户要求读取度假交接并继续任务，恢复此前暂停的一期开发与验收。此工作包仅接入交接中已完成复核的 query→checkpoint 转换器，不启动游戏，不改变产品运行文件或 native 实现。

从 `0349ffc5a35a0b582db7dbadf6c1358896ece012` 接入九个新源码/合同/夹具文件。候选 README 的 ADD_ONLY 目标已存在，因此保留原 README，将候选原文新增为 `SDK-CHECKPOINT-QUALIFICATION.md`，只在原 README 追加链接。三项 inherited reader/parser/save_fields 的字节保持。应用回执及实际测试原文见 [INDEX](INDEX.json)。

外置当前依赖复核及仓库安装后的 15 项 seam 测试均实际退出码 0。复核确认 12 个 DTO 纯函数 AST 与现有 codec 一致、69 项产品业务文件 SHA 一致。这里的测试只证明 SDK payload 转换和失败分类，不证明 G2/G3 已在本轮实机读回，不证明宗主章程成立。

后续使用 actual G2/G3 SDK response、同帧 checkpoint、source/session/PID、public/native revision 和日期绑定填新 request。G2/G3 capture_epoch 独立，不要求相等。缺失字段继续为 NULL，旧 attempt 和模板保持。下一步是新 clean HEAD export/native build、官方 default21/private23 metadata，再沿 0240 分立存档执行正式 I3b。

Open Kaishek：NOT_APPLICABLE。本机三处已知 checkout/JAR 缺席，转换器测试覆盖 Python SDK/存档 DTO 边界，没有已声明支持的 CK3 宗主合议 runtime profile。本报告不产生游戏行为信用。

并行拓扑：新增转换器集成、C3 完整查询、R13 consumer/profile 和 R13 cold/launch 准备四项；各自外置工作区隔离。root 独占最终源码应用、提交和实际游戏操作，screen 尚未领取。C3 在后续独立构建/实机轮次进入。

提交前按仓库 LF 规则对七个新增依赖/合同文件做 CRLF→LF 机械投影，JSON 含义不变；[换行回执](LINE-ENDINGS.json)记录原/新 SHA。已执行的 converter 本体和 seam 测试文件原本为 LF，未再改变。旧候选及原应用哈希继续保留。

首次 staged whitespace check 报两个 helper 末尾额外空行（exit2）；只移除该空行后继续提交，原失败 stdout 在外置 attempt 保留，[修正回执](EOF-PROJECTION.json)记录原/新 SHA。
