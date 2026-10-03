# G2 v33 paused event and religion observations / 1.20.0.3

## 12:22 v33 最小化冷恢复与真实只读能力

实际记录 `2026-10-03T12:22:23+08:00`。四目标 fresh-cache `/W4 /WX` 构建 GREEN：522 次编译、519 个独立源、1002 个实际输入，115 flags＝63 ON / 52 OFF；source/native/compiled `6934feb12b7da876b1ec9b639cf32d024a6d4e38`，冻结 `Z:/g33`。DLL SHA `470af75b2113822b53ad7d9e82f8d1cff5918a174b1a53af9213ea26d8db8d51`，最终 manifest SHA `f5c69bf69b73df3cac710670fa1b069fcbd7be058d88d52217012d729bce8c06`；environment `8660ca2f27a20e0a02fa2bbcaa1b443d767b99f3c1acbc19f9c6cc452ce1801f`。开发源码另在 `Z:/g34`，已发布县 v34 `9be27840c8c6d86004b155374c783f7dbce1b9f8` 不当作当前 DLL 的来源。

官方 prepare/verify/stage/rebind/preflight 后，`xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0011` 新 PID **96112** 从原 save4639 冷恢复 GREEN，角色29829、episode、raw53236608和六账本保持。实读窗口 minimized=true、CK3 foreground=false、无窗口修改或桌面输入。现仍暂停，stock faction event23 未选择；ordinary campaign／xar_off／pact absent、nonwar-only、WAR OFF 保持。一次正常 save 到 **4643**，checkpoint **90951584B**／SHA `ecb3537ee59d78720a6e512fa00547251ed082e0ccc015934920b871ae233b16`；3845保存天、G2 5/8、NW 2/4、自然继承0保持，无新增日、宗教动作、净收益或完整OODA信用。

成功 queries 分列公开/native revisions：事件与派系 **2/3**；religion **2/3**；clergy/县 **2/4**；悔罪 **2/5**，raw date均53236608。事件真实 FullFactionID33554465、leader70766、target29829、peasant_county2102／target_title2115／new_title16795606；native2→API3接受，native3→API4拒绝。身份 `binding_ready=true`，但当前割让 producer `surrender_title_collection_unavailable`，不能把空集合说成零损失；对应 actual independent-liege 路径正在最小修复，未选项或战争。

新增只读叶取得 **production-live primitive**：奉献1329.43177／level1／cap5／65.886%，Rite152七traits均neutral，贫穷誓愿final terms（shown=false、CanTake/affordable=true、四费用0），固定忏悔permission status0／permitted=false（决议shown/take=false）。朝圣5候选全CanSelect、5出程route全valid／arrival DateRaw可读；phase_choices均空、activity quote0，报价仍static-ready，继续查default phase输入。候选与route成功资格独立保留。详见[宗教实际提取](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/devotion/actual-consumer-v33-01/ACTUAL-READINESS-AND-REPORT.md)。

县 query available：当前chaplain56513、task_religious_relations；合法未改宗，真实目标／进度／当前改宗月率为null。5个valid候选 title2102、2111、2115、2165、2173 的最终预测月率分别1.09917、1.17175、1.17175、1.20804、1.22013百分点/月；2165为封臣32716，其余4直辖。新value_inputs仍仅v34 static-ready，未将月率排序写成完整改宗策略或收益。独立绝罚trait **true**，Faith23 head29097/title4 的六角色和final terms实际available，但shown=false／CanSend=false／十成本0；recipient接受度−23，不能把零费用或隐藏head称作合法免费解除。继续补原生优先收件人选择。

保留失败并按性质分开：首batch缺clergy Python opt-in为harness RED，补已有opt-in后同PID clergy成功；圣骑士团selected-title查询为真实capability RED，诊断首版筛选遗漏无step失败帧形成harness RED，修正后的第二次诊断保存原生结果供修复。成功event/religion/县/悔罪不被后续batch停止污染。ROOT独占MCP/game/pipe/Git；派系、holy、朝圣与合法悔罪候选继续独占文件并行，不抢窗口。机器回执：[ACTUAL-V33-REPORT-FIELDS.json](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/ACTUAL-V33-REPORT-FIELDS.json)。

已完成源码包正常commit/push，首9个native组件、Python consumer `caa7bb5b` 和县v34 `9be2784` 各自exact-head官方CI GREEN；CI只证明static。下一步优先修复实际派系观测→新严格DLL→原最新save正常冷恢复→完整损失决策及后置，随后恢复原日推进；Sway原实例与recorders保持，不重Start。

原生专题入口：[事件作用域](current-event-scopes.md)、[派系事件树](ck3-1.20.0.3-faction-demand1001-populist.md)、[奉献德性](religion-devotion-virtues-native-ai-12003.md)、[县改宗](religion-fervor-county-conversion-native-ai-12003.md)、[朝圣](religion-pilgrimage-headless-candidate-activity-quote-native-ai-12003.md)、[悔罪](religion-excommunication-repentance-native-ai-12003.md)。
