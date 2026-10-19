# C11真实送礼：付款有证，防御资金比较缺失

**这100金币确实用于送礼，但本次只买到9好感；派系仍在，威胁没有解除。** 同时玩家处于主导防守战争，当前可见己方995、敌方2525，原生战术投影为operational overmatch。送礼把现金从297.27866减至197.27866，低于现有普通军费政策的200金币下界。旧gift通道只保固定100金币，没有把这笔可推迟的开支与战争军费、承诺及应急合同一起比较。这是本场确认的策略缺口。

`machine_id: xenoamess-full-tower-eb9d2c1186`；实际观察UTC、精确源及SHA见[证据](evidence/c11-faction-gift-war-cash-2026-10-19.json)。输入只取runtime已封 `c11-prisoner4286-failure85/FROZEN.json`及具名小响应，每件不超过64KiB。0新Game/MCP/OBS调用，0活Driver/SAVE/视频正文读取，当前C11未热改、未回滚或重放gift。

## 原动作与独立后验

| 原来源 | 实际事实 |
| --- | --- |
| AUTO4276，11:08:09.384–11:08:10.492Z，native26 | actor40526向liberty faction33554460领袖34973送礼；原生合法、auto-accept，完整报价100金币、预计+9好感；request `faction-gift-b00c2f683f3f46b2b4dd2a1b33993ff7`。 |
| 同帧派系观测 | power115.521%，阈值80%，discontent0，每月+7；原生`months_until_max_discontent=15`、stock dangerous=true。15月是当前原生指标，不保证最后通牒准确日期。 |
| 同帧战争16777278 | 玩家主导防守方，战分+40，可能受影响目标2488；原生当前路线存在敌军operational overmatch。兵数不代表胜率，target也不证明败战必然失地。 |
| AUTO4284，11:08:12.778–11:08:13.456Z，独立native27 | receipt确认实际100金币支付和−58→−49好感；gift modifier+9，recipient仍在派系，power不变，`threat_resolved=false`。 |
| 同4284财政诊断 | 实读钱包197.27866；现有普通军费buffer200金币、最大军费来源为same-frame observed；完整应急雇佣报价/到场未知，退款/借款未到账为零。 |

付款因果来自原动作与独立receipt，未用截图金币差替代。`mitigated`在此只表示付款/意见修正已发生；不能写作已退出派系、已消除威胁或保住领土。另一方面，9好感可能有后续作用，现有材料不能证明“永远没有收益”，也不能计算一个伪精确反事实胜率或断言当时一定可以买到有用佣兵。

已核C11采用的`4d9791c12019c4e86d745bee7d7ca3aaba4e415c/src10`五个小源叶与修改前canonical逐字相同。原gift policy只要求付后留下100金币；formal route的stock dangerous守卫已正确工作，问题在它之后没有战争现金比较。P83建设门并未被这份材料证明绕过；+40战分与原现金保护理由为空，也不能当成可以放心花钱的证明。

## 最小修复

新增[独立gift战时现金叶](../../ck3_autonomous_player/src/xar_autoplayer/faction_gift_wartime_cash_v1.py)，接入formal route的dangerous检查后、创建checkpoint或新intent前。保留pending/receipt原优先顺序。

- 战时先检查真实钱包减完整礼物报价是否低于既有普通军费200金币下界；4276的真实小子集已足够得到“延期新gift”，不需要编造军费率、佣兵报价或其他承诺。
- 通过下界后，必须有同帧最大军费×既有18月政策、已观察未付承诺、当前完整原生合法可用应急合同及无未知雇佣pending。保守保留合格市场最大完整合同报价，不伪称公司一定及时到场或足以获胜。资金未齐只延期gift。
- 和平沿原合法gift路线；战时来源完整、付款后仍充分留款也可送礼。200/18月是现有军费政策参数，不是用户硬限制或原生规则。此门没有把gift冒充building或佣兵contract。
- 延期只附typed原因，保留原战争hold/时间推进的step和phase；不创建新checkpoint/intent。已提交的这100金币仍走原独立receipt，不能因新门反悔、重复提交或停止已发生动作的后验。

不会把“正在打仗”简化为永远禁止政治开销，也没有据此改变宣战、战术、投降或雇佣的既有门槛。更完整的军事/派系效用比较仍缺当前可用合同、到场及gift后成员行为等来源；本次先堵住已观察到的基础军费下界被可推迟开支侵蚀的问题。

最终定向 **13 passed / 1.40s / exit0**（`ea733d`），覆盖真实4276下界拒绝、和平/充裕战时允许、缺/过期报价与承诺、完整合同留款、原helper输入复用零RPC、重复延期仍推进及已有pending receipt优先。首次collection因误从`war_strategic_reserve_v1`导入`observed_frame`失败（`f42a9c`），已改用原实际owner `m5_observed_opportunity_selector`；中间12项和最终13项各按当时来源保留。不重跑P83/build/merc矩阵，软件通过不等于当前C11已经采用。

本包新增源码/测试/精简记录按统一存储策略1.0.0，预算不超过Root追加授权的64KiB；单件输入不超过64KiB，无重型写入/新预留/删除，不刷新旧存档或素材期限。Root统一commit/push及后继合批freeze，实际采用另记。
