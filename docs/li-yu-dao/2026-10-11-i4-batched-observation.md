# I4 同轮只读查询减少一次提交

R51 的六日观察中，35 个 host step body 合计 48.139512 秒，step 间隙合计 232.652848 秒。[原耗时分解](acceptance/2026-10-11-i4-natural-r52/r51-six-days-duration-report.actual.md)只定位到重复提交边界；子进程、校验及任务总线各自占比仍未测。

本轮将学校决议的前模型和详情树放进一个有序公共 `execute_plan`，最后模型仍在调用方取得真实 `after_tree.revision` 后单独提交。三个查询由三次提交减为两次，初始 snapshot、每步 after_snapshot、暂停与事件检查、PID/generation/actor/date 同一性及两个模型的 native revision 资格保持。未提交决议动作，没有减少逐日观察频率，也未更改原 900/8400/7200 秒预算或 366 日上限。

三查询一次提交的原外置候选 001 无法证明内部 fresh 后模型与调用方原生帧的对应关系，保持 UNPROVEN，未执行。本次只采用修订 002，不增加内部 fresh。六项新 focused 检查及原自然到期合同检查实际通过，已接入官方静态 CI；[实际检查与采用 pins](acceptance/2026-10-11-i4-batched-observation/INDEX.actual.json)。该变更只涉及 Python 的公共计划提交及原断言；不包含原版脚本/IR 执行语义，`open_kaishek` 预验为 not-applicable，不能替代 MCP/native 实机资格。

本包为 STATIC_ONLY。尚未取得新场耗时，不能给出提速百分比、自然到期或 I4 PASS。下一场按公共入口使用实际缓存 seed、新案例和容量准入；Source11/O11 是否可复用由精确公共绑定验证，不自动复制源码或重建 native。
