# R6：库存修复通过与原生日推进失败

`machine_id: pc-20260924rtuf-f11af23c08`。2026-10-22 UTC，场次 `pc-20260924rtuf-f11af23c08--living-artifacts--R0006`，冻结源码 `f5c9b83d274b3e823b4160a9cc62851cc35becc2`。游戏仍为 CK3 1.20.0.4 / build25734779，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。来源见[R6 原始证据索引](evidence/r6-observation-index.json)，同机原件在 `D:/workspace/ck3-living-artifacts-20261022/`。没有产品整体验收或发布通过。

05:23:54Z 后台原生确认 Steam 离线，公共入口随后启动 CK3 PID 11856。只提交一次罗贝尔 Start，原生根角色为 31254。独立 Win32 读回客户区 **1800×980**，桌面截图为 1920×1080；新视口设置确实采用，不能把设置文件本身当作这个事实。

实际初始检查点经 MCP 保存、官方 Rakaly 严格解码并与独立原生归属/装备状态交叉核对。目标为宝物 402，等级 1、经验 92，初始未装备。MCP 库存打开前拒绝经过精确异常 consumer 后正确转入原 GUI 打开；原始截图、坐标合同回执及 Root 回复保留。随后装备提交序号 **121**，独立读回在 05:35:18Z 确认同一目标装备于武器槽 3。这支持库存恢复及装备子项，不能外推为成长通过。

公共 `CaseClient.advance_day` 根据实际 capabilities 选择了 **`life-advance-one-day` 原生 composite**，并未走另一个 host campaign advance 分支。因此这场不能用于宣称上一轮 host 通知修复已实机资格化。四个原始日推进均独立确认恰好 24 小时，从 9 月 15 日到 19 日；第五次失败，不计入日数。并未到达 10 月升级检查点，卸装、喂养、NPC、诅咒及其他内容也未验收。

## 真实故障

05:37:09Z 第五次推进报出：`native life-advance second resume-map request failed`，`resume_attempts=2`，第一 ACK 为 `submitted`，第二次请求得到 `CK3 map state is unavailable`。共享 SDK 在收到原请求 ACK 后仅短暂等待，未观察到运行状态就再次提交 resume。现有回归甚至要求这个重发行为，不能只给活武器另做一个 attempt 推进入口掩盖它。

host 的 hold 循环只保留某一种暂停诊断错误，其他控制计划异常会直接退出。此次其退出触发受管 Job 清理；原清理记录显示终止前 Job 仍有 **1 个活动进程**，最终为 0，retained CK3 退出码 **1**。因此已知的是运行器终止了仍存活的游戏，不能宣称游戏独立崩溃或完成原版 GUI 正常退出。host 原 wait 为 1、公共 run 原 wait 为 2；这些失败值完整保留。

## 共享修复及验证边界

SDK 的实际 `_resume_life_advance` 改为一次提交后，在原命令剩余期限内只观察该请求；不因旧 paused 帧重发 ACK 已返回的恢复命令。四个现有真实 driver 入口回归同步修改，覆盖迟到运行帧、原期限、owner 漂移、原 ACK 与无第二提交。没有测试 runner 进入生产模块。

实际 `PlanClient.execute → hold` 闭环补上回归：普通计划异常保留原步骤、原异常、原有限 hold 期限及已消费计划，供 Root 正常退出；不重放计划，不增加期限，不将取消信号吞作普通错误。新失败回执使用单一类型合同；历史窄字段不会被改写为新格式。

此外，原生日推进 consumer 原先只投影 active event，遗漏 pending character interaction。现共享 producer/consumer 在推进前及推进后都绑定真实通知，与原生结果和独立完整帧核对；错误字段、缺少字段、错误类型及不同实例拒绝，零小时边界不计为完整日。新增产品回归经过真实公共路由、真实 projector 和活武器 Session，再进行原窗口独立消失核对，而非只测局部转换函数。它们接入持久 CI；离线通过不冒充新的实机通过。

06:10Z 后的实际验证：产品 **92 项**通过，共享本地 CI 组 **76 条原始命令**全部实际完成且退出 0，其中包含四个 resume driver 回归、实际 execute/hold 生命周期回归和通知 producer 到产品 consumer 的闭环；类型检查覆盖产品 tools 27 个文件，以及共享原生日推进和通知合同模块。完整 host/driver 都运行了 strict mypy，完整模块仍有历史诊断。按各检查实际 cwd 归属输出后，host 五函数范围为旧 69 项、现 58 项、新增 0；driver 改动函数范围为 0 项。最初比较器误把 frozen checkout 的相对路径归到开发目录，原错误比较被拒绝并保留，随后从同一原始检查输出修正归属，未重跑或改写原输出。正式修复比较与完整检查源码副本保存在同机 `environment/r6-runtime-type-scope-a01/`，只有 `comparison-cwd-corrected.json` 可用于范围结论。

## 现场收尾与图片

05:41:04Z 在原 host/public wait 与 native Job/进程树/控制文件清理均有真实证据后，协作停止 keeper，实际退出 0；05:41:36Z 使用原 task-bus，expected sequence **381**，实际释放事件 sequence **383**，屏幕资源为空（中间全局序号由 Root 心跳使用）。05:41:37Z 再次后台确认 Steam 离线；05:41:53Z 统一存储闭场检查无删除。该闭场只证明失败场次资源已释放，`normal_close_qualified=false` 保持原值。

归档了[原始中文库存实机图](evidence/r6-inventory.png)与[原 capture 元数据](evidence/r6-inventory.capture.json)，没有修改像素。它展示正式模组与中文测试输入加载后的库存，拍摄在实际装备之前；不能当作自然掉落、成长、喂养、诅咒或完整正式 UI 验收图。GitHub 上传与匿名回读须另记实际结果；Workshop 尚无 item ID 或上传事实。当前必要原件的用途复核至 2026-10-29 UTC，仍服从通用存储策略。
