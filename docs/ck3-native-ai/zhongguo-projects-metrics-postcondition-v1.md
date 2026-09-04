# 天朝项目贡献到指标结果只读观测 v1

状态：**static-ready / fixture-tested；共享 mailbox/bridge/Python/MCP 已按默认关闭方式接线，未运行 CK3，非 production-live。**

能力名：`game.command.query-zhongguo-projects-metrics-postcondition-v1`。它只回答一个窄问题：CP #026 的真实贡献 receipt，是否被 Phase 3 #229 的指标结果以相同 ID 与 revision 明确回链，而且 source、result、contribution、metrics 是否属于同一 manager/subject/cycle/project case。

## 为什么需要产品字段

CP #026 属于 case E，Phase 3 #229 属于独立 case AA；两者各自拥有不同的 kernel case serial 与 revision。旧脚本只有 #026 的 kernel operation receipt/可见贡献值，以及 #229 自己的 metric object/version/dictionary code，无法证明“这一条 metrics 消费了那一条 contribution”。把两个碰巧相等的 case serial 拼起来会制造不存在的业务事实，因此本次先在权威生成器里补了显式 lineage，而不是在 provider 中猜测。

真实写入链如下：

- CP #026 A/B 在 operation 成功后递增受评人作用域的 `zg361_cp_contribution_receipt_cursor`，写 contribution receipt ID，并把成功后的 `case_e_revision` 写为 receipt revision；C 不签发。
- Phase 3 初始化器只在当前 owner/subject/cycle 与 CP receipt 一致、ID/revision 为正时冻结项目四元身份、receipt 与贡献值。
- #229 A/B 在自己的 case AA operation 成功后，原样复制冻结的 receipt ID/revision 与项目四元身份，并发布 metrics revision/dictionary code；C 不发布。

```mermaid
flowchart LR
    CPA["CP #026 A/B\ncase E operation committed"] --> CR["mint contribution receipt\nmonotonic ID + case-E revision"]
    CPC["CP #026 C\ndefer only"] -. no business receipt .-> U["typed unavailable / not ready"]
    CR --> G{"Phase 3 init guard\nowner + subject + cycle\npositive ID/revision"}
    G -->|pass| F["freeze project identity\nreceipt ID/revision/value"]
    G -. fail .-> U
    F --> M["#229 A/B\ncase AA operation committed"]
    M --> R["publish metrics result\nproject identity + receipt backlink\nmetrics revision + dictionary key"]
    M229C["#229 C\ndefer only"] -. no metrics lineage .-> U
    R --> P["native fixed-allowlist provider\ntwo complete same-frame reads"]
    P --> Q{"four identities equal?\nID and revision backlink equal?\nAA consumed tuple and visible value valid?"}
    Q -->|yes| READY["readiness.ready = true"]
    Q -. no .-> NOTREADY["available payload\nreadiness.ready = false"]
```

## Exact-build ABI 与访问边界

该 reader 复用已经冻结的 CK3 `1.19.0.6` 变量 ABI：EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，scope-variable context RVA `0x3329A40`、identifier table/lookup/name RVA `0x3B971A0/0x3B97020/0x3B97090`、character storage/fallback slot RVA `0x570C130/0x570C138`。完整机器可读合同位于 `ck3_autonomous_player/native_bridge/research/zhongguo_projects_metrics_postcondition_v1_abi.json`。

查询只读 played character scope，subject 永远来自同帧 `played_character_id`；caller 只能提供 request nonce、expected snapshot revision 与 owner filter。caller 不能选择 subject、变量名、receipt 或 dictionary key，也不能读取 owner/第三方角色 scope。固定 allowlist 恰好 40 个字段：15 个 CP #026 直接 receipt/consume/provenance 字段、1 个 P3 portfolio cycle 字段，以及原有 24 个 P3 source/result 投影字段。

provider 在 application main thread、paused snapshot 上做两次完整 allowlist 读取；前后 frame 或原始行任一变化即返回 `state_changed`。它不保留引擎指针。CP #026 receipt owner 缺失返回 `project_source_not_found`；直接 CP 身份、A/B choice、receipt、consumed tuple 或 visible provenance 不闭合返回 `project_source_not_ready`。只有直接 CP source 闭合后才发布 available payload；后续 P3 字段缺失保持 typed unavailable，并由显式 checkpoint state 区分。

## Readiness 合同

`checkpoint_state` 有四个 available 状态：`cp26_ready_p3_absent` 表示直接 CP #026 A/B receipt 已闭合且同周期 P3 initializer 尚未运行；`p3_initialized_source_not_ready` 表示同周期 initializer 已出现但 copy 尚未闭合；`p3_source_ready_result_pending` 表示 copy 闭合而 #229 result 未提交；`p3_result_committed` 才允许最终 `ready=true`。顶层 unavailable 必须使用 `checkpoint_state=unavailable`。这使 source-checkpoint capture 不再依赖尚未运行的 P3 source 投影，也不使用 ACK、fixture 或 clone 冒充业务状态。

最终 `ready=true` 同时要求：played subject 和 owner filter 正确；source/result/contribution/metrics 四组项目关联身份完整且逐项相等；contribution ID/revision/value 与 metrics revision/dictionary key 完整、范围合法；metrics 的 source receipt ID **及 revision** 都等于 contribution；#229 自身 consumed owner/subject/cycle/state/choice 与 visible value/provenance case 一致；双读同帧。

注意：#229 的 AA kernel case identity 只用来证明 metrics operation 确实提交，它不替代 CP 项目关联身份，也不要求 AA case serial 等于 CP case serial。

## 当前证据和下一步

当前已有权威生成器输出、生成器单测、独立 C++ fixture reader/serializer 测试、JSON schema、ABI/source contract 与 Python source-contract 测试。fixture 只证明闭合投影和负例逻辑，不证明 CK3 内存可读或事件可见。

当前 canonical `5c54014` 的 fresh private build、schema-2 source-capture manifest、
stage 7→8 与 effect 文件边界取证、精确但未执行的 CK3 命令，集中冻结在
[projects/metrics source-capture no-launch freeze](zhongguo-projects-metrics-source-capture-no-launch-5c54014-2026-09-04.md)。
该候选仍只到 `static-ready-live-pending`，不会改变本页的 live/readiness 边界。

中央 production choreography 已把同一不可变 cycle 的 Credit/Project producer 固定为 stage 7、Metrics/Delivery consumer 固定为 stage 8；P3 opener 只能在 CP portfolio 同周期闭合后运行。生成器分片仍为 10 个 whole-file purpose shards、每文件最多 9 个 effect，无 `>20` 例外。

共享 `CMakeLists.txt`、mailbox 第 24 固定槽 `permitted_executor_quattuorvigintary`、`bridge.cpp` handler/result frame/query counter、Python driver/service、MCP 与 facade 已接线。默认 CK3 adapter 仍不广告该 capability，因此没有 paused live 时会 fail-closed。下一步仍须在 exact build 上取得真实 `cp26_ready_p3_absent` paused response，再从该保存点执行有界时间推进并核对同一 receipt 的 `p3_result_committed`；在此之前不得写 `fixture-live`、`production-live primitive` 或生产 GREEN。
