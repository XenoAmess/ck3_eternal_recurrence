# 连续稳定自动游玩窗口

用户于2026-10-16更新本轮验收目标：**连续30游戏年没有需要停机修复或人工解除的自动游玩错误**。历史从1066开局累计的天数、角色寿命和战果继续保留，但不能折抵新的稳定窗口。旧工具goal未改成新文字时，以本政策及本场共用运行账本为准；这不代表工具goal已完成。

## 计时和重置

本战役所有SDK prefix与feeder读取同一份 `ROOT-CONTINUITY-WINDOW.json`，不各自建立起点。目标为 `ceil(30 × 365.25) = 10958` 游戏日；CK3 `date_raw`单位为小时，目标差为262992。只消费已结算循环的实际日期与计数，不给pending、命令ACK或测试结果授予结算和业务成绩。

需要人工修复或解除的query、策略、classifier、harness等阻塞都使窗口中断，即使原请求只读或零动作也不例外。原失败与最后已结算帧保留；修复部署的实际readiness通过后，才以新基线日期重新起算。首次准备状态为 `prepared`，起点与目标日期均为空，不冒充已经开始运行。

已实现的未知事件自动fallback、有限只读retry、例行SAVE和自动恢复记录日志，不重置窗口。纯外置开发不影响现场；为修错误而停下自动流程的部署属于修复。合法自然继承按游戏日期持续计时，actor/episode变化记入绑定沿革，不按角色寿命重置；合法性仍由原Native/Driver继承合同证明，不能只凭actor变化推断。

watchdog重复观察旧原始控制不能重复授予日期或轮数。完成目标时也不能留有待人工修复的错误；目标同日若出现阻塞，仍应保留失败并重置。新的自动恢复路径须依据其实际合同接入，不能把需人工修复的失败改名成自动恢复。

## 可复用代码及接入方式

公共模块为 [root_continuity_window.py](../../tools/g2_saved_campaign/root_continuity_window.py)，只做纯状态转换、本地原子快照和不可变转换回执；不调用MCP、游戏、录制、桌面或Driver。转换接口包括 `repair_required`、`attach_verified`、`settled_batch` 和 `automatic_recovery`。事件保存来源绑定及前后状态，快照写入中断可从已提交的下一个事件恢复；重复同源事件不双记，改写同一来源ID会拒绝。

[continuity_window_feeder_adapter.py](../../tools/g2_saved_campaign/continuity_window_feeder_adapter.py)以明确旧文本跨度适配一份尚未运行的feeder：移除旧累计campaign起点的停止条件，在实际readiness后起窗、按已结算批次记账，并保留既有自动恢复调用。输出为新文件，不能覆盖活跃冻结feeder。未来prefix可以复用已适配feeder，保持共用账本名不变；也可对未适配的同合同feeder运行一次适配器。原跨度不匹配时应调整已审接线，而不是猜测通用runner已接入。

```text
python -B -X utf8 tools/g2_saved_campaign/continuity_window_feeder_adapter.py --source <not-running-feeder> --output <new-feeder>
python -B -X utf8 tools/g2_saved_campaign/root_continuity_window.py --ledger <campaign-root>/ROOT-CONTINUITY-WINDOW.json initialize-repair --state <closed-small-queue-state> --failure-response <original-failure-response> --launch <actual-game-launch> --machine-id <actual-machine-id> --reason <actual-blocking-repair>
```

这些命令只产生源码或本地账本。游戏/SDK/录像准入、实际readiness、动作资格和继承资格沿用原合同。有限小型账本边界不等于游戏会话或录像时长/容量限制。

## 当前部署、验证及边界

机器 `xenoamess-full-tower-eb9d2c1186`，Root于2026-10-16确认已将此helper和适配器输出部署于本场N42/P09外置feeder，并初始化共用账本为 `prepared/start=null`。P08实际已结算6143轮、raw53328720；P09实际readiness通过后预期从53328720起窗，终点53591712。此源码包未读取或改写现场账本、SDK或Driver；实际激活与后续进展由Root运行证据追加，不由部署和离线测试追认。

公共模块逐字保留本场已审helper的SHA-256 `5426cd4acff6168c1adf09745bd91219f058ee3095c8b47db35cac7211ba7d25`。外置交付索引为 `continuity-window01/DELIVERY.json`，SHA-256 `5592afde09a942764e0762d8e2a13d8cece804959a976e44bd463efca76d4601`；它记录本场实际来源与候选部署边界，属于有期限的本机证据，不是其他机器的运行资格。

公共定向测试覆盖11个纯状态/持久化用例和3个原feeder函数回放用例，共14项。回放夹具只归档必要原函数跨度；运行输入全部明确为synthetic，不依赖本机D盘、私人存档、Native或游戏。测试真实执行适配后的 `status/admitted/main` 至少一批，核对旧累计30年不能结束新窗口、新目标边界、目标同日阻塞、人工重置、自动恢复不重置、合法继承沿革、同源幂等及快照写失败恢复。

已部署于本场外置feeder，与公共通用runner覆盖是不同结论：**公共代码及定向fixture已就绪；尚未证明所有公共runner都接入；连续30年实机稳定验收仍未完成**。本包不新增玩法能力，也不改变原生查询、策略或动作语义。`open_kaishek`预验为not-applicable：本包是Python本地计时/记账，不消费Paradox脚本语义。
