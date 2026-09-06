# R133 管理者周期恢复实机取证（2026-09-06）

## 结论

- R133 在 frozen source `3ec697925b358b3c49b6313d2f4121bc11aa5886`、R130 正式产品投影下完成加载；loader 为 303 个数据库节点、fatal 0。
- 初始暂停帧绑定玩家 `32904`，随后以 5 速推进。31 个暂停 MCP 帧从 `date_raw=53147088` 到 `53149368` 均为 `B1=true / Central=false / PP=false / review_now=false`，期间没有未知事件，也没有产品 runtime diagnostic。
- 下一运行帧触发 native one-life terminal：`one_life_terminal=true`、`one_life_terminal_reason=played_character_changed`。全程 PID `200604`、connection generation `1`、restart count `0`，因此不是 MCP 重连或 revision 增长误判。
- 本轮没有执行切换玩家命令。证据支持“原管理者失去可玩身份/自然交接”，但旧 runner 未保存被拒绝的原始 snapshot，不能据此声称具体死亡原因或继承人 ID；R133 记为 manager-owner scenario invalid，不记为产品 RED。
- R134 验证了本机不能省略 frontend-first：直接载入停在数据库 303、fatal 0，但 420 秒内未进入 Load Save/In Game。它是启动路径 RED，没有进入业务帧，不计角色死亡次数。后续恢复使用 frontend-first。

## 修复

- `_binding` 仍严格固定原玩家和 connection generation；revision/native revision 允许正常递增。
- 拒绝绑定时保存紧凑帧：snapshot/revision/date/paused/speed/map-ready、actual/expected player、actual/expected generation、PID、one-life terminal/reason 和 active event。
- `played_character_changed` one-life terminal 分类为 `SCENARIO_INVALID / manager-owner-terminal`；不得改绑继承人、不得选择事件、不得保存伪 clean seed。

## 实机证据

- `Z:\p2m133_a\manager-cycle-recovery.json` — SHA-256 `ADE1A50C786209E07750CB6FA265DB9409049C4F8EE8270CEBC7D5D23F1F75D2`
- `Z:\p2m133_a\runner-report.json` — SHA-256 `CD73075AF9F180F3B80089B2336EE4FFFD3FC8289327ABCE1FF4E3FAD8890797`
- `Z:\p2m133_a\09_phase2_native_session_cleanup.json` — SHA-256 `9D7665A617FACC9FC5B4DC3C5EAF81CC09DE80CC6D6614EF3854BBEF9D51C132`
- `Z:\p2m133_a\runner-failures.jsonl` — SHA-256 `2465D3E26D94B8A0696EB4B0A04A272E13E960675CCDC91A6CDE403788B09BAB`
- `Z:\p2m133_a\ck3-logs\dedicated_server.log` — SHA-256 `35C488EF29BB55E2830FB10C8BD605142731588C4EF2F76E030D44BFA03F6150`
- `Z:\p2m133_a\ck3-logs\debug.log` — SHA-256 `C38C103632D27D48760A61E653FD8643E526426BB5D93286C9D40E886DD360FC`
- `Z:\p2m133\native-state\native-session\driver-state.json` — SHA-256 `A69DF92446ABE632F6070D3E3D5AFD94C2E1B90ED572E51D3D70A380989D5045`
- `Z:\p2m134_a\runner-report.json` — SHA-256 `67B12382B9E5B64A778ED75069A9AD75DAB54CE8EBF72AF3773E9391CF1232B9`

## 下一步

R135 使用 frontend-first 和增强取证复验同一检查点。如果再次发生 owner terminal，按真实帧计数；只有满足项目所有者授权的连续三次角色死亡条件后，才在 acceptance-only fixture 中给原管理者添加健康值与有界 buff。产品树和 R130 正式投影不得因此改写。
