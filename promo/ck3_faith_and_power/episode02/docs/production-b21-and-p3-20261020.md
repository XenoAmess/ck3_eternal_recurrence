# Q21修复、朝圣抵达与共享研究接入

`machine_id: 4-8e1c2f1861`；观察截止 `2026-10-20T13:54Z`。本页只记录这台机器的实际结果，不外推其他机器的安装、运行或拍摄资格。

## 研究如何交给游玩智能体

[共享参考入口](../../../../docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md)与既有 `ck3_query_holy_site_planning_knowledge_v1` 已连通。七种action保持不变，返回中的 `knowledge.episode02_research` 提供六组机制资料、来源SHA、当前必须重新观察的输入和不支持项。智能体可先查知识，再通过当局原生查询核实资格、费用与后态；知识返回不直接授予动作许可。

本轮加入四个历史事件定义及各自实例来源：1060出发事件、1020城市事件、5001罗马抵达、4100徽章。共享资料区分查询时的选项/源码分析和选择后的独立post，不把历史人物、日期或结果投影成调用者当前局面。原5项／11次注册MCP调用、早前修订1项／1次、实例接入1项／1次、抵达增量1项／1次分别实际通过，范围不重复累加；抵达增量的真实注册MCP调用没有执行游戏动作。普通auto尚不自动消费这些知识，完整事件实例合同仍未注册。

两条可直接用于以后决策的教训已经入共享入口：4100的简略效果列表为空仍会收费，不能据此判断免费；原版活动日志的50分不是50虔诚。本例徽章选择实际花31.25金币，未来费用仍须读当前报价，不能写成固定价格。来源：[4100分析](knowledge/pilgrimage-4100-source-analysis.json)、[5001实例](knowledge/pilgrimage-5001-r0012-occurrence-analysis.json)、[独立后态](knowledge/r0012-5001-4100-post.json)。徽章实际所有权、装备收益及特质经验仍未独立验证；录像中出现朝圣者特质通知是另一层视觉证据。

## 本轮实拍结果与失败边界

B19/R0011在任何降级或扣款前发现骑士效果reader与项目自己安装的context detour冲突；正常退出、原run/host/keeper/allocator均实际0，CAS12727释放，没有Demote26或骑士净收益信用。

B20/R0012始终为原PID2052／gen1／人物31254。普通朝圣Start实际成功，独立活动身份可见，金币243→173，规划器全十资源报价70金；出发原片74.966秒、62,431,292 B。途中城市事件第一显示项实际花50金、压力0→15；5001唯一显示项实际消费后压力15→4，该按钮前后金币与虔诚不变；4100第一显示项另花31.25金。ACK与旧事件窗口独立消失均分别留证，不能把相邻自然日收入或整段余额变化归给一个按钮。

抵达原片实际28.500秒、28,548,480 B，SHA-256 `d3059ddad459bbc6dd15555e9ac0fbcd695a2dc2773f935fdf59ae740d576ab3`。实际PTS2.000显示罗马抵达单项；10.033与18.033出现“获得朝圣者特质”，同时活动仍显示距结束约三个月；26.000已经是后继徽章事件。四帧未见旧蓝窗或关键遮挡，只授这些画面信用，不认证连续clean片段或完整人工听看。来源：[抵达媒体审阅](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b20-a01/media-review-p3-arrival-a01/REVIEW.actual.json)。

原自然日0038成功，0040在resume后、最终pause提交前发生Python读回条件31失败。0040结果未知且未重发，Start也未重发。恢复后复用现成原生单日composite；每次成功日与只读收敛分别计数。最后实际日期53145720，比Start晚58日，其中46日区间没有成功单日回执闭合，不能归为0040一次成功推进。最终原report仅有1060／1020／5001／4100四种已查询定义，没有7000／9001查询证据；完整朝圣、结算、归返与总费仍未证明，也未保存本次旅程供后继冷载。

退出执行过晚，未完成typed或GUI正常Quit。`13:30:27`原保留句柄等待结束时仍为signaled=false、exit_code=null；`13:30:29`受管会话到期执行Job cleanup，原生报告CK3 exit1、tree_gone/cleanup=true。原run退出2、host退出1；normal_close_qualified与failure_lifecycle_completed均保持false，不能把后来的清理追认成原句柄退出成功。keeper与allocator实际退出0，fresh Steam离线画面已审、桌面恢复1024×768，CAS12783／resources[]已释放。来源：[实际闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b20-a01/SCENE-CLOSURE.actual.json)、[资源释放](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b20-a01/SCREEN-RELEASE.actual.json)。

最终分配上界672,440,320 B；nonraw为581,365,760 B，超原512MiB子额44,494,848 B，整体仍在896MiB内。原超额已经登记，预算资格false，不通过事后修改或删证据追认。后继按实际占用做fresh准入，并评估闭场大journal的无损压缩回收。来源：[超额记录](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b20-a01/STORAGE-CAP-BREACH.actual.json)。

## 共享修复与后续制作

Q21标准CMake增量构建已完成，真实编译源 `dc680ba9228dc962555acdd150f857c740753c3a`；只重编2个生产单元，21个有限目标／51个直接编译单元实际通过，新增29个安装/卸载场景与OFF路径通过。DLL为15,589,376 B，SHA-256 `44c6ad21aa4a7f56b7ca96b2607d0a7918adf09baefc3cef261a8032eda7d335`。这是有限原生合同资格，尚未取得游戏内骑士净收益。来源：[资格](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b21-a01/qualifications/native-a04/PUBLIC-RUNTIME-QUALIFICATION.expanded.actual.json)、[交付索引](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b21-a01/qualifications/native-a04/INCREMENTAL-DELIVERY-CATALOG.actual.json)。

公共CaseClient单日路径已接入既有原生composite；只在实际能力齐备且同人物暂停局面下使用，派发后没有fallback重发，原始回执与旧消费者投影分开保留。核心6项及缺少事件查询能力的1项消费者实际通过；修改方法与共享helper的类型检查通过。合入后的便携exact-tree九项首次实际执行通过、无skip，不能把这些源码测试称为新游戏通过。

远端新增三份Native/research Python文件已经保留。它们不在实际FileAPI、build.ninja和893对象依赖中；原编译树5472路径与集成树5473路径并不完全相同。显式研究差异绑定保持 `full_native_tree_equal=false`、`compiled_inputs_equal=true`、`ancestry=false`，原Q21编译来源与资格不改，不为离线研究脚本重编DLL。后继仍须实际公共builder消费新来源绑定；旧共享资格不能替代当局业务结果。

导演范围继续保持四组核心案例：圣物与圣地两臂、同一朝圣规划、一次完整普通朝圣、双报价与一次真实建制及当前宗教状态。无需为四类奖励全部为正或固定事件ID重刷；H3最终许可未知不说成游戏拒绝，也不要求发动大圣战。当前可播放预览70段24:33.600；73段24:59.733仍是作者配方，未重渲染。补入核心案例的净编辑预算177–243秒，预计27:57–29:03，尚非新TTS或成片实测。

闭场读取兼容已使用B20原件跑通完整消费者，6项定向检查及新增类型/函数范围的严格检查实际通过。显式 `retained-wait-expired-then-native-cleanup` 只允许后继行政资源准入，保留原句柄未退出与后来原生清理exit1的区别；不改normal/failure-lifecycle/business=false。来源：[真实后继闭场输入](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b21-a01/late-native-cleanup-closure-a01/B20-ADMINISTRATIVE-RESOURCE-CLOSURE.a02.actual.json)。

本轮并行包已完成共享事件接入、日推进源修复、骑士修复编译、抵达画面审阅、后继case源码与失败闭场兼容；当前继续源码提交/CI与新公共runtime。下一场实拍再补骑士/圣物净收益、完整朝圣和建制；案例旁白、字幕与素材投影可与实机并行，单机CK3仍由唯一操作者持有。
