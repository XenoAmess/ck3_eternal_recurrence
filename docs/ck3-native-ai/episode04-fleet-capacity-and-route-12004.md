# 海上扣补给不等于已取得陆地增长机会

`machine_id: desktop-3fevhd2-1c74096080`；2026-10-21的[来源绑定候选说明](evidence/episode04-next-negative-supply-20261021/fleet-capacity-a07/FLEET-CAPACITY-AND-ROUTE.candidate-a01.md)与[原索引](evidence/episode04-next-negative-supply-20261021/fleet-capacity-a07/SOURCE-INDEX.actual-a01.json)分别保留，不表示新Game查询或动作。

已持原版capacity getter读取当前统帅的aggregate keys467/468；没有直接按“海上300、陆地100”切换的分支。登陆可能有额外效果，当前没有完整执行链可排除，所以实际登陆后必须独立读回stock、capacity和最终rate。

R226的Army18在原08:47快照中route为`complete_empty`，source_count0、move_target null，没有到港中的已存路线。这不保证将来的脚本或命令。已有日期阈值和条件海上负率也不证明下一callback必发生，不能把首次海上扣量直接算成陆地B增长或R05。

新的有限窗口仍需实际负率、实际扣量、合法到达后的新headroom和独立正向endpoint差值。此专题只补机制与来源；没有新B、R05或ABC信用，普通planner不自动加载。

[a08有限两省候选](evidence/episode04-next-negative-supply-20261021/two-province-a08/FINITE-TWO-PROVINCE-B-ROUTE.candidate-a01.md)提出2624→2623作为待核路线，没有执行Move。Army18海上到2624的实际fresh preview仍缺；两个点必须各自先确认headroom，不能用首点输入替代第二点。首点的+20可能已经把stock回满300，因此“七日一次海上扣量”不自动足够形成两个增长点。
