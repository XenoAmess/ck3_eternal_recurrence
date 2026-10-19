# M1：月度MET的真实来源采集接缝

新增[`campaign_score_monthly_met_v1.py`](../../ck3_autonomous_player/src/xar_autoplayer/campaign_score_monthly_met_v1.py)作为下一次维护可采用的生产collector。它在paired post-AUTO MET处理器内取得当前普通semantic帧，只在固定月点顺序调用现有cash-v2和公开campaign-root接口，再复用[已有纯投影](g2-m1-existing-month-inputs-2026-10-19.md)。当前运行树与冻结SDK未采用本叶；旧月样本不回填，不能声称本场月度财务已经取得。

机器`xenoamess-full-tower-eb9d2c1186`，本次`tools/ck3_live_run_id.py machine`实际读回；源码审计时间`2026-10-19T04:34:58.302149+00:00`，基于HEAD `d74afbf395301c8546d861d6130902b425deab32`。源码pins、7项软件验证与容量见[小回执](evidence/g2-m1-monthly-met-production-2026-10-19.json)。没有调用现场RPC、读取活Driver/SAVE、改COW、编译Native、stage或commit。M1历史complete、G2仍6/8，没有新增业务信用。

## 生产所有权和唯一接线点

runtime owner在本轮确认实际路径已经是以下C3文件，旧`root_p37_mcp_entry.py`不是当前入口：

| 生产者 | 所有权及职责 |
| --- | --- |
| `runtime/root_p37c3_mcp_entry.py::root_current_runtime_metrics` | Runtime/Root所有；当前MET快照入口；下一维护批替换原snapshot+candidate两行 |
| `runtime/root_score_month_samples.py::candidate` | Runtime所有；现有固定开局锚与cadence入口；不能回写历史锚或月样本 |
| `runtime/root_p37c3_sdk_queue.py:2232` | Runtime所有；AUTO结算后的paired-MET与persist；继续负责实际response/SHA/Game tuple及create-only/fsync |
| repo `campaign_score_cadence_v1.py` | 已有固定365日/准点月界合同；本轮未修改 |
| repo `campaign_score_existing_inputs_v1.py` | 已有纯DTO口径与来源核对；本轮未修改 |
| repo `campaign_score_monthly_met_v1.py` | 本轮独立新增；只调已有接口，输出窄candidate，无IO/缓存/重试 |
| `GameplayBridgeService.query_campaign_root_context_v1` | Root所有；本轮只审源码，未修改 |
| Driver `query_war_cash_current_resources_private_v1` | 已有private只读接口；本轮不改permission、不新建Native入口 |

`runtime/`绝对根为`D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime`。runtime owner确认当前业务SDK仍为`src03/063531c4`，未采用新collector。后续由Root给出exact HEAD，整包source冻结并实际readback。

唯一待维护生产接缝是MET入口用本collector取代原来的快照读取和`candidate(...)`调用；不能在它之前再取一次快照，否则普通非月点也多一次SEM。现有Queue配对与持久化继续使用返回candidate：

```python
snapshot, score_sample = collect_monthly_met_candidate_v1(
    service,
    start_date=configured_start_date,
    machine_id=actual_machine_id,
    campaign_anchor=fixed_campaign_anchor,
)
```

调用必须位于同一runner拥有的post-AUTO MET中，前一个AUTO已经结算、下一次action/advance尚未开始。collector不接收外部snapshot参数、不搜索旧AUTO包，也不能单靠本函数证明Queue的动作顺序。原MET响应的实际pin和Game绑定仍由既有Queue完成。接线维护前尚需owner把当前helper中的固定anchor/config传入，不能另造开局身份。

## Native真实范围：两个暂停只读捕获

源码没有现成cash+campaign-root复合查询。`bridge.cpp::RunWarCashCurrentResourcesQuery12003`在actual4路径给cash独立envelope/ticket，执行`ExecuteWarCashCurrentResources12004`；campaign-root经`RunTypedQuery12002`、`ExecuteTypedQuery12002`的campaign分支另起envelope/ticket。每项都用`EnterQueryMailbox`/`FinishQueryMailbox`核对暂停帧与原Snapshot。`CaptureTypedFrame12002`中的`snapshot_revision`来自`expected_snapshot_revision`，不是main-thread `pump_epoch`。`PublishSnapshot`在完整Snapshot未变时保留revision，不能据相同revision推出同一次捕获。

因此candidate明确记录`mode=paused_readonly_bundle`、`same_native_capture=false`、两个epoch均null及`not_exposed_by_existing_cash_and_root_interfaces`。没有制造capture ID。原`planning-source-frame/v1`逐项保留snapshot/public/native/date/actor/episode/bridge_pid/connection_generation；cash DTO自身的queried三元组和root public binding仍独立验证，绝不把结尾的新frame盖给旧DTO。

Python cash transport已有query前后`_binding`稳定核对；public root已有开始/结束snapshot与build、queried三元组核对。collector每项之后再用原fast SEM accessor检查现有planning frame，补齐episode/PID/generation。其SEM accessor本身不是新Native业务查询；Native查询仍由原接口完成。中途frame变化即停止后续query；只允许最终实际帧形成准点candidate，旧包由纯叶拒绝。若跨离月点/不再暂停则不生成月样本，不能重建刚才的旧slot。

缺方法或明确`UnsupportedStepError`为已有接口/资格不支持，保unknown；不启用private权限。cash的Bridge/transport/结果或格式异常可能尚有inflight，稳定SEM也不能据此再发root，collector停止本bundle且不retry。关闭SEM不可读时不提升任何可选DTO；初始普通SEM本身不可读时仍沿原MET异常合同，没有可伪造的sample。调用owner必须继续遵循现有client恢复守卫，不能用本叶绕过未结算请求。

## 数据收益与持续开销

| 帧 | 本collector开销 | 可记录内容 |
| --- | --- | --- |
| 非准点或未暂停 | 原fast SEM一次，0 query | 沿原MET返回，没有月样本 |
| 准点且接口可用、帧稳定 | collector自身SEM至多三次；顺序调用现有cash/root各一次 | 四个财务月率、native domain大小/上限、直接地理county和继承转移暴露诊断 |
| 缺资格/字段、发生漂移或请求未知 | 不补读、不retry、不发不确定后继query | 已证明同源部分或unknown/null，缺口写入candidate |

cash仍是Q100000金/月：gross、total expenses、current military、all-raised military；全部依现有v2标记，当前军费已含在总支出，actor军费跨全部战争只计一次。不从net反推gross，不从余额差反推流量。`due_commitments`、P_quality、合法player-heir、全realm与dynasty品质继续unknown，四个新率不等于确定E/M。输出不带完整root原包、命令历史或世界对象；软件fixture的candidate低于32KiB。Native实际发送次数没有现有DTO计数，故`new_RPC_calls=null`配`native_requests_at_most`与方法调用数，不伪称实际RPC为0或固定2。

## 低频领地与宗族损失反馈

每月root可可靠观察当前个人domain及直接地理county集合变化。相比上一个**同actor/episode**实际root，失去某个直接county可产生个人领地变化诊断；不能把它改名为realm loss，也不能单凭第一头衔继承人推出失地结果。切换actor时应与独立T0/current-player范围对齐，不能混合两个人的domain。

全realm/dynasty现有可用来源是[`campaign_score_save_reader.py`](../../ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py)：已有`locked_save`、Rakaly stdout streaming、`SaveProjection`和`project_metrics`。其中完整saved titles的holder/de_facto_liege链给realm县成员；holder→house→固定T0 dynasty/parent-house链给宗族成员及折价；county发展/控制、当前holding与occupation决定Q/K或上下界。T0采用[本场独立基线](g2-m1-robert-v20261019-T0-baseline.md)，不能借用旧局县集或旧174锚。

最小生产方案是异步消费**已经产生并由owner保护的**checkpoint SAVE：年度复核，并由继承、己方战争结束或fresh root直接领地减少触发提前复核；同一SAVE SHA只解析一次，合并重复待办，不阻塞AUTO。worker一次流式读取，只保留带机器/时间/SAVE SHA/日期/actor/固定创始锚的窄县成员、holder/house和Q/K摘要及差集；不每月新SAVE、全量melt落盘或永久留全部checkpoint。原件保护与派生物期限由统一storage owner登记，不能因“评分用途”无限续期。

这部分仍是可实施方案，本轮未新增后台worker或历史丢地结论。必要producer缺口是：现有reader的`in_realm`遇缺失/循环liege链直接返回false，未输出逐县不确定成员；生产loss feedback在把不完整链判为境外前必须加完整性审计。动态无地家族county也须先由当前地图定义确认地理资格；不能只靠`c_`前缀。holder/house冲突、父支系缺口、occupation缺字段或source binding不齐时，差集及品质相应保unknown/区间，不声称实际损失。Native root目前没有完整realm/dynasty县目录，这个范围缺口与MET接线不同，不能通过更多月度root查询补齐。

## 本轮验证和留存

新增7项fake-driver定向回归一次通过（内部0.005秒、外层0.9212702秒，exit0）：真实月界数据接线、非月点/未暂停快路、缺方法、明确cash资格拒绝后root可用、revision/generation中途变化、未知inflight不再提交、关闭SEM不可用。测试只使用已有小fixture的合成改写，不是Native验收；未重跑旧矩阵。所有新文件合计低于64KiB，计Root共享研究剩余128MiB，不新设预算。观察时Z盘total4,096,787,476,480 B/free178,400,665,600 B仅为当时读回，不是空间预留；记录180日复核。Root统一提交，下一维护批实际采用后仍需独立记录运行版本与真实首个富化月样本。
