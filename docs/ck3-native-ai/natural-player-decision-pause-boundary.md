# 玩家决策到达时的自行暂停读回

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-17 10:49:55.721673 UTC，P41 FULL1688／AUTO1731 在已提交的战术哨兵推进中报“fresh paused boundary not stable”。随后实际 SEM1732 在同 Game51028 读到 raw53220840、地图已暂停及交互实例1610612749；相对起点已过6日。窗口7以786日失败保留，原 AUTO 不能重放，也不能把观察到的日历变化写成原命令完整成功。

原错误合并了多个边界校验，没有暴露失败子谓词。本次 Driver 修复针对一个可复现的竞态：读取到运行中的同一玩家决策后，CK3 已自行暂停，既有幂等暂停步骤因此没有再发 `pause-map`。旧消费者硬性要求恰好一次暂停动作，可能拒绝这份真实暂停读回；当前材料没有证明这就是原1731的唯一原因。

公共源码仅在 `_execute_battle_sentinel_advance` 换用一个新增纯函数。一次显式暂停沿原规则；零次暂停必须同时满足此前仍运行、之后实际暂停、同一个已观察到的决策，并继续通过原有 fresh frame、Game／connection／actor／episode 与新决策校验。超过一次暂停动作仍拒绝。本函数不授日期、动作或业务信用，不选择交互，也不重发原时钟。其余已有函数 AST 全等。

便携测试直接导入公共 NativeDriver，执行生产实际调用的 helper：2个方法、9个否例子用例通过，另保留一次显式暂停回归。暂停帧是实际 SEM1732 的字段投影；起点、运行帧及变形否例明确为合成输入。它不是完整 `Service→Driver.execute_step→Native` 调用链，也不是未来分支实机验收。CI 只接入既有路线时钟检查步骤。

来源：候选 `p41-natural-paused-decision-boundary-driver01/DELIVERY.json` SHA-256 `f6a8453446c46f8a4695a6c5f7b3cdf7bee979bab4caa5faecf00c7c6712ba0e`；3033字节两处补丁 SHA-256 `01a7ff9bd385a582b8f26aaa9d0696e133ff1a668cf080a415d7c7ee8c1583cf`。测试夹具内保存原 SEM1732 SHA-256 `f8d0ce86a0d42c8296a331ae17863f5a1209011b59e7e0a7c2213655f3ce40e8`。这些身份仅指该机器外置来源，不把盘符或固定 PID 变成生产参数。

SDK42 仅准备了未启用备用源：1320叶中1319叶复用不可变输入，只有 Driver 原子 COW；保留原 LF，语义与候选 CRLF 源相同。该备用源不代表发生 SDK 切换。同 SDK 部分推进核对由独立控制修复负责，不能当作普通只读失败清理；本公共包不安装控制器、不改现场 source epoch。连续稳定30年优先，其后低于1秒／日、再0.5秒／日，均未达成。

Public COW/AST pins, test fixture hashes and the unarmed SDK42 source identity are recorded in [the transplant receipt](research/p41-natural-paused-boundary/PUBLIC-TRANSPLANT.json).
