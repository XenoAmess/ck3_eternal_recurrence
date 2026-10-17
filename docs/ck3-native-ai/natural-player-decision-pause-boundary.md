# 玩家决策到达时的自行暂停读回

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-17 10:49:55.721673 UTC，P41 FULL1688／AUTO1731 在已提交的战术哨兵推进中报“fresh paused boundary not stable”。随后实际 SEM1732 在同 Game51028 读到 raw53220840、地图已暂停及交互实例1610612749；相对起点已过6日。窗口7以786日失败保留，原 AUTO 不能重放，也不能把观察到的日历变化写成原命令完整成功。

原错误合并了多个边界校验，没有暴露失败子谓词。本次 Driver 修复针对一个可复现的竞态：读取到运行中的同一玩家决策后，CK3 已自行暂停，既有幂等暂停步骤因此没有再发 `pause-map`。旧消费者硬性要求恰好一次暂停动作，可能拒绝这份真实暂停读回；当前材料没有证明这就是原1731的唯一原因。

公共源码仅在 `_execute_battle_sentinel_advance` 换用一个新增纯函数。一次显式暂停沿原规则；零次暂停必须同时满足此前仍运行、之后实际暂停、同一个已观察到的决策，并继续通过原有 fresh frame、Game／connection／actor／episode 与新决策校验。超过一次暂停动作仍拒绝。本函数不授日期、动作或业务信用，不选择交互，也不重发原时钟。其余已有函数 AST 全等。

便携测试直接导入公共 NativeDriver，执行生产实际调用的 helper：2个方法、9个否例子用例通过，另保留一次显式暂停回归。暂停帧是实际 SEM1732 的字段投影；起点、运行帧及变形否例明确为合成输入。它不是完整 `Service→Driver.execute_step→Native` 调用链，也不是未来分支实机验收。CI 只接入既有路线时钟检查步骤。

来源：候选 `p41-natural-paused-decision-boundary-driver01/DELIVERY.json` SHA-256 `f6a8453446c46f8a4695a6c5f7b3cdf7bee979bab4caa5faecf00c7c6712ba0e`；3033字节两处补丁 SHA-256 `01a7ff9bd385a582b8f26aaa9d0696e133ff1a668cf080a415d7c7ee8c1583cf`。测试夹具内保存原 SEM1732 SHA-256 `f8d0ce86a0d42c8296a331ae17863f5a1209011b59e7e0a7c2213655f3ce40e8`。这些身份仅指该机器外置来源，不把盘符或固定 PID 变成生产参数。

SDK42 仅准备了未启用备用源：1320叶中1319叶复用不可变输入，只有 Driver 原子 COW；保留原 LF，语义与候选 CRLF 源相同。该备用源不代表发生 SDK 切换。同 SDK 部分推进核对由独立控制修复负责，不能当作普通只读失败清理；本公共包不安装控制器、不改现场 source epoch。连续稳定30年优先，其后低于1秒／日、再0.5秒／日，均未达成。

Public COW/AST pins, test fixture hashes and the unarmed SDK42 source identity are recorded in [the transplant receipt](research/p41-natural-paused-boundary/PUBLIC-TRANSPLANT.json).

## 同 SDK 的部分推进核对

Root 随后实际执行控制1734，只读取新 SEM1735／1736，两帧一致：public1426／Native1443、raw53220840、同一个待处理交互。原1731仍是错误，原计划截止53220864没有被写成完成；观察到144raw／6日变化，completed_cycles仍1940，失败待结算周期／日期／业务信用均为0，没有原动作重放或新的暂停、继续、哨兵、取消及UI提交。[实际小回执](research/p41-natural-paused-boundary/ACTUAL-PARTIAL-RECOVERY.json)保留控制、audit及明确的新runtime source epoch身份，不伪称原冻结源码全字节未变。

公共 `g2_saved_campaign.sentinel_partial_recovery` 只提取纯资格与状态投影：核对精确错误、真实 before-submit 计划、原未结算周期和截止日期，再用调用者注入的生命周期规范化及两次内核出生身份观察核对两份新鲜暂停帧。状态投影只清除失败分支、刷新已观察帧并标记存档 dirty；已有计数、业务 pending、治理状态和 checkpoint 日历原样保留。调用者必须先完成资格核对，再将返回帧用于投影；API本身不读文件、不发请求、不持久化、不清HALT，也不安装运行端分派。

这不是只读准入失败：`original_submission_may_have_applied=True`、`read_only_precondition=False`，不宣称原时钟物理上未执行。公共6项／18个变形子例包括 public／Native序号不同、完整Game出生身份负例及持久业务状态保留；原3项cached-parent dispatcher／持久化测试属于外置场次链，不冒称公共纯API重建了整条队列。SDK42仍未启用；同SDK局部恢复不等于连续30年完成。

后续 Root 以 `ROOT-P41-CONTINUITY-RESUME02-ADMITTED.json`（SHA-256 `cf9c847adfbffa77d955d852a557cf3edac111c5b6f3ce36b3bc89dc800f77b1`）重新准入，first FULL1826在raw53221848／1979周期建立窗口8，交接截点报告该窗口已推进266余日；Game／SDK／OBS未重启。另一个presentation watcher30639因读取原子替换中的NEXT元数据时遇PermissionError退出，造成提示滞后；这是独立展示故障，不据此重置游戏窗口或称游戏再次堵塞。本公共包未修改该watcher，不宣称提示持续健康。
