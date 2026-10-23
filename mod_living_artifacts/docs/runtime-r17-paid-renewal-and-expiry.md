# R17：真实付款、续期、自然到期与恢复成长

`machine_id: pc-20260924rtuf-f11af23c08`，观察截至2026-10-23T02:49Z。EXT 为 `D:/workspace/ck3-living-artifacts-20261022`。本场实际完成 **198自然日、852次计预算调用、7份真实保存、五项计时检查全部PASS**；已正常GUI退出并独立完成进程、keeper与屏幕资源闭场。冻结入口公共verify因导入故障实际退出1，原失败保留；复用主线既有共享导入维护重新验证，于02:38:59.402638Z实际退出0，case/GUI/正常闭场及qualified boundary通过。不授冷加载或发布资格。

## 冻结来源与启动

c19 `0b96283d7d3eed696ffca6ddb3ac2f3459651776` 仅在 c18 上增加声明的初始 fixture 印记输入；正式57文件与 c18 相同，不夹入最新主线 host/native。a28外置产品清单使用hold10800/timeout12000，保持212自然日上限、7保存、1200调用和5项业务断言。配置、Prepared、runtime与原a24均未覆盖。

新卡为 `EXT/environment/storage-timer-a28-20261023-a01`：单份own D5GiB/C2GiB、other D512MiB/C0，截止2026-10-23T23:45:49.521031Z。原a26未来预留被串行替换，旧卡保留；fresh双trigger实际0，服务→readback→真实producer存储校验通过。没有删除资产或将候选回收算为空间。00:12:10Z精确三域为881466700 B；随后核得本场媒体11379433 B，原9MiB估计少1942249 B，合计修正为892846133 B，仍低于本场5GiB。保留原 `EXT/environment/storage-r17-own-snapshot-01-20261023-a01/snapshot.json`，补正于同目录 `media-correction-a01.json`；场次继续写入，后续保存需重新观察。

公共allocate `20261022T235020545328Z-allocate` 实际分配 `pc-20260924rtuf-f11af23c08--living-artifacts--R0017`，keeper a28于23:50:25Z就绪。23:51:08Z后台原生probe确认Steam offline/true，随后bound preflight实际0，public run `20261022T235111186915Z-run` 启动。实际CK3 PID13076、出生1792713085.5974245；host3652，actor31254、generation1、初始date_raw53144328。实际退出与独立资源释放见下文，启动资格不代替闭场后态。

## 七份真实保存与计时结果

| 保存 | 实际日期 | 装备 | 等级/XP | 金币 | 威望 | 压制期限/chain |
| --- | --- | --- | --- | ---: | ---: | --- |
| timer-checkpoint-01 | 1066.9.15 | 否 | L1/92 | 248 | 2200 | 无/0 |
| timer-checkpoint-02 | 同日 | 是 | L1/92 | 223 | 2150 | 389437/1 |
| timer-checkpoint-03 | 1066.11.14，第60日 | 是 | L1/92 | 231.77073 | 2154.13220 | 389437/1 |
| timer-checkpoint-04 | 同一暂停日 | 是 | L1/92 | 186.77073 | 2104.13220 | 389527/2 |
| timer-checkpoint-05 | 1066.12.14，第90日 | 是 | L1/92 | 191.39497 | 2106.19830 | 389527/2 |
| timer-checkpoint-06 | 1067.3.14，第180日 | 是 | L1/92 | 205.24043 | 2112.39660 | 字段缺失/2 |
| timer-checkpoint-07 | 1067.4.1，第198日 | 是 | L2/0 | 209.85627 | 2114.46270 | 字段缺失/2 |

两份Save与同日原生钱包一致，首次实际扣25金、50威望；第二保存压力8。初始Save确有 `xalw_feeding_imprint`，类型flag、raw identity为null、值 `primary_armament`。这是声明的fixture输入，不是喂养动作或90日持久化通过。两份producer原wait均0；原件与melt分别约71MB/104MB，现有保存守卫保持。

第三、四保存于同一暂停日期对比，实际再扣45金、50威望，压力10→18；期限由389437延至389527，chain1→2。第四份producer于00:47:49.460210Z实际wait0。第90日的第五份producer于01:08:17.478186Z实际wait0，解析结果保留新期限和chain2，装备及L1/92未变；初始90日印记变量此时已缺失。它证明旧到期事件没有清除续期，不替代第180日的自然到期检查。

库存回调于00:01:02Z保留原生预意图拒绝，Root没有追加通用库存查询。新原图与同尺寸坐标工具仅打开一次库存，延迟原图实际显示5件宝物、★目标402及空武器槽，随后交由原冻结adapter原生装备并独立读回。人工审阅为 `EXT/environment/r17-inventory-root-review-a01.json`；canonical点击回执为 `EXT/media/r17-inventory-open-a01.png.json`。

第180日第六份保存中 `xalw_growth_suppressed_until` 已真实移除，chain2与timer sequence1保留，同一原件仍装备且为L1/92，没有到期补发经验。第198日第七份保存为1067.4.1、L2/XP0、pending0、成长序号1，证明下一个真实月结恢复自动成长。两份保存均与同日原生钱包/装备交叉绑定；producer process分别于01:49:22.004618Z、02:00:58.420893Z实际退出0。本次文档核对只读既有observer/process回执，没有重新解析melt或重放业务动作。

原 `case-output/living-artifacts-suppression-timer-result.json` 于 **02:14:33.155591Z** 生成，1246547 B、SHA `66eef39ddb82121adcf86bc53bcf075078b1ad6cdbc6d19dca34d49f0c8cf5d0`。五项为 `TIMER-FIRST-PAID-90-DAYS`、`TIMER-RENEW-ADDS-90-DAYS`、`TIMER-OLD-EVENT-KEEPS-RENEWED-DEADLINE`、`TIMER-NATURAL-EXPIRY`、`TIMER-NEXT-MONTH-GROWTH`，全部PASS；`error=null`、`original_action_unknown=false`、case与GUI资格为true。原结果生成时仍为 `normal_close_pending=true`，`business_pass=false / product_release_pass=false` 保留，后续闭场另有真实回执。

Save4后精确用量见 `EXT/environment/storage-r17-own-snapshot-02-save4-20261023-a01/snapshot.json`（SHA `7676bf012fcef0996f96ed0a6653e988fc76d90c0780911f76ad6f6934aebbb4`）：三域1463592600 B，实际媒体10文件11379433 B，own合计1474972033 B，5GiB余3893737087 B。下述第二通知的原report早于采样，已包含其中；不重复加计。此为该次采样，后续输出仍须重核。

## 原生中断及冷加载准备

第52日的 `bookmark.1070` 实例3已先保存原生窗口、双方角色、10个saved scopes加root及三个实际显示选项，既有c19策略27项检查成立，选择显示第三项一次。原生选择3→null后，独立同暂停帧确认窗口消失；军队before/after均unavailable，不授250兵或claim效果。只读post曾使用不存在的工具名，公共队列在派发前拒绝；保留失败，再用实际 `ck3_take_snapshot` 读取，没有重放选择。离线来源与既有规则精确匹配，见 `EXT/environment/r17-event-0001-offline-analysis-a01.json`（SHA `829cda106b255019fe0033c6c5e50218898fa0c477236329248f489431fb8d9e`）。

第73日婚约通知实例117440607按既有 `arrange-marriage-reject-only-v1` 策略单次拒绝，native rejected与独立通知消失分别记录；本机四份原版来源及两份冻结策略SHA与R16已核来源一致。离线回执为 `EXT/environment/r17-interaction-offline-analysis-0002-a01/result.json`（SHA `0e85b2a40396b8135b3b2ae717173ed8f92e308a0659a2f4d7ed6c9ff87d8064`），不授婚姻变量或其他效果。

a27冷加载准备只引用真正renewed04的retained `original.ck3`，71482465 B、SHA `bd7cedc41a3bcf3c38ee84a011276dc3beddbca704efeea4e674bb2587f70ea7`；八项来源闭合，未复制该原件。现成cold入口先公共prepare消费完整saved_campaign，再以显式Prepared公共plan，最后preflight，三项原wait均0。未执行不读取case_inputs的unbound plan，未allocate/run或授予冷加载资格。新formal-only profile63文件2079161 B，完整小包2306698 B，计父other512；见 `EXT/environment/cold-public-prepare-r17-a27/result.json`（SHA `a8a6a695de30bacff57b01ffb921f0376d4af99efe3b81e688a63af903026e76`）。

## 保存服务时限维护

既有ignored operator服务原固定等待7200秒，现支持显式 `--wait-seconds`，缺省7200保持，本场传12000；没有改冻结SDK、公共请求或游戏动作。原22项回归、两个完整模块strict及12项参数/原期限循环回归实际0，无Save或游戏调用。服务源码SHA `655d2d348bfd18d1f9332632ac784ec295af000b31014b0f83d931af3c3cc0e3`，小回执 `EXT/environment/checkpoint-service-timer-wait-a01/result.json`。它属于操作包维护，没有持久CI覆盖信用。

## 正常退出、独立资源闭场与公共verify

Root于 **02:21:19.938852Z** 直接审阅自动保存未勾选的原图后，经正常菜单选择退出桌面；`case-output/normal-quit-root-result.json` 为1818 B、SHA `99ef38e7f34755ef8b7f324b02ce212aa82fc70e48ab2d3baf5ed79a0f28be38`。共享owner保留的OS handle实际signaled/exit0；原生于02:21:32.948036Z以process_exit/exit0结束，tree_gone与cleanup_proven均true，最终CK3进程清单为空。完整 `normal-close-result.json` 为8802 B、SHA `875f7f16a3ead41cecb599a77386841025f7b7ac23a001a2c027c1f05838d5f4`，`normal_close_qualified=true`、`host_error=null`。

原host PID3652于02:21:40.541855Z由原Popen wait取得 **exit1**，库存回调的历史预意图拒绝保留，不能将本场报告改写为全host GREEN。原public run于02:21:40.865804Z实际wait0，原工具27378也已wait0；外层0与五项业务PASS分别记录。

keeper于02:23:58.723806Z STOP，原allocate于02:23:58.850586Z实际wait0，原工具18966也已wait0。keeper最后序号749且自身 `screen_released=false`；Root随后经现成CAS750单独完成 `done / resources=[]`，不是由keeper退出推断屏幕已释放。证据为 `EXT/environment/r17-screen-resource-close-a01/release.stdout.json`，1326 B、SHA `66c2efaf2bd0c5216e4dd84603759b975900209edb6f895ce055061b789e1be9`。

闭场后台probe于02:24:15.509088Z实际确认Steam `offline / offline_mode=true`，PID8580、出生FILETIME `134371126587222837`；回执 `EXT/environment/steam-offline-r17-close-a01.json`，2332 B、SHA `f7bbdb6d2475eae000457338b69e02fde8bc2bfe39743b5964d533dd04b77841`。下一场仍须新鲜观察。

公共verify `20261023T022452008067Z-verify` 于02:28:47.303428Z由原Popen wait取得 **exit1**，原工具36677也实际退出1（chunk `b37fe9`）：c19 `suppression_timer.verify_case → evaluate → _audit_natural → project_native_day → pending_instance` 在导入 `xar_autoplayer.bridge.campaign_interaction_boundary_v1` 时报 `ModuleNotFoundError: No module named 'xar_autoplayer'`。原stderr为2213 B、SHA `0848df7f6f111ecf02f3e10872075790154175b49fc2ade1d8d02b0d53da1f72`，失败保留。

后续对照确认current-main的既有 `case_imports` 已支持完整隔离导入，冻结c19缺少这项既有更新；本次没有因此新增生产修复、另造resolver或临时设置PYTHONPATH。Root使用 `runtime/next-public-operation-a28-current-main-verify-a01.json` 只将repo入口指向主仓，显式保留原runtime/products/Prepared/context；当前公共入口78502 B、SHA `63bc317410400f874e107f3ffe8eaec4c007ec9f5f0766d1d309ffbb276c1a62`。

新公共verify `20261023T023440382570Z-verify` 于 **02:38:59.402638Z** 由原Popen6480取得returncode0，原工具80834也实际wait0（chunk `0fae5f`）。它真正重读同一七份Save并重算五项，输出 `case_contract_qualified / gui_contract_qualified / case_acceptance_pass / qualified_boundary_pass=true`，嵌套 `normal_close.normal_close_qualified=true`；`business_pass / product_release_pass=false` 保留。新stdout1281851 B、SHA `b53227fd0776c6dace1133509649fa2806a69a27a3e59f370019bb38af05518d`；原结果1246547 B及SHA再次核对精确未变。没有改冻结c19、原结果或保存，也没有重启或重跑198日。

a27实际cold仍NOT_RUN；余下按 **curse_representative → cold_persistence → 发布交付** 执行，不扩63格或重跑已绿NPC/喂养。最终发布前另在description、单数Notes和永久changelog说明代表实测范围及其余独有高风险生命周期未逐项验；若Notes变化，保留旧674字草稿并重新冻结，不复用旧intent。本次不修改发布正文或Notes。

## 存储闭场、最小回收与后继启动

R17闭场三域与28份实际media合计 **2258970847 B**；a28共享task-close实际0。当前用量回执 `EXT/environment/storage-r17-actual-close-20261023-a01/current-usage-reaccount.json` 为2267 B、SHA `4f146da6eb7603a129f53b1476ba495f45775761ae72267317235e83d181f043`，早期Save4采样保留为历史截点。实际回收仅删除R14 checkpoint01–03的三份派生 `melted.ck3`，逻辑311663158 B；对应原始Save、精确SHA、官方melter、command/process和重建配方仍可读，R17/R16没有删除。已删除的三份melt不再可读，不以同名重建物替代历史证据；并发磁盘变化使物理释放归因保持null。回执 `reclamation-actual.json` 为5993 B、SHA `6fc13c567ca7fd7878513db2ae2f524a7200caa91d9bdb4bc456adec5f07c2f2`。

新的 `EXT/environment/storage-curse-a25-20261023-a01` 已正式采用单份own D5GiB/C2GiB、other D512MiB/C0，截止 **2026-10-24T02:38:39.601285Z**；fresh task-start、before-heavy-write和实际consumer compatibility均0。admission SHA `bb2496f9985b68982a7511ebdec2fb9f7327f9f246e006a9bae6f9857dd623cd`，consumer compatibility SHA `14bbd539df1d49222394a2b7401fe87dc2cd01d2864a1b76724f99d047211fd9`。旧a28 future own归0，旧卡字节保留；最终交接 `final-handoff.json` 为3820 B、SHA `fdbdcb1c4742e393ad9befa9374afc96dc5cc304ee2e2217c2512bb5b7f4f30a`，不是额外并行扩一份游戏预算。

Root已用公共allocate `20261023T024408940213Z-allocate` 取得真正后继 **R0018**，原工具60287仍保留；既有keeper路径 `living-core-a25` 已注册序号751/READY，PID4348。02:46:20.407137Z新后台Steam回执offline/true后，bound preflight `20261023T024620747021Z-preflight` 于02:46:23.079458Z实际wait0，public run `20261023T024623182946Z-run` 原工具43502仍运行，保存服务71650按新卡等待七份Save。启动观察为CK3 PID9324、出生1792723600.2433865，host14080、bootstrap无error；该截点尚无业务Save，不授curse PASS或退出码，不重复开局。R17本场结果与后继启动分别记账，下一业务门槛是curse实际七保存及正常闭场，再执行a27 cold。

03:18Z续记：上述启动截点已结束。R18实际首Save钱包276金、预期20金，旧夹具清款被引擎拒绝；装备前BLOCKED、0日/8calls/1Save、五项均BLOCKED，正常闭场与CAS766资源释放已完成。公共verify实际2/BLOCKED，后继须修共享夹具后新候选重测，详见 [R18报告](runtime-r18-invalid-curse-fixture-wallet.md)。这项失败不撤销R17原计时通过，也不授诅咒或cold信用。

R17公共verify的隔离导入路径另已接入现有持久CI测试文件：独立Python进程实际调用公共verify，再进入真实timer verifier与自然日projector，覆盖正例和bool实例ID拒绝，不mock verifier或projector。原完整CI step110八条和111八十九条共97命令逐项退出0；原工具88338实际wait0。111中的HOF一项因缺原生输入仍为NOT_EXECUTED，不能写全部native通过；历史host和allocator的限定函数类型检查也不外推完整大模块strict。软件回归不新增游戏推进信用。小结果 `EXT/environment/java-ci-qualified-child-a01/resume-20261023-public-timer-import-result.json`，SHA `c789720502ecd614a40545100a44a5e8ac8eac0ae810e6365c4c57101736450e`。
