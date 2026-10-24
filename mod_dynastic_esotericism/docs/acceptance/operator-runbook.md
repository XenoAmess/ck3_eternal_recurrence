# 公共入口与现场操作卡

适用机器：`desktop-3fevhd2-1c74096080`。记录日期：2026-10-24。以下是尚待实际执行的操作合同，命令示例不构成启动、业务或发布通过记录。执行者须保留每一外层命令真实退出码。

R0004 已实际消费下文 a06 runtime、a19 keeper、`prepared-core-a07` 与 `attempt-a07/state`，并再次暴露整句日志参数展开失败；这些路径和分配例现为该失败场次的历史输入，不能复制重放。R0004 完整资源闭场与创建资格调查完成前，不填下一场前序或新 run ID。下一场须使用重新构建的静态日志候选及新的 runtime／prepared／state 父目录，经当时容量准入与 canonical allocator 重新分配；C 上 R0004 冻结源码保持原样。

本次使用已有公共验收入口、c09 宿主和公共原生 provider 的有限后继。Java 工具只生成外置 fixture 与精确来源绑定的共享 runtime；它不启动 CK3，也不授予 live qualification。最终 native index、SDK 提交验证入口和扩展 fixture 全部冻结后，才生成正式 prepared case。

## 冻结与准备

默认 `mvn` 曾由本机工具链回执核验为 3.10.0；恢复时重新读回默认 `mvn -version` 与 Maven home。Maven 构建由唯一构建线程执行，输出在本次获准外置根。R0003 后的四份 fixture 资源已有修正，旧 JAR 不能继续生成下一场 fixture；新干净 checkout 须重新执行默认 Maven `clean verify`，再由新 runner 生成并核对实际源、打包资源及 fixture 字节。

下列 `fixture-core-a02`、`host-successor-a06`、`common-runtime-a06`、`prepared-core-a07`、`attempt-a07` 与 `a19` 均是后继候选名，尚不证明目录不存在或参数未消费；Root 在实际写入／分配前核对并固定最终名字。`<new-runner>` 指本次新 Maven 构建的 `quarkus-app/quarkus-run.jar`，不能指向交接中的旧 JAR。

```bat
java -jar <new-runner> fixture --repo-root <C-clean-checkout> --output C:/ck3-dynastic-esotericism-20261024/fixture-core-a02 --machine-id desktop-3fevhd2-1c74096080
<python> <C-clean-checkout>/tools/ck3_mod_acceptance_build_runtime.py host-canonical-successor --base-runtime C:/ck3-common-runtime-20261024/runtime.selected-common-c09.json --source-root <C-clean-checkout> --runtime-binding C:/ck3-dynastic-esotericism-20261024/common-runtime-a06/runtime.json --output C:/ck3-dynastic-esotericism-20261024/host-successor-a06 --machine-id desktop-3fevhd2-1c74096080
java -jar <new-runner> runtime --repo-root <C-clean-checkout> --base-runtime C:/ck3-common-runtime-20261024/runtime.selected-common-c09.json --native-index <final-native-source-index> --host-projection C:/ck3-dynastic-esotericism-20261024/host-successor-a06/canonical-host-projection.json --output C:/ck3-dynastic-esotericism-20261024/common-runtime-a06 --machine-id desktop-3fevhd2-1c74096080
```

`<C-clean-checkout>` 必须包含该提交的产品 17 个正式运行文件、Java 源码与资源、需求/测试文档、公共入口和产品 case 合同；fixture 的 producer pins 全部须处于此根目录中。Composer 会另冻结实际 SDK 与公共 helper。父 index 的旧绝对路径按明确的父 source root 转为相对路径，再与新 checkout 的同路径比较，不能因 C/D 根目录变化漏记差异。

宿主投影保留父 R05 的六个控制工具，并将其原有同一 Service 的构造边界绑定到当前共享 SDK factory；外置 `registration_mcp.py` 的父文件、当前 factory 和新文件均由投影回执固定。不能热改旧 wrapper。`lease_repo` 指向实际干净 checkout；现有 `screen_bus_lease.py` 与该 checkout 的 task bus 也进入 source index 和 allocator overlay。keeper 的旧默认 SHA 不作为本次输入，公共 allocator 会显式传入 runtime 中实际 installed task bus 的 SHA。

后续 `<entry>` 指新 `common-runtime-a06/source/tools/ck3_mod_acceptance.py`，`<products>` 指相邻 `ck3_mod_acceptance_products.json`，`<runtime>` 指新 `common-runtime-a06/runtime.json`；若候选名调整，全部输入同步使用最终冻结路径。`<python>` 使用 runtime 声明的解释器，本机父 runtime 当前为 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`。这不允许回退到旧 D 盘 helper 或 SDK，也不能热改 a05 的冻结图。

输入文件是一个 JSON 对象：

```json
{
  "state_dir": "C:/ck3-dynastic-esotericism-20261024/attempt-a07/state",
  "case_inputs": {
    "product_dir": "<exact-formal-staging>",
    "prebuilt_fixture_manifest": {"path": "C:/ck3-dynastic-esotericism-20261024/fixture-core-a02.fixture.json", "bytes": 123, "sha256": "<actual-SHA256>"},
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
<python> <entry> prepare --runtime <runtime> --products <products> --product dynastic-esotericism --case core --case-inputs <inputs.json> --prepare-output C:/ck3-dynastic-esotericism-20261024/prepared-core-a07
```

## 分配、预检和运行

本机已有公共 admission，不能使用 first-machine-bootstrap。2026-10-24 的 R0001、R0002 均保留 RED，SCREEN 实际释放分别为 8596、8607。最新真实前序为 R0003：原生 observer 读到 CK3 原进程退出 0，宿主原 Popen 退出 1、公共 run 退出 2、keeper 原 Popen 退出 0，SCREEN 实际释放 **8619**。R0003 的业务和完整 normal-close 仍为 false，原 `autosave_verified=false` 必须保留。恢复先完成公共 verify 和 typed observer 的资源 closure producer／consumer 校验，不能拿旧 R0002 或伪造 GUI 退出回执接续。下例 `<R0003-verified-resource-closure>` 必须替换为实际生成并验证的原件；未完成前不得 allocate。以下路径属于 `machine_id: desktop-3fevhd2-1c74096080`；分配前仍由 Root 重读当前 canonical admission。

```bat
<python> <entry> allocate --runtime <runtime> --products <products> --product dynastic-esotericism --case core --prepared-case <new-prepared-case> --attempt a19 --keeper-output C:/ck3-dynastic-esotericism-20261024/keeper-core-a19 --previous-live C:/ck3-dynastic-esotericism-20261024/common-runtime-a05/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0003 --previous-keeper C:/ck3-dynastic-esotericism-20261024/keeper-core-a18 --previous-release C:/ck3-dynastic-esotericism-20261024/R0003-screen-release.actual.json --previous-failure-close <R0003-verified-resource-closure>
<python> <entry> preflight --runtime <runtime> --products <products> --product dynastic-esotericism --case core --prepared-case C:/ck3-dynastic-esotericism-20261024/prepared-core-a07/prepared-case.json --run-context <reviewed-context-1>
<python> <entry> run --runtime <runtime> --products <products> --product dynastic-esotericism --case core --prepared-case C:/ck3-dynastic-esotericism-20261024/prepared-core-a07/prepared-case.json --run-context <reviewed-context-2>
```

Root 在真实分配前完成存储原子准入、干净 checkout 和屏幕 owner 前置。受管启动前用公共后台 Steam probe 取得新鲜 `offline=true` 回执。未知状态不能启动。R0001–R0003 的固定 hold 3600 秒、整个命令 5400 秒及原失败记录保留。R0004 分配前改为固定 hold 9000 秒、整个命令 10800 秒，readiness 1800 秒、正常退出保留 180 秒、400 自然日上限保持。依据是 R0003 实际单日动作 8.566 秒，加后续队列／snapshot 约 3.749 秒；仅 400 日的规划估计已约 82 分钟，另需原生 GUI 和退出时间。该估计不代表业务通过，也不延长任何已冻结场次的 deadline。

上例 a19 是候选参数，分配时须重验未消费；预计下一 run 为 R0004，以 canonical allocator 实际分配为准。新 state 使用新的父目录，例如 `C:/ck3-dynastic-esotericism-20261024/attempt-a07/state`；R0003 已消费的 `attempt-a06/state`、single-use-ledger 和目的文件均保留，不能只在同一父目录换 state 名。绑定旧 runtime 的 prepared 不改写复用，须对新 runtime 重新 prepare。前序释放后没有插入其他 SCREEN 任务时，省略可选的 `--latest-screen-release`。只有出现更晚的 SCREEN 释放时才传它的实际原件，且其序号必须严格大于 `--previous-release`；不能把同一释放传两次。2026-10-24 a17 首次分配已实际在 ID 前拒绝同序号参数，任务、keeper 与新 run 均未产生；后续按真实未消费状态以新日志重试。

分配后由 Root 以新文件提交 reviewed context，字段是 `reviewer: "/root"`，并补 `steam_offline_receipt` 的新鲜后台回执路径；实际 `run` 消费此新 context。四个产品合同显式声明 `execution_purpose=product_acceptance`。公共入口在启动前生成一次目的文件，宿主核 Root context、prepared/contract、冻结 argv、当前 run/state/pipe 后，按真实首帧身份与原自然日上限推进。R05 的独立 scope、30 日与 once 守卫保留；本产品场次不申请 R05 scope。

当前冻结后台 gate 的新鲜窗口为 **30 秒**。完整顺序是 probe1 → 新 Root context1 → public preflight → 全新 probe2 → 全新 Root context2 → 立即 public run；第二 probe 至 run 必须在同一执行脚本内连续完成，中间不得等待模型回合。run 自身仍执行预检和 launcher 守卫。先前 60 秒的描述已更正，不修改历史失败回执，也不放宽 gate 或目的文件一次守卫。进入稳定地图及首个自然日后，业务操作前先通过同一 queue/driver 只读查询 `ck3_query_normal_exit_context_v1`，确认本次 normal-exit profile/source inventory 确实被消费；不提交退出请求，实际闭场时再按新 revision 查询。

## 六个 GUI phase 的操作与签认

控制器会打印 `CK3_ROOT_CHECKPOINT <run>/case-output/<phase>-awaiting.json`。Root 先读取该文件的实际 snapshot、要求、原始 hold deadline，再提交原生操作。控制器此时保持同一会话；每个公开队列计划必须用新的文件名与 step ID。

R0004 起，首个 phase 等待实际 `DESAF: TEST PASS fixture_ready`，不按“已到第 1 日”推算延迟事件已执行。准备 fixture 不改角色 Faith；保留开局 Catholic／Roman Rite，实际知识、无先知、资源和原生 `Can` 均须重新读回，不能把儒家身份当作前提。

R0004 的日志故障候选修复只改日志位置：`.3/.4` 外层完整 observer／outsider 守卫保持，四条 PASS 采用静态带引号 `debug_log`，移除重复的 positive／negative 日志 helper；不能再传整句 `$PASS$`／`$FAIL$`，也不另换 CASE 宏猜引擎行为。旧 R0004 原输入及两份坏资源在 Java 回归中保留，实际旧输入须被非字面量日志检查拒绝。新 JAR／fixture 和后继实机尚未因此通过；完整证据与边界见[测试方案](../test-plan.md)。五项名称、教义与资源齐备仍不能代替实际原生 `Can`，R0004 观察到的创建资格缺口须独立闭合。

后继 fixture 的原版关系输入已明确公开：优先当前真实宫廷司祭，缺失时只运行一次原版 landed realm priest 筛选；其后仅为合格司祭与空槽建立原版神学傀儡关系，不清除冲突、不选择六项互动支持、不声称互动已经提交、接受或支付。setup 的 `fixture_ready` 需要真实关系和已知脚本资格读回通过。开窗前调用独立 `[测试] 观察原版神学傀儡前置输入` 决议，检查 cp／puppet／反向 puppeteer／puppet_action_valid 的静态日志，并从新 epoch 另读 council full ID。该决议只读原版关系，只更新 fixture 观察旗标；它不重新任命或创建傀儡。草案五名称、教义和资源齐备后仍须原生完整 Can；关系前置日志不能替代该结果，原版确认仍只能执行一次。

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
6. 仅对 `confirm_once` 的 pending 结果调用 `ck3_collect_player_rite_creation_action_result_v1(action_request_id)` 收集原最终确认。非 confirm 操作没有此 final-confirm claim；开窗 pending 时保留原 receipt，不重放，用原 action context 的 `observation=draft/current_rite` 独立观察，再按真实草案查询 groups。UNKNOWN 不重放。
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
<python> <entry> verify --runtime <runtime> --products <products> --product dynastic-esotericism --case core --prepared-case C:/ck3-dynastic-esotericism-20261024/prepared-core-a07/prepared-case.json --run-context <reviewed-context-2>
```

同会话通过仍不能追认为冷重载、真实旧档 bootstrap 或多人通过。后续三个公开 case 均沿用同一共同 runtime；每次都消费当时最新真实前序关闭来源，不能重复使用 core 之前的历史前序。

1. `cold_reload`：从 core 的实际冷载锚点保存取精确 `.ck3`、player ID 和 date_raw；Java `fixture` 命令追加 `--case cold_reload`，生成不带启动 registrar 的 12 文件被动 fixture。公共 prepare 的输入顶层另加 `saved_campaign`，恰为 `{save,bytes,sha256,player_id,date_raw}`；其中保存原件必须处于新 profile 之外。case_inputs 仍填正式 staging、四份配置和该 fixture 的 FilePin。共享 prepare 生成正式产品/fixture 角色明确的 v2 inventory，再以新 PID 加载。Root 在零自然日 phase 先独立读取存档原图、再调用 `des_acceptance_cold_readback_decision`、实际 Save 并比较。不能先补初始化掩盖保存缺失。
2. `pre_product_seed`：Java 追加 `--case pre_product_seed`；case_inputs 的 `product_dir` 为 `null`。共享 prepare 只挂 2 文件日志 fixture，不挂正式产品，不执行产品初始化。Root 在零日 phase 正常 Save，独立核无产品状态并保全真实 profile/进程/保存身份。这是明确为兼容验收准备的真实前产品新局，不声称历史年份旧档。
3. `old_save_bootstrap`：Java 追加 `--case old_save_bootstrap`，同样生成无启动 registrar 的被动 fixture；加载上一步真正保存的无产品母档，这次挂正式 staging。新进程中依次操作 `des_acceptance_legacy_before_decision`、原版公开正式 `des_initialize_decision`、`des_acceptance_legacy_after_decision`，分别留存初始化前后真实状态及 Save。上限 2 自然日。绝不通过删除 `des_initialized` 造旧档。

这些 case 的 hold 预算在各自分配前固定：cold 与 seed 为 900 秒，旧档初始化为 1800 秒，均保留 180 秒正常退出；case 的整体 timeout 为 3600 秒。每次分配都使用当前最新真实机器 admission/释放回执并重新核存储与后台 Steam 离线。准备或回执形状通过不代表已经实际完成这些场次。发布前须按测试方案完成三条链；多人仍只如实记录实际测试边界。发布缓存阶段只核真实下载文件与正式 staging 一致以及 CK3 实际加载，遵守项目现行规则，不重跑业务。

### 原生正常退出路由（后继候选）

R0003证明同handle退出0，但原正常闭场因宿主错误及缺少路由证据仍为false。后继共享CaseClient增加独立typed路由；正常关闭组40项与原共享step全部91条命令已实际通过（分次修复后汇总，原RED保留），不追认R0003。`autosave_verified=false`按SDK表示没有保存完整性资格，即使关闭退出自动存档也保持false；真正Save与独立保存读回另验。

业务场景完成后，等本次CaseClient写出`normal-quit-awaiting.json`，在其原deadline内走同一queue：新query→prepare_confirmation一次；pending后仅query，确认stage0已消费、stage1可用才continue_preparation一次；新query见真实确认框后disable_exit_autosave一次（should_save已false时保留原生已关闭观察）；再新query取新context signature→confirm_desktop一次；pending后仅observe_normal_exit_v1收集同原handle到实际exit0。未知或已消费stage不重放。不先退出游戏再调用normal_close。新的路由保留GUI review=null，并独立消费原fact/close/claim/profile/source inventory；原finish_hold仅一次，最后仍要求原handleOS0、无host error、完整native清理。
