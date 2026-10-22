# 罗贝尔 Source32／N39 接续与质量整改

`machine_id: xenoamess-full-tower-eb9d2c1186`；本文开始截点 `2026-10-22T03:37Z`。承接 [Source26旧交接](2026-10-20-robert-source26-a05-vacation-handoff.md)及[质量整改专题](../ck3-native-ai/current-saved-code-quality-correction-20261022.md)。其他机器的安装、Steam、容量或现场结果不能替代本机读回。

**04:27 接续注意：N40 仅 readiness 批次已闭场，未提交 FULL11472，仍为 1082-02-15／5628 日。SDK 正常 persist 已改变当前 Driver；当前恢复输入改为下文 Q40 新 basis／qualification，已经真实原生校验。Q39 仅保留上一保存资格，不能直接冒充当前冷启动输入。新的运行配额、Steam、整图和首帧门禁仍须重新执行。**

## 当前实际状态

- 没有本轮受管Game、SDK、录制或Task留在运行。N39闭场三Task均Job0且注销，screen137释放序号8124，R0026为completed-red；SDK与录制正常退出，Game原Job清理exit1，不能称正常闭场。
- 首FULL11407实际成功30周期：5152→5182，1082-02-09→1082-02-15，新增6日，累计5628/10950日，剩5322日。G2仍6/8，M6/M7未完成。完整批墙钟41.4099253秒／6日＝6.9016542秒/日；1秒/日未达标。Native32 journal没有实际RPC验收信用。
- SAVE11469已实际saved，117661285B／`c52326604ce1d6aefc493c1bc5d088e26600b001a59978a93ca951b383440ca9`，history5944。Driver43056764B／`6471ffec42a0dd85f29271f02b8ff844686f20cff1e149ae96c9b5150e58ed7c1`。Driver仅有replace-returned证据，不授fsync或断电持久性。
- 当前窗口2、起点raw53144328、目标53407128、创始人31254／D0 174、当前角色40526及episode `native-40526-1bec95182886`保留。实际canonical head232，last_settled5182／53279400，cold_handoff_count14。
- 下一unused序号11470。10565、11386、11404仍作为历史unknown保留，零信用、禁止重放。新维护保存不增加ordinary或游戏日信用。

## 当前恢复输入

下列文件均在：

```text
Q39 = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/
      p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100/
      current-saved-a39-runtime-prep01
```

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| CURRENT-SAVED-BASIS01.json | 10372 | `71d9f017624daab0dfc6a02f05739ffe45361c3e2a29f51d576ce09c2a7b50c3` |
| CANONICAL-SAVED-BASIS-QUALIFICATION01.json | 2147 | `fdf2683744e030a3db0d287cc987b8ad9a2297137069f7245109c97db8c8454aa` |
| CURRENT-SAVED-MAINTENANCE-SEED01.json | 11343 | `fc9a4c123047ea07fb859ce1f6dda22316d2bde1fc1bfd55cfb1a47e991c2904f` |
| ROOT-A39-CONTINUITY-HEAD-FROZEN01.json | 36466 | `b596f4c2e136eaf30cc43c9fc5f63127fc79eed6a277f4c969766426b9b0d05e` |
| ROOT-A39-CANONICAL-RECOVERY-ACTUAL01.json | 5779 | `ce694247a0767a50b10760d52b17f03d553c85f0953fa90cc4a2ef8dd9e5b8849` |
| ROOT-A39-ACTUAL-CLOSEOUT01.json | 8704 | `0cb09179555d075cf85e46f501db15808511fff858898d530ca44aae3f1e23a2` |

原N39 raw累计状态保留旧11372维护CP，未被手改。新seed由公共 `project_completed_maintenance_save_v1` 生成：checkpoint_saved77→78、dirty=False，其他ordinary计数／T0／5182保持。前三sidecar与当前文件原字节相同；婚约resolved冷读回记录已变化，另外保存当前原件18793B／`c6ded6441f24071a8e42838b8c4cd7d8571f14ac0bb1d04a4023d727a9e1846f`，没有将旧副本冒成当前状态。

Root只物理读取Driver一次，保留RAM bytes；完整解析及SHA各两次（检查一次、原公共校验器一次），未放宽原内容守卫。实际Source32 checkpoint validator只调用一次，对SAVE散列一次；通用闭场、cold inputs和prepared SDK消费者均实际通过。Driver／SAVE读共享锁和取证进程19200已释放，进程实际exit0。最终控制台打印误写history_rows曾抛AttributeError，发生在验证、文件发布和句柄关闭之后；改用实际driver_history_rows读回，未重跑资格。Q38恢复包现在只能作历史来源。

## 已整改及剩余限制

共享请求准入增加实际配置的UTC审期守卫，permit前、最终transport前及readiness发布前重验 `now < review_at_utc`；等于截止即拒绝，STOP／既有清理继续允许。新增6项及完整34项实际通过，零跳过；三全文strict通过。截止前已发出的调用可能在截止后返回，独立journal control仍需单独准入。

通用settled-progress闭场合同替代新场次冒用A20 schema，共用原SDK／Game／身份守卫，保留旧历史分支。独审发现三份不同路径可复制同一Task代的P1，已修跨三nonce唯一性并加入真实复制反例；5项回归及两全文strict通过，独立复核收口。Game forced exit1仍按原事实记录。

面板新行动文案和saved回执优先级已修，error／unknown仍优先；4个真实N39输入回归零跳过。整20项为19通过、1个既有实机环境跳过，不能称20项全绿。面板及资格表三完整模块另由Root实际strict/equality/explicit/silent检查通过。发布器曾消费包含战分、双方兵力和资金风险的实际卡，不能据此冒称实帧富化验收。

新的首FULL计时builder生成既有adapter五字段准入，30周期／仅首批／64KiB上限／零新增RPC；8项真实binder回归通过。下一图必须在原Gate的cold admission中实际调用 `build_current_saved_first_full_control_timing_v1(machine_id=..., next_sequence=basis.next_sequence).to_wire()`；11470是启动SEM序号，预期首FULL为11472。未接Gate前不能称已启用，也没有提速信用。

开始截点时，面板当前来源向新cold的显式RendererRef接线正在最终验证。计划升级为Planv4／Quotev5，旧Q39 Planv3／Quotev4保留历史，不能只改标签追认为新资格。必须核双部署body、Outer的26项来源、canonical8／closure66及最终封包；后续实际结果另追加。

## 继续执行

1. 消费本轮最终提交及软件验收结果，使用上面的新basis／qualification。不要改旧N39、重放11404、重置窗口或以旧FileID替换新身份。
2. 下次执行前重新核机器、统一存储策略、实际容量及新有限准入；Q39的03:45范围只允许软件和恢复准备，没有新Game／SDK／录制资格。旧03:00Full不续用。
3. 后台运行新鲜Steam probe，仅offline/true准入；最后闭场观察是03:08:14.792367Z，不能当作未来启动时永久有效。禁止为Steam确认截图或抢焦点。
4. 新图必须采用显式renderer ref及首批计时，完成实际公共prepare、完整前缀、原Task顺序启动、原帧审看、SEM／CAP／BOUND／feeder真实qualification；检查每个嵌套退出码。
5. 保存和STOP须在业务截止前留出足够时间。N39 feeder按时停，但Root03:00:15 SAVE、03:00:50 STOP均超期；保存成功和调度超期同时保留，不能以cleanup grace追认。

当前检查点、原始失败及关键媒体按用途保护至2026-10-23T03:45Z复核；不能无限续存，也不能只因过期就删除活跃恢复输入。媒体395613446B只做stat／probe，未重散列、未做最终媒体质量验收。个人OBS未操作。

## 03:43软件终验追加

57项强制关键回归、完整preflight34项均实际通过，零跳过；20个完整模块联合strict/equality/explicit/silent通过，源码前后pin稳定，面板3完整模块另通过。回执分别为Q39 `ROOT-FINAL-MANDATORY-SOFTWARE01.json`（1409B／`7536ff67dfb5f31644cd0e715c9219e4bd88625d35c4c78a34867b48ca764be1`）及 `ROOT-FINAL-JOINT20-STRICT02.json`（6182B／`d31204dea96a6abcfcb7316528869e3abb0b98aac34102a48c25f18452a24486`）。新组合夹具的空源输入曾真实RED，修为非空合法源并同步SHA后重跑通过；原生产正长度守卫保留。

Planv4／Quotev5显式renderer字段及当前双路径接线已完成。实际当前材料完整RAM compose为165叶／3649995B，26外部项、8 canonical、66闭包及全部最终len／SHA逐一通过；便携intake→实际继承构造器及拒绝回归也进入57项。完整145份历史材料的compose是本机集成，仍不授便携全图或运行信用。producer最终111591B／`2802ec6c660f03b2eeee6b8e2a474d18221ef7282d5315aab653569e231a6cc6`，testcold145689B／`035c6885268d07dfec7cfb44fb23e25e1cfd20740edc18fc09cb9fac25d89273`。

Root正在按独立新04:15范围准备N40容量数据，须实际完成新四消费者复核、fresh Steam和完整公共prepare才可启动；不是延长旧03:00或软件03:45票据。此前部署与现场历史事实不变。

## 04:11 N40 实际闭场与暖态修复

本机 N40 的新 Planv4／Quotev5、165 叶物理部署、公共 prepare、完整原 supervisor prefix、后台 Steam offline/true、原 Task 启动及录制均实际通过。Game85076／出生 FILETIME 字符串 `134371147974445277`；首帧直接审看了 1082-02-15 暂停地图，2560×1440／1:1、右侧灰色文字可见、无旧蓝窗及影片标题。面板仍为等待文案，不授实际决策富化信用。首 FULL 的 control_timing 已写入真正 cold admission，但该 FULL 未运行，仍无实测提速信用。

SEM11470、CAP11471 和 BOUND 实际成功。随后公共 `load_current_saved_warm_inputs_v1` 因 `current closed Driver/SAVE exact identities` 拒绝：新 normal closure 错把历史闭场 Driver 身份继续当成 SDK persist 之后的当前身份。没有绕过守卫、提交 FULL11472、业务动作或 SAVE；canonical 窗口仍232／5182／53279400，新增游戏日和周期均为0，原 SAVE11469 保留。

共享修复将历史闭场来源校验与当前冷态身份检查分开；原公共 closed validator 和真正 cold inputs 都保留 Driver／SAVE 双前后精确 stat，warm 继续校验原六来源、Game／SDK 活代、SEM／CAP／BOUND、当前稳定 header 和 SAVE。完整 warm 消费者及反例实际8项通过；Root 联合关键60项、完整 preflight34项均零跳过，20完整模块 strict/equality/explicit/silent 通过。独审指出的 cold SAVE 后置时点也已补齐。该修复尚未在新实机批次重演，不追认已冻结 N40 源码。

Root STOP 实际为04:02:21.806185Z，在04:15前收场。两 SDK 0/0、OBS与发布器正常退出；Game 未在原30秒等待中正常退出，原 Job 清理 exit1，不能称正常闭场。两个 Task 均 Job0、注销，screen138 释放8130。媒体248385978B，小于467364602B硬上限；Root未读媒体正文、未散列、未作最终质量验收。04:03:46.640753Z 后台 Steam 仍 offline/true。

两个执行错误保留原件：第一次桌面定位漏 SDK import root，在窗口操作前报错，补实际 `PYTHONPATH` 后成功；Run ID 未在启动前分配，闭场后才将实际 launch nonce 绑定为 `…--vanilla--R0027`，明确 `late_allocation=true` 并记 completed-red，不回填历史启动时间。后继必须先分配 run ID，再启动；定位沿实际 display 子环境执行。

Q40 为同一 O 下 `current-saved-a40-runtime-prep01`：`ROOT-A40-ACTUAL-CLOSEOUT01.json`7035B／`b3859180815075a4b167bc87e53e8606b8a334f999ec8609a3b19d363257420f`；`ROOT-A40-MANDATORY-SOFTWARE-FIX01.json`1409B／`efa9928adb3524a06aa9f7ef13c00724032a48ba01aa39e390b2d01391da88fe`；`ROOT-A40-JOINT20-STRICT-FIX01.json`6183B／`0a23153e9b1b7e1dd5b7f242d8bc1449ae9ca2155ce530bedca2f9d6b2788ac7`。当前 Driver 仅 stat 为43057250B、FileID字符串 `281474989076443`，还没有新的完整内容资格；SAVE 的原 FileID仍为 `281474988852756`。

正在以独立有限软件范围实现明确的 readiness-only 正常闭场合同：仅两 Task，绑定实际只读请求、BOUND、unused NEXT、新 Driver 与原 SAVE，保留全部旧业务帧、CP、seed、ledger、T0和unknown。现有三个 Task 的正常闭场、continuity-forward及失败 schema 均不能冒充此状态。新合同及恢复资格完成前不再启动游戏。

## 04:27 当前恢复资格与 CI 真正失败原因

正常闭场 v2 已明确区分 `saved_settled_progress`／`readiness_only`，保留历史 v1。Root 对当前 Driver 仅物理读一次，原件43057250B／`5a15846ab6d2a0f53cd34722875ee993c562155db86b97474fc4a04c868d883ca`；实际 history5945，仅在原 CP5944 后追加一条合法 `restore-checkpoint`，生命周期259436→85076，原 raw checkpoint、日期和存档完全保留。解析和SHA各两次均使用同一RAM原字节（检查一次、原资格入口一次）。原 Source32 canonical checkpoint API 实际调用一次，含原 SAVE 验证路径；未另造零读复用特例。

新 normal/v2 闭场、公共 cold inputs、prepared SDK closure 消费者实际通过，业务 FULL11407／SEM11468／SAVE11469、seed、ledger、T0和unknown均未改。Driver／SAVE句柄已关闭，RAM取证进程271256实际exit0。Q40当前输入为：

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| CURRENT-SAVED-BASIS01.json | 10364 | `fb7cf75adde16fe7717283cfb629f91869f09b25e1cd48a050745826c252ab13` |
| CANONICAL-SAVED-BASIS-QUALIFICATION01.json | 2145 | `a6537bc3ff5b02bfbedb1787d181196e619df4e1104d04164fee955d3a9b31c7` |
| CURRENT-SAVED-READINESS-CLOSURE01.json | 8111 | `98ddb7829c4958c83bd77cf86d008cd6d3f96cf10da50410a50e45a2ec004029` |
| ROOT-A40-CANONICAL-READINESS-RECOVERY-ACTUAL01.json | 3117 | `f4abe808e0f27b8920c9b4b845d900d9db53e9ab72921de833b9052788fe8461` |

unused NEXT仍11472；下一批正常启动应使用SEM11472、CAP11473，首FULL由公共计时builder派生11474。没有重放旧unknown或为维护资格增加ordinary／日期信用。新共享闭场 SDK ref resolver用于后继Gate，禁止再按某个attempt的schema私猜；新运行必须新scope，不续用已过期04:15 Full。

远端144f Official run39718671223/job119626797621实际RED：mypy和57项关键测试已过，随后独立 `CurrentSavedSdkPersistenceTests.test_sdk_persist_closed_rejection_warm_binding_and_wrong_generations` 的配置夹具漏必填 `review_at_utc`。不能称严格类型报错，也不能用本地20模块通过外推整step通过。testcold已同步唯一review字段与新版typed `_trail` fixture签名，完整单例1/1、零跳过及整叶strict通过；没有放松生产截止守卫。后续本地mandatory必须执行这条独立SDK用例，不能只跑选择列表。

新软件范围到04:45仅许恢复和检查，不授Game资格。原32KiB两叶源码子帽曾实际超2883B，已停止写入并前向重分配为36KiB，保留此前超限事实。原256MiB范围内取证的peak private为261812224B，但peak working set为276344832B，超过原working set帽7909376B；独立补注前向改为384MiB，不追认旧阶段合规。实际容量、来源账和用途分别见Q40的 `ROOT-SOFTWARE-SCOPE0445-01.json`、`ROOT-SOFTWARE-SCOPE0445-RAM384-SOURCE-AMEND01.json`、`ROOT-SOFTWARE-SCOPE0445-OWNER36K-FORWARD01.json`。

04:38软件终验：完整CI step40的28条命令均实际exit0，454项含1项既有optional actual-WAL跳过；critical62与独立SDK1均零跳过，fixture已清空。Q40回执 `ROOT-A40-FULL-STEP40-ACTUAL01.json`25926B／`c963628f80d9c69c406a426b011c5cbf2b51e66c23ea6dc0a0fdacd9a1e7784d`。此为本机离线结果，不能冒远端CI通过或新实机信用。
