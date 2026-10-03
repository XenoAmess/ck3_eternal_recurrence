# R0002 核验报告候选

Run ID：`bf-202609141645-5434332d4d--change-holding-types--R0002`。CK3 `1.20.0.3`／Steam build `25652598`。

产品核心路径与状态矩阵已取得PASS；整轮仍保留一项fixture diagnostic，不能标为干净实机GREEN或发布完成。

父任务在真实决议UI看到Taranto／Rossano，选择Rossano并执行转城市。本文核验前后原生snapshot：同一人物、同一`date_raw=53144328`且均paused，个人金币`1246 → 846`，精确支付400。隔离测试此前加入1000金币，不把它写成正常开局财富。实际engine debug markers证明Rossano由玩家直辖且为city、未选中的首都仍为castle。

另经外置fixture调用六个真实生产effect，并通过同类型拒绝／不变、AI实际actor阻止和非男爵领predicate拒绝，共10项PASS。此矩阵与真实GUI操作是两类证据，不把effect调用写成十次GUI执行。

唯一error来自`events/chtt_events.txt:17`：fixture在已经是castle的地产上无条件`set_holding_type=castle_holding`。捕获error.log中没有产品源码diagnostic；fixture错误和产品PASS均保留。`inbox_marker_confirmed=false`也原样记入JSON；结果根据新增实际debug markers核验，不根据命令ACK判PASS。

已另建`holding-live-fixture-02`，仅对castle初始化加NOT-same-type条件；原fixture不变。结构预验通过，Open Kaishek环境缺root，后继fixture尚无engineGREEN。R0003需从保存的R0002重载，验证Rossano结果持久化并取得干净矩阵。过程清理与正式发布闭环继续等待父任务回执。

精确证据文件、SHA、状态和未完成项见同目录`report.json`；本报告候选未写入仓库docs，未修改runtime或当前运行副本。
