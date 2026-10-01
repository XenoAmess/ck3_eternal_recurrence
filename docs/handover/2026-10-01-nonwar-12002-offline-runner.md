# 2026-10-01 非战争 1.20 runner 离线准备

本包接续 [09-30 休假交接](2026-09-30-nonwar-maintainer-vacation-handoff.md)，交付 **static-ready 的命令准备器及显式 file-only profile 模式**。默认只生成 metadata；显式模式复用生产准备核心，只写全新的隔离 profile。两种模式均不运行 operator、CK3、named pipe、桌面、进程查询或 live allocator。工具实际实现于 [run_nonwar_12002_offline.py](../../tools/run_nonwar_12002_offline.py)，配置为 [ck3-1.20.0.2-nonwar-runner.json](../../ck3_autonomous_player/configs/ck3-1.20.0.2-nonwar-runner.json)。

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

## 已执行的离线验证

```text
python -B tools/test_run_nonwar_12002_offline.py
```

初始 **5/5 PASS**，覆盖：普通 lane 的 official prepare/run 参数、rogue preflight/lifetime/next 参数直接通过真实 CLI parser、fake sample/game/state/allocator 目录未读写、历史 1.19 seed metadata 被拒绝混入 1.20 lifetime、完整 lifecycle 三元组保持一致。新增 file-only 分派后 **7/7 PASS**：增加直接消费生产核心且 `ck3_processes/ck3_process_inventory` 如被调用就确定失败的 fixture，以及拒绝刷新已有 state；没有调用实际 profile core或写实际 game/profile/pair。实际解释器的生产 fingerprint 所需 **25 项 distribution 全部存在**，无需额外安装依赖。未连接 native pipe，也未取得任何新 live readiness。

本次真实 metadata 生成 artifact 为 `Z:/ck3_mod_rewrite/.task-tmp/nw12002/.task-tmp/nonwar-12002-offline-20261001/GENERATION-RECEIPT.json`。`operator-manifest.json` SHA-256 为 `fd8f1189daf00d78a557461743365d37c49e145782e42de947dd1c4285117f4b`，`OFFLINE-RUNNER-PLAN.json` 为 `e80df3f0dda138b813ab693dce8a305212ab7137824565774a700ae6a23840ae`。该计划使用旧迁移 frozen bundle 的**声明** SHA 与当前集成 worktree 的源码文件 pins；它不是新的 master 私有 NW build admission。集成后的新 DLL/源码 freeze 如发生变化，应生成新的 output 目录，原 artifact 保留，不覆盖旧 pins。

`open_kaishek` 为 **not-applicable**：本步是 argv/lifecycle/JSON composition，不包含 CK3 script、IR、finite runtime 或 replay 语义。没有为形式启动 parser/validator；此说明不代替以后真正脚本/事件预验。

## 何时才需要 CK3

当前代码、配置、两条真实 CLI 参数的 offline 接线及 file-only profile mode 已完成。后续先在后台完成 selected source/native bundle 的 freeze、公开/私有 capability 匹配和独立 profile 文件准备；不为这些步骤占用游戏。本文初始 metadata artifact 没有实际 profile prepare；实际准备后另存新 receipt，不能倒填初始结果。

拿到游戏时段以后，最小顺序为：official prepare/rebind 与 exact no-launch preflight → 本机 owner、Steam 离线证据与 run ID → 一次新 PID cold 恢复、短正式循环与匹配 checkpoint → 实际 LIFE/ECON/FAMILY consumer 后置、下一 turn、规定 cold。自然合法婚配、建设完工收入、Council 阳性、完整一代人/百年及新 seed 资格，都仍只在实际 production outcome 后升级。本包没有新增日期、typed gameplay、profile/save mutation 或 G2 完成数。
