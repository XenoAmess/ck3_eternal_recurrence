# R09：真实创建点与R07 pair之后的唯一微实验顺序

本增量仅审查已持有的exact1.20.0.4源码和小型typed消费者，机器 `desktop-3fevhd2-1c74096080`，研究源树b42afbbd85df3802b1fa6222f7aac403c2adf735。EXE资格复用SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。实际观察时间、相对源码引用和字节pin见 [source-points.json](evidence/episode04-r09-birth-scene-12004/source-points.json)。本次没有新EXE、SDK、桌面、构建、存档/巨raw读取或主树写入；**当前R178不动**。

最小可复用producer是 `28CC150` 清旧统帅分支中的 `28CC332→2A96D40`，并非后面的refresh。完整来源已在 [角色producer](episode04-merge-commander-character-record-producer-12004.md) 和 [拆分源码](episode04-split-half-source-12004.md) 入库，无须再读body。

| 调用/写点 | 能证明什么 | 单独不能证明什么 |
|---|---|---|
| `24DFA6C→28CC150(&oldCharacter,DL=1)` | SetCommander在写Army120之前有旧角色清理分支 | 条件门均满足、必生成记录 |
| `28CC332→2A96D40` | 进入具名factory | 分配成功；factory有`2A96E4D`失败fallback |
| `2A96E42→2632CB0`，随后`2A96E47` | 成功路径构造空DATA对象，并把registry选择/递增generation得到的FullID写到对象10 | 已与正确Army/Character关联、最终缓存已1/1 |
| `2A96E73/76`，parent `28CC33A` | factory写caller-owned FullID输出，RAX返回**输出指针**；parent以`*[RAX]`取ID | RAX本身不是FullID或新ArRg对象指针，不能猜ID+1 |
| `28CC33E→24E0C50`与`24E0CF4` | attach同FullID并写ArRg140=Army10 | attach能创造此前不存在的ArRg |
| `28CC37D→2633ED0` | 写ArRg148=旧Character18、其extensionF8=ArRg10 | Knight成员或当前统帅身份 |
| `28CC3B9→2633320` | 刷新已有对象；角色predicate可令cache1/1 | 对象刚刚出生、物理DATA增加 |

创建分支还要求已闭条件链：额外`28B2150`门、Character扩展存在/16C非零、F8关联ArRg的140为-1、108为0、DL真、F4解析有效Army。`28B2150`内部语义未闭，不为得到1/1随意换将。split的整ArRg迁移与末尾`28CC460`清角色也可能**移除**旧空记录；该下级处置分支不能冒充此创建factory。R0176实际只见Army18空DATA ArRg59移除、Character34232成为新军/合后统帅，没有新增1/1，不能追认为观察到出生。

现有typed字段 `native_character_role_v1` 能将一个**当前**ArRg的FullID、140/148、解析Character、predicate和F4/F8关联起来；配合完整DATA、cache及独立current commander，足以严格解释post-state角色变化。它没有创建时间、factory返回或执行parent信息。完整玩家roster前后新ID差也只证成员新增，不能排除原先未挂军的对象被接入。当前 `classify_current_regiment_character_role_12004`、freshsplit及R0176 reader因此正确保持 `birth_producer_observed=false`。

现有 `SubmitSplitArmyHalf` / `SubmitMergeArmies`在原生Validate之后只走 `submit_copy`；提交ACK和命令history不是该factory的成功回调。目前没有可直接复用的typed“已出生”字段。未来最小观测应归到**实际引擎执行的28CC150 parent**：把原command实例及PID/create/gen/episode绑定到旧Character/目标Army；观察factory成功constructor/store路径与输出FullID，再关联attach和148/F8读回。必须分开success与fallback、append与refresh。仅包围SubmitCommandCopy的parent callback没有这个证据粒度。本增量不加hook、callback/API或新schema；未真实接线及观察时出生仍false。

R07 pair结束后，Root使用如下固定顺序，当前只准备、不执行：

1. R07两臂完成后，另存一个独立普通 `S_R09`，冻结SHA、实际source/DLL、日期、完整cohort/DATA、统帅、stock/cap/weights及战争/队列状态。保护该原始baseline，不让任何一臂覆盖它；不把R07某个付款臂终态或R176仅人数相同的seed静默当共同起点。
2. Root经实际分配的normal运行/新runtimeproof进入forward臂，正常加载 `S_R09`。以fresh snapshot/caps、完整Strength/DATA/role及独立统帅读数保存F0，末尾same-frame核对。fullIDs只从当次数据取；不猜未来run号、source93或child162。
3. 对冻结且当次可控同日非战斗原军U只提交**一次split**；claim先落盘。ACK后只读F1：独立roster唯一差分发现childV，核CUnit→CArmy完整generation、原军存续、全部physical DATA/occurrence守恒、角色与双方实际统帅。合法性false或原响应未知均保留并停此臂，不重发、不resume制造后态。
4. 直接复用完整同帧F1作为premerge，提交**一次 `merge-armies-U-with-V`**。若帧真变才额外fresh pre-merge；不插入换将/休整/第二split。独立F2核U存续、V消失、原完整ArRg/DATA、所有额外/移除角色、统帅及库存公式。先保全packet，再解释任何strict变化；不套旧59例外。
5. 正常结束/保全forward结果。Root另开独立normal臂，重新加载**同一 `S_R09`**，用新实际运行绑定保存R0；完整起点observable核同F0，不能从F2或临时逆合开始。PID/episode各自绑定，不要求跨冷载相等。
6. 反向臂仅**一次split U**，独立R1发现实际childW；W可以与V不同，必须重新验证。随后仅**一次 `merge-armies-W-with-U`**，独立R2核W存续、U消失，按与F2相同规则保存完整结果。不能沿用forward的child/native ID。

这是新共同S0下正反split/merge的4个动作、6个必要Strength端点；每个端点已有完整同帧查询就复用，不补同义日志。R07后的S0若与R0176原baseline不符，旧forward不能替代F臂。对既有pair只做2次merge虽更少，但不能替代此R09 split→merge卡。录制由Root按新scene既有规则管理，本helper不二次start recorder、不自动开游戏。

新空记录须逐FullID保存count0/records[]、1/1、native predicate及角色148/F8/140；physical DATA另外严格守恒。若本次未新增记录，结论就是“该条件下无新增”，不强造producer阳性；若只有新记录后验，标为source-consistent当前角色结果，出生观察仍false。只有实际成功factory parent关联后，才可能给具名新FullID授真实创建资格。动态镜头、双臂公平性和R09整卡继续分别验收。
