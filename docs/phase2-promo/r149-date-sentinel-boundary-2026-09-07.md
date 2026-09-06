# R149 经理续接的日期哨兵边界（2026-09-07）

## 实机结论

- frozen source：`e06f34c3edbfce04fab5623575a716c5ee00bcac`；源代码 ZIP SHA-256：
  `fe88538fcf979546067758e969d69bdb8fdc342553bbdc943e974715a53aef51`，共 3,189 个 tracked files。
- no-launch preflight GREEN；R130 的 1,031 文件产品投影及四个关键 B2 effect 继续逐字节 GREEN。
- CK3 最终实机进程只有 PID `164356`；玩家 CharacterID `32904`、connection generation `1`、默认 5 速。
  warmup PID `55512` 只用于前端着色器预热，随后已回收；最终进程和 watchdog 也全部 cleanup GREEN。
- manager recovery 精确处理 `tribute_mission.1002` / `.1005` 后，在 `date_raw=53154144` 首次达到
  `review_now_eligible=true` 且 B1/Central/PP 全 false 的暂停 clean review boundary。该阶段结果是 GREEN。
- 旧 runner 在该边界暂停等待 1 秒后仍未看到 `zga_phase2_manager_seed.1`，随后按 R146 设计只发送一次
  speed-5 `resume-map`。提交前发生一次正常 revision 竞争（public `256`、internal `257`）；重新读取后唯一一次
  resume 被接受，但下一帧直接到 `date_raw=53154264`，比 clean boundary 增长 120 raw hours，且 seed event 仍为空。
  maximum-date gate 立即用 revision `257` 提交保护性暂停并 RED，没有继续推进或伪造 seed。
- `manager-cycle-recovery.json` SHA-256：
  `ef38ff04dad10e48a6b06ba39351f7f51a852ca530503eabeb126b8f7dd1bde0`；
  `runner-report.json` SHA-256：
  `a472986e3cac07b67012f008347e4e4a7f766d483df9e76ecc2b5fdb343ea588`；
  `bootstrap-event-wait.jsonl` SHA-256：
  `7d8f30386f1d2f2cc6a4a087f08310bd8cd8971c193938bf68a7389bc8ba5ddc`。

## 定位与最小修复

R149 否定了“普通一次 5 速 resume 可以提供同日 GUI 运行帧”这一夹具假设。Python/MCP 在观察到 running 帧后再暂停，
无法保证只推进一天；这不是产品脚本、产品投影或经理恢复链 RED。当前 paused snapshot 的 `player_armies=[]`，既有战术
daily sentinel 又要求至少一个 ArmyID，因此不能直接复用其旧 arm 合同。

修复把原生终止哨兵扩展为仅在 `mode-terminal` 下允许 canonical `a-0`：它不读取军队/战斗图，只在原生 daily final-stage
按绝对次日边界暂停。decision 模式与省略 mode 的 `a-0` 仍拒绝，原有正数 ArmyID 路线不变。Phase2 runner 只允许：

1. 在 clean boundary、paused/map-ready、speed 5、零玩家军队时 arm；
2. 提交恰好一次 resume；
3. 在 `clean_date + 24` 校验 generation、one daily tick、date deadline、零 overshoot 和原生 pause；
4. 只接受该精确日期上的 `zga_phase2_manager_seed.1`，否则 RED。

原生 focused CTest `2/2`、date-only runner 单测 `4/4` 以及 seed runner 普通/`-O` 双回归均 GREEN。新桥接 DLL
`Z:\b3probe-msvc4\xar_ck3_bridge.dll` 的 SHA-256 为
`68a16d6669efb1f42057bd36ea2f7c19b61f382e631659519a0dcae275307204`。

玩法状态、事件与按钮仍全部来自 MCP/native。报告中的 OCR/image 只用于非玩法 legal-consent/front-end gate，
`coordinates_used=false`。本轮 loader 正常完成，未出现新的加载性能 RED；因此没有新增产品 effect 拆分动作，既有按用途
1–10、原则上不超过 20 个 effect 的强制边界继续生效。
