# R189：两次 preview 默认 unavailable，不是县条件 false

机器 `machine_id: desktop-3fevhd2-1c74096080`。实际 SDK小回执分别于2026-10-16T19:32:50.290187Z与19:34:48.225691Z记录Army18→2644、18→2610失败；Root本批已消耗 **2/5总尝试**，不重放、不继续刷2636/3720、不Move。其后独立context仍native:3/public4/native3/date53149080、paused、actor31254、Army18@2635/sieging3/完整空route/无combat或retreat。本文没有推进或接触SDK/桌面。

## 本次真正保留了什么

两份响应均`is_error=true,body=null`，错误全文共同后缀是`native gameplay step failed: CK3 move-army route preview is unavailable`。现有SDK错误回执没有native numeric status或producer stage。只读检查native-session/bridge/outbox为空；没有声称找到了已被消费删除的原始wire。一次读取253534B driver-state，仅提取command_history index8/9，仍只存相同 `_NativeCommandRejectedError` 字符串。没有读12MB Army-query或存档，也没有重发失败请求。

精确post与两history的≤3KiB原值在`FAILURES.actual.json`。不要把same native/public revision看成所有mailbox内部比较成功；Worker的预采、提交、wait、reclaim和frame比较未发布本次细项，仍可能失败。

## 从这条错误能排除哪些错误解释

`bridge.cpp:29472–29514`默认采用本次字符串，但对以下实际enum均替换为专属文本：`province_not_found`→destination province was not found；`army_state_rejected`→army state rejects movement；`route_unavailable`→could not build a complete move route；还有paused/origin/move-mode/character/validation专属文本。因此本次**不能说目标不是nativeProvince、围城状态不许移动或寻路没有路**。这不是县最终predicate false；`ck3_12002_adapter.cpp:324–328`仅在preview available后才调用县child。

在已读源码控制流下，默认enum是`PreviewMoveArmyStatus::unavailable`（game_contract.hpp:2384–2396，序号11）；这是从源码和默认文本得到的有界解释，**原wire没有直接观察到数字11**。

actual4走`ck3_12002_adapter.cpp:314–330`→`ck3_12002_military.cpp:353–497`。后者仅以下三个自身路径保留默认unavailable：

* 360–371：binding/world所需函数缺失或未enabled；
* 373–375：ReadCurrent失败；
* 444–445：原construct_move_path返回指针不是command.path.data()。

在其外层，`WorkerAdapter::preview_move_army`（semantic_adapter.cpp:638–641）在`Run`false时直接返回默认对象，丢弃具体原因甚至已计算的preview。`Run:382–429`可能在pre snapshot/paused/map、submit、wait/reclaim/frame或catch失败。军事逻辑是否实际进入、真实province是否已解析，目前没有本次分支事件可分别证明。完整允许的结论是：**当前a30这两次路线查询未发布可用结果，真实最早失败点仍未观测**。不猜唯一根因，不把默认enum数当raw字段。

## 最小候选：保留默认失败原因，不放宽任何守卫

只采用 `preview-unavailable-reasons-a02.relative.patch`。首份未封a01草稿曾把新增field放aggregate前端；a02将其置于末尾以保持已有aggregate参数位置。a01存于历史zip，不用于集成。

六个路径，新增typed `PreviewMoveArmyUnavailableReason`及尾部field、一个标签header；军事三处默认失败设置各自原因；现有semantic Run仅为preview记录pre/submit/wait/reclaim/frame/exception原因；Worker失败仍清空所有route/P并保持status unavailable，只保留reason。bridge默认错误追加`[native_preview_status=11;reason=<tag>]`。原native函数/validator调用次数、frame守卫、成功wire、Move和县条件执行不变；没有新hook/query/ring或补默认true。

成功原路径继续调用一次；失败mailbox不能借已计算的available结果越过frame守卫。getter/原函数都没有重放。enum字段不分配动态存储。修改内部C++ DTO意味着Root必须下一coherent native build；不对R189热换或复用旧OBJ。

已为现有military fixture追加**只跑新三例**的`--preview-unavailable-reasons-only`入口：binding缺失、snapshot不可读、path constructor返回不符，各核不同reason、原validator计数及无submission/错误cleanup。此native fixture **AUTHORED_NOTRUN**；worker失败与bridge透传也尚需Root窄资格，不冒充native GREEN。本lane只做最终patch只读`git apply --check`，exit0；未build/运行EXE、未重跑旧fixtures。下次先完成必要资格，然后Root在新鲜绑定中只做一份已来源目标的preview便能知道到底是哪层，而不是再扫终点。

## 交付与边界

`DELIVERY.actual.json`记录最终patch、原actual响应pins、source pins、压缩历史和copyplan。旧a31与fix-a02均保留；a02的只读embarked修正和generic preview语法仍有效，但**当前R189两次失败之后停止其候选执行**。Root已同意按真正typed Province/Unitkind/definition/specialflag门审后续Move；普通wire没有standalone embarked，不能补false或以它要求再次full导出。

本包新增的是可重现的actual失败事实、已收窄的默认失败入口，以及下一build可读的窄原因publisher候选。R04 positive、actual P/Q返回、物理扣兵、研究/镜头信用均未新增。
