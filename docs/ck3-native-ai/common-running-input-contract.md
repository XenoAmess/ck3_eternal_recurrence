# 共用运行时输入校验

`frozen_run` 默认 `input_phase="launch"`：启动准入继续逐字节检查所有冻结输入。录制请求和 keeper 内录制服务在实际游戏启动后显式选择 `input_phase="running"`。后者保留并校验全部不可变 mod、DLC 加载声明、源码、工具、配置、原始 `input-snapshots`；只把该次分配 profile 顶层 `pdx_settings.txt` 作为游戏可改写输出另行观察。

这一例外要求冻结列表中存在原始 `input-snapshots/profile/pdx_settings.txt`，而且其原 pin 必须和启动时 profile pin 相同，快照当前字节也必须仍然相同。当前游戏输出的实际大小和 SHA 作为 `_runtime_input_observation` 返回，既不覆盖原 pin，也不修改 profile 或快照。其他路径即使同名也不豁免。扩展可变集合须有新的真实证据；不能把整个 userdir 排除。

allocate 在启用录制时将共用校验 helper 加入原冻结文件。新代码必须在下一次正常 prepare/allocate 之前部署并更新 runtime pins；不能靠修改活动 checkout 或活动冻结账来热修。活动 keeper 内的旧 Python 对象不会从磁盘自动更新。

```text
python -B -X utf8 tests/test_mod_acceptance_running_inputs.py
```

测试只使用临时文本与冻结账，验证启动仍拒绝变化、运行期设置输出可变、原快照与 mod 仍不可变，以及未知阶段拒绝。它不创建 lease、游戏或录制。

统一实现位于 `xar_autoplayer.bridge.runtime_input_contract_v1`，public helper 是显式 pin 后加载的薄入口。normal-exit inventory verifier 默认仍为 `input_phase="launch"`；实际 driver 仅在 managed profile 的 evidence directory 已有 allocated ready/frozen context 时使用 running，否则保留历史专用 profile 的严格验证。running 分支先核 ready 的原 frozen SHA/run ID/state/userdir，核 inventory.settings_file 与原冻结设置 pin 相同，再共用全部不可变输入与快照检查；当前设置仅作输出观察。inventory schema、原 inventory SHA 与 native wire 不变。

这份 Python 修复不代替 native verifier 的对应修复与新 DLL 实机验收。原 native `normal_exit_map_source_v1.cpp` 也会重核当前设置字节，必须按同一 allocated snapshot 合同更新；旧进程的失败/Jobkill/exit1 保持 RED。

```text
python -B -X utf8 tests/test_normal_exit_running_inputs.py
```
