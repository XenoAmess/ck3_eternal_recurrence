# B3 fresh-seed 前置 `zg361b2.40` 取证（2026-09-04）

状态：**实机事件身份已冻结；一次性 drain 为 static-ready，尚待下一轮实机互证。**

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
