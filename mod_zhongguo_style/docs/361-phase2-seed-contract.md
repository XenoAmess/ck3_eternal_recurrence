# 361 二期 MCP-only 存档种子合同

状态（2026-09-01）：仓库中的固定种子合同是
`blocked_seed_generation_required`，不是 ready，也不是 production-live 证据。它可以作为
旧存档来源账本，但不得启动二期正式批量验收。权威机器合同是仓库根的
`tools/zg361_phase2_seed_contract.json`。

## 已纠正的旧存档身份

旧合同把事件保存作用域里的上司误当成事件 root：

- 来源运行：
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-worktrees\v0.4-main_process_assets\zg361\runs\zga_20260830_191131_7e82d061`
- `report.json` 的 `witnessed_result_identity` 中，事件 `zg361.4` 的
  `root_scope.typed_identity.character_id` 是 **29037**；这才是当时实际扮演的历史角色
  `han_6875`。
- 同一窗口的 `saved_scopes[name=zga_reviewing_superior]` 是 **32904**；它是上司
  `han_8052`，不是玩家。
- `cell/10_phase2_witnessed_result_identity_01_prequery_pause_gate.json` 也绑定玩家
  CharacterID 29037；`cell/10_phase2_result_accept_speed_one_gate.json` 的
  `starting_character_id` 同样是 29037。
- 原版 `Crusader Kings III/game/history/titles/e_china.txt` 的 1066 段把
  `k_hedong` holder 绑定为 `han_6875`。

因此旧合同现声明 `date_raw=53147016 / CharacterID=29037 / han_6875`。旧 autosave
不是 typed `save-checkpoint` ACK 的产物，日期仍只是待验证的来源假设。

## 为什么旧存档不能继续冒充 ready

该存档早于现有 B1、B2、Incident、Workforce 产品状态。当前 runner 又需要五个真实
selector：B2、Incident、Workforce 三个 received-self owner，以及 AI-owned B1 case
的 owner/direct-subject。旧 MCP 没有枚举这些关系的通用查询，旧 artifact 也没有捕获
这些五项。故机器合同的 `domain_query_matrix` 目前精确保留五个 `null`；blocked 合同
允许 `null`，ready 合同必须五项都是正 int32 CharacterID，且 owner 不能是玩家、
AI owner 不能等于 subject。禁止填假 ID 只为让 loader 通过。

旧 save、报告与索引仍保留如下来源信息：

- save：52,902,730 bytes，SHA-256
  `98687d21fe816a4a42d1d6bef85cea9d8a0ed9e74d53cdeadf653b0d3a57ecb3`；
- product tree：`ddac4703...`，fixture tree：`e2c092a4...`；两者只作 provenance；
- 当前代码加载后仍必须用 mount inventory、loaded-feature manifest 和 paused MCP
  snapshot 验证当前 runtime，不能用 OCR 猜测。

## 最小 MCP-first bootstrap

专用外部 fixture 位于
`tools/fixtures/zg361_phase2_seed_bootstrap/`。它与普通
`tools/fixtures/zg361_acceptance/` 分离，只有 seed-generation acceptance 可以挂载，
发布构建和宣传运行时永远不能加载。它没有 decision、GUI、角色/头衔/关系创建命令，
也不直接写任何 `zg361_*` 产品变量、receipt 或 Workforce history。
seed-generation profile 应把此树单独复制到既有外层 mod ID
`zga_acceptance_fixture.mod` 的目标目录；不得与普通 acceptance fixture 同时合并，且
candidate runtime 中记录的是本专用树的实际 SHA-256。

流程如下：

1. 从旧存档继续，fixture 只接受真实历史玩家 `han_6875` 与其现存直属 AI 天朝上司。
2. 在 manager-root 隐藏事件中调用 shipped B1、Incident X、Workforce public entry；
   若旧存档确有真实已交付 3.25 result，则在 player-root 隐藏事件中调用 shipped B2
   adapters。缺少前置事实时 shipped effect 自行 no-op，fixture 不补造输出。
3. 打开唯一可见事件 `zga_phase2_seed.1`。该事件保存：
   `zga_phase2_b2_owner`、`zga_phase2_incident_owner`、
   `zga_phase2_workforce_owner`、`zga_phase2_ai_owned_owner`、
   `zga_phase2_ai_owned_subject`。
4. MCP 调 `query-current-event-window-context-v1`，严格读取 root 与五个 typed character
   scopes，并保存同帧 paused/map-ready 玩家 snapshot；不使用 OCR。
5. MCP 选择唯一的 `select-event-option-1`，要求 postcondition ACK，然后调
   `save-checkpoint`。
6. `tools/zg361_phase2_seed_bootstrap.py` 验证事件定义、scope 唯一性、真实正整数 ID、
   paused snapshot、close ACK、checkpoint path/size/SHA/date/player，并保留原始四份
   JSON、report、index
   与 candidate contract。helper 永远先输出 blocked candidate；selector 捕获不能替代
   四个产品 provider 的状态证明。

已有 native session runner 可直接调用 helper 的 `capture_mcp_evidence(service,
artifacts)`：它只使用现有 `snapshot`、`query_current_event_window_context_v1`、
`select_event_option`、`save_checkpoint` 四个 MCP 方法，严格保持“同帧查询 → 唯一选项
关闭 ACK → paused checkpoint”的顺序；它不负责启动 CK3、lobby 或视觉导航。

完成一次 MCP 捕获后的物化命令为：

```powershell
& "tools\.venv\Scripts\python.exe" "tools\zg361_phase2_seed_bootstrap.py" `
  --event-context "<run>\event-context.json" `
  --paused-snapshot "<run>\paused-snapshot.json" `
  --event-close "<run>\event-close.json" `
  --checkpoint-response "<run>\save-checkpoint.json" `
  --profile "<isolated-profile>" `
  --output-dir "<new-empty-run-dir>" `
  --source-git-commit "<40-hex-commit>" `
  --product-tree-sha256 "<64-hex-product-tree>" `
  --fixture-tree-sha256 "<64-hex-seed-fixture-tree>"
```

fixture/loader/helper 的静态验收：

```powershell
py tools/test_zg361_phase2_seed_fixture.py
py tools/test_zg361_phase2_seed_bootstrap.py
py tools/test_run_zhongguo_promo_capture.py
```

## 仍不能由 seed fixture 消除的两项产品阻塞

### Incident mixed matrix

当前 X/Y/Z 都写同一 subject 的 `zg361_ip_probe_*`。native provider 的 N/A validator
要求共享 probe result/source/consequence 全为 0；positive validator 要求同一 tuple 为
positive。每次 public open 又会覆盖共享 probe。runner 在同一 paused snapshot、同一
玩家上要求 terminal kind 集合精确为 `{na, incident}`，因此现合同不可达；直接写变量
也无法让一组 tuple 同时为 0 和 1。应在产品/provider 冻结 profile-specific terminal
probe，或把 acceptance 改为聚合两个 checkpoint/snapshot。fixture 不得伪造。

### Workforce 三周期 charter

Workforce ready 必须完整跑三个严格递增真实 review cycle；每周期消费 shipped B1/B2
生成的 #357/#358/#359 receipt，通过 #360 history gate，第三周期才由产品生成 #361
charter。不存在诚实的一键 effect。fixture 只能调用 public entry；直接写 receipt ID、
rolling history 或 charter 输出都属于制造产品证据，禁止。

只有 Incident 合同变为可达、Workforce 三周期真实跑完，且 B1/B2/Incident/Workforce
四个 provider 在新 checkpoint 上独立 GREEN 后，才可把 candidate 改为 `ready` 并进入
一次二期批量实机。宣传视频仍只加载真实产品 runtime，不得出现或挂载这个 fixture。
