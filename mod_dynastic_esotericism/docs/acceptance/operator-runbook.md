# 公共入口与现场操作卡

适用机器：`desktop-3fevhd2-1c74096080`。记录日期：2026-10-24。以下是尚待实际执行的操作合同，命令示例不构成启动、业务或发布通过记录。执行者须保留每一外层命令真实退出码。

本次使用已有公共验收入口、c09 宿主和公共原生 provider 的有限后继。Java 工具只生成外置 fixture 与精确来源绑定的共享 runtime；它不启动 CK3，也不授予 live qualification。最终 native index、SDK 提交验证入口和扩展 fixture 全部冻结后，才生成正式 prepared case。

## 冻结与准备

默认 `mvn` 已由本机工具链回执核验为 3.10.0；下列路径是本次产物事实，不能写成其他机器的安装约定。Maven 构建由唯一构建线程执行，输出在本次 C 盘准入根。

```bat
java -jar C:/ck3-dynastic-esotericism-20261024/java-build/dynastic-esotericism-tools/quarkus-app/quarkus-run.jar fixture --repo-root <C-clean-checkout> --output C:/ck3-dynastic-esotericism-20261024/fixture-core-a01 --machine-id desktop-3fevhd2-1c74096080
<python> <C-clean-checkout>/tools/ck3_mod_acceptance_build_runtime.py host-canonical-successor --base-runtime C:/ck3-common-runtime-20261024/runtime.selected-common-c09.json --source-root <C-clean-checkout> --runtime-binding C:/ck3-dynastic-esotericism-20261024/common-runtime-a01/runtime.json --output C:/ck3-dynastic-esotericism-20261024/host-successor-a01 --machine-id desktop-3fevhd2-1c74096080
java -jar C:/ck3-dynastic-esotericism-20261024/java-build/dynastic-esotericism-tools/quarkus-app/quarkus-run.jar runtime --repo-root <C-clean-checkout> --base-runtime C:/ck3-common-runtime-20261024/runtime.selected-common-c09.json --native-index <final-native-source-index> --host-projection C:/ck3-dynastic-esotericism-20261024/host-successor-a01/canonical-host-projection.json --output C:/ck3-dynastic-esotericism-20261024/common-runtime-a01 --machine-id desktop-3fevhd2-1c74096080
```

`<C-clean-checkout>` 必须包含该提交的产品 17 个正式运行文件、Java 源码与资源、需求/测试文档、公共入口和产品 case 合同；fixture 的 producer pins 全部须处于此根目录中。Composer 会另冻结实际 SDK 与公共 helper。父 index 的旧绝对路径按明确的父 source root 转为相对路径，再与新 checkout 的同路径比较，不能因 C/D 根目录变化漏记差异。

宿主投影保留父 R05 的六个控制工具，并将其原有同一 Service 的构造边界绑定到当前共享 SDK factory；外置 `registration_mcp.py` 的父文件、当前 factory 和新文件均由投影回执固定。不能热改旧 wrapper。`lease_repo` 指向实际干净 checkout；现有 `screen_bus_lease.py` 与该 checkout 的 task bus 也进入 source index 和 allocator overlay。keeper 的旧默认 SHA 不作为本次输入，公共 allocator 会显式传入 runtime 中实际 installed task bus 的 SHA。

后续 `<entry>` 指 `common-runtime-a01/source/tools/ck3_mod_acceptance.py`，`<products>` 指相邻 `ck3_mod_acceptance_products.json`，`<runtime>` 指 `common-runtime-a01/runtime.json`。`<python>` 使用 runtime 声明的解释器，本机父 runtime 当前为 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`。这不允许回退到旧 D 盘 helper 或 SDK。

输入文件是一个 JSON 对象：

```json
{
  "state_dir": "C:/ck3-dynastic-esotericism-20261024/state-core-a01",
  "case_inputs": {
    "product_dir": "<exact-formal-staging>",
    "prebuilt_fixture_manifest": {"path": "C:/ck3-dynastic-esotericism-20261024/fixture-core-a01.fixture.json", "bytes": 123, "sha256": "<actual-SHA256>"},
    "plain_configuration": {
      "pdx_settings.txt": {"path": "<actual-file>", "bytes": 0, "sha256": "<actual-SHA256>"},
      "tutorial.txt": {"path": "<actual-file>", "bytes": 0, "sha256": "<actual-SHA256>"},
      "presets.txt": {"path": "<actual-file>", "bytes": 0, "sha256": "<actual-SHA256>"},
      "player/game_rules/presets.txt": {"path": "<actual-file>", "bytes": 0, "sha256": "<actual-SHA256>"}
    }
  }
}
```

这里的 0 和尖括号仅为字段说明；执行前必须填真实路径、字节数与 SHA。公共 prepare 会再次读取并校验原件。正式 staging 不能混入验收 fixture。

```bat
<python> <entry> plan --runtime <runtime> --products <products> --product dynastic-esotericism --case core
<python> <entry> prepare --runtime <runtime> --products <products> --product dynastic-esotericism --case core --case-inputs <inputs.json> --prepare-output C:/ck3-dynastic-esotericism-20261024/prepared-core-a01
```

## 分配、预检和运行

本机已有公共 admission，不能使用 first-machine-bootstrap。2026-10-24 的 R0001 已保留为 RED 并正常关闭：原宿主退出 1、公共 run 退出 2、CK3 原进程退出 0、keeper 退出 0，SCREEN 释放序号 8596。后继使用该真实 R0001；其有限 failure-close 只准入已结束资源，保留业务与正常关闭资格为 false。以下路径属于 `machine_id: desktop-3fevhd2-1c74096080`；分配前仍由 Root 重读当前 canonical admission。

```bat
<python> <entry> allocate --runtime <new-runtime> --products <new-products> --product dynastic-esotericism --case core --prepared-case <new-prepared-case> --attempt a17 --keeper-output C:/ck3-dynastic-esotericism-20261024/keeper-core-a17 --previous-live C:/ck3-dynastic-esotericism-20261024/common-runtime-a03/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0001 --previous-keeper C:/ck3-dynastic-esotericism-20261024/keeper-core-a16 --previous-release C:/ck3-dynastic-esotericism-20261024/R0001-screen-release.actual.json --previous-failure-close C:/ck3-dynastic-esotericism-20261024/R0001-preserved-failure-close/failure-close.json --latest-screen-release C:/ck3-dynastic-esotericism-20261024/R0001-screen-release.actual.json
<python> <entry> preflight --runtime <runtime> --products <products> --product dynastic-esotericism --case core --prepared-case C:/ck3-dynastic-esotericism-20261024/prepared-core-a01/prepared-case.json --run-context <allocated-context>
<python> <entry> run --runtime <runtime> --products <products> --product dynastic-esotericism --case core --prepared-case C:/ck3-dynastic-esotericism-20261024/prepared-core-a01/prepared-case.json --run-context <allocated-context>
```

Root 在真实分配前完成存储原子准入、干净 checkout 和屏幕 owner 前置。受管启动前用公共后台 Steam probe 取得新鲜 `offline=true` 回执。未知状态不能启动。本次开局前声明固定 hold 3600 秒、整个命令 5400 秒、readiness 1800 秒、正常退出保留 180 秒；400 自然日上限覆盖真实 280 日妊娠、出生翌日和 31 日维护观察。运行中不延长冻结 deadline。

上例 a17 只是在此次读回时尚未注册的参数，分配时须重验未消费。新 state 使用新的父目录，例如 `C:/ck3-dynastic-esotericism-20261024/attempt-a04/state`；先前 `state-core-a03` 的父目录已有实际消费过的 single-use-ledger，不能只在同一父目录换 state 名。若期间发生新的 SCREEN 任务，`--latest-screen-release` 必须换成它的实际释放原件。

分配后由 Root 以新文件提交 reviewed context，字段是 `reviewer: "/root"`，并补 `steam_offline_receipt` 的新鲜后台回执路径；实际 `run` 消费此新 context。四个产品合同显式声明 `execution_purpose=product_acceptance`。公共入口在启动前生成一次目的文件，宿主核 Root context、prepared/contract、冻结 argv、当前 run/state/pipe 后，按真实首帧身份与原自然日上限推进。R05 的独立 scope、30 日与 once 守卫保留；本产品场次不申请 R05 scope。

## 六个 GUI phase 的操作与签认

控制器会打印 `CK3_ROOT_CHECKPOINT <run>/case-output/<phase>-awaiting.json`。Root 先读取该文件的实际 snapshot、要求、原始 hold deadline，再提交原生操作。控制器此时保持同一会话；每个公开队列计划必须用新的文件名与 step ID。

```bat
<python> <frozen-source>/tools/ck3_mod_acceptance_queue_control.py --live <run> --plan <new-plan.json> --name root-rite-001.json
```

普通查询计划例：

```json
{"steps":[{"id":"root-religion-context-001","tool":"ck3_query_player_religion_context_v1","args":{},"fresh_revision":true}]}
```

队列 step 使用 `args`，不能写 `arguments`。`fresh_revision` 让共享宿主在提交前绑定当前 revision；角色/Rite ID 等业务身份仍必须来自当前真实查询。读取 `<run>/native-report.json` 中该 step 的 `finished_at/ok/error/result/after_snapshot`，不能把 queue ACK 当成功。

礼仪操作全部复用 `ck3_execute_player_rite_creation_action_v1`，每步传当前 `expected_source_rite_id` 并绑定当前 revision：

1. 从真实 religion context 取当前完整 `faith_id`，先调用 `ck3_open_faith_window_v1(faith_id,expected_revision)`，再用 `ck3_query_ingame_ui_window_v1(window_kind="faith",expected_revision)` 独立核原版窗口与所选身份；实际信仰窗口可见后才提交 `open_create_draft` 或 `open_edit_current_rite_draft`。
2. 查询当前 draft groups、doctrine choices、resource costs 和 action context，保留两个教义实际 `shown/can/selected` 与默认“无”。知识查询未接入本宿主；其范围由真实 UI 可选状态与可玩角色的真实 `knows_doctrine` trigger 共同验收。原版不允许向不可玩角色写教义知识；不可玩成员与新生儿的 Rite、Dynasty、House 断言仍全部保留。
3. `select_doctrine` 使用 `group_key=des_dynastic_membership`、`doctrine_key=des_doctrine_dynastic` 或 `des_doctrine_none`。创建需要的原版名称字段用 `set_name_field`；保持其他教义不变以得到同 Faith 的新 Rite。
4. 保存实际完整 `Can`、价格和 draft identity；`prepare_confirmation` 打开原版确认界面。
5. 仅在原始结果已知时 `confirm_once` 一次，传真实 `expected_preview_identity` 和预期 `create_rite/edit_rite`。
6. 返回 pending 时仅用 `ck3_collect_player_rite_creation_action_result_v1(action_request_id)` 收集原请求；UNKNOWN 不重放。
7. 新的 `ck3_verify_player_rite_creation_action_completed_v1(action_request_id,expected_revision)` 独立核对真实当前 Rite、名称、core、doctrines 和窗口/确认框关闭后态。该最终 SDK 工具实际冻结并进入 required tools 后才可执行；旧 collect/ACK 不代替本步。

原版取消草案也必须保留真实取消前后 Rite/Dynasty/House/资源和窗口证据。新版同一 execute 工具提供 `cancel_draft`；取消后用原 query 的 `observation=current_rite` 独立观察持久图与窗口关闭。未知 claim 禁止发送取消，不能用 fixture 改状态模拟取消。

fixture 决议也通过公共原生决议工具依次打开、query、select、confirm：`ck3_open_ingame_decisions_v1` → `ck3_query_ingame_decision_item_v1(decision_key)` → `ck3_select_ingame_decision_item_v1(decision_key)` → `ck3_confirm_ingame_decision_outcome_v1(decision_key,expected_outcome="decision_closed")`。每次都重新绑定 revision。决议只是公开的测试输入，真实产品后态仍由日志 trigger、独立存档和 GUI 验证。

处罚预览用 `ck3_query_character_interaction_ordinary_v1(interaction_key,recipient_id,expected_revision)`；`pardon_interaction` 在实际同 realm/liege 条件合法时仅提交一次 `ck3_initiate_character_interaction_ordinary_v1`，随后独立检查罪行被消费且 31 日后不刷新。不能把交互 ACK 当作赦免结果，不能为预览自动监禁或处决。

在 phase 等待期间推进自然日仍走同一公共原生通道：每次队列 `{"id":"unique-day-id","kind":"advance_day","days":1,"timeout":300}`；遇实际事件/通知先保存当前实例和实际选项，按项目规则处理再继续。不要盲目批量跨越出生当天，出生翌日必须由真实日期和子 observer 身份精确定位。出生准备、旁支、外改 House 等只改原版测试输入，不调用产品同步效果、不直接写产品 trait/绑定变量。

完成要求后，Root 以新文件一次写入 `<run>/case-output/<phase>-root-result.json`：

```json
{
  "run_id": "<actual-run-id>",
  "reviewer": "/root",
  "assertions": {"<each-exact-required-assertion>": true},
  "evidence": [{"path": "<actual-evidence>", "bytes": 123, "sha256": "<actual-SHA256>"}]
}
```

每个 assertion 只在其实际证据完整时为 true。`<phase>` 与要求均读取 awaiting 原件，不自行补签尚未测到的路径。控制器重新校验 evidence 的实际字节和 SHA。UI mailbox 用于该控制器明确生成的实际 UI await；不能用它替代这里的 native queue 或 Root phase 签认。

## 收尾与剩余验收

保存用 `ck3_save_checkpoint`，保留实际 materialized save 和独立解码的 Rite/Dynasty/House/知识/意见来源/索引。公共 CaseClient 执行正常退出；不得强杀代替原进程退出后态。

```bat
<python> <entry> verify --runtime <runtime> --products <products> --product dynastic-esotericism --case core --prepared-case C:/ck3-dynastic-esotericism-20261024/prepared-core-a01/prepared-case.json --run-context <allocated-context>
```

同会话通过仍不能追认为冷重载、真实旧档 bootstrap 或多人通过。后续三个公开 case 均沿用同一共同 runtime 和真实前序关闭来源，不能继续使用上面的历史 R0037 作为每次前序。

1. `cold_reload`：从 core 的实际冷载锚点保存取精确 `.ck3`、player ID 和 date_raw；Java `fixture` 命令追加 `--case cold_reload`，生成不带启动 registrar 的 12 文件被动 fixture。公共 prepare 的输入顶层另加 `saved_campaign`，恰为 `{save,bytes,sha256,player_id,date_raw}`；其中保存原件必须处于新 profile 之外。case_inputs 仍填正式 staging、四份配置和该 fixture 的 FilePin。共享 prepare 生成正式产品/fixture 角色明确的 v2 inventory，再以新 PID 加载。Root 在零自然日 phase 先独立读取存档原图、再调用 `des_acceptance_cold_readback_decision`、实际 Save 并比较。不能先补初始化掩盖保存缺失。
2. `pre_product_seed`：Java 追加 `--case pre_product_seed`；case_inputs 的 `product_dir` 为 `null`。共享 prepare 只挂 2 文件日志 fixture，不挂正式产品，不执行产品初始化。Root 在零日 phase 正常 Save，独立核无产品状态并保全真实 profile/进程/保存身份。这是明确为兼容验收准备的真实前产品新局，不声称历史年份旧档。
3. `old_save_bootstrap`：Java 追加 `--case old_save_bootstrap`，同样生成无启动 registrar 的被动 fixture；加载上一步真正保存的无产品母档，这次挂正式 staging。新进程中依次操作 `des_acceptance_legacy_before_decision`、原版公开正式 `des_initialize_decision`、`des_acceptance_legacy_after_decision`，分别留存初始化前后真实状态及 Save。上限 2 自然日。绝不通过删除 `des_initialized` 造旧档。

这些 case 的 hold 预算在各自分配前固定：cold 与 seed 为 900 秒，旧档初始化为 1800 秒，均保留 180 秒正常退出；case 的整体 timeout 为 3600 秒。每次分配都使用当前最新真实机器 admission/释放回执并重新核存储与后台 Steam 离线。准备或回执形状通过不代表已经实际完成这些场次。发布前须按测试方案完成三条链；多人仍只如实记录实际测试边界。发布缓存阶段只核真实下载文件与正式 staging 一致以及 CK3 实际加载，遵守项目现行规则，不重跑业务。
