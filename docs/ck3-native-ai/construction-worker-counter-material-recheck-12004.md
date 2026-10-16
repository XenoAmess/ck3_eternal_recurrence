# Native工作线程重启后的建造物料回读

2026-10-16，`machine_id=xenoamess-full-tower-eb9d2c1186`。P18 AUTO738在同Game
PID249712、日期53339880、Native revision3/public630失败，实际before-submit计划为
`construction_cold_applied_requery` / `private-query-player-construction-receipt-v1`。
错误为 `construction receipt requires a later paused actor frame`。该异常发生在独立
原生物料查询调用之前，不能把本次查询错误误报为新的建设提交失败。

已验证的旧applied回执仍保存原行动的pre_native_revision806/pre_proof_epoch4339977，
最近回读为native1070；既有Stop/Start重建Native worker后计数重新从1开始。同一Game
PID/创建时间只能证明游戏进程身份，不能证明Native revision/proof counter同代。
transport既比较native3<=旧pre806，又要求新proof_epoch大于旧4339977，因此会拒绝合法
独立回读。旧行动pre字段仍是历史事实，不能为了恢复把它们改成3。

修复只用于durable ledger中已applied、身份匹配的cold_recheck：保留原pre字段、ACK与
start_receipt，跳过旧行动与当前worker的两项计数比较。暂停、map、actor/episode、日期、
游戏进程身份和独立原生source frame仍须通过验证，实际active/completed tuple与同日
金币检查继续执行。未决pending提交仍要求原有later native/proof守卫，不能用此路径
消除未知提交或重发行动。

新回执用真实本次物料query更新post_snapshot/public/native/date/process/proof字段，并
保存 `readonly_material_recheck` 的原query ID及source_frame；它是独立只读查询来源，
不虚构worker标识或修改旧行动。这样随后普通规划比较最新post基线，完成本轮必要旧
回执重读后不会一直等待计数增长回806。队列的sameGame worker重绑分支独立更新治理
tracker，保持zero material/closure/date信用，不把重绑本身升级为建设完成。

7项SDK focused验证使用实际738错误/计划、737标量frame及旧applied记录，Native packet
明确synthetic；验证了独立物料回读、原行动字段保留、两次后续普通plan不再cold重查、
未决native/proof守卫及actor/date/source/material负例。公共仓库另保存可移植精简夹具与
同样7项测试。队列冷回读工具的既有与新增worker场景共13项通过。没有由这些离线结果
宣称P19实机已通过。

外置最小证据位于 `continuation42-cold-prep/p19-construction-worker-counter-candidate01/`
的DELIVERY、实际标量/错误/计划和applied字段投影；完整ledger仍由runtime保留，未复制
所有历史大字段。P19一叶以COW替换，P18活叶SHA未变。当前证据下次复核为2026-10-23，
遵守通用存储策略；这些索引不是跨机器固定运行路径。
