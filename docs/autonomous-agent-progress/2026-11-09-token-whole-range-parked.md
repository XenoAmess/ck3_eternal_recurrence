# P161：完整候选比较的近末反例，默认 PARK

候选只把新增matcher的256-byte前缀否决改成完整expected候选范围否决：可信start及remaining长度条件不成立或候选字节不同，只返回miss；字节相同仍必须原TOKENS skipChildren／finishToken／end guard／最终完整区间比较，没有earlytrue或绕解析。原private stateToken／factory／Guard／hash／parser／writer／oldencode体不改。exact多一遍完整范围读取，近末差仍读取约3.4M字节，不称零扫描、免费miss或内存峰值改善。

首轮BEGIN前发现旧internalpretty／byte1024晚差的expected长于compact body剩余范围，会先len-veto，不能代表完整memcmp-miss。因此保留原160输入字节／顺序，预锁第六形态：packet内compact末brace前加space、actual同位TAB，长度相同、首256及近末差异前全部字节同、完整typed／canonical相同。fixture-derived起点及expected长度≤body剩余硬断言通过，确实比较到近末才miss。六形态各8ABBA／16A16B，共192；旧cached160／两VM提案仅历史，从未执行。

必要Reader1TU4＋新Test1921TU4＋sole JUnit实际0／accepted／CLOSE释放、1P0skip；A为currentP150 Reader＋Assembler与P143 Driver3，B为新Reader4＋已闭未采用P158 Assembler6＋同Driver3，各13类来源核对，parent DTO／contracts Decimal共享。不编或复制Assembler／Driver／旧App／Main／SDK，不新增profile。SourceReady继承的cachedTest机制措辞由独立alias说明纠正，实际计数和输出始终是首次新Test4，没有拿旧160代跑192。

保留报告106,490B／SHA256 `515ed10f21934378b3ba3011f33fb9fd5b36c3058098f93d620d51283492ae88`；@TempDir.NEVER＋CREATE_NEW。全部192端点、typed／member order／canonical bytes／原件SHA后验，以及17功能case／34次公有调用／8个DATA probe通过，含1001digit窄parser miss仍旧接受、depth64正例／65拒收、>4MiB旧路与错误先后。0setup目标调用／0额外warmup，冷首、暖行、异常尝试及输出成本全保留。

| 六形态分别报告 | allocation mean A→B，B/call | wall mean A→B，ms | wall median A→B，ms | 八配对wall B−A |
|---|---:|---:|---:|---|
| compact exact | 50,880,783.5→50,886,821.5 | 12.90635625→14.03670625 | 10.5694→10.1195 | 4负4正 |
| pretty exact | 91,552,146.5→50,874,445.5 | 19.382075→9.3712 | 17.0792→9.66915 | 8负 |
| 外侧空白miss | 91,551,245→91,551,242 | 21.7170875→20.77553125 | 16.4199→17.395 | 3负5正 |
| 内部pretty miss | 91,551,464→91,552,248 | 21.37215625→20.11831875 | 17.38485→17.32155 | 5负3正 |
| byte1024晚差 | 91,556,083→91,559,218.5 | 23.33304375→18.522625 | 17.58205→17.56035 | 5负3正 |
| 同长近末space／TAB差 | 91,555,776→91,556,576.5 | 21.90845625→23.51411875 | 19.0118→20.64095 | 4负4正 |

pretty wall mean−51.6502%、allocation−44.4312%，均8/8配对改善，作为条件事实保留。compact wall mean却＋8.7581%、4/8逆，median反向变好；allocation均＋6,038B，首cycle＋111,456B、后7配对下降，冷首归因UNKNOWN。外侧miss wall mean下降但median＋5.9385%、5/8更慢。内部pretty每调用多784B且8/8分配配对增加；byte1024晚差分配均＋3,135.5B、7/8配对增加。

新同长近末反例wall mean＋7.32896%、median＋8.56915%、4/8配对更慢，allocation均＋800.5B且8/8配对增加。nearend和internalpretty的CPU均值相等不表示零开销：全部CPU median15.625ms并含0量化，配对仍正负交错；byte1024 CPU累计亦反向。自然频率UNKNOWN，不合并headline，不用pretty-only采用、不拼P160旧时间作因果A/B。Root最终DEFAULT_PARK，current350仍P150；Source／Test保D，不补样本，不继续调整token matcher分支。

setup2.2218672秒、功能0.1322074秒、before-report7.3608216秒不是完整进程或准备窗；三个actor合20.2638925秒／operator资源子窗合23.715156秒。JUnit actor10.0506045／outer11.1915068秒，child stdout481B／stderr300B保留。最终资格metadata1,133,119B＜4MiB、报告＜256KiB，预算通过不授整个parent瞬时峰值。

更早已知Root锚 `2026-11-08T21:16:21.885907Z`→末CLOSE556.302007秒／→Nativequal740.166282秒；此前契约与准备UNKNOWN，不记0。Native后起的488.753535／672.617810秒仅子窗，旧取消提案、覆盖修正、实际新Test、冷启动、等待和后处理费用不删。0新增SAVE，不报有限秒／保存日，不授Runtime、whole worker、峰值或10秒目标。

本次仅unit／daily11-09／weeklyW46三事实文档，不改业务／Test／AGENTS／CI。P159／P160及P155／156旧PARK、P152原失败继续保留；P162真实身份反例与P163独立诊断格式化研究另账，不靠文档延迟必要工作。

原件：[Native最终资格](D:/ck3-state/resume91-native-integration/p161-token-whole-veto-prod01/QUALIFIED-P161-TOKEN-WHOLE-VETO-PUBLIC-STATE-FIXED192-SOFTWARE01.json)（52,772B／`64816c08b677c6ad4049c8d7cb49e079127c72b87dc24b895bc53d5e57f7923e`）；[全部192行](D:/ck3-state/resume91-native-integration/p161-token-whole-veto-prod01/tmp-junit/junit-1842670032392779032/p161-original-state-token-whole-veto-fixed192.json)；[Root最终163原件／更早费用／默认PARK](D:/ck3-state/resume91-root/post-vacation-20261107/P161-FINAL-QUALIFIED-REFS-XML-EARLIER-COST-AND-DEFAULT-PARK-REVIEW01.json)（2,165B／`0f8b933e203034d053f2b05df1a9cc6f3dc975fdc946ec8d53c27b49d5eeebd8`）；[六形态独立核验](D:/ck3-state/resume91-root/post-vacation-20261107/P161-ACTUAL-192ROWS-SIX-SHAPE-AND-DEFAULT-PARK-REVIEW01.json)。
