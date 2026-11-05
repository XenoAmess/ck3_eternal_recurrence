# Incident 原件使用命令 codec 的确定表示

原事件521已收到原生正 ACK，随后 incident 后态读取报 `Plain bounded original incident file required`。三个旧 JSON 均为普通文件且低于原64MiB边界；问题是 before 用 DriverJson 的插入顺序编码计算路径，持久化 ActionCodec 往返后参数排序改变，同值参数查到了另一个不存在的路径。本次不改 parser、hash 算法或读取边界。

新 capture 使用现有 ActionCodec 的命令表示取得参数；已有原件只允许原始表示或该规范表示的两个确切路径。两个不同路径同时存在、任一路原件坏损、source／kind／参数不符均拒绝。记录后的 policy receipt 与 unsettled 行继续使用所选原件的同一表示；不按 actionId 扫描寻找替代原件。

actual 变体 d1f9 为单TU14类编译0，5.5592701秒；新增Test单TU3类编译0，5.9611203秒。两个新用例2P（7.8372551秒），四个受影响旧用例4P（7.1167761秒），XML分别d56dfdca、66fd5086，均无失败、错误或跳过，各phase已释放。测试通过公共 capture→命令往返→after／receipt→cold scan 路径验证幂等、精确旧schema兼容以及冲突／损坏拒绝。旧schema原件是临时 authored DATA，不能冒称旧521的真实 producer。

正式源码只投影八个owned span，保留formal其它字节；新增portable Test及其原3352B golden资源使用正常Maven路径。actual与formal其它代码有差异，因此实际变体6P不授整个formal组合软件通过。没有把私现场JSON或Hosted测试加入仓库。

生产模型首派43.5117672秒、TTFT6.1381764秒，finish=length／6500；整份CONTENT和SSE未读未hash，代码0采用，不重派。测试模型完整stop38.0309006秒，新方法0采用；owner实现新增行为，仅两处旧expectation的规范表达式按任务机械修正。

此单元只能修复未来capture及两个精确表示的已有原件，不能恢复旧521记录的eae59原commitment。严格真实producer诊断仍1F；去掉action_id后的完整canonical字节相等，未重排字段或替换原ID。旧521保留UNKNOWN。另一个显式v1恢复单元由Runtime在真实只读issued scope验收，不能借本6P授其通过。

后到切点：v1最终05已完成类型、四个公开DATA／拒绝用例和独审，Runtime29已正常loader启动；在进入v1回调前，批次恢复错误落到FOCUS-only路由，正常B4 RETAIN170被phase3门拒。原521／ACK／deadline／head522均保留，正在补严格EVENT隔离路径，未授结算、新动作或保存。新epoch169eligible／8saved仍分开，任务继续RUNNING。
