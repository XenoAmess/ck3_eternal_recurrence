# 2026-10-01 非战争 1.20 runner 离线准备

本包接续 [09-30 休假交接](2026-09-30-nonwar-maintainer-vacation-handoff.md)，交付 **static-ready 的命令准备器、实际新 Z 盘 production profile 与原样复制的真实 1.20 save/full-driver pair**。最终 file-only 准备于 2026-10-01 12:50（Asia/Shanghai）完成，绑定已提交源码和已冻结 DLL；具体 receipt 与下一阶段入口见文末。默认工具只生成 metadata；显式模式复用生产准备核心，只写全新的隔离 profile。两种模式均不运行 operator、CK3、named pipe、桌面、进程查询或 live allocator。工具实际实现于 [run_nonwar_12002_offline.py](../../tools/run_nonwar_12002_offline.py)，配置为 [ck3-1.20.0.2-nonwar-runner.json](../../ck3_autonomous_player/configs/ck3-1.20.0.2-nonwar-runner.json)。

## 保留的身份与资格

- G2 仍为 **3/8**，Robert 仍为 **3,153/36,524** 持久游戏日；首整局、百年、独立种子没有本包增量。Robert h4025/raw53220000、BA5/Guy/首继承人/prisoner ledger 均保留为 1.19.0.6 原始证据。本工具不读取、复制、截尾或重新绑定这些资产。
- 1.20 MCP 迁移中的 R2、死亡换局及其 Character29829 不构成 Robert 延续证明。CharacterID 相同不能替代 episode、合法 save/full driver/profile/ledger 的对应关系。
- H3937 日期 hold 的 release、原战争责任人的接口与六项读口不由新命令计划解除；新计划不改正式战争意愿、不修改旧 owner/任务总线、不调用另一台机器 endpoint。
- 本配置只生成独立 1.20 pair 的施工入口。若要迁移 Robert h4025，仍由原 official prepare/restore 判断兼容并保留全部未完成 action ledger；本包没有该次游戏格式转换或 cold 资格。

## 两条已有生产路径

| lane | 生成的入口 | 完成条件 |
| --- | --- | --- |
| `ordinary` | `g2_preview_operator.py prepare-state` → `run --turns 20`，`xar_off/ordinary_campaign_succession/ordinary_campaign_no_pact=true` | 官方 prepare 从实际配对派生 rebind/preflight pins；受管 20 turn 只按实际材料、checkpoint、cold 结果记账，不算整局 |
| `rogue` | official `prepare-state` → exact `native-one-generation-preflight` → `native-one-generation` → 独立的 `native-next-episode` | 输入必须是合法 1.20 `xar_on/rogue_one_life` seed；一代人以真实死亡结算完成，达到 max-turns 只算 incomplete；next 仅在已验证 terminal settlement 后执行 |

两条 lane 使用原仓库 `agent.py`/operator，不新增 gameplay loop，不改消费者或 bridge。普通继承的 G2 不能通过切成 rogue 死亡结算来获得长期资格；`native-one-generation` 也没有伪造的 ordinary-lifecycle 参数。新 native 私有 NW provider 的 ABI/版本资格由各施工包独立证明，旧 BA5 源码完成或新公共 migration DLL 不能自动外推为全部私有能力可用。

生成器所有机器路径均显式传入，没有账户、机器 PID 或临时 profile 的协议前提。默认输出只包含 `operator-manifest.json`、`OFFLINE-RUNNER-PLAN.json` 两份 metadata；game/sample/state/allocator/DLL/injector 路径仅作为命令参数保存，不打开或创建。DLL/injector SHA 是操作者声明值，计划明确记录 `binary_files_read_or_verified=false`，不把声明称为 build admission。源码文件逐项 SHA 与配置共同保存，方便 final 集成后重新生成匹配计划。

## 可运行的离线入口

在任意兼容机器，使用该机器的实际参数生成普通 lane。下面只有生成器执行；它不会执行输出中的命令。

```text
python tools/run_nonwar_12002_offline.py --lane ordinary --source-repo <repo> --python <python.exe> --game-dir <game-root> --state-dir <new-state> --dll <bridge.dll> --injector <injector.exe> --dll-sha256 <sha256> --injector-sha256 <sha256> --pipe \\.\pipe\<local-pipe> --sample-dir <valid-12002-paired-sample> --output-dir <new-metadata-dir> --live-run-state-root <local-persistent-allocator>
```

`--lane rogue` 还需 `--seed-identity <json>`。此 JSON 仅为已冻结 pair 的输入 metadata，格式如下；工具不会从这些值制造或修改 save/driver，也不接受把 1.19 声明改名为 1.20 的旧 metadata。

```json
{
  "game_version": "1.20.0.2",
  "episode_character_id": 100,
  "episode_run_id": "the-actual-frozen-episode-id",
  "checkpoint_sha256": "actual-64-character-save-sha256",
  "driver_state_sha256": "actual-64-character-full-driver-sha256"
}
```

输出 `commands[].argv` 是可交给 Python `subprocess.run(argv, check=True)` 的真实参数数组，避免命令行转义改变 pipe/path。它是分阶段计划，不是可直接自动批量执行的脚本：先审阅 official preparation 的实际返回，再进入下一阶段；native-next-episode 不能无条件接在超出 turn bound 的 incomplete lifetime 后。ordinary operator 自行分配 live ID；rogue/next 前分别生成正式 allocator 命令，运行者必须把产生的完整 machine/mod/run ID 绑定到对应 artifact。

## 不占用 CK3 的 profile 实际准备

沿生产调用链核实后，不能把所有 `no-launch` 都当作当前可执行的纯文件步骤：

| 原入口 | 实际依赖 | 当前处理 |
| --- | --- | --- |
| `environment.prepare_profile` | `ck3_processes()`，全局零 CK3 判断；随后调用 `_prepare_profile_locked` | 不执行外层；显式 file-only 模式在全新 state 取得原 `exclusive_state_lock`，直接复用纯文件核心 |
| `ordinary_seed_rebinder.rebind_ordinary_seed_v1` | `_zero_ck3_inventory()`；修改 full driver 的三个 lifecycle environment anchors | 不伪造 inventory，不复制/改绑定 Robert 或其他实际 pair，留到授权实机时段 |
| `native_one_generation_preflight` | `ck3_process_inventory()`，检查零实例；实际 full driver/checkpoint consumer 验证 | 不以 fake process 信息封为 READY；留到同一真实配对的正式 preflight |

`_prepare_profile_locked` 的调用只包含：launcher identity/version、生产 source allowlist/projection、`rule_contract`、源码/解释器/依赖/Git fingerprints、游戏 EXE/game_rules/DLC 文件 SHA、隔离 descriptor/settings/presets/tutorial 初始化、`verify_profile`。`verify_profile` 也是纯文件校验，不调用进程枚举、allocator、pipe、输入或游戏启动。核心会更新 profile control 文件，因此显式模式只接受此前不存在的 state，不能用于正在游戏的实际 profile。

在上面的生成命令末尾添加 **`--prepare-profile-files`**，并给出全新 Z 盘 state 和 metadata output。它生成实际生产树和 `profile/xar-autoplayer-environment.json`，输出等级为 `static-ready-profile-files`；`profile_file_preparation.pairing_or_cold_preflight_complete=false` 保持真实边界。此模式固定 `EnvironmentSpec.expected_game_version=1.20.0.2`，并把准备结果的 EXE SHA 与配置里的 `AE1BA6…81B2D` 比较，不凭版本字符串绑定任意新二进制。

所需实际读取输入为：`launcher/launcher-settings.json`、`binaries/ck3.exe`、`game/common/game_rules/00_game_rules.txt`、`game/dlc/*/*.dlc`，以及 **selected source 的主 mod allowlist**。不会读取真实 Documents userdir、Workshop cache、Robert/Guy/first-heir/prisoner ledger、任何 save/driver。主 mod 新 1.20 trait snapshot/catalog、原生 succession GUI projection、rite modifier 名称应先由已验证迁移结果正确投影进 selected source；master 的旧 `224` 条静态期望不能用来校验新版 `226` 条结果，profile projection 成功也不等于完整 mod L0 已完成。

最终 source/mod projection/native bundle freeze 后，此 file-only 模式即可实际执行，无需游戏时段。真实 pair 绑定、game parse/runtime、新 PID cold 与可玩闭环仍是后续独立步骤。

## 初始 A-only pair 实体盘点

为判断是否还能继续做真实 file-only pair staging，初始阶段只盘点冻结 migration artifact 根 `Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2`，当时没有读取 current P/state、真实 profile 或 D 盘。实际发现 **save 实体 0、full driver 实体 0、seed/checkpoint/state/pair archive 实体 0**。`canonical-registered-live-attempt-01/result.json` 包含实际保存记录与 native command history，但不包含完整 persisted driver-state v2 record；不从观测 history 重造 full driver。后续扩大只读取件范围的实际结果见下一节。

| 冻结 metadata 已证明的 pin | 值 |
| --- | --- |
| canonical 证据 SHA-256 | `073e31d5884c7bad8100b6319416301621531b93853d0735d4430b97e1eef127` |
| save SHA-256 / size | `15fec60d3ec284161f135b095402181be9f64de966c002e1282e9bd2e5827825` / `67,083,928` bytes |
| date / actor / history | `53169072` / `29829` / `74` |
| episode / pipe | `native-29829-3f80e147d033` / `\\.\pipe\xar_ck3_bridge_migration_12002` |
| save metadata 指向的位置 | `C:/Users/xenoa/AppData/Local/XarAutoplayer-1.20.0.2-migration/profile/save games/xar_checkpoint.ck3`；**本包未访问** |
| full driver metadata 指向的位置 | 同 state 的 `native-session/driver-state.json`；**未访问、无 frozen full-driver SHA/实体** |

盘点与提取分别保存为 `S/.task-tmp/FROZEN-12002-PAIR-ASSET-INVENTORY.json`、`S/.task-tmp/FROZEN-12002-PAIR-METADATA-PINS.json`，其中 `S` 为本次集成 source worktree。初始阶段没有添设无实体输入的配对实现，也没有以 fake fixture、改写 1.19 metadata 或 command-history 重建替代实体。此历史记录不代表后续取件后的当前资产资格。

## 后续只读取件与实际冻结

root 随后依据用户“不要占用 CK3”的真实边界，允许只读 canonical metadata 精确指定的本机 save/full-driver 两文件；没有扩大到遍历 Documents、Robert、D 盘、另一机器或操作游戏。实际 save 仍完全符合上表 frozen pins；实际完整 persisted-v2 driver 为 **536,722 bytes**、SHA-256 **`7eba0a48b78c06d6ee31bef47ecaf7f8408bc24702bf88a5966dd1ab94dbbaa7`**，history 完整 **74** 项、episode/actor/date/pipe 均相符。源资格记录为 `S/.task-tmp/CANONICAL-12002-SOURCE-PAIR-QUALIFICATION.json`。

源资格另保留于冻结 A 根的 `nonwar-offline-2026-10-01/CANONICAL-SOURCE-PAIR-QUALIFICATION.json`，SHA-256 `9c3c309d1f44bb99a0c9ac68d462fadd424f6efb438cb5b8ec7929f7675f0ab4`；不依赖临时源码 worktree 继续存在。

据此实现了真正有输入和施工价值的 [stage_nonwar_12002_pair_files.py](../../tools/stage_nonwar_12002_pair_files.py)。它只接受明确 save/full-driver 路径与预期 pins，调用实际 `inspect_ck3_save_artifact_v1`、`require_seedable_ck3_save_v1`、`load_native_driver_state_for_resume`、`validate_cold_start_checkpoint_for_pipe`，逐字节复制到新 canonical 文件布局，并在目标重复使用同一生产 file validators。它不解析/重写 save，不截尾/归一化回写 driver，不调用 ordinary rebind、official preflight、process inventory、pipe、desktop、Steam 或 allocator。原 driver 没有 persisted lifecycle 字段，consumer 正常采用已有 **legacy rogue_one_life** binding；没有因此改成 ordinary G2。

实际冻结到：

```text
Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2/nonwar-offline-2026-10-01/canonical-seed-files/
  profile/save games/xar_checkpoint.ck3
  native-session/driver-state.json
  SEED-IDENTITY.json
  PAIR-FILES-QUALIFICATION.json
```

**`PASS_STATIC_FILE_PAIR`**：源与目标 save/full-driver 的 SHA 完全相同，完整 pipe/episode/history 保持；原 P 两文件未写。本 pair 来自已验证的 1.20 公共生产入口，不是旧 BA5 私有 NW pair，不携带/宣称 Robert/Guy/first-heir/prisoner ledger 或 tutorial 延续资格；其 file pairing scope 只覆盖 save/full-driver。raw save 格式识别仍明确为 **header-only + canonical full-file SHA/size**，不是完整 gamestate 语义解析。

`PAIR-FILES-QUALIFICATION.json` SHA-256 为 `a244c0d5c7fb63fa63a41e145d0bc48623bc9e0f5647ae048a16cf3a027c480e`，`SEED-IDENTITY.json` 为 `0e4d144fc71ae446d293bfb7c75a078a8e515cd16199ac8a7760027e3fe4b196`。两份 receipt 都明确 `official_zero_process_preflight_completed=false`、`real_game_cold_restore_completed=false`、Robert/G2 增量零。

工具的 portable 调用入口为：

```text
python tools/stage_nonwar_12002_pair_files.py --source-save <canonical-save> --source-driver <full-driver> --target-state <fresh-Z-state> --pipe <original-pipe> --expected-save-sha256 <save-sha> --expected-driver-sha256 <driver-sha> --expected-character-id <actor> --expected-episode-run-id <episode> --expected-date-raw <date> --expected-history-index <history>
```

最终 fresh production profile 已准备时，可增加 `--into-prepared-profile --game-dir <game-root>`，纯文件验证该新 profile 为 `xar_on/1.20.0.2` 后把这份 Z 盘冻结 pair 写入仍无 save/driver 的目标。不得以此刷新或覆盖原 P/其他运行 state。生成器 `--lane rogue --seed-identity <frozen-pair>/SEED-IDENTITY.json` 直接复用实际冻结身份；official exact zero-process preflight与真实 cold 仍在后续游戏时段执行。

新 staging fixture **2/2 PASS**（真实生产 file validators、byte-preserving copy、SHA 不匹配拒绝），之后对 main 的既有目标拒绝路径补了 **1/1 PASS**，证明重复请求不写已有 archive。全部 fixture 都是明确 fake save；实际 P 的 PASS 则来自上述独立真实源/目标文件资格，不混记成 fixture 或 live。

## 已执行的离线验证

```text
python -B tools/test_run_nonwar_12002_offline.py
```

初始 **5/5 PASS**，覆盖：普通 lane 的 official prepare/run 参数、rogue preflight/lifetime/next 参数直接通过真实 CLI parser、fake sample/game/state/allocator 目录未读写、历史 1.19 seed metadata 被拒绝混入 1.20 lifetime、完整 lifecycle 三元组保持一致。新增 file-only 分派后 **7/7 PASS**：增加直接消费生产核心且 `ck3_processes/ck3_process_inventory` 如被调用就确定失败的 fixture，以及拒绝刷新已有 state；没有调用实际 profile core或写实际 game/profile/pair。实际解释器的生产 fingerprint 所需 **25 项 distribution 全部存在**，无需额外安装依赖。未连接 native pipe，也未取得任何新 live readiness。

本次真实 metadata 生成 artifact 为 `Z:/ck3_mod_rewrite/.task-tmp/nw12002/.task-tmp/nonwar-12002-offline-20261001/GENERATION-RECEIPT.json`。`operator-manifest.json` SHA-256 为 `fd8f1189daf00d78a557461743365d37c49e145782e42de947dd1c4285117f4b`，`OFFLINE-RUNNER-PLAN.json` 为 `e80df3f0dda138b813ab693dce8a305212ab7137824565774a700ae6a23840ae`。该计划使用旧迁移 frozen bundle 的**声明** SHA 与当前集成 worktree 的源码文件 pins；它不是新的 master 私有 NW build admission。集成后的新 DLL/源码 freeze 如发生变化，应生成新的 output 目录，原 artifact 保留，不覆盖旧 pins。

`open_kaishek` 为 **not-applicable**：本步是 argv/lifecycle/JSON composition，不包含 CK3 script、IR、finite runtime 或 replay 语义。没有为形式启动 parser/validator；此说明不代替以后真正脚本/事件预验。

## 何时才需要 CK3

当前代码、配置、两条真实 CLI 参数的 offline 接线及实际 file-only profile/pair 准备均已完成。本文初始 metadata artifact 保留原始含义，最终准备另存下面的新 receipt；没有倒填初始结果。

拿到游戏时段以后，该已准备的独立 rogue pair 先执行 official exact zero-process preflight，再绑定本机 owner、Steam 离线证据与正式 run ID，完成新 PID cold 恢复、短正式循环与匹配 checkpoint，验证实际 LIFE/ECON/FAMILY consumer 后置、下一 turn及规定 cold。普通 G2 lane 仍只有参数计划，正式 prepare/rebind 留到该 lane 自己的合法输入与实机窗口。自然合法婚配、建设完工收入、Council 阳性、完整一代人/百年及新 seed 资格，都仍只在实际 production outcome 后升级。本包仅写新的 Z 盘 profile 与复制 pair；没有新增游戏日期、typed gameplay 或 G2 完成数。

## 最终实际 file-only 交付（12:50）

源码已提交并推送为 `adb19c92cb16a458aeaef7381201d0e9ce762885`。最终集成 manifest 为 `Z:/ck3_mod_rewrite/artifacts/offline-nonwar-2026-10-01/integration-final-manifest.json`，SHA-256 **`5f17b6515e34427ed6ee7626fbf6f185753c0c0daf6cb732e30294462dec0222`**。本次准备先验证该 manifest 的完整 SHA，再消费它绑定的最终 binary；没有重用初始计划里声明的旧 bundle。

| 最终 bundle | DLL SHA-256 / bytes | injector SHA-256 / bytes |
| --- | --- | --- |
| `artifacts/offline-nonwar-2026-10-01/build-native-msvc`，selected-private | `def2617b7dd67b01b08a576c99c3bfa8dc90fa908921671b4b79f9bbad47da1e` / `4,926,464` | `e402b569c6677dc7072ff70455564f3b2ce7f4a67c8710bd682e98e5c2f5239b` / `39,936` |
| `artifacts/offline-nonwar-2026-10-01/build-native-msvc-default`，shipping default-OFF | `aa26ddb30d9f044d66fc9307ba65c32a1218acd7f2bd189981ac479892f4855a` / `4,051,968` | `23c39b1f247e75ec539484495ba4851cb3b037e0238cbf9a24715f66a6e254ec` / `39,936` |

selected-private 构建启用 LIFE_FORMAL、CONSTRUCTION_VIEW、WORLD_BUILDING_ACTION、RANKED_MARRIAGE、ALLIANCE_PROJECTION、HEIR_MARRIAGE、CHILD_MATRILINEAL 七项私有 native 编译选项；shipping 七项均为 OFF。**正式 Python consumer trialflags 仍为 OFF**，编译资格没有升级为 live 或正式 gameplay 资格。

实际新 state 为 **`Z:/ck3_mod_rewrite_process_assets/nonwar-12002-canonical-independent-20261001/state`**。按顺序实际运行 `run_nonwar_12002_offline.py --lane rogue --prepare-profile-files`，再通过 `stage_nonwar_12002_pair_files.py --into-prepared-profile` 从上述 Z 盘 frozen canonical pair 复制两份实体及身份 sidecar。实际 production projection 为 **86 文件**，准备核心与 `verify_profile` 均通过，EXE SHA 仍为 `ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`。

| 实际 profile 绑定 | SHA-256 |
| --- | --- |
| environment contract | `1b2b79023a481537d929051e6e51c05f9b75f6674eaf2570dea02558b40b4bb5` |
| agent runtime | `96d24800f57017edfdbdd2ab79806e2988548b27bb83a064d2836c7570014a77` |
| production tree | `2c000fa0f6d30aa3c9dd58f4471aace2c408d73a0e8c7bed6509dbbe17d5cda2` |
| `state/profile/xar-autoplayer-environment.json` | `e05a568dfa9593c307f11c79802fdcd25f3f85e077a7f4157eaddce9be527f36` |
| `state/PAIR-FILES-QUALIFICATION.json` | `ce5b5460207932365bc3b93a6fe88e4c5feed8401ecd9491bac8c8718eab42aa` |

新 state 的 save/full driver 分别保持 `15fec60d…827825`、`7eba0a48…bbaa7`，actor **29829**、raw date **53169072**、完整 history **74**、episode `native-29829-3f80e147d033` 与原 pipe 全部保留。`SEED-IDENTITY.json` SHA 仍为 `0e4d144fc71ae446d293bfb7c75a078a8e515cd16199ac8a7760027e3fe4b196`。这是独立 legacy rogue pair，**ordinary state 未准备、历史 Robert 延续未成立、G2 与 Robert 增量均为零**。最终操作只读取 Z 盘 frozen pair，没有再次读取或写入原 P profile，也没有改写 frozen seed。

最终 receipt 为 **`Z:/ck3_mod_rewrite/artifacts/offline-nonwar-2026-10-01/runner-files-adb19c9/FINAL-FILE-PROFILE-PAIR-RECEIPT.json`**，SHA-256 **`da05c04bddb9228426290c38e495572a61c714cc9fe1e32d238afb977abc26d4`**，生成时间 `2026-10-01T04:50:27.837945+00:00`，结果 **`PASS_STATIC_PROFILE_AND_FILE_PAIR` / `static-ready`**。同目录保存：

- `rogue/operator-manifest.json`、`rogue/OFFLINE-RUNNER-PLAN.json`：最终 selected-private 源码/binary/profile/pair 绑定。
- `ordinary-plan-only/operator-manifest.json`、`ordinary-plan-only/OFFLINE-RUNNER-PLAN.json`：shipping bundle 的普通 lane 参数计划，未执行 prepare/operator/rebind。
- `NEXT-LIVE-PHASES.json`：SHA-256 `e083c4178362c179fdb17fea91f280fccf3e9aaf8f371049dea9400e0e02ecbd`，保留实际 CLI 的 exact preflight、lifetime allocator/lifetime 与 next allocator/next 分阶段 argv。已移除被本次真实 file-only 准备替代的 prepare 阶段，避免后续覆盖该已冻结 profile；next 仍必须等待 verified terminal settlement，不能在 max-turns incomplete 后自动执行。

此次实际准备没有调用任何 CK3/process inventory/pipe/desktop/Steam/allocator 入口，未启动或占用本地游戏。`official_zero_process_preflight_completed=false`、`real_game_cold_restore_completed=false` 保持不变。剩余最小实机工作为：**正式零进程 preflight → 新 PID cold restore/readiness → 代表性 paused 非战争读口及材料/下一 turn/checkpoint 后置 → 自然完整 lifetime/next**；普通 G2 的 durable lineage 另按真实生产结果记账。
