# R05 条件目标月变与试驻点

本批机器 `desktop-3fevhd2-1c74096080`，观察/实现于 2026-10-15 UTC（本地 10-16）。这是旧已封 R05 preparation patch 之后的独立增量；不覆盖旧封包，不表示已经部署、换将、行军或扣兵。主树基线为 `d9322bcfb3e17a3fe78607cea777bbfaf7be0a11`，R05 consumer 基线另外包含已封 final patch `1dbc510f6a9fd596df7ebcf274749c72506d9b1720dc0a4e9ecc8f5016f07b7c`。

## 可以实际选择条件试驻点

现有 `plan_r05_zero_stock_preparation` 入口新增远端条件月变分支。它沿用现有 paused frame lease、真实 route preview、战争路线审计、当前原生供给资格及原有零库存时钟 consumer；不另建行动框架。完整条件负率可返回普通 `move-army` step，抵达后必须重读真实 stock/cap/月变及供给时钟，才能进入实际扣兵观测。候选条件值与 `observed_current_monthly_raw` 分列，抵达前后均不宣称物理死亡。

`project_conditional_target_land_rate_12004` 的前提是同一暂停帧的 target preview 与 selected Army query。目标当前 `native_supply_usage_soldiers` 单独保留。完整 selected union 中每支尚未位于目标的 Army，其实际 flags2 合资格当前兵力只加一次；已位于目标的 Army 不重复加。不会从当前省用量扣除再加入，也不把目标当前用量直接当作抵达用量。union 要求实际双 FullID、完整 own roster、逐 ArRg 原生资格/current、flags2 总数一致；共享 eligible ArRg、重复 Army、身份冲突和不适于普通抵达的 signed32 总量溢出均拒收。Province 中不相关的坏 occurrence 不抹去完整 own witness。

假设必须随输出保留：普通抵达只插入所选 Army 一次；其余已捕获的目标用量、上限、owner、commander、roster、loaded 参数在抵达时保持。战争变化、驻军出入、兵力变化、换将和天气变化后需重新查询。此投影不重建未来 Province roster，不计算行军途中 stock，也不把成功 bucket 机会数换算为日历天数。

## 实际 .4 源闭合

复用 Root 已绑定不可变 `ck3.exe` 身份，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本批仅定点读 `[24E5180,24E5FDA)` 完整 3674 code bytes；body SHA `36ffa60acf90c96a61299625427706a7891c83c8d337d38bb4b5b62c24e72fb3`，时间 `2026-10-15T20:28:26.997779+00:00`。原件及 PE/identity 绑定在外置 `target-rate-delta-a08/FINITE-READ.actual.json` 和 `source/full_land_and_foreign_rate_24E5180.{bin,json,asm.txt}`。没有重新整 hash EXE，没有执行 EXE，也未重读原已闭 24E5FE0 调整函数。

`24E5AD2` 原生 limit getter 的 signed32 返回值先扩展并乘 Q。`24E5AED` 原生 mode0 usage 同样扩展后乘 Q。`24E5B04..5B0C` 比较实际当前省与目标省 ID；相同省跳过 own addition。异省 `24E5B85` 调原资格 helper、`5B8E` 以 signed32 ADD 累积 eligible ArRg+38；`5BA0..5BAA` 扩展此 count、乘 Q 后与 QWORD base usage 相加。不能先对 base+own 做 int32 wrap。consumer 对普通抵达额外拒绝该总量越过 signed32 的情形。

`24E5BB4` 的 `usage <= limit` 分支才允许 native resupply gain；超限则依 slope/min/max 计算 excess loss，不再加 gain。局部 `P-loss` 为负时才走原已闭 `24E5FE0` 的 commander M1A9/floor/max 调整，最后加 gain。代码提取并复用既有 full-land projection 的同一数值 kernel，保留 fixed mul/div、截向零、signed64 wrap、max/min 顺序及 divisor=0 返回正 `4294967295` 的反直觉边界，不以“负 P”独自证明最终负月变。

只要求执行到的操作数：未超限且 P=0 时，缺 M1A9 仍能得到实际 inputs 支持的条件 0 或 gain；负局部项缺 M1A9/floor/max 继续 unknown。超限分支不因未执行的 resupply predicate 缺失而失去完整数值投影。

## 最小原生观测增量

海上 Army 的既有 current-land collector 在 `not_land` 早退，因此确实未读当前 commander M1A9。不能把 `null` 当 0，也不能把另一 Army 的 M 移过来。沿现有 preview 的 `captured_target_land_supply_inputs_v1` 新增 optional child `loss_adjustment_operands_v1`：当前 Army+120 的 raw commander FullID、按原 storage generation/fallback 解析的 resolved FullID/fallback bool、经既有 qualified aggregator/reader 读取的 1A9，以及既有四个 loaded loss 参数。没有 target rate getter、额外 detour、命令、更换统帅或 global/source field 写入。

新 bindings 标志默认 false，仅已资格化 actual .4 binder 开启；旧 .3/旧 wire 形状仍接受。child 可缺失或 unavailable，不改变原 P/resupply 两分支 readiness。Python 严格校验 source/scale、signed widths、bool、完整身份 witness、fallback、一帧内 loaded 冲突。M 只能用于与 preview 相同的 resolved commander。原生候选未编译、未部署、未实机查询；只在下一正常 build 后产生实际新数据。

## R0177 八地点实际消费

读取 Root 8 份小 preview，原 machine/time/SHA/body frame 存在 `R0177-EIGHT-SITES.actual.json`。它们为 date `53146848`、native/public revision `33/34`；Army18 commander `31254`。8754 与 2613 都一跳、P=-200000、resupply=false、target usage=0、limit5405；2607 三跳、limit1600、P=-200000；2602 三跳、limit1900、P=-500000。2630 P=0 且可 resupply，其余三点 P=-200000 但可 resupply。

就地点准备成本，8754/2613 是合理的正常试驻点；2602 是更强负局部项的三跳对照。Root 报告 Army18 仍1195，低于上述四点上限；这不代替同帧完整 eligible union。若该完整 union 与当前已读参数保持，四点不触发额外超额用量损耗；精确负率及归零成功机会数取决于实际 M1A9。

已有 010 compact 是更早 date `53146632`、native/public revision `3/4`；完整 own eligible1195、stock/cap300可证明该历史帧，但不能与新八预览拼成 same-frame。八次旧帧 join 均被机器拒绝；本批没有新 frame34 的 actual full roster/M/stock/cap，也没有 SDK 调用去补造。保留这些 required fields，下一正常 build 沿同一 query/preview 即可产出数值。条件公式与正常 move 路径已在新行为检查证明可选出负率目标，不再要求远端已抵达才允许任何预测。

## 验证、范围与保留

新 9 个行为检查最终通过（`-O`，旧 tests 执行 0）。覆盖同省不重加、异省一次、等号/超限与真实截断、union alias/flags2 冲突、只缺未触达 M 的 0/+20、缺已触达 M 的 unknown、同帧/commander/source widths 冲突、原决策普通 move 与实际到达重读、native divisor0。一次 bootstrap import 缓存问题已修正；随后加强身份守卫引出的 test 错误消息匹配已更正，保留 prior failure receipt，不冒称首次全部绿。没有 C++ build、SDK、游戏或桌面动作。

存储仍归 Root shared512MiB、此 lane 累计2MiB，不新增永久 reserve。统一 policy1.0.0，原截止 `2026-10-16T07:45:01.597Z` 不续；源/小回执因本次未完验收保护到该截止复核，派生候选按48小时复核，入库文本按180日复核。没有删除其他 lane 或个人资产。source 和测试通过不替代新 build、真实抵达、自然 stock 归零或 physical writer 实扣验收。
