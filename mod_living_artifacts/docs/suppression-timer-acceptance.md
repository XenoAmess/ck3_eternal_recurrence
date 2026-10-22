# 真实镇压续期、到期与成长恢复

当前为 **实机 NOT_RUN**。独占条目 [suppression_timer.registry.json](../tools/suppression_timer.registry.json) 供 Root 合并公共 cases；文件存在不代表已经注册、启动或通过。合同见 [suppression_timer.contract.json](../tools/suppression_timer.contract.json)，实现见 [adapter](../tools/suppression_timer_acceptance_adapter.py)。本包不修改正式产品、共享 host、Session、原保存 producer/observer、NPC、preview 或 threshold 文件。

沿用既有 core 初始夹具：1066.9.15 罗贝尔普通前端开局、L1/XP92/pending0/成长序列0、未装备活剑及四档材料。夹具不增加本包专用资金、不预置 deadline、不调用镇压或续期。先用真实保存识别目标，再走原生个人装备和普通管理决策。初始实际金币不足70或威望不足100时保留 BLOCKED，不补写钱包。费用按正常产品实际执行：首次25金、50威望；续期45金、50威望。压力只随普通产品产生，本包不授予压力修正公式验收。

| 保存 | 实际时间与动作 | 必须读回的业务结果 |
| --- | --- | --- |
| S0 | 开局day0，初始未装备 | 独立保存识别同一剑、物品owner与四材料；L1/92；没有deadline和timer序号，链次0。此后才原生装备。 |
| S1 | 同暂停日，普通管理→首次镇压 | 实扣25金、50威望；deadline=保存内初始current_date锚点+90，链次1、timer_sequence1；仍装备、L1/92。 |
| S2 | 实际推进到day60，续期前 | 原deadline和序号仍在；进入剩余≤30日的合法续期窗口；之前月度簿记推进而XP仍92。 |
| S3 | 同暂停日，普通管理→续期 | 实扣45金、50威望；在原deadline上加90，得到初始锚点+180；链次2，序号仍1。不能改成从续期当天重新算90日。 |
| S4 | day90，原首次定时点之后 | 同一剑仍有延期后的deadline、序号1、链次2；仍L1/92。旧事件不能误清新期限。只观察保存后态，不据此声称直接观测了隐藏事件调用次数。 |
| S5 | day180，自然到期 | deadline实际消失，序号1、链次2保留；本月未额外得XP，仍L1/92。 |
| S6 | 到期后第一个日历月首日 | 不训练、不喂养、不卸下，正常月度+8自动得到L2/XP0/pending0/成长序列1；月度游标当前、未镇压装备月数1。 |

最多 **7次实际 Save/严格 melt、212个真实自然日、1200次预算公共调用**。在当前固定开局日历，最后观察预计为1067.4.1/day198；消费者仍根据实际到期保存日期计算随后月首，并与原生日期区间交叉核对。弹窗可能在单日内打断，沿用现有 Session 的专用策略及原生合法续行；不重提结果未知的镇压、续期或装备动作。

预算沿用已有 LYD 长场量级：timeout8400秒、固定hold7200秒、readiness1800秒、单日请求timeout60秒、正常关闭预留180秒。计划按212×15=3180秒推进、7×180=1260秒保存解析、1800秒既有 Root/事件余量、180秒退出，共6420秒估算。这不是全场实测耗时，也不能延长任何已启动场次。实际推进、解析耗时和调用数由本场真实文件另记。

Root 使用共享公共 `prepare → allocate → preflight → run → verify`，每步先消费原终态和退出码；以本场新鲜 Steam 后台离线回执、机器身份、存储准入和冻结来源启动。准备输入仍为现有 `product_dir` 与四份 `plain_configuration`，不新增资源、deadline、角色ID或“已经镇压”的输入参数。7个 `checkpoint-readback-01..07` 请求沿用原 `checkpoint_producer` 的严格保存回读协议，无新增画面审阅或新原生查询。共享入口负责正常 Quit、retained OS0、原native0及现场释放，未闭场不能把部分业务结果写成发布完成。

保存文件验证复用既有 `ThresholdCheckpoint` 字段合同及 `consume_observation` 通用历史保存/原生物品/钱包解析，不运行 threshold 场景或其夹具。每份记录绑定 machine/run/reviewer、原始暂停帧、Save、严格melt回执及独立原生owner/装备读回；保留验证重新消费这些原件。自然推进重读共享 `case-natural-day` 原始行并调用同一 `project_native_day`，核对原始快照、配对来源及连续时间区间；不能只凭日期差、派生JSON或ACK判断PASS。

本场不覆盖冷载、换主、赠送、继承、NPC、全部诅咒或完整产品验收。真实冷载仍需单独处理共享 host 对 `on_game_start_after_lobby` 的过宽拒绝，以及 Session 当前前端Start身份绑定；**保留正式产品bootstrap**。随后才能用既有 `saved_campaign` 新进程加载真实保存、重新Save/原生读回。赠送还缺带artifact目标的合法原生payload通道，这些缺口不阻塞本独立自然计时场。

离线回归入口为产品现有 discover 自动发现的 [test_suppression_timer_acceptance_adapter.py](../tools/test_suppression_timer_acceptance_adapter.py)。离线编写状态与实机事实分开；本包目前未发游戏命令，未截图或发布。

2026-10-22离线验证：`machine_id: pc-20260924rtuf-f11af23c08`。15:09:58.490400Z至15:11:42.444223Z完整产品discover实际187项通过，全部工具顶层Python/JSON来源前后未变；15:10:21.099395Z整产品44个Python文件strict通过。本包7个回归包含原producer→公共Root消费→统一保存验证→历史物品/钱包消费者→保留验证、独立公共Selection冷导入、未知原动作不重提、错误计时反例，以及原生Q64/FILETIME在Python整数域的精确读回。外置回执为 `D:/workspace/ck3-living-artifacts-20261022/environment/suppression-timer-a02/result.json`；这些结果不授予真实212日运行或游戏冷载资格。
