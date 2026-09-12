# R584–R588 `.8030` 原版事件 RED 与合同恢复（2026-09-13）

## 验收状态

- T0 P1 保持 `9/9 GREEN`；本轮没有重跑或改写 P1。
- T0 P2 仍为 `0/8`。R585–R588 所属 take 没有连续完成八段，因此前四段虽已走通，也不单独计入正式分母。
- 最终宣传片硬锁保持生效；本轮没有制作、更新、发布或预热最终视频。
- R584 为 frontend warmup；R585、R586、R587、R588 为依次恢复不同来源的 gameplay 进程。R584–R588 均已终止，捕获清理为 GREEN，收口时 CK3、FFmpeg 和 injector 均为零实例。

失败 take 位于：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r584-plus-804815e-20260913`

主报告为 `capture/report.json`，SHA-256：

`DF6184EAE6791044505AE1BEDB8DA083B55540B221C9DA4CDFD7C9854E5B79FF`

## RED 现场

R588 恢复登记的成熟 endgame `.356` 来源并选择 authored option 1 后，时间线尚未到达产品事件 `zg361we.360`，先出现原版多选事件：

`ep3_story_cycle_admin_eunuch.8030`

等待门按既有规则保留 RED，没有选择任何按钮。现场 native event-window 查询固定了：

- CK3：`1.19.0.6`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
- `date_raw=53366664`、event instance `621`、root/player `32904`；
- snapshot authored option count 为 `4`；实际可见映射为 native `0, 1, 3`，其中 authored C/native 2 隐藏；
- 保存域为 `story / eunuch / emperor / admin_title / student / rival / background_throne_room_scope`，原生类型分别为 `story / character / character / landed_title / character / character / character`；
- 选择未发生，R588 随后按 RED 清理。

冻结门文件为：

`capture/cell/phase2_promo_phase2_hc_workforce_mature_endgame_source_zg361we_360_native_event_wait_gate.json`

SHA-256：

`47BCBC5ACA0FACEEE804ED082D0DC7EB381438DC86B6F24DE2DBFBF549F8696D`

## exact-build 原版调用链与安全选择

定义位于 `events/dlc/ep3/ep3_story_cycle_admin_eunuch_events.txt:6282-6430`，文件 SHA-256：

`AD0EAC903C87FBE869A70709F8C674C6557862B28E14BD242B6EF0FB3D946734`

调用位于 `common/story_cycles/ep3_story_cycle_admin_eunuch.txt:195-202`。五日 invalid-state 检查发现故事记录的阉人仍存在、但其 employer 已不同于 story owner 时，保存 `eunuch` 并向 story owner 触发 `.8030`。调用文件 SHA-256：

`CB8D231D31DC8C269B738F9801E971225D434CF078EB94D4641D06D1662FB9E3`

四个 authored 选择的实际效果边界为：

1. A/native 0：支付少量金钱并把旧阉人招回宫廷，特质还可能带来压力；
2. B/native 1：把学生设为新故事阉人，可能释放被玩家囚禁的学生，并继续故事；
3. C/native 2：对宿敌执行同类替换和可能的释放；R588 中该按钮隐藏；
4. D/native 3：清除本故事的 liege/eunuch 两类 modifier，并结束这条行政阉人故事。

合同继续选择 authored D/native 3。它不会支付金钱、招募人物、释放囚犯、替换故事人物或进入随机分支；实际改变严格限定为清理这条原版故事的两个 modifier 并结束该故事。该选择适合恢复被偶发原版故事阻断的宣传时间线，但仍只在 exact event、root、保存域名称/类型、authored count 和可见 native 映射全部吻合时允许执行。

## 修复与验证

代码提交并推送为：

`7641679a90b50762a12c863362666a543dc359cd` — `Handle P2 eunuch timeline interruption`

实现没有增加第二份 `.8030` 合同。既有共享原版事件注册表已经包含该事件及 2/3/4 按钮变体；本次完成：

- 把 exact-build 定义、五日调用链、简中本地化指纹和 R588 现场写回既有共享知识记录；
- P2 产品事件等待门可显式启用 reviewed-vanilla drain；
- 只有共享注册表已登记的原版事件才进入严格扩展合同执行器；未知事件返回原有 RED；
- 合同执行器在同一暂停帧核对 root、保存域、选项映射和选中 native index，并验证事件实例确实前移；任何漂移在选择前 RED；
- 修正注册表迁移测试遗漏 `tgp_travel` 分组造成的旧计数漂移，真实默认分组为 188 条。

聚焦验证：

- normal：`12/12 GREEN`；
- `python -O`：`12/12 GREEN`；
- `py_compile`：GREEN；
- `git diff --check`：GREEN。

测试覆盖 R588 的 native `0/1/3` 投影选择 authored 4/native 3，同时证明漂移为 `0/1/2` 时保持 RED 且不执行选择。修改仅涉及 Python runner、共享原版事件知识和测试；未改 mod 产品树、DLL、游戏文件、启动配置、加载顺序或 MCP schema。

## 兼容性与下一步

- 已更新 MCP 可复用的原版事件知识资产；接口/schema/version 不变。
- 没有改变 T0/T1 对外行为和 open_kaishek 兼容接口，不需要 open_kaishek 同步。
- 因 R588 已在失败 take 收口时终止，不能原位热恢复。下一次 CK3 启动必须从新轮次 R589 开始，并继续保持单实例串行。
- 下一步只执行一次新的连续八段 P2 捕获；若再撞到未登记原版事件，继续按同一 SOP 保留 RED，不扩大为无关长跑或全库事件审计。
