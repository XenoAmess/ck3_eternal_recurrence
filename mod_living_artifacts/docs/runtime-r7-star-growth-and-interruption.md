# R7：星号名称与自动升级通过，后续验收未完成

`machine_id: pc-20260924rtuf-f11af23c08`。本场 `pc-20260924rtuf-f11af23c08--living-artifacts--R0007`，冻结源码 `7559ccccf66348d9dae3b50b1cc2f40145c05df3`，实际 CK3 1.20.0.4/build25734779，PID10940/generation1。实际观察发生于 2026-10-22T07:26Z–08:19Z；[来源及终态索引](evidence/r7-observation-index.json)绑定原始文件、时间与 SHA。正式投影为 57 文件；该源码的 Official Runner CI 39740187692 实际完成 success。

新增名称需求已在实际库存和真实存档中观察到：目标402显示 `★待测活武器`，普通喂养材料无星号。[原图、capture及来源](media-provenance.md)已归档，且[上传 GitHub](https://raw.githubusercontent.com/XenoAmess/ck3_eternal_recurrence/10c37fa927e1df033c2d837c96f8d696ed4eadc2/mod_living_artifacts/docs/evidence/r7-star-inventory.png)后完成匿名逐字节回读。两次真实存档的全部3件已识别活武器名称均只有一个前缀；其中两件属于其他持有者。这只证明所观察物品的名称，不能推为所有 AI、转赠或冷载验收。

公共适配器实际通过原生装备与 LW-G01：同一目标、同一主人31254，从1066.9.15的1级/92经验/growth_sequence=0，经过16次真实原生日推进到1066.10.1，变为2级/0经验/growth_sequence=1，仍装备于原槽。没有点击升级确认，也没有用夹具补经验。实际checkpoint、独立原生装备读回和全部日推进原件均在索引中。

之后正常卸下目标。适配器共完成25个原生日区间，遇到实例67108864的求婚通知后交给Root。Root先运行冻结源码中的既有求婚拒绝策略，再通过原生MCP拒绝；独立快照确认原通知消失、角色/暂停日期不变。该已覆盖通知的定义、双方及婚配角色、原版拒绝效果来源 SHA 和 GUI 左侧拒绝语义均已保存，没有鼠标选择事件或通知。

**执行错误**：Root返回的JSON只有两个成功布尔字段，漏填公共checkpoint要求的 `run_id` 和 `reviewer`。公共入口拒绝为 `Root checkpoint crossed scene`，适配器原结果保持 BLOCKED。这是回执身份缺失，不能写成产品升级失败、通知处理失败或请求超时。补上字段不能回写原结果；原文件原样保留。

Root随后在原有host、原有预算和原有截止下尝试补取卸装证据。首个公共host日推进完成；第二个在原生暂停恢复处失败，错误为 `initial running exact-build owner binding unavailable`。源码中该恢复仅认可一生模式episode身份，而本场普通战役不建立episode。失败的私有起始帧没有导出；[回归输入](evidence/r7-running-pause-frame.json)是稍后实际公共原生读回的运行中帧，明确标为字段投影，不冒充私有起始帧或已通过恢复。

此次暂停失败后游戏继续运行。Root通过原始桌面截图及统一坐标换算点击游戏暂停按钮，随后原生读回确认1066.12.24暂停；从开局观察到的总日期进度为100天，其中仅26个完整区间有受控通过证据，超出预设72天。因此卸装月结、喂养及完整本场均不授PASS，不把失控推进计算为测试吞吐改进。

正常退出亦未通过：Escape输入虽有英文布局/焦点与按键回执，实际未打开菜单；后续映射点击没有完成可审阅的正常Quit流程。原定截止到达后，运行器清理仍在运行的游戏，native job退出码1。原保留句柄观察为未signaled/无退出码，不能称其观察到了OS0；host原始wait1、公共入口wait2、keeper及allocator原始wait0分别保存。屏幕CAS从410释放为411，实际resources为空。释放stdout因子进程默认CP936编码而导致读取失败，但原调用实际成功；保留原字节、无损UTF-8投影及重新查询结果，没有重复释放。

闭场后台实际确认Steam仍离线，存储检查无删除。没有Workshop物品ID或上传成功事实。后续修复将普通战役暂停身份、Root回执编码/解析和真实公共checkpoint闭环回归纳入共享代码及持久CI；源码修复与离线测试不追认本场后续业务、正常退出或工坊发布通过。
