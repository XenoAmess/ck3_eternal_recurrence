# 本期 knight_killed 案例的关闭条件

范围只包含同一进程、同一次受控原版推进中的 event 11、选中骑士与受害者、该战斗两侧，以及这次死亡派生的通知写入。`global_mutable_bundle_complete=false` 必须保留。下面的“关闭”是对此范围的独立语义判定，不能用机器检查项数量替代，也不能由旧 R0139 的数据补齐新 run。

每条结论须绑定当次源码/DLL/EXE、driver 进程身份、每日 token、原始请求与返回、两个不可变原版存档、完整原始 trace、原图，以及采集窗口起止。原生记录不可截断、failure flags 必须零、钩子安装与卸载均须有实际收据。类型化角色、军团、战斗身份保留完整 generation 校验。缺失字段不填默认值。

证据的时间分辨率分为：`endpoint`（原版存档的净变化）、`operation-before-after`（原版操作入口/返回的状态）、`actual-write`（原版写函数的目标与实际请求值）、`branch-no-write`（完整实际执行树及原版写入口库存证明此分支没有该域写入）。前后相等本身不能排除中途修改又恢复。没有执行的成长或勋号分支可以关闭为 `branch-no-write`，无需制造一次不存在的写入。

| 域 | 本案生产者与对象 | 关闭所需实际证据 | 不能替代的证据 |
| --- | --- | --- | --- |
| skills | event 11 的选中敌骑士成长分支，及死亡/出伤时两层属性 | 全部实际节点、选中 random-list 条目与子节点；节点前后同 ID 基础 martial/learning/prowess（直接char+D8/E4/E8）；同 run 存档六项基础属性。实际有效战斗stats由 entries 单独对账。若空条目且写入口库存排除其他成长写，判定本案没有成长属性写 | 将char直接字段称作有效战斗属性；仅存档相等 |
| trait_set | 同两角色的实际成长/伤势/死亡分支 | 预绑定原版 trait ID/key 表、完整 trait 集在对应操作前后与下一暂停的读数；实际 trait 写节点，或完整空分支/未进入分支及写入口库存 | 仅 ordinal/key 名字、旧 run 特质 |
| trait_tracks | 同两角色特质经验 | 本case实际始终空且growth空分支时，由完整branch和当次空数组关闭branch-no-write，无需扩无本case对象的平台。有实际条目/写入时，character+138 原始 int64 数组与 +144 count 完整快照，配合同 run 原版存档完整 XP 数组及原版定义的索引映射、实际经验写边界 | 以数组索引猜 track ID；getter 输出 +0C 当 count；只存档净零 |
| death_date_reason_killer_artifact | CCharacterDeathEffect → request/queue/commit → 受害者死亡数据 | 同节点上下文、六参原始 tuple（manager/victim/reason/date/killer/artifact）、队列项及实际相关 commit；reason key 独立原生读取；marker false→true、date/reason/killer/artifact 与存档一致；整个采集窗口其他同受害者 request/commit 也完整保留 | 仅节点进入、finish ACK 或只读回 DEAD |
| prestige_currency_and_accumulated | 实际 CAddMultiLevelValueTypeEffect，选中敌骑士 | 写入口/节点与原目标，extension+130/+138 raw 前后差值，原版 execute 写锚；存档 currency/accumulated 同 run 校验。+138 的语义由原版写/保存锚证明 | 单凭两个净差值相同便把 experience 命名为 accumulated |
| regiment_link_and_membership | 实际死亡提交/脱离，受害者与军团 | request/commit/casualty/下一暂停同 ID link、regiment full ID 与反向角色 ID、双方完整骑士名单；原生保存态与角色/名单原图独立核验 | 不同 run 的 039→040 名单变化；历史 UI |
| entry_current_soft_stats_and_owner_hard | 本战斗的 phase、死亡提交、出伤和 casualty 操作 | 七边界与每次相关 casualty 前后完整 entries/current/soft/effective stats/owner-hard；同军团身份、操作 damage 与原版保存状态投影；按实际操作顺序对账 | 只提供新的一对端点；把少数行等同完整战斗窗 |
| battle_event_ledger | 本次 CBattleEventEffect 及目标战斗侧 | 实际 node/context 与 ledger 写目标/事件值；节点前后或严格独占写入口窗口的完整 ledger，新增 row 的类型/双方人物/位置；同 run 保存态一致 | 仅看见 knight_killed 字面，未证明目标或时序 |
| slain_side_knights | CJominiAddListVariableEffect → 33463D0/33DD720，本 combat-side variable owner | 实际 owner/key/typed16B victim value/duration，完整 list row 与并行 expiry 前后；owner 来源与 event 11 context 绑定，符号 key 原生解码；存档新项一致 | 一次执行节点加最终 duration=1，未捕捉实际请求值 |
| killer_kills | 死亡详情 setter 2609210 → 209F7F0，实际 killer 的 alive/dead kills 容器 | commit 前后完整 kills full-ID vector；2609210 的原 victim/killer tuple 与实际 append callee/静态调用锚；原 killer identity 与存档新增项一致 | 把 deferred health-check 264D750 当 kills append |
| signature_weapon | 原版 set_signature_weapon_effect，可能由死亡通知 immediate 触发 | before-day 起监控，两 scoped 角色的原 owner getter/写函数，actual key、请求 typed words、before/after；独立 identifier 表 epoch/index/name 解码；actual setter node/context/root scope/stack/上层 producer；另列 beforeUI→afterUI checkpoint/RNG/写次数 | 最终 save axe 反填写值；把 on_death notification 写归给 battle event 11；仅 stack 字面猜事件 |
| house_relation | 本案 CImpactHouseRelationEffect → 2DF7030 start guard，两角色当次 house | 原 house ID/type key/原 guard AL/caller。false 且完整分支无 create/write、完整 pair/相关 DB 端点一致，可关闭为未写；若要解释为何 false，另需实际子 predicate 或 source-bound 当次条件事实。true 时必须观察实际 create/steps 写与最终 relation ID | 从无持久关系猜出某条 guard 失败；把所有执行节点视为实写 |
| accolade_feedback_branch | 同两角色 is_acclaimed 分支及相关 liege/accolade 对象 | 完整实际分支树，相关 accolade 身份/值与 liege 变量的同 run 原版保存投影；未进入时配合 writer 库存关闭 no-write，进入时须实际目标/值/前后 | 为无执行分支要求虚构 XP 写；用旧 run 字段 |

实际写入可用原版 callee 前后状态与原始请求参数关闭到 `operation-before-after`/`actual-write` 层级，不要求虚构每条 CPU store 的独立日志。若一个 callee 内存在多个有关子写，须从 exact-build 调用库存列出并证明这些子写得到覆盖。整个日内状态结论必须显式列出分辨率，不能把 `endpoint` 自动升级为完整日内链。

选择器另需完整 materializer 返回原数组、source/shared filter 原始谓词数量、逐候选实际原 return、短路和 tail-swap 后数组、最终 stored order、真实 RNG counter/salt/draw、index、typed return 与实际 death 的 killer 对账。prefix 旧元素与只过滤新附加范围也须保留。仅最终候选数组不能关闭完整筛选路径。

“唯一死因”指本次受控窗口内该受害者实际死亡提交只有这一条相关执行路径，不宣称游戏只有一种死因。关闭须满足：完整实际 selector → 本节点 death effect → 原 tuple request → 对应 enqueue 或直接 commit → 唯一相关提交 → marker 与脱离 → 后出伤/伤亡 → 下一暂停；窗口内全部同受害者 request/commit、拒绝/无效路径都必须可数，源锚能覆盖本案实际死亡入口。一次独立正确的 DEAD 存档只能关闭生命状态。

最终六项清单要把 UI 门禁与机制门禁分开：角色 UI、名单 UI、完整战斗窗使用当次原图及原生身份/日期独立对照；选择器、实际死因、13 域链使用上述运行时证据。每项写 `closed` 或 `pending`、确切证据路径/SHA、缺少的具体条件。自动 PASS、全局旗标 false、老素材诚实保留都不直接决定该项状态。视频在六项前置完成前保持暂停。
