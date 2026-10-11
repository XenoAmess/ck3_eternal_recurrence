# R57 successor 拒绝诊断候选

仅补诊断，未修改 MAIN/Source15、未调用 SDK/游戏、未再读 R57 report。
原 OR AST 和错误字符串保留；PlanClient 除五个静态 diagnostic_callsite 参数外 AST 完全相同。
既有 execute except（原2335–2341）读取 ck3_campaign_pause_frame_diagnostic，finally（2342–2344）调用 write，候选复用此路径。
诊断含 source/current typed binding、六项 predicate、首失败项、明确调用位置，未知底层原因仍 NULL。
不改变 pending-ready/readmission、deadline、RPC、重试或成功 JSON；旧完整帧诊断仍用旧 schema。

首轮新3项：成功/五标记项 PASS；两个失败路径测试因抽取 __init__ 缺 JsonLines 依赖 ERROR。
修正为只注入 synthetic IO 初始化；两个生产失败路径方法 AST 未改，唯一重跑这两项 PASS。
覆盖六个独立拒绝原因经真实 execute→advance_event_boundary→advance_campaign_event_boundary→guard→except→finally 写出 JSON；另覆盖真实 postpause helper 拒绝经 execute 写出。
首轮原stderr/RESULT及重建首轮测试的逆向patch精确压缩保留；没有重跑已PASS项或旧套件。

R57原RED保持：day0004 error owner/clock/rejection changed；具体原callsite/predicate UNKNOWN，事件边界仅plan允许。
本候选 STATIC_READY / LIVE_NOT_RUN，不是引擎卡顿或拒绝原因修复。ROOT释放lease后按SOURCE-CHECK beforeSHA审阅应用host patch并create-only加入新test；host原UTF-8/LF不变。
首个作者准备断言在写patch前失败：tool 8c53ce/exit1，签名空格匹配；未单独冻结该作者旧版本，不假造其原件pin。
