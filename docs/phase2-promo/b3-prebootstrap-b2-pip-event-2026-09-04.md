# B3 fresh-seed 前置 `zg361b2.40` 取证（2026-09-04）

状态：**B2 PIP 与原版 no-secrets 两个一次性 drain 均已实机 GREEN；630-file fresh seed 已从
原始 bootstrap 基线重采并晋升 canonical。**

## 本轮真实边界

GUI provider 闭包补齐后的 630 文件产品在独立 `-userdir` 中成功完成前端与存档加载：

- frozen source：`f830f5f1159f50e806b72bff3bac9bea53b6ba4a`；
- source seed SHA-256：
  `233e70536d736c32efb9bbd20ef4bab9e0be8f96ee13524707b9ee31e319dc9c`；
- product：630 files，tree SHA-256
  `9e75d8e55bbbf5170da3b40c8411dafc7387cf2a8b0f51c2f06c71b0856ee723`；
- frontend ready：52.032 秒；
- loader：`loader_stage_ready / GREEN`，54.403 秒，303 个 database nodes；
- `CJominiScriptedEffectTemplateDatabase`：596 ms init / 763 ms inclusive；
- `gui/zg361_promotion_source_bridge.gui` 已随产品挂载，本轮日志没有上一轮的
  `Could not find widget 'zg361_promotion_source_bridge_window'`；
- runner report：`Z:\p2v\a\runner-report.json`，SHA-256
  `2ec4f8a8922cfc9733f892364c599c100a393b6052eb6a54c703b38bb39fbb66`；
- event wait：`Z:\p2v\a\bootstrap-event-wait.jsonl`，SHA-256
  `d0acefcca8172129496757db4316aac7bbf315500c7e61a45bbc5207d8fe92ea`；
- driver state：`Z:\p2v\r\native-state\native-session\driver-state.json`，
  SHA-256
  `d99e0cb5f4c66c6cecd17b34574fb00e02633ca95ada7adb00f46e41598fd29f`；
- managed cleanup、tree gone、driver closed 均为 GREEN，结束后 CK3/injector 为 0。

因此本轮 RED 不是加载性能 RED，也不是单文件过大。现有 effect 边界仍是按用途拆分、
非 legacy 单文件最多 10 个 effect、超过 20 的文件为 0；没有证据支持为了本轮故障继续拆分。

## 精确业务 RED

载入后时间线从 `date_raw=53147016` 正常前进到 `53147040`，随后出现此前 seed 已排程的
玩家 PIP 回应窗：

- event key：`zg361b2.40`；
- process-local instance：13；
- root / prompt subject / personal result target：character `29037`；
- reviewing superior / prompt owner：character `32904`；
- 正好三个 authored、shown、enabled、非 fallback、非 cancel 选项；
- 三项依次为“接受计划及配套支持 / 修改一次目标 / 拒绝”。

seed runner 原先只登记了旧 `bfc73f...` checkpoint 的 `zg361.4` 与
`spymaster_task.0381`，所以按 fail-closed 规则在选择前停止：
`unexpected visible event before bootstrap: 'zg361b2.40'`。这证明 loader 与 GUI 闭包已通过，
阻点移到了业务时间线编排。

## 一次性处理合同

`tools/run_zg361_phase2_seed_capture.py` 只为上述 exact source save 登记
`KNOWN_PRE_BOOTSTRAP_B2_PIP_EVENT`，并在每项身份检查通过后选择 option 1（accept，native index 0）。
选择前再次核对暂停、日期、instance 与三选项形状；选择 ACK 必须证明旧 instance 消失且 option
编号/索引一致。save SHA、事件 key、日期、玩家、上级、PIP owner/subject/target 或选项形状任一漂移，
都在动作前 RED。它不是 `zg361b2.*` 通配器，也不允许任意 mod event 自动关闭。

普通与 `-O` 两轮 `tools/test_run_zg361_phase2_seed_capture.py` 均 GREEN。当前能力等级仍为
`static-ready`；只有下一份 immutable clean checkout 的 seed capture 实机 GREEN 后，才能推广为
已验证的前置 drain，并更新 canonical seed 合同。

## 第二轮：PIP drain GREEN，`spymaster_task.0399` fail-closed

提交 `945f7d470647761ff3b5f238ec6d145a25bd572f` 的 clean checkout 重跑后，PIP drain 的所有
identity、pre-selection 与 option-1 ACK 检查均为 GREEN：

- drain artifact：`Z:\p2w\a2\known-pre-bootstrap-b2-pip-event-drain.json`，SHA-256
  `a8fe8d70efd71d3193eecc33958b04b4131a999f8e0ca9069bb7955d4f99c166`；
- runner report：`Z:\p2w\a2\runner-report.json`，SHA-256
  `466b4c33118610188f8335cac9a2860737a2d3e78eb00c33ecad09ed074b2732`；
- event wait：`Z:\p2w\a2\bootstrap-event-wait.jsonl`，SHA-256
  `51f1359cc9358adee3eaa6db182b0ae1edfe6c0895479b81f4951ad11c60558a`；
- driver state：`Z:\p2w\r2\native-state\native-session\driver-state.json`，SHA-256
  `adb9fb2f3e74d5ba79f32153dbec75e88c226c51e6fad69be1138ac2050eb97f`；
- loader 再次为 GREEN（51.955 秒），cleanup/tree gone/driver closed 均 GREEN。

PIP 关闭后时间线继续到 `date_raw=53148768`，出现 exact `spymaster_task.0399`，runner 因它尚未登记而在
动作前 RED。1.19.0.6 原版定义位于
`game/events/councillor_task_events/spymaster_task_events.txt`，文件 SHA-256
`2d7f0237d9888812a55c14b7a8a3bba551ff64d8ae72ae28088456af93fcff57`。该事件表示密探没有发现秘密：
option 1 会令密探改回 default task，option 2 不改当前任务。故新合同只为 source seed `233e...dc9c`
的这一实例登记 option 2，并绑定：root `29037`、councillor `27963`、councillor liege `29037`、
target `27051`、存在且类型为 boolean 的 `no_secrets_here`、两个 authored enabled options。

旧测试里用 `spymaster_task.0399` 代表“未登记事件”的假设已被真实证据推翻，反例改为仍未登记的 `.0398`；
这不是放宽 namespace。新增 exact GREEN 与 identity-drift-before-action RED 用例，normal/`-O` 均 GREEN。
截至本节 `.0399` drain 仍为 static-ready，不能把它或完整 seed 写成 live GREEN。

## 第三轮：无窗口 `resume-map` revision race

提交 `8d0c408be452bd13c185f4653ea80649705e1600` 的下一轮 run 在 loader GREEN（43.253 秒）后，
第一份无活动事件 snapshot 为 revision 4；提交 `resume-map` 前 native revision 已变为 5。原 waiter 只在活动事件的
`pause-map` 路径处理 `PreSubmissionRevisionMismatchError`，无窗口的 `set-speed-1` / `resume-map` 会把同一种正常
乐观并发竞态放大成 terminal RED。它发生在任何事件选择前，不否定上轮 PIP drain，也没有执行 `.0399`：

- report：`Z:\p2x\a\runner-report.json`，SHA-256
  `250b3f28b237838541609f7d554868fcf49e327891623f62672daddae3cf19bc`；
- event wait：`Z:\p2x\a\bootstrap-event-wait.jsonl`，SHA-256
  `65b7f1df848bed6f25485d7d323d8b766a220b53ac08fccdc9036faa7efab6a5`；
- driver state：`Z:\p2x\r\native-state\native-session\driver-state.json`，SHA-256
  `7cb2b6b09be3ddde776ea9642e810ced5265d2e7c654ef8b87c95b3050d44240`；
- cleanup、tree gone、driver closed、clean source unchanged 均 GREEN。

最小修复在相同总期限内记录 `timeline_revision_changed_before_submission`，重新取得 snapshot/revision 后再提交原
timeline step；不重放事件选择，也不放宽其他异常。新增确定性 resume-race 测试证明尝试 revision `4 → 5` 后抵达 seed，
normal/`-O` 全套均 GREEN。该修复仍是 static-ready，须下一轮 clean run 实机互证。

## 第四轮：两个 drain 均 GREEN，但 completed seed 不能二次 bootstrap

提交 `218026a65d61db0a4c0d5248a2a68d3a4f42ce4e` 从 `233e...dc9c` seed 重跑时：

- PIP accept drain GREEN，SHA-256 `5b0866fad644d68915a15ed984bfd48a6c3f1ec53bef09ad0cc83d3abc3a3e49`；
- `.0399` option-2 drain GREEN，SHA-256
  `d6917616168bf30ddc865207b46d9a91c69cacd808fffacbe2dce8ad2ed1e697`；
- revision-race 没有再次终止；loader 51.876 秒 / GREEN；
- 两个窗口关闭后时间线继续到 `date_raw=53150544`，300.098 秒内没有重新出现
  `zga_phase2_seed.1`；
- report / event wait SHA-256 为 `ca9bc08c...e23f4` / `171dc80a...e1e9`，cleanup GREEN。

这不是新的产品 RED：`233e...dc9c` 本来就是一次 seed fixture 已完成后的输出，不能再次触发同一个 bootstrap。
继续延长 timeout 或登记更多事件都不能修复这条错误输入路线。正确做法是从原始 `bfc73f...` bootstrap seed 直接在
新产品上重采。

## 第五轮：从原始基线重采 630-file seed GREEN

同一 `218026a` clean source 改用冻结的原始 bfc seed 合同后，no-launch 预检与 CK3 串行 run 均 GREEN：

- product：630 files / 28,906,930 B，tree
  `9e75d8e55bbbf5170da3b40c8411dafc7387cf2a8b0f51c2f06c71b0856ee723`；
- loader：46.583 秒，`loader_stage_ready / GREEN`；
- exact `zga_phase2_seed.1`：`date_raw=53147016`，revision 12；
- capture / checkpoint / provider baseline capture / cleanup / driver close / source invariant 全 GREEN；
- report：`Z:\p2y\a2\runner-report.json`，SHA-256
  `ee121aa2968159706006c3aa6694c7d3a1de811abe53c66b7ba7075f022f451a`；
- candidate contract：`Z:\p2y\a2\candidate\zg361_phase2_seed_contract.candidate.json`，SHA-256
  `c5d0b27e9d32eb28b134d316aa5b6a8d6872cd048aeef65b2d0ada0acbdce4d9`；
- canonical save：`Z:\p2y\r2\native-state\profile\save games\xar_checkpoint.ck3`，
  57,377,787 B，SHA-256
  `8e6ceb97e97cd6b9185ebbcce38b42fc087e0b800cd5e321037c9f29a79e45b9`。

`tools/zg361_phase2_seed_contract.json` 及 promotion / incident / projects-metrics 三份 choreography 合同已更新到
新 seed；HC-workforce 同步测试也更新。五份合同测试合计 27 项 GREEN，effect 边界 4 项 GREEN。新 seed 只证明
可复用 paused 基线和 provider baseline capture，不证明 B3 promotion action/postcondition 或其余业务域已经完成。
