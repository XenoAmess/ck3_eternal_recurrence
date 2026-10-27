# 决策详情重开：共享 SDK 验证记录

`machine_id: 4-8e1c2f1861`；观察时间截至2026-10-27T10:56:29Z。本记录接续[R0031实机失败](live-review-R0031-navigation-2026-10-27.md)，任务仍继续执行，八项要求尚未全部完成，不是0.2发布验收。

R0031取消草案后，原生详情模型实际关闭且definition为空，SDK却将同帧重新选择视为不可重放动作。共享修复区分可逆选择与Confirm：已有详情通过新鲜只读观测返回；先前选择有独立完成证据且详情确已关闭时，允许创建关联的新选择声明。UNKNOWN仍拒绝重放，Confirm仍保持一次提交。新增回归覆盖真实service及礼与道消费者、并发声明和四次独立Python进程中的continuation。

执行代码是基于`79a7ce38d4d7864129708e59df94289e3383b5e2`的`SCOPED_WORKING_TREE`。命令分别保留实际前后源码Pin与原Popen wait；这不是clean提交上的新执行。后继六链资格须逐文件核实最终Git文件与这些实际输入相等。

| 实际验证 | 结果及范围 |
| --- | --- |
| 当前CI完整11模块组 | 152 passed、4 skipped、118 subtests；四个跳过是旧sway专用用例在其他letter参数上的不适用分支，不计通过，严格汇总保留FAIL |
| 本次涉及的完整4个决策模块 | 58 passed、94 subtests、零跳过 |
| 两个合同整模块strict及NativeDriver两个完整方法提取 | 通过；不外推为整个NativeDriver strict通过 |
| 分类器完整classify及实际常量、require提取 | strict通过；新增测试类strict另有4处调用旧无类型pin/qualify的RED，未忽略或伪报整模块通过 |
| 公共构建/恢复完整5命令step | 36＋77＋28＋28项通过，两完整模块strict通过；公共三个reader的既有mypy命令通过 |
| 完整RRF Maven verify | 99项、零失败/错误/跳过，生成新Quarkus产物 |
| 完整5模块产物消费者及compat strict | 48项通过；compat整模块strict通过 |
| 完整12命令原生wire消费 | 全部原wait0；三组98／11／6，实际SDK导入来源正确、14个execution包及readonly4实际消费，两个原CTest通过；原Native2679生产及9df continuation身份保持，不称重编译或新实机 |

本机原件根为`C:/workspace/rrf-development-20261024/review-fixes-a01/review-validation-a16`，总预算128MiB。主要原件：`sdk-affected-four-a01/COMMAND.actual.json`、`rrf-verify-a01/COMMAND.actual.json`、`consumers-a01/COMMAND.actual.json`和`native-wire-a01/EXECUTION.actual.json`。新wire seam为111576 B，SHA256 `0237e989f72904cbea609aac59307cbd8acf4685b5dbdf6d5d2cf2125ba279ae`。

两次验证监控中断均保留原失败：旧pytest current链接不能计费，随后临时文件句柄拒绝。操作工具分别修正为不跟随的链接元数据计费，以及仅对WinError 2/3、32/33保留不完整采样记录；最终扫描、未知错误和reparse守卫保持。实际完整重跑通过后才计上述结果。首次39个点没有summary且未持久保存child wait，不重构其退出码。

Root操作元数据256KiB作用域实际超额65536 B（含parent口径69632 B），历史RED保留，旧目录停止写入。独立512KiB新作用域在统一容量检查后由CAS257→258准入；全Root12MiB、owned6GiB、gross8GiB、项目84GB上限及12Z期限保持，未将旧作用域追认为通过。此项不授游戏准入。

并行工作由共享SDK修复、Java/Python资格生产者维护、操作计费修复与后续准备候选分工完成；Root串行消费实际测试原wait。当前没有新增CK3业务信用。下一门槛是最终源码绑定、新独立场次容量及公共prepare，随后实机验证取消后重开、融合与邀请后态。
