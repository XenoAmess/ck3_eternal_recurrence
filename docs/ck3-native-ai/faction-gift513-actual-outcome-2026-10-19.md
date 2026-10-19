# 513赠礼实际后验：钱与好感已生效，派系尚未退出

`machine_id: xenoamess-full-tower-eb9d2c1186`；时间、原件SHA和小投影见[实际效果证据](evidence/faction-gift513-actual-outcome-2026-10-19.json)。只读已完成513/523/527响应和runtime封存的小侧车；无新RPC、活Driver/SAVE读取或现场修改。

**527独立回执确认实付100金币、好感7→22；同一帧没有消除派系威胁。** 原请求`faction-gift-d29a273508614be4aa0fdfaba560667c`从pending转为resolved applied；不是重新提交赠礼。523实际只是war-results隐藏窗口查询，不能拿来验赠礼。正确527为same-process receipt，native420/public2、日期53153472，原pending两项revision418和raw出生时间完整保留。

| 原生事实 | 513前 | 527独立后验 |
|---|---:|---:|
| 玩家金币 | 222.70113 | 122.70113 |
| 34973对玩家好感 | 7 | 22 |
| gift opinion modifier | 无 | +15 |
| faction52成员 | 34973、35899、36445 | 相同 |
| faction52领袖 | 34973 | 相同 |
| power | 108.482 | 108.482 |
| discontent | 0 | 0 |
| 仍以玩家为目标／成员退出 | 是／否 | 是／否 |

这是`liberty_faction`，不是独立派系。513当时Native stock danger为true，原因`non_peasant_discontent_increasing`；power threshold80、discontent每月+7、原生months-until-max15，后者不等于精确最后通牒时点。策略只证明礼物合法、保留100金币reserve、同帧stock danger；实际成本约45%现有现金，后余额高于reserve22.70113。它没有计算成员退出或威胁减少的边际收益。

527的`mitigation_applied=true/status=mitigated`只表示付款与gift opinion后验匹配。Native源码明确允许成员仍在时返回这个状态；实际`recipient_left=false/faction_dissolved=false/threat_resolved=false`。527未重新读取完整stock危险谓词或discontent增长率，不能将未变power/discontent当作其全部重新求值，也不能声称已避免叛乱、战争或领土损失。

本次结果未证明长期浪费。源码中的`opinion_modifier`使用multiplier=-1、max0，不能误解为把正好感本身截成0；liberty modifiers还受权威法档和其他完整AI项影响。好感7→22可以影响意愿，但本包没有当前完整join score、退出判断或稍后成员状态。不能据同帧未退出新造禁赠阈值；没有发现确定的Native错误输入，因此不改当前策略。后继若比较这类开支，应取得成员的当前原版最终意愿/相应资格与预期收益，再比较成本，而非把stock危险直接当礼物收益。

实际527证明当前同进程receipt分支、native进度与钱包/好感/派系独立后验可达。它没有回显本次OS出生时间字符串，不能确认`+480/+000`转换分支当场被用到；当时native已经前进，也未触发新typed wait/replan race。后两项仍是源码/合成回归资格，不能以普通续跑追认全部实机覆盖。07:27封存侧车再次见pending=null，只证明其捕获时的resolved状态，不倒填527。

本包无新测试或构建，未改冻结SDK；record复核期2027-04-17T07:30:00Z，遵守统一存储策略1.0.0。Root统一提交。
