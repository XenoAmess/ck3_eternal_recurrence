# 独立圣物观察口：缓存、当前原生求值与未知收益

本候选提供 `ck3_query_player_holy_site_relic_context_v1(expected_revision, holy_site_id)`，不扩展原有 HolySite或采用DTO。新reader/serializer与Python transport分别位于独立文件，只通过共享宗教owner mailbox和现有Driver→Service→MCP接线。**独立MSVC target、生产reader/serializer的9包fixture、真实Driver→Service→MCP ClientSession消费已通过；尚未链接完整runtime、部署或实机验收**。本页资格是源码与合成内存合同，原版getter/TLS/trigger仍未在CK3中执行。原版来源与边界见[圣物专题](holy-site-relic-native12004.md)，精确本机回执见[离线资格](holy-site-relic-readonly-mcp12004/source-fixture-qualification.json)。

machine_id: `4-8e1c2f1861`。2026-10-17 UTC在外置 `episode01/relic-candidate/implementation-a01`准备和验证，精确观察时间、文件SHA和机器存储检查见本页离线资格及该目录交付回执。实现初始输入checkout为 `201606305bfb2f8ec4f4730e20d751c8ce68e288`，交付时逐文件重新核对当前main基线；目标CK3 1.20.0.4/build25734779、EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本任务未改主树和共享runtime source/build、未操作游戏/桌面/Steam/lease，未复制游戏或DLL；候选总预算512MiB。独立构建额外64MiB峰值同时计入3GiB runtime和候选预算，空间检查见资格回执。

## 智能体收到什么

| 数据域 | 原生来源和结果 | 不能据此推断 |
|---|---|---|
| `cached_world_state` | site+18 Active、site+1C有效rarity缓存；各自读取当帧值并在getter结束后再次比较。 | 最近刷新时间、世界manager本轮已落地、最终角色modifier。`refresh_time_known=false`、`world_effects_applied_observed=false`。 |
| `inventory` | site Inventory引用DWORD数组与真实24B slot表分开返回，保留原序、重复和空槽；对象union按首次出现保序去重。每对象核storage/fullID/magic、读rarity与原生HolySite owner引用。 | 引用数组长度等于有效圣物数；空槽是失效对象；某个物品一定可供奉；个人owner或槽位类型已经完全观察。 |
| 动态认可来源 | 每对象读取artifact+498实际sanctified-faith全ID集合，独立availability。 | 列表空就不认可；物品名字或模板表足以穷尽认可；已单独求得模板trigger结果。 |
| `recognition_for_*_faith` | 分别调用原版 `2530EF0(artifact, faith_full_id, null)`，对玩家faith及县主faith取得实际combined结果。该原版逻辑为动态圣化OR模板trigger。 | 把两个faith的结果互相复制；把动态列表当combined getter替代；从某个结果断言其余关联faith也认可。 |
| `current_relic_evaluation` | 单独调用原版 `265A3F0(site)`取得当前原生总等级，并报告sum>0及与缓存是否不一致。桥接不重排/去重原版内部slot求值，也不写回cache。 | per-object前一刻认可值必然可复用于native内部每次求值；它就是已应用效果、永久Active状态或供奉许可。 |
| `county_context` | barony→county→holder→rite→faith，每域全ID核代际；partial读取保留已知ID，后续未知为null。 | 县民、男爵、最高领主及全部受益角色已全部读取；县主faith与玩家faith必然相同。 |

失效fullID、读内存失败、getter异常、未提供native getter和真实观测false分别记录，不将unknown变成false或空数组。根`available`只证明本次对象/frame读取稳定，不把所有子组件提升成完整业务结果。缓存与当前求值不一致时保留两套原值；当前采样没有主动刷新或修复世界。

`beneficiaries_observed=false/beneficiaries=null`、`can_enshrine_observed=false/can_enshrine=null`及`window_candidates_observed=false`固定保留。原版窗口候选本来就不是最终CanEnshrine；本口根本未触发候选重建、窗口选择或供奉/移除。

## 求值线程与副作用范围

原版getter仅从既有应用主线程宗教mailbox callback执行：先沿用当前玩家、暂停地图、epoch/TLS、revision及exact-build检查，后用原有FinishQueryMailbox进行帧稳定核对。wire thread不直接调用getter，无法通过本口任意调用RVA或选择其他actor；显式site只按完整引用解析。

site cache读取本身只是复制字节。原版认可getter会建立脚本context、使用TLS并可能分配/释放临时内存；当前总等级producer内部也会再次求认可。源码没有给“任意当前加载模板trigger完全不影响RNG”授证明。因此JSON明确 `script_rng_effects_verified=false/script_rng_effects="unknown"`，MCP不声明幂等，不能声称进程内存零写入或任意重复采样世界状态完全不变。本候选不提交gameplay command、不写世界cache、不推进日期；完整上游manager调度不作为实现或继续游玩的前置。

getter异常仅记录本次不可用，不重试未知副作用的求值，不补fake布尔值。每对象player/holder认可、当前total producer是独立采样调用，返回不强行要求数学相等；`native_getter_calls`只计桥接顶层尝试次数，不能当作内部脚本评估总次数。

## 接线、默认关闭与验证顺序

独立权限为 `allow_private_player_holy_site_relic_context_query`，独立CLI为 `--private-player-holy-site-relic-context-query`。公共受管case显式把该tool加入 `required_mcp_tools` / `opt_in_read_only_mcp_tools`，其余case默认关闭。底层复用 `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1`，仅actual4允许新step，site ID必填；没有供奉或移除action注册。

便携fixture源码 `ck3_12004_holy_site_relic_context_test.cpp`准备9种输入：正常、缓存不一致、旧generation、县主faith缺失、getter缺失、真实空库存、无效但未占槽引用、重复slot与cache不可读。它使用owned memory与显式注入的getter依赖，不运行CK3引擎；生产reader与正式command_result serializer必须实际编译运行后才有包。输出backend标为 `owned_fixture_injected_getter`，不能把这些包说成实机或原版trigger运行。

`consume_holy_site_relic_native_packets.py`随后读取实际编译输出，经真实NativeDriver、GameplayBridgeService、create_server和MCP ClientSession消费；只替换endpoint I/O、hello与snapshot。不得用Python预制业务DTO代替native包，不得把没有native输入而跳过的测试算成功。至少核public revision与native revision确实不同，检查实际发送的native expected_snapshot_revision及独立后读。

构建入口独立target为 `xar_ck3_12004_holy_site_relic_context_test`，最小standalone CMake位于 `cmake/holy_site_relic_context_12004_first_fixture`，显式传 `XAR_REPO_SOURCE_ROOT`提供冻结的既有header。实际使用项目 `tools/run_native_msvc.py`、Release、MSVC19.51及 `/W4 /WX`编译三个源文件，并完成新EXE精确路径Defender登记实际读回。fixture要求全新输出目录，已存在目录拒绝覆盖；重跑必须换新输出。带启用宏的生产宗教mailbox新分支也已独立编译为对象，不把它说成整DLL已链接。

离线资格包含28条native检查、9个未改原包逐SHA核对、4个实际Python/MCP测试且0 skip；public revision=2实际转换为wire native expected_revision=701和expected_snapshot_revision=701，capture_epoch=17。正常、partial、unknown和stale-generation均经实际MCP消费；另外4个明确标为人工变异的包验证foreign-build、错site、cache-write及虚构beneficiaries被拒绝，不是实机失败。首次MCP尝试因测试overlay过晚设置搜索路径、base NativeDriver提前缓存而RED；回执与stderr保留，修复为在执行原package initializer前设置搜索路径，并断言实际加载候选Driver后重跑通过。不能把最早1 PASS/3 SKIP的静态检查或失败attempt当作本次完整资格。

首次新DLL冷载再执行同一site query，保存实际机器/EXE/DLL/actor/site/revision、返回原包及独立后读；只读链闭合后才可申请下一窄动作实现。第一期采用后态可据此决定“尚欠认可圣物/控制/观测能力，是否值得经营”，不能因为圣地已加入名单就预填收益。

复核期限2026-10-24或游戏/source SHA改变时提前复核。外置patch在Root实际应用核验48小时后复核为可重建派生物；当前必要source pin和失败回执仍保护，按通用存储策略管理，不无限保留所有源码镜像与重复包。
