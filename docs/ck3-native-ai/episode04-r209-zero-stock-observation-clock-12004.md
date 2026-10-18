# R209 两天零库存无扣兵：实际桶相位解释

R209 的四份完整查询原件，已经足以区分“没有轮到目标 callback”和“目标 callback 执行后没有扣兵”。本窗口属于前者：Army0 只在 phase0 的真实桶中出现一次，而四份暂停帧走的是 phase14、15、15、16。**这两天没有目标供给 callback 或 writer，不是零库存损耗已被测试为不存在。**

执行机器 `machine_id: desktop-3fevhd2-1c74096080`。来源为 R209 `R0003/case-output-observe-only-a01` 下请求 0009、0016、0020、0025 的既有 `full-history-derived-normalized-full.json`；本次只离线读取 Root 明确指定的四件原件，没有追加游戏查询。原件每份约 15 MB，没有复制入库。对应精确原件路径/字节/SHA、目标字段和条件投影保存在 [便携目标 extract](evidence/episode04-r209-zero-stock-clock-12004/R209-TARGET-CLOCK-EXTRACT.actual-a01.json)。

| 查询 | date raw | stored D / phase | 到下一冻结 phase0 的自然日数 |
|---|---:|---|---:|
| day01 before /0009 | 53147376 | 389474 /14 | 16 |
| day01 after /0016 | 53147400 | 389475 /15 | 15 |
| day02 before /0020 | 53147400 | 389475 /15 | 15 |
| day02 after /0025 | 53147424 | 389476 /16 | 14 |

四帧的 all30 schedule 均 ready，只有 phase0 的 `matching_positions=[0]`。这里相位恰为 0 来自实际 pointer-match，不是从 ArmyID0 取模猜测。

最后一帧 stock raw 为 0、capacity raw 30000000、rate raw −877192；grace anchor raw53144256，loaded grace30，当前年龄132天。Unit170=0、combat=false、gathering=false、Army gathering count=0；loaded levels `[60,10,0]`、fractions `[0,0,5000]`、fleet suppression=false、commander modifier0。当前 loss inputs 的供给合格人数 E=6746、供给整数预算337；围城另有预算67，raid0。这些是该暂停帧的输入和预算，不是已经扣掉的人数，也不能固定移作下一次实际预算。

两 journal 均显示 observer installed，overwritten=0、unattributed capture failures=0，但目标 Army0 的 event_count 都为 0。全局 callback latest11、writer latest375 是全局计数，不能当作本军执行次数。

沿四份冻结输入分别使用已经闭合的 source 日期/D 公式，首个条件机会都落在 raw53147760、D389490、phase0；该时点相对旧 anchor 年龄146天，冻结门可通过。**这只是未改变 membership、身份、准入和后续上下文时的候选窗口。** 到站前可能跨月首补员，实际兵数、rate、loaded component 或物理 target 仍须当时重新读回。

因此，对于从同一 Jan20 基线、且新鲜同帧仍具有相同桶身份的后续场次，30日上限能覆盖一个有意义的目标机会，优先盯第16日附近的实际 phase0。后续场次必须重新绑定自身 clock/membership；R209 的数值不追认为 R210 的当前状态。

事件级正例与阴性判据见 [30日观察窗口的来源解释](episode04-r210-starvation-observation-window-12004.md)。本页没有新增饥饿物理正例、死亡人数、自然未初始化业务验收或完整周期总损失。
