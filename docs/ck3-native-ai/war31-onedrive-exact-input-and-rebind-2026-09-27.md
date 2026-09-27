# WAR31 本机精确输入转移与无启动重绑（2026-09-27）

用户指明同事将 R0197/R0221 文件放入 OneDrive 的 `WAR31-R0197-R0221-2026-09-27`，并单次授权对**匹配检查点**执行 `surrender-war-16777231`。这条授权只覆盖该动作一次，不把 R0221 旧的只读结果改写成投降已执行。受管实机动作与结算观察须另记新 attempt。本页只记录传输和无启动预检。

OneDrive 客户端的“选择文件夹”中，目标目录显示约 96.4 MB，原先未勾选；本机只将该目录由未选改为已选，其余 17 个可选复选框状态未变。Files On-Demand 下目录投影出 19 个文件：只对以下四个**指定路径**读取内容并计算 SHA-256；再次逐项检查 Windows 文件属性，其余 15 个仍是 `0x400020` 的在线占位，已读取的四个是 `0x20`。未打开或下载其他 OneDrive 文件。

| 文件 | 本机读取字节 | SHA-256 | 冻结身份 |
| --- | ---: | --- | --- |
| `R0197-final-frozen-pair/xar_checkpoint.ck3` | 77,478,199 | `1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A` | R0197 一致 |
| `R0197-final-frozen-pair/driver-state.json` | 16,681,512 | `1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336` | R0197 一致 |
| `R0221-original-bridge/native/xar_ck3_bridge.dll` | 3,235,840 | `C36ECCEB67A0DCA7C8C1C6C855A5036771B46617E9F1BF5F4185D965C1951BCE` | R0221 一致 |
| `R0221-original-bridge/native/xar_ck3_bridge_injector.exe` | 39,936 | `C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF` | R0221 未冻结 injector；本次新记 |

四份文件又逐字节校验后复制到外置 `D:/ck3-research-artifacts/war31-live-20260927/source-verified-01/`，保持源目录只读、不覆盖。`local-transfer-verification.json` SHA-256 为 `9D20CA6F4950EECA7A609F293FE21313A623699B62787C67519E573FD8795B3D`。历史 `xar-autoplayer-environment.json` 与 `ordinary-seed-rebind-v1.json` 仍保持在线占位：前者绑定另一台机器，后者是旧重绑证据，都不应作为本机 live 输入直接覆盖。

外置 `attempt-01/state` 以 CK3 EXE `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 和 `xar_off` 重新 `prepare-profile`，再放入上表原 save/driver。原 driver 的管道名是 `\\.\pipe\xar-g2-robert-1066-seed-66f926d`；运行官方 `rebind-ordinary-seed-v1` 后，新 driver SHA-256 为 `FBB0734B5E8818B0300E98476D35AC5D912F9EDA76239F9CCA27A0CB9329C7E0`，本机新 rebind 回执 SHA-256 为 `6AC3F66FA3FB5D1822493AAAE7D4D465B367A5AF67E18B58B94BBD3860BD3F68`。原 driver 原件与派生件分开保留；存档 SHA 不变。

第一次 `native-one-generation-preflight` 使用 CLI 默认管道，按预期因与原 driver 不同而 `blocked`，原报告保留。第二次显式使用冻结管道后，报告 `status=ready`、`ok=true`、`ck3_launch_attempted=false`、CK3 进程清单为空，精确绑定 CharacterID 29829、episode `native-29829-2bc2d599f7f9`、history index 2134、date_raw 53215920、原存档 SHA 和上述派生 driver SHA。该 `report.json` 位于外置 `attempt-01/state/preflights/20260927T143526Z-one-generation-preflight-58c22544/`，SHA-256 `1DD258CB44DD4706EEB27356B54D77A85F579D67369623C7B359B9CDAAC9C6E4`。

这些只是**输入及恢复准备就绪**，尚无 CK3 启动、同帧 WAR31 复验、硬件双点、投降动作或结算结果。受管动作前还须独立验证 exact source、授权回执、R0221 DLL、派生状态和实际 CK3 PID/创建时间；动作后须观察原生状态、下一 turn 和配对恢复。`attempt-01` 的 prepared agent runtime revision 为 `345eb451f`；后续代码若改动运行时，应建立新 attempt/profile，不改写该历史预检。
