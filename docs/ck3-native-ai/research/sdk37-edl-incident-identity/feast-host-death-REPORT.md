# M6 原版宴会：主办人死亡后的终态边界

本轮只补一个原有M6活动生命周期的源码缺口，不新增能力。当前原版1.20.0.4的宴会主办人死亡回调、通知事件和SDK37的原actor守卫已精确关联；没有Game、Native、MCP、SDK服务、EXE或活Driver操作，没有重跑旧实机/单测。G2仍6/8，M6未完成。

原版 `common/activities/activity_types/feast.txt:60` 的 `on_host_death` 只向活着的参加者延迟1天触发 `feast.5003`，向 `host_var.player_heir` 延迟1天触发 `feast.0800`。该块没有 `set_activity_host` 或通用 `activity_try_use_new_host_effect` 调用。它不能证明引擎整体不继承主办人，更不能单凭脚本推断Native completed/invalidated标志及具体执行时序。

原版 `events/activities/feast_activity/feast_events.txt:1059` 的 `feast.5003` 和 `:3119` 的 `feast.0800` 都是单一 authored option 的character通知，选项只含名称和custom tooltip，没有本块内资源/关系/活动变更。源码唯一选项不等于某次现场Native shown/enabled已验；真正遇到仍须MCP可用项语义选择、after采集及现有异步worker学习。通知被消除不算宴会成功、收益或活动终态。

SDK37现有 `activity_feast_stage5_start_formal_consumer.py:445` 在原resolved Start的actor与当前角色不一致时，先返回 `lifecycle_other_actor_or_frame`，之后才可能进入`:459`的Native hosted-post查询。该函数分支返回诊断字典，不抛异常、不制造原活动terminal或再次Start；这不是对全部外层classifier无阻塞的实机证明。原resolved full Activity ID/actor的审计身份得到保护；它也意味着不能用后继角色的一份普通post或继承通知补出旧主办人的完整活动终态。本结论仅覆盖已resolved Start，不扩到pending动作恢复。

剩余实际缺口是旧主办人活动的匹配终态/独立材料在继承边界是否已经保留。已有精确 full Activity ID+原actor+type 的Native retained terminal/material可继续复用；若没有，就保留旧生命周期unknown，让后继普通游戏继续。通知、Activity行消失、actor改变和+prestige均不替代该证据。无需为了本静态缺口新增provider、重新开游戏或阻塞新录制；一个正常同主办人的完整宴会周期也可按原M6合同独立验收，不要求先扩成所有继承场景矩阵。

逐件source SHA、line和有限校验结果见 `SOURCE-AUDIT.json`；没有复制整份原版文件，只有小型来源摘要。该结果是源码边界澄清，不是新局实际宴会、host-death、terminal、收益或30年资格。
