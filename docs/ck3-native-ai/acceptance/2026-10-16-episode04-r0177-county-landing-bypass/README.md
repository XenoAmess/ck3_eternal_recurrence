# R0177 R04：实际 landing 输入旁路与下一条陆路边

本场没有授予 R04 county physical positive。043 的实际第一站输入已足以排除
held-input 县预算：旧/目标 definition `+1B` 是 **0/1**，native county condition
也是 **available/false**。原生当前 B100 仍然可用；它没有变成实际扣兵100。
后续围城的扣兵归 R03 处理，不因它发生在 landing 附近而归到 R04。

本机 `machine_id: desktop-3fevhd2-1c74096080`；运行 R0177，actor31254，
PID7240/create134365679117288462/generation1，episode
`native-31254-00b796ef873c`。观察与逐文件 SHA/原件引用见
[OBSERVATIONS.actual.json](OBSERVATIONS.actual.json)。EXE 继续绑定已核的
1.20.0.4/build25734779、SHA256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；
本增量没有读取 EXE、联系 SDK/游戏/桌面、构建或写主树。

## 043 原值和准入

043 查询 frame 为 `native:65 / public66 / native65 / date53147088`，
Army18/native18，whole1195。它的具名8,633,859B完整 Driver result 曾在 Root
授权下只读一次，size/mtime 前后稳定；不是原始 pipe bytes，也没有重新hash。
本增量复用4,907B baseline，不再读取大包。

| 实际输入 | 043 值 | 来源解释 |
|---|---:|---|
| native current county B | 100 | 当前 getter 结果，非 writer debit |
| F / M / loaded N | 5000 / 100000 / 100 | 保留原生取整结果 |
| loaded base / nonzero floor / raw Army1D4 | 10000 / 0 / 0 | signed64 floors 与原始 byte；不补假常量 |
| condition | available / false | actor31254、source1032、target2635、mode1 |
| old / target definition1B | 0 / 1 | 只用非零准入，不命名未证地形类型 |
| observed / conditional post-entry Unit170 | 0 / 0 | 既有 prefix ready，特殊flag0 |
| stored first edge | 1032→2635 | 完整route `[2635]`；两 Province tag 均为 Prov、Unit kind0 |
| predicted first arrival | 53147184 | 当前 committed timeline；不是已执行回调证据 |
| S_pref | 1195 | 同query loss_application whole1195 |

已闭 source `24E23E0` 要求 old/target definition1B 都非零，特殊flag0，且
`24E2230` 条件true。043 至少有两个 false gate。**raw1B0 是准入失败，
不是将 B 计算成0**。若准入才有 P=min(B,S_pref)=100、R=B−P=0；不能将这个
反事实预算写成已扣100或已扣0。R0 时本来就不进入 residual allocator，
不能把没有 residual token 当作额外零损耗证据。

baseline writer installed；latest3377、oldest2866、overwritten2865、
unattributed failures0，当前Army18匹配事件0。ring 全局容量512，旧事件可被
其他Army覆盖；空ring、Army净变化、当前budget及同日siege都不能代替逐writer
来源和实际物理槽 debit。零预算/准入失败在现有非零 residual scope 前旁路，
当前 journal 没有这类 callback 的独立负事件。

## 044/045 和闭场边界

本增量只读取这两个具名小envelope，不读其9MB完整结果：

- 044：query7 / public79 / native78，accepted，摘要Army18/native18为1195人；
  response-local原件9,031,245B，capturer SHA
  `0a2e7bc41d763a40b9927e5d043573c513d7c397795f33bd4ea78d846167a910`。
- 045：query8 / public82 / native81，accepted，摘要同为1195人；
  response-local原件9,164,263B，capturer SHA
  `07254b531103c33ff4a20163c07b9f8bd58a3c011a8fffbd4ce6434e0a390467`。

小摘要没有当前位置/日期。Root 现场owner明确报告044已经到2635、日期53147184；
文件名的 `preland` 不代表实际仍未landing。这项位置/日期在JSON标为 Root 提供，
本lane未从大原件独立投影。Root随后报告047/date53147472的R03 siege positive11，
已交R03 owner；本R04增量不读取、不重新分类该事件，也不以1195净数归因。

因此本场支持“观察到的第一站准入被排除，后续实际到达由现场owner报告”的
边界结论，不支持“整个县损耗为0”、县callback实测零事件或 R04 positive。
Root已通知本场闭场，本增量不要求继续推进或再查询。

## 下一场最少操作与验收

目前没有同时通过 native 合法路线和 county condition 的具体新目标；
`selected_target_province_id=null`。下一场先在 fresh 身份/局面上取得合法陆路
native route preview；获准提交一次路线后，保持暂停，用已有同Army
`ordinary_core_v1` 检查实际 stored first edge。地图陆路标签只是预选，最终
必须读 actual old/target definition1B，而不从 sea/land 名字推断 byte。

推进这一条边前，要同帧确认：typed distinct Province 与 Unit kind0；两byte
均非零；既有 prefix 给 conditional post-entry Unit170，特殊flag0；native
condition 对 exact actor/source/target/mode available/true；当前B>0。保留实际
loaded floors或具体 unavailable，不能在缺字段时补0。另取同query的S_pref；
S_pref≥B时优先验证primary，R0不等 residual。若gate false，记录这条边的真实
负例再选其它合法候选，不为拍正例盲推进。

同一observer lifetime保存 latest_sequence、unattributed failures 和运行身份；
只推进该first edge，到达后暂停，取**一次**同Army ordinary_core查询即可。
现有 serializer 在history profile守卫外发布 actual writer family，无需重复full
profile或新增hook/query。使用以下现有consumer：

```python
classify_retained_loss_writer_window_v1(
    row["actual_loss_writer_observations_v1"],
    current_regiment_ids=actual_full_ar_rg_ids,
    executable_sha256=actual_bound_executable_sha256,
    after_sequence=before_latest_sequence,
    before_unattributed_capture_failures=before_failures,
)
```

输入来自完整Driver row `/army_strengths/i`，按实际army_id匹配i；同query保留
完整regiment FullID、county child、loss_application、current_movement和query
snapshot/revision/native/date/generation/episode。primary raw return必须是
`0x24E25EE`；native caller_kind为other也不能滤除。residual inner
`0x2A958E8` 还必须有完整county_entry父上下文、outer `0x24E2630`、flags0、
实际CArmy/array/writer FullID匹配。flags0单独不能分县和siege。

existing physical consumer须验同instance、complete capture、完整DATA alias→
unique物理槽，unique raw current-before/after差之和等于实际debit且>0。
不以request、ArRg缓存、军队净变化或当前roster membership授原生invocation
owner。缺日期只能不给dated资格；窗口覆盖不足保留缺口。没有合格事件时，
结论是未获得 retained county positive，整个县总额仍unknown。

源码、公式与只读决策入口见
[R04 source](../../episode04-county-entry-loss-12004.md)、
[route risk consumer](../../episode04-county-route-risk-decision-12004.md) 和
[residual parent](../../army-county-residual-parent-scope-12004.md)。本增量仅文档及
literal投影，没有改consumer，也没有重复旧测试矩阵。

口播：“原生当前县预算是100，但登陆前实际旧省份字节为0，县进入条件也为false，
这条边不满足县扣兵准入。后续围城扣兵单独归因。要展示县扣兵正例，下一场先找
实际双字节非零、原生条件为true的合法陆路第一站，再用writer物理槽验一笔。”
