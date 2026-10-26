# 公共入口与现场操作卡

适用机器：`desktop-3fevhd2-1c74096080`。记录日期：2026-10-24；继承候选更新于 2026-10-25。以下是尚待实际执行的操作合同，命令示例不构成启动、业务或发布通过记录。执行者须保留每一外层命令真实退出码。

2026-10-25T00:00Z当前接续边界：R0012在初始加载帧的玩家角色尚为null时被旧clock拒绝，未进入产品动作；当前主线已有该共享修复，必须生成全新runtime，不能重跑或热改a11。R0012实际typed退出Game0、host1、public2、keeper／allocator0、SCREEN8858；冻结消费者已实际接受资源闭场，业务及完整normal-close仍为false。原件摘要见[R0012](R0012-2026-10-25.json)。下一图新建a15工具、a16正式18文件包、a15 fixture13文件、runtimea12与prepared21，具体RunID仍由canonical分配；下文R0003／a06示例仅保历史。Root在新图中先验真实head交接／singleton NPC分支和家庭转换即时全员归族，不能拿旧a14产物或原phase1局部通过抵扣。

R0004 已实际消费下文 a06 runtime、a19 keeper、`prepared-core-a07` 与 `attempt-a07/state`，并再次暴露整句日志参数展开失败；这些路径和分配例现为该失败场次的历史输入，不能复制重放。R0007 后继实机已独立确认创建 Rite 150／Faith 13／actor 31254，但后续 capture 因产品 House→Dynasty 链错误被原生提交前拒绝，整体仍为 **0/6、业务 RED**；原件是 `C:/ck3-dynastic-esotericism-20261024/common-runtime-a07/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0007`。新 House 修复、下文真实继承顺序及共享 clock／fixture 均须在新构建图验证，不能热改或追认该原场。Root 在真实分配前消费当时最新 canonical closure／release 原件与容量准入，重新固定全部 runtime／prepared／state／keeper 路径；下文历史命令中的旧前序与 a 编号不代表当前可执行值。

本次使用已有公共验收入口、c09 宿主和公共原生 provider 的有限后继。Java 工具只生成外置 fixture 与精确来源绑定的共享 runtime；它不启动 CK3，也不授予 live qualification。最终 native index、SDK 提交验证入口和扩展 fixture 全部冻结后，才生成正式 prepared case。

## 冻结与准备

默认 `mvn` 曾由本机工具链回执核验为 3.10.0；恢复时重新读回默认 `mvn -version` 与 Maven home。Maven 构建由唯一构建线程执行，输出在本次获准外置根。R0003 后的四份 fixture 资源已有修正，旧 JAR 不能继续生成下一场 fixture；新干净 checkout 须重新执行默认 Maven `clean verify`，再由新 runner 生成并核对实际源、打包资源及 fixture 字节。

下列 `fixture-core-a02`、`host-successor-a06`、`common-runtime-a06`、`prepared-core-a07`、`attempt-a07` 与 `a19` 均是后继候选名，尚不证明目录不存在或参数未消费；Root 在实际写入／分配前核对并固定最终名字。`<new-runner>` 指本次新 Maven 构建的 `quarkus-app/quarkus-run.jar`，不能指向交接中的旧 JAR。

```bat
java -jar <new-runner> fixture --repo-root <C-clean-checkout> --output C:/ck3-dynastic-esotericism-20261024/fixture-core-a02 --machine-id desktop-3fevhd2-1c74096080
<python> <C-clean-checkout>/tools/ck3_mod_acceptance_build_runtime.py host-canonical-successor --base-runtime C:/ck3-common-runtime-20261024/runtime.selected-common-c09.json --source-root <C-clean-checkout> --runtime-binding C:/ck3-dynastic-esotericism-20261024/common-runtime-a06/runtime.json --output C:/ck3-dynastic-esotericism-20261024/host-successor-a06 --machine-id desktop-3fevhd2-1c74096080
java -jar <new-runner> runtime --repo-root <C-clean-checkout> --base-runtime C:/ck3-common-runtime-20261024/runtime.selected-common-c09.json --native-index <final-native-source-index> --host-projection C:/ck3-dynastic-esotericism-20261024/host-successor-a06/canonical-host-projection.json --output C:/ck3-dynastic-esotericism-20261024/common-runtime-a06 --machine-id desktop-3fevhd2-1c74096080
```

`<C-clean-checkout>` 必须包含该提交的产品18个正式运行文件、Java源码与资源、需求／测试文档、公共入口和产品case合同；fixture的producer pins全部须处于此根目录中。Composer另冻结实际SDK与公共helper，新source index仅输出 `ck3-common-source-index-v1` 的相对路径→`{bytes,sha256}`；外部registration／lease仍由overlay／projection精确绑定。历史parent及已闭场predecessor按显式旧schema只读导入，不能将旧列表当新输出或绕过原身份／来源守卫。所有外层manifest／evidence／runtime按真实新index SHA重封；C/D根变化不能漏记来源差异。

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

创建后的 capture 决议仅提交一次，保留独立后态。新 fixture 的实验等待为 +2 日：Root 必须在签认 phase 1 前，先于 capture 后真实 +1、+2 自然日分别固定完整原生成员名单、同帧 Save／原 SDK pin／保全副本，并完成独立解码核图；签认后先消费控制器自动推进、重新读取实际日期，再决定是否推进下一日。按本场实际 ID 对照 House→Dynasty 和 stock 回调标记；不复用 R0009 的成员 ID，不以单一 flag 授资格。只消费原 `binding_and_members` 全量守卫；+2 未同步或其他原守卫失败仍为 FAIL，不延后等待周期修复、不补写产品状态、不重放 capture。两次读回计入原 deadline／400 日预算。R0009 不追认，REQ-05 普通转换同次同步另按原要求验收。

R0015（`machine_id: desktop-3fevhd2-1c74096080`）只固定了 +1（1066.9.17）和 +3（1066.9.19）的成员 Save；+2 时点未保存，原缺口与签认保留，不能把 +3 充当 +2 证据。

R0013已实际通过前两阶段、两日全部61名成员归族及两种head建族分支，但第三阶段的合法囚犯预览未完成。Game／host实际0，public2、keeper／allocator0、SCREEN8892；normal-close=true仅生命周期。后继不修改其冻结图，不重复提交其动作，不把原监禁查询的`can_send=true`当作监禁已生效。原件见[R0013](R0013-2026-10-25.json)。

后继phase 3仍由原`same_faith_apostasy` marker进入Root等待；不要把尚待Root调用的囚犯准备marker加入该入口条件。先从本场baseline保存读取`des_test_ref_prison_control`的真实完整ID。该独立廷臣与主`des_test_target`分开，初始创建和后续普通改信均为公开fixture输入。只提交一次`des_acceptance_prisoner_control_decision`，经过真实一日，并处理实际事件边界。`.8`只有在原生引擎判定该control的实际背离、好感、penalty及全部三类理由成立后，才调用原版`imprison_character_effect`形成受限囚犯输入；原主目标、产品状态和计时器不写入。`DESAF: TEST PASS prisoner_control_ready`还要求control存活、确由当前Root监禁且驱逐／处决理由仍在。该日志证明fixture观察范围，不代表原监禁互动已发送或自动处罚功能。

保存并独立核对control身份与Root的实际监禁关系，再查询原`execute_prisoner_interaction`的完整当前预览。驱逐必须使用`release_from_prison_interaction`的`banish`选项；不存在独立的`banish_interaction`。新图仅在实际DLL的两项囚犯只读编译开关、来源／ABI及本core的宿主权限都资格化后，通过既有`ck3_query_player_prisoner_collection_private_v1`传`release_option_keys=["banish"]`（原合同mask=4）。读取实际control行、精确所选flag、原完整Can及成本／接受度和同一暂停帧；工具注册、编译或ACK不能代替这些读回。执行与驱逐均只预览，不发送；保留全部action开关关闭。接口不可用、仍非Root囚犯、选项映射不符或原Can拒绝时如实保留未验，不用默认释放预览抵扣。

普通囚犯交互菜单先查询本场实际 keyed scripted-widget tree 与可见状态；菜单已显示时直接选择当前实际 key，不在同 revision 再调用 opener。只有菜单尚未显示且原生通道可用时才提交一次打开请求，随后独立 query。R0015 的同 revision 重复 opener 被 once 守卫正确拒绝，属于调用顺序错误；不修改 SDK、一次性或持久化合同，不重放已提交或结果未知的打开动作。

主目标的−100唯一来源和三类理由另按原要求核对，非礼仪观察者的负例方向必须是`outsider→apostate`，不能用`Root→outsider`或反向记录替代。完成囚犯预览及上述读回后，才调用原跨信仰输入决议并签认phase 3。新增control不进入继任者迁移白名单，保留原24个marker含义；本次另加入`requested_head_cells`，core共25个必需marker，其他case仍保留各自原输入及范围。

### 两位真实 head 的后继 core 顺序（候选，未授继承资格）

保留 core 全部六个 phase、原 required assertions 与 marker 含义。原始 `dynastic_esotericism_core.json` 是 adapter 配置，`allow_actor_change=true`、`actor_transition_days=[]` 和 `continue_as_heir_requirements` 是其**顶层现有字段**，没有新的 `adapter_config` 对象。空数组表示不指定自动 advance 序号，不是游戏日期；许可仅使同一 run／pipe／PID／generation 下的新实际 actor 可被观察，不能证明继承或允许任意换人。共享 purpose／clock 必须从同一已 pin 原合同消费该布尔值，保留初始起日、日期单调与预算；缺字段的其他 case 默认 false。R0007 实际 tools/list 注册了 `ck3_set_played_character_v1`，但注册不授予原生可用性或真继承资格；本流程绝不调用它。当前没有已核可用于本次真继承验收的 Continue-as-Heir 路径，遇必须点击 Continue 且无合法原生路径时保留未合格，不创造命令或改玩家。

phase 1–4 按原要求完成；phase 5 从 `repentance` 就绪后按以下顺序执行，Root 必须始终读取本次 awaiting 原要求与原 deadline：

1. **先在旧 Root 上完成全部长程路径**：`des_acceptance_extended_start_decision`；`des_acceptance_second_rite_decision` 后真实 31 日；`des_acceptance_cross_rites_decision`／`des_acceptance_cross_migration_decision` 后各真实一日；`des_acceptance_stock_crime_decision`／`des_acceptance_stock_repent_decision` 后各真实一日；实际出生再推进恰好一日并独立验证身份／归属／有资格者知识；生成、合法旁支、外改 House 校正、原 timer 的真实 61 日与两次 callback 证据。最后也须完成原 `des_acceptance_founder_death_decision` 的**第二位 NPC founder 死亡后真实 31 日**，可在 second_verified 后与其他计时重叠，但不能以稍后的玩家死亡替代。此时不执行 pardon_prepare，不先开关教义。
2. 旧 Root 全部长期 observer 通过后，新 step 执行 `des_acceptance_primary_heir_prepare_decision`，pin 当前真实 `primary_heir`、前任及原主头衔。继承人 Faith 不同时公开执行 stock `set_character_faith = root.faith`，随后执行 `set_character_rite = root.rite`；不预先要求同 Faith，不另选继承人，不设置其 Dynasty／House／产品绑定。若该继承人也是旧后代负例，先固定其仍未改信且未被连带迁族的历史证据；本次主动改信之后不再把它标为未改信负例。至少经过一个实际自然日（`current_date > des_test_heir_input_date`，不是要求恰好一日）后调用 `des_acceptance_primary_heir_readback_decision`，并独立保存 native／Save 的 heir 身份、存活成年、当前继承资格及实际 Rite／Dynasty／House。缺失、未成年、继承改变或不合格均为 NOT_READY，不能造继承人。
3. 对当前真实旧 head 执行 `des_acceptance_edit_input_prepare_decision` → `des_acceptance_edit_input_readback_decision`。它们只复用空槽原版司祭／神学傀儡 helper；没有清理冲突或重置 once flag 的权限。编辑资格与创建资格分开，创建后 aggregate create-ready 不能当作 edit-ready。通过下文通用礼仪操作真实选择 None，验证实质变化、完整 Can 与报价，prepare／confirm 各一次，按事件规则处理后独立 verify，再 `des_acceptance_closed_readback_decision`；固定同一 Rite／绑定 Dynasty。
4. 旧 Root 的全部 observer 与 closed 原件齐全后，`des_acceptance_primary_death_stage_decision` 只安排一次次日 stock death。使用现有事件边界原生 advance，并显式允许观察 actor 改变；返回后先处理实际事件，再独立确认可用暂停帧。不要预先认为 title heir 就是 Rite head，不重置 clock 或原 deadline。
5. 先从实际 native 和独立 Save 固定四项证据：`actual_predecessor_death_and_primary_title_succession`、`actual_current_player_is_the_pinned_living_primary_heir`、`actual_same_primary_rite_and_bound_dynasty_survive`、`actual_native_current_rite_head_is_the_successor`。再调用 `des_acceptance_successor_readback_decision`，其脚本必要条件还核原 title holder／primary title、olddead、真实新 head 与绑定；它不等待额外 fixture 事件，不设置玩家／head。唯一新增 marker 是 `DESAF: TEST PASS actual_primary_heir_successor`。四证据同时列于 phase 5 requirements，不能依赖可能未触发的 dead-player fallback。
6. 仅在真实新 head 身份合格后，在其身上重做同名 edit prepare／readback；独立读取其 `has_edited_a_rite` 未消耗。用真正原生编辑选择 Dynastic，完整 Can／当前报价、prepare／confirm 各一次，处理事件并 verify，然后执行 `des_acceptance_reopened_readback_decision`。原版按 head 的一次编辑限制保持，不能清除／复制 `has_edited_a_rite`、`has_created_a_faith` 或制造 head。
7. **最终新当前 head 才做完整原赦免链**：`des_acceptance_pardon_prepare_decision` → 真实一日 → 原版合法 `pardon_interaction` 一次 → `des_acceptance_pardon_observe_decision` → 真实 31 日。逐项留存原 pardon consumed／stable marker、trait／opinion／pair 及新 head 对同一目标无三种产品犯罪理由；不用旧 Root 的赦免结果替代。先前独立原版犯罪保留仍保留其原 observer／原件，不重标为新 head。

新 fixture 引用仅为 `des_test_ref_predecessor`、`des_test_ref_primary_heir`、`des_test_ref_primary_title`；前任仍由原 `global_var:des_test_extended_owner` 审计。旧 Root 的 `des_test_primary_heir_prepared`／`des_test_primary_heir_ready`／`des_test_primary_death_staged` 不迁移，`des_test_successor_verified` 只在新 Root 必要身份守卫后产生。迁移仅用 producer 明列的真实有限 fixture 引用和有旧 actor 原件支持的历史完成旗标；缺失值不补默认。不扫前缀、不转移 pardon／reopened／冷载锚点／原版 once flags，不写产品绑定、犯罪、trait、opinion、head 或 player。

phase 5 只有在最终新 head pardon31 完成后才能返回。phase 6 的原 `reopened_binding` marker 仍是就绪门槛；到它时重新核全部历史 pin、实际出生+1／timer61／第二 founder31、真实继承与当前新 head／原绑定／最终 pardon31。然后调用 `des_acceptance_cold_anchor_decision`，为**当前新 head 与最终目标**计算新锚点，再真实 Save 并独立解码当前 player ID／date、Rite／Dynasty／House／关系。cold 仅加载这份精确新 head Save，零自然日仍要求新 head 对目标无三种产品犯罪理由；不能用前任 Save 改标签，也不豁免独立旧档 bootstrap。

整个 case 仍为 400 自然日、9000 秒 hold、10800 秒整体 timeout，原 readiness 1800 秒与正常退出预留 180 秒保持。安排死亡和最终赦免前核实际已用自然日／墙钟／剩余预算；时间可重叠不是额度保证。完整 Java producer／13 资源／manifest／导入闭环、共享 clock CI 与新图来源固定完成前不分配执行；通过后仍只授新场开始条件，实际继承／head／编辑／业务各自取证。

R0004 起，首个 phase 等待实际 `DESAF: TEST PASS fixture_ready`，不按“已到第 1 日”推算延迟事件已执行。准备 fixture 不改角色 Faith；保留开局 Catholic／Roman Rite，实际知识、无先知、资源和原生 `Can` 均须重新读回，不能把儒家身份当作前提。

R0004 的日志故障候选修复只改日志位置：`.3/.4` 外层完整 observer／outsider 守卫保持，四条 PASS 采用静态带引号 `debug_log`，移除重复的 positive／negative 日志 helper；不能再传整句 `$PASS$`／`$FAIL$`，也不另换 CASE 宏猜引擎行为。旧 R0004 原输入及两份坏资源在 Java 回归中保留，实际旧输入须被非字面量日志检查拒绝。新 JAR／fixture 和后继实机尚未因此通过；完整证据与边界见[测试方案](../test-plan.md)。五项名称、教义与资源齐备仍不能代替实际原生 `Can`，R0004 观察到的创建资格缺口须独立闭合。

后继 fixture 的原版关系输入已明确公开：优先当前真实宫廷司祭，缺失时只运行一次原版 landed realm priest 筛选；其后仅为合格司祭与空槽建立原版神学傀儡关系，不清除冲突、不选择六项互动支持、不声称互动已经提交、接受或支付。setup 的 `fixture_ready` 需要真实关系和已知脚本资格读回通过。**首次创建**开窗前调用独立 `[测试] 观察原版神学傀儡前置输入` 决议，检查 cp／puppet／反向 puppeteer／puppet_action_valid 的静态日志，并从新 epoch 另读 council full ID。该决议只读原版关系，只更新 fixture 观察旗标；它不重新任命或创建傀儡。创建后的两次编辑采用上节各 head 自己的 edit prepare／readback，不使用包含 `can_create_rite_trigger` 的创建聚合资格代替。草案五名称、教义和资源齐备后仍须原生完整 Can；关系前置日志不能替代该结果，原版确认仍只能执行一次。

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
4. 保存实际完整 `Can`、价格和当前 `preview_identity`；`prepare_confirmation` 必须同时传真实 `expected_preview_identity` 和 `expected_outcome_kind`（实际创建为 `create_rite`，实际编辑为 `edit_rite`），才可打开原版确认界面。
5. 仅在原始结果已知时 `confirm_once` 一次；它同样必须同时传当前草案的真实 `expected_preview_identity` 和实际 `expected_outcome_kind`，不能省略任一字段，也不能用另一草案或旧 revision 的身份。
6. 仅对 `confirm_once` 的 pending 结果调用 `ck3_collect_player_rite_creation_action_result_v1(action_request_id)` 收集原最终确认。非 confirm 操作没有此 final-confirm claim；开窗 pending 时保留原 receipt，不重放，用原 action context 的 `observation=draft/current_rite` 独立观察，再按真实草案查询 groups。UNKNOWN 不重放。
7. 每次 confirm／collect 返回后，先读取该 step 的实际 `after_snapshot`，再用 `ck3_take_snapshot({})` 独立读取当前帧。出现 `active_event` 时先处理事件，不调用礼仪完成验证；扣费或 pending 不能代替完整后态。按下文原生事件顺序采集与处理，事件消失并取得新的 event-free 暂停帧后才进入下一步。
8. `ck3_verify_player_rite_creation_action_completed_v1(action_request_id,expected_revision)` 独立核对真实当前 Rite、名称、core、doctrines 和窗口/确认框关闭后态。使用原确认的 `action_request_id`，并以新的 event-free 帧绑定 revision；该最终 SDK 工具实际冻结并进入 required tools 后才可执行。旧 collect/ACK、扣费或处理事件的 ACK 均不代替本步；未知确认不得重放。

原生创建事件必须在宿主尚无 error 时处理；以下只使用 a07 已注册工具，下一场先重读其实际 tools schema，不能给已经失败的 R0006 宿主续发业务计划：

1. 从本场新鲜 snapshot 的 `active_event.instance_id` 取实际实例，以 `ck3_query_current_event_window_context_v1(event_instance_id, expected_revision)` 查询。保存原生 `current_event_window_context` 中的 `event_definition_key`、`calculated_event_id`、`current_event_instance_id`、root／saved scopes、实际显示的 `options`、readiness／provenance 及该 step 的前后帧。R0006 的实例 1、revision 10 只证明历史现场，不能复用于下一场。
2. 已覆盖事件采用现有专用策略；未覆盖事件先保存原定义／实例、双方角色与当前帧、实际显示选项和策略缺口，再选择第一显示项。要求本次查询的真实实例仍相同、`status=available`、选项呈现已就绪；从 `current_event_window_context.options` 的实际 `rendered_index=0` 那一项读取 `native_option_index`、`shown`、`enabled` 和 `resolved_name`。`ck3_select_event_option` 接受的是 **`option_number = native_option_index + 1`**，不是显示序号加一；不能从 R0006 的两项概览、历史标签或选项数量猜测映射。无法取得实际显示顺序或首项禁用时保留真实缺口，不伪造已选择。
3. 用新的 queue plan／step ID，仅提交一次 `ck3_select_event_option(option_number=<本次映射值>, event_instance_id=<本次实例>, expected_revision=<当前帧>)`；队列使用 `args` 和 `fresh_revision=true`。选择返回 pending／未知时只观察该原动作，不重复选择。记录原生 ACK 与后态，不把 ACK 当作窗口消失。
4. 另用新 step 调用 `ck3_take_snapshot`，`args={}`、不注入 expected revision。独立保存当前原生帧，核原实例已不再是当前窗口；若出现另一个实例，重新采集该实例并按同一规则处理。只有取得选择前之后的新原生帧、`active_event=null`、`paused=true`、`map_ready=true`，且实际 run／state／pipe／进程／连接／玩家绑定未漂移，才可进入完成验证。不要对已消失的旧实例再调用要求“当前实例匹配”的 event-window query，制造新的宿主错误。
5. 用新的 plan／step ID 调用 `ck3_verify_player_rite_creation_action_completed_v1`，`args={"action_request_id":"<原确认请求ID>"}`、`fresh_revision=true`；宿主在提交前加入当前 revision。只有其独立当前 Rite／完整提交内容／窗口关闭证据通过，才能报告确认完成；之后再验产品绑定与其他业务断言。该顺序不修改 SDK 的 event-free、来源或 UNKNOWN 不重放守卫。
6. 保存新事件的离线分析输入，并在该轮结束后核原版定义／效果与来源 SHA，补入现有共享知识入口；事件选择和离线研究分别记录，不把保存待办当作分析完成。

R0006（`machine_id: desktop-3fevhd2-1c74096080`）的实际顺序缺口：2026-10-24T15:43:06.263586Z 的合法 `confirm_once` 得到原请求 `rite-action-df640506a3144010aedbf34b8db4ebb0`，原结果保持 pending；随后 collect 的 `after_snapshot` 为 public revision 10／native revision 9，同一 R0006 的 managed binding 完整、paused／map-ready 为 true，但出现原生事件实例 1／两个概览选项。虔诚由 10,015,000,000 扣除报价 370,500,000 后为 9,644,500,000；这一扣费只证明资源变化。15:43:54.290358Z 的实际 MCP snapshot（id 847）仍含该事件；紧随的 verify（id 848）正确绑定 `expected_revision=10`，却因事件尚未处理而触发 `title_map_navigation_contract.py:236–243` 的 `active_event is not None` 守卫。该共用错误文本为 `title-map native campaign lacks an allocated run and full current paused frame`，不能据文本反推 run binding 缺失。

直接导入 a07 冻结 SDK、对保全的 confirm／collect／id847 JSON snapshot 运行 `_binding`，分别得到 PASS／同原错误／同原错误；JSON 序列化往返不改变这些结果。仅在明确标记的内存合成对照中去掉 `active_event` 后，同一 managed identity 通过；该对照没有游戏后态效力。证据为 `C:/ck3-dynastic-esotericism-20261024/rite-completion-diagnosis-a01/guard-reproduction.actual.json` 与 `actual-MCP-id847-id848.excerpt.json`。宿主 `RecordingDriver._with_one_life_episode` 在公共 snapshot 投影中附加实际 allocator binding；`take_snapshot_without_native_command_history` 仍调用同一 `take_snapshot`，没有本次漏绑定的证据。保持现有 SDK 守卫与异常合同，R0006 原错误和 0/6 结果保留；错误发生后只按生命周期白名单正常闭场，不补发事件选择、verify 或确认。

每次排队前，先对本次真实值只读调用冻结 SDK 的 `request_fields(operation, actual_source_rite_id, **selectors)`，按该 operation 的 exact required selectors 预验；它只校参数合同，不查询或提交游戏，也不证明草案仍新鲜、完整 Can 或业务成功。`prepare_confirmation` 与 `confirm_once` 的 selectors 都恰为 `{expected_preview_identity, expected_outcome_kind}`。`expected_revision` 由 MCP 参数层独立绑定，不放进这个函数的 selectors。不能只看 MCP 包装器为统一多 operation 而声明的 Optional 签名：缺失字段会被过滤后在 SDK 拒绝。来源固定为 `7def6fe3e740b85099e1016f7ee0027048cb7d1a` 的 [request_fields 第 508–516 行](https://github.com/XenoAmess/ck3_eternal_recurrence/blob/7def6fe3e740b85099e1016f7ee0027048cb7d1a/ck3_autonomous_player/src/xar_autoplayer/bridge/rite_creation_action_private_v1.py#L508-L516)；R5 实际冻结文件 59,698 B，SHA `ce030a17f8d024460052deede2069f5cff3c34c876e13d2b359af3d1d6e62284`。

R0005（`machine_id: desktop-3fevhd2-1c74096080`）于 2026-10-24T15:09:20.731249Z 提交的 `root-create-prepare-once` 仅带 `operation=prepare_confirmation`、`expected_source_rite_id=0`，漏了上述两个 selector；15:09:21.132971Z 在原生 dispatch 前被 `unexpected or missing Rite creation selector` 拒绝。该场保持 0/6 与业务 RED，shared host 保留原错误，不能续发业务操作、取消礼仪草案或重放 prepare。原件为 `common-runtime-a07/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0005/native-report.json`；闭场进行中的原报告可能继续更新，本次错误及原失败 step 已只读保全到 `C:/ck3-dynastic-esotericism-20261024/R5-selector-rejection-a01.actual.json`（3,522 B，SHA `24a64e4dbbd3c5dab421a6cf0ece600c2cde6f5cf727bc95f8232bf3eab14910`）。原拒绝不清除，正常退出后再用同一 runtime 分配新场次；本段不追认正常关闭或下一场成功。

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

宿主已经记录 error 时，每个队列 plan 只能放**一个**有全新 step ID 的 typed lifecycle step：`ck3_query_normal_exit_context_v1`、`ck3_request_normal_exit_v1` 或 `ck3_observe_normal_exit_v1`。正常退出 query 和 request 也必须分成两个独立 plan，不能合成“先 query 后 request”；礼仪 `cancel_draft` 等业务操作不在白名单。这里的正常退出 `prepare_confirmation` 是 `ck3_request_normal_exit_v1` 的 action，不能与前文礼仪工具的同名 operation 混用。该规则来自同一冻结 SDK 的 `normal_exit_host_terminal_v1.py:21–60`，文件 SHA `a0c07cb90e2be72f3f54802e17660d41a4c00d7baad40bd2a18e2c8d7d96922f`；失败宿主只允许完成原生命周期，原业务错误始终保留。

2026-10-25 新head要求：phase1签字前的 primary `binding_and_members` 仍保留全部原守卫，另核初始实际提交actor与主头衔未变、本人为新House head和bound dynast。若另一个真实信徒／NPC曾中间建族，其actual dynasty_founder须仍存活且不再是最终head。名称须由实际Native／界面及独立Save比较真实字符串；纯loc key或源码表达式不算实际名称通过。两项预置CoA另留实际代表证据，通用自创Rite图标复制尚未完成，保持NOT_RUN。

primary `binding_and_members` 的 D1／D2 全员 Native＋独立 Save 及原未改信成员、原宗族／House 对照全部通过后，在 phase1 仍等待时使用同一个 `des_acceptance_head_cells_decision` 分两段输入。第一次仅为 P0：在原 `des_doctrine_none` source Rite 准备 A（handover）、B（旧 House 接任者）、C（singleton），保存实际角色、旧 House／Dynasty、各自 head、Root 身份、source Rite／Faith 与准备日期；此时不创建新 Rite、不采用，不能把输入准备算作业务 PASS。

至少经过一个真实自然日，确认 A/B/C 仍在原 None Rite 且初始化已成熟，再第二次执行同一决议。决议和 effect 均须重验同一准备 actor、持久 source Rite／Faith、旧 head／Dynast、Root 身份与一次性守卫。第二段才是 H0：A/C 的 stock factory 使用 `convert=no`、`target_divergence=0` 和仅作用于两个新测试 Rite 的 Dynastic override；确认工厂未自动转换后，以实际工厂日记录 H0，再普通 `set_character_rite` 采用。保留 Root 的 `des_test_handover_*`、`des_test_singleton_*`、准备日期、`des_test_head_cells_capture_date` 与两项实际 `creation_date`；全部 ID 取本场持久引用，不套历史值。

primary D1／D2 已完整通过且 P0／成熟／H0 输入证据齐全后，可按真实 Core case 签认 phase1；phase1 不以 cells H2 全部完成为额外条件。随后在 phase2 处理以第二段真实 H0 为锚的 H1（+1）及 H2（+2），保全各日原生帧、完整实际成员与同暂停帧独立 Save。原 `.81 days=2`、`deferredDate == creationDate`、handover 旧 House 由 B 接任／A 为新 House head 与 bound dynast、singleton 的 C 最终双 head／真实 NPC founder 存活同 Rite／Faith／House／Dynasty且非 head，以及 Root 原身份守卫均不放宽。phase2 原 `binding_and_members` 与 `requested_head_cells` 均须实际 PASS 后才继续 same-faith 输入；NOT_READY／FAIL 及 UNKNOWN 原义保留，不重放已消费阶段或补写产品 state，不把 P0 日期当 H0、也不以 cells +2 替代 primary +2。仍为原25 markers／6 phases，全部推进计入原300日目标、400日上限及9000秒预算。


2026-10-25 R0010操作顺序勘误（machine_id: desktop-3fevhd2-1c74096080）：每次日推进前先读原最新完成step的实际after_snapshot；已有active_event或pending_character_interaction时先按原生事件定义／实际显示选项处理，不能直接推进。即使只推进一日，也统一使用已审日推进捕获器：其开头守卫会在提交前停止并交Root处理。allow_event_boundary只允许本次推进中新出现的事件边界，不授权绕过开始时已有事件。R0010的guard9因Root漏处理+1事件而正确拒绝，诊断日期仍53144376、未执行+2名单或保存；不改共享守卫，不重放原推进。旧创建prepare参数误写也被前置拒绝、没有native dispatch，原失败回执保留。

2026-10-25 R0011操作顺序勘误（machine_id: desktop-3fevhd2-1c74096080）：创建confirm、收取原结果、事件context、选择、消失后验、独立completion与current-Rite查询分别使用独步plan；每一步先检查实际after_snapshot再决定后继。输入决议与每次日推进也采用同一顺序。收取结果后已有事件时，current-Rite及completion的无事件帧守卫会正确拒绝；不能把这次操作错误归因于SDK或产品。首个实际显示项按其native index加一取得option_number，不能把数组槽数当显示选项数。

退出操作也必须逐步重新观察：disable_exit_autosave的响应不是下一次confirm所需的新context signature，必须再query。原生签名拒绝不授予清除SDK terminal claim或再次confirm的资格。若原CaseClient已经产生仍在原deadline内的normal-quit-awaiting请求，可沿其现有GUI Quit备选保存未勾选截图、同PID守卫的映射点击及直接review，再等待真实原进程退出和清理；它不追认为typed退出成功或业务通过。R0011实际走此备选后Game0、host1、public2，资源接续消费者通过，原业务RED保留。
