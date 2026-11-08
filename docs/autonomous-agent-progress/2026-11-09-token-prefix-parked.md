# P160：前缀否决仍有晚差反例，默认 PARK

候选仅在新增 DATA matcher 的原 TOKENS 导航取得state起点后、skipChildren之前，比较最多256个公共前缀字节；不同只作miss，相同仍需原skip／finish／边界与完整区间比较。没有earlytrue、语法或权限改变；原private stateToken／factory／Guard／hash／parser／writer／oldencode体逐字保留。4MiB仅优化否决，64MiB接受域与旧fallback不缩减。

A来自currentP150共享Reader＋Assembler和P143 Driver3；B为新Reader4＋已闭但未采用的P158 Assembler6＋同Driver3，各自同child13／parent DTO共享，逐类真实CodeSource／SHA通过。仅必要Reader1TU4、新Test1TU4、sole JUnit实际0／accepted／CLOSE释放，1P0skip；不编或复制Assembler／Driver／旧App／Main／SDK，不新增profile。P159的128输入字节／顺序不变，第五形态在compact state byte1024的`x`改为字面`\u0078`，首256及前1024同、完整typed／canonical同、wire异，预先固定32次晚差；总五形态各8ABBA／16A16B，共160。无setup目标调用或额外warmup，保留全部冷首与后续暖行。

@TempDir.NEVER／CREATE_NEW保留90,316B原报告，SHA256 `5bb7a75207a29c90450f65705d28e6945d926d5944f68fb9a0464eb1d3058167`。全部160端点、完整typed／member order／canonical bytes／原件SHA后验，以及17功能case／34次公有调用／8个DATA probe通过；包括1001digit窄parser miss仍旧接受、包嵌套64正例／65拒收、多故障错误顺序和>4MiB旧路。不是只返回成功便称通过。

| 五形态分别报告 | allocation mean A→B，B/call | wall mean A→B，ms | wall median A→B，ms | 八配对wall B−A |
|---|---:|---:|---:|---|
| compact exact | 50,880,733→50,886,872 | 15.92135→12.9934 | 12.34505→9.84965 | 6负2正 |
| pretty exact | 91,552,146.5→50,874,445.5 | 20.25550625→9.57801875 | 18.225→9.1833 | 8负 |
| 外侧空白miss | 91,551,245→91,551,250 | 21.806175→18.31165625 | 17.78915→16.48635 | 5负3正 |
| 内部pretty miss | 91,551,464→91,552,248 | 20.80064375→19.95915 | 17.6215→17.56125 | 5负3正 |
| byte1024晚词法miss | 91,555,968.5→91,559,477.5 | 21.8687125→18.6739625 | 16.58605→18.31575 | 3负5正 |

pretty wall mean−52.7140%、分配−44.4312%，两项均8/8配对下降，保留条件收益。compact wall mean−18.3901%、6/8下降，但分配mean＋6,139B，首cycle＋113,072B驱动，归因UNKNOWN；后7配对下降不能抹去冷首。外侧miss分配近乎持平；内部pretty每调用多784B且8/8配对增加，wall仍3/8反向。晚差wall mean虽−14.6088%，median却＋10.428643347873656%、5/8更慢；分配mean＋3,509B且8/8配对增加，首cycle差额42,264B及后续变化完整保留，不全归因算法或初始化。

五形态所有wall均值下降不等于稳健改善。current-thread CPU累计compact140.625→218.75ms、外侧miss187.5→203.125ms、晚差265.625→281.25ms也有反向；所有CPU median15.625ms并含0量化，其他输入累计下降亦不能授可靠CPU百分比或零cost。自然频率UNKNOWN，不合并headline、不用pretty-only采用、不拼P159旧时间作跨轮因果A/B。Root最终DEFAULT_PARK，current350仍P150，Source／Test只保D，不补样本、不回滚正式生产。

Native原qual／summary一处手写晚差median为10.4262%，后到独立append纠正为上述10.428643347873656%；原始median、全部raw／数值分析／配对始终未改。不是业务或Java测试失败，也不覆盖旧原件。

setup2.1686799秒、功能0.1352709秒、before-report6.2814114秒均为子边界。三个actor合19.1068699秒／operator资源窗合22.9690602秒，JUnit actor9.4396479／outer10.9915405秒，child stdout481B／stderr296B保留，不能以outer空输出代替它。资格预算1,105,508B＜4MiB、报告＜256KiB，预算通过不授整个parent瞬时峰值或Java堆峰值。

已知Native准备锚 `2026-11-08T21:03:31.142047Z`→末CLOSE459.024129秒／→qual629.119603秒；更早Root契约、实现、审阅费用UNKNOWN，不记0，也不把该Native子窗叫完整Root准备。全部冷启动、源／metadata修正、等待和后处理保留。0新增SAVE，不报有限秒／保存日，不授Runtime、whole worker、峰值或10秒目标。

本次仅unit／daily11-09／weeklyW46三事实文档，业务／Test／AGENTS／CI不改。P159／P158及P155／156 PARK、P152原失败均保留；后继P161按首BEGIN前的新独立候选与六形态192计划评估，不回填本轮数据。

原件：[Native最终资格](D:/ck3-state/resume91-native-integration/p160-token-prefix-prod01/QUALIFIED-P160-TOKEN-PREFIX-PUBLIC-STATE-FIXED160-SOFTWARE01.json)（51,516B／`351b2e85cc6a5f3624aa7f8354a8811ae9e13c9674f56b01e7f69000b77c7818`）；[全部160行](D:/ck3-state/resume91-native-integration/p160-token-prefix-prod01/tmp-junit/junit-5824401316454201827/p160-original-state-token-prefix-fixed160.json)；[Root最终164原件／默认PARK](D:/ck3-state/resume91-root/post-vacation-20261107/P160-FINAL-QUALIFIED-REFS-ERRATUM-AND-DEFAULT-PARK-REVIEW01.json)（1,849B／`e0535c9bd090f59b9c5b5362b00ddf53ffe8ad7a5fe61ccd0eea01590f66780e`）；[median文字勘误与决定附记](D:/ck3-state/resume91-native-integration/p160-token-prefix-prod01/ROOT-DEFAULT-PARK-AND-EXACT-LATE-MEDIAN-ERRATUM01.json)。
