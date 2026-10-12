# G2 普通循环的原始异常保全

2026-10-12：普通循环与有界 SAVE 包装器在业务异常之后写诊断文件；诊断构造、写入或打印再次失败时，原始业务异常可能被收尾错误遮盖。

`tools/g2_saved_campaign/ordinary_loop_root_checkpoint_stop.py` 与 `bounded_ordinary_save_root.py` 现在分别保存本次调用的原始异常对象及 traceback。诊断成功仍沿用 REVIEW／返回 1；诊断再次失败时附加有限的错误及请求引用，并重新抛出原始异常。没有原始异常时，收尾错误继续传播。中断立即重新抛出，finally 只使用本次调用保存的对象。

错误 note 和 stderr 摘录有界且尽力写入；失败文件不自动重写、清理或换名。未生成的响应上下文保持未知。原有业务门槛、队列、请求不重发规则、SAVE 配对和天数计数保持原样。

Source17 的 297 行候选经 Root 全文阅读及两份独立静审后，按精确旧行和 hunk 位置应用到 master；未执行工具入口、测试或游戏验收。默认 `git apply` 两次拒绝窄上下文 hunk，均未改变跟踪内容；随后使用精确文本应用，没有模糊匹配。固定 SDK91 的两个原文件在写入前后均核对 SHA，未修改该 SDK。

实际源码采用回执：`D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/ROOT-SOURCE17-ERROR-PRESERVATION-ADOPTION.json`，3,844 B，SHA-256 `8c758125611acea359f1f857f847aeed569bd2df217702a56ef5af6f98116373`。外置过程原件沿用原复核期限 `2026-10-12T16:47:28.264315+00:00`，不因源码入库续期。

该变更不诊断 R103 的原生快照发布错误，不授予新的运行、M7、继承或天数信用。后续运行必须明确选择这两个新工具的实际提交和 blob，不能把 master 修复外推到旧 SDK 或已经启动的会话。
