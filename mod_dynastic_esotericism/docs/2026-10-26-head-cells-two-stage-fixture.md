# Core head-cells 两阶段输入修复

machine_id: desktop-3fevhd2-1c74096080  
observed_at_utc: 2026-10-25T22:24:44.739460Z（已保全的参数文档观察时间）  
状态：源码修复；Java/JUnit/Maven 和新场实机尚未执行。

R0019 的 H0 factory 自动转换没有产生普通采用队列；H1 新角色 finalization 才首次写入 requester/date，H2 真实 FAIL。原失败、原 +1/+2 后态与 phase1 独立 PASS 1/6 保持，不改写为通过。

## 输入顺序

同一个 `des_acceptance_head_cells_decision` 首次仅在原 `des_doctrine_none` source Rite 准备 A/B/C，保存实际旧 House/Dynasty、接任者、Root 身份和准备日期。fixture-once 旗先于生成写入，重复第一段不能再生角色。角色不留在 primary Dynastic Rite 过夜。

至少经过一个真实自然日后，同一决议第二段从 Root 持久变量恢复角色 scope；重新验证来源 Rite/Faith、Root 身份、真实旧 House head/Dynast、隔离关系和接任者。第二段在 effect 内独立重验成熟日期与一次性守卫，不从第一段自动落入工厂。

成熟 A/C 的 stock `create_dynamic_rite` 使用 `convert=no`、`target_divergence=0` 和唯一 `doctrine_override_entry=doctrine:des_doctrine_dynastic`。这只配置两个新测试 Rite，不修改玩家已有教义。确认工厂未转换角色后，记录该真实工厂日 H0，再通过普通 `set_character_rite` 采用新 Rite。

工厂继承 scope 角色的当前 Rite；真实 EXE 参数文档没有 base/source Rite 参数。此处允许的 doctrine override 正是该 EXE 的公开参数。依据：R0019 `operator-evidence/independent-headcells-h2-full-graph-observer-a10-a01/HEAD-CELLS-STOCK-EFFECT-CANDIDATE-SOURCE.corrected.actual.json`，5801 B，SHA-256 `b31c0db2d2017e393e94b61f0216bd8d8638ffe5fb1df765d09e59f5d4ce50e1`；factory 帮助1809 B，offset `0x481e9b0`，SHA-256 `304380551f53f7fe41aa415b597a9550cd33990751ba084bcabcf928c57d9e9e`。早期抽错前缀的未 corrected 卡不作为此依据。

## 不变的验收

原 `.81 days=2` 观察时限、新旧 House/Dynasty 的真实头领与 founder、singleton 中间真实 NPC、Root 身份和全成员守卫继续保留。R0021（machine_id: `desktop-3fevhd2-1c74096080`）在两段真实输入后仍触发原 `requested_head_cells` FAIL：H0 creation date 为389351，两 Rite 的实际 deferred date 为389352；两新 D/H 的实际双 head 已正确。`deferredDate == factoryCreationDate` 是 fixture 对引擎回调时机的错误假设，不能当作产品的当日回调需求，也不能改写原失败。后继 fixture 只在原 `on_rite_change` 链追加被动见证，严格匹配全局 owner 的 A/C、对应新 Rite、原 None source Rite、started 与 input_prechecked，在首次实际引擎回调中把 `current_date` 写到 Root 专用 `des_test_*_adoption_callback_date`；不合成+1、不取 Rite 产品日期自证，也不修改产品 state。H2 要求两份见证存在，并严格比较 `des_deferred_binding_date == des_test_*_adoption_callback_date`；H1/H2 独立 Save 继续核 requester 与首次日期持久不变。原 post-adoption `input_ready` 不提前，H0 refs 保持在普通采用前记录。H1/H2 仍以第二段实际 factory H0 的+1/+2为观察日，不顺延。13 fixture 文件、25 必需 marker、6 公共 phase 不变；这项共享 fixture 修复须经新生产构建与新冷实机验收，不能追认 R0021 通过。

生产 binding、on_action、native UNKNOWN/barrier 不改。普通 setter 的实际回调时序仍须新场 H0/H1/H2 原生和独立 Save 证明，源码或 marker 不授予修复通过。

## 共享回归与实际命令组

Java 真实 emitter 的既有 AST 回归增加针对重复 stage、同日启动、来源/恢复 scope 漂移、同帧生成、自动转换、错误 override、history setter、产品变量写入、日期换锚和延迟读回的独立反例。原失败回归保留。

SharedRuntimeComposerTest 将实际 CORE emission 接入现有公共 registry/import、Selection.prepare、generic profile、Prepared 和冻结 source pins；同时验证实际装载13文件、25 markers、6 phases。合并 empire/transfer 并补齐 cold 所需真实工具／SDK 模型后，synthetic source count 为36，不另加公共 case 或私有 runner。新9个 CK3 资产源统一 UTF-8 BOM，真实 emitter 的 packaged/current 资源比对仍须通过；a07不能追认新源。

容量准入及干净最终 HEAD 后，在仓库根按现有 Static CI 组完整执行，使用命令行默认 Maven；下面输出根是本机本工作包路径记录：

```bat
mvn --version
mvn --batch-mode --no-transfer-progress -f mod_dynastic_esotericism/tools/pom.xml -Ddes.build.root=C:/ck3-dynastic-esotericism-20261024/resume-builder-a20/attempt-a09/java-build -Djava.io.tmpdir=C:/ck3-dynastic-esotericism-20261024/shared-temp-a20/attempt-a09 verify
python -B -X utf8 tools/test_prebuilt_fixture_prepare.py
python -B -X utf8 tools/test_canonical_host_successor.py
python -B -X utf8 tools/test_product_acceptance_purpose.py
python -B -X utf8 tools/test_preserved_failure_native_os0.py
python -B -X utf8 tools/test_ck3_mod_acceptance_offline_ttl_unrun.py
python -B -X utf8 -m mypy --strict --strict-equality --follow-imports=silent --no-incremental --cache-dir=C:/ck3-dynastic-esotericism-20261024/shared-temp-a20/attempt-a09/mypy tools/test_prebuilt_fixture_prepare.py tools/test_canonical_host_successor.py tools/test_product_acceptance_purpose.py tools/test_preserved_failure_native_os0.py tools/test_ck3_mod_acceptance_offline_ttl_unrun.py tools/ck3_mod_acceptance_launcher_protocol_v1.py tools/ck3_mod_acceptance_background_types.py
```

沿用 CI 环境 `PYTHONPATH=ck3_autonomous_player/src`、`MYPYPATH=tools;ck3_autonomous_player/src`，在导入会冻结配置的模块前设置。未执行的命令不能写为 PASS。完成静态构建后走同一正式生产链和新公共 Core 场，不复用 R0019 原 request 或热改其 runtime。

## a08 真实失败及 a09 输入闭包修复

a08 完整 Maven 原退出1：44项中43通过、1 failure、0 error／skip，没有生成应用 JAR。失败原件保留于本机 `resume-builder-a20/attempt-a08/captures/maven-verify-a01.stdout.log` 和 surefire；不能写为验证通过或从其 classes 推认可运行包。

失败发生在七个新增 fixture 的公共 prepare 循环，非 CORE／preset／initial 已完成链。前两个 fresh 不导入 saved-profile SDK；首个 cold 分支经 Main12 的 saved-profile 工具懒加载时，其 `__file__` 将 Main12 SDK 插入路径。synthetic 父树缺少真实 saved-profile 工具及 `saved_campaign_profile_inventory_v2` 模型，`_case_loaded_sdk_sources_v1` 因此在退出时正确拒绝 `xar_autoplayer` 逃出选定冻结 runtime。本次在已声明的 a08 临时根未找到失败临时树；分支定位来自原 traceback 与实际循环／导入路径，不声称留存该临时目录。

修复只补 Java 测试的真实两叶输入，并按 host 的冻结 tools 优先顺序导入；共享 composer 原有全 SDK／`ck3_mod_acceptance*` 选择规则会实际封包它们，source count 两处由34改为36。回归明确核对工具、SDK模型及 package 的实际导入文件、当前／冻结字节和 source-index pins。生产 Python、源身份守卫及声明环境不放宽、不 monkeypatch。

同一循环另纠正两个 blocked restoration 输入：公共 `Selection.prepare` 必须抛原始 `Explicitly blocked product adapter cannot prepare`，且没有 Prepared／state 输出。真实执行准备的范围是两个 fresh empire、两个 cold empire及 transfer 共5项；两个 restore 只证明公共拒绝，仍 NOT_READY，不能冒称 Prepared。

a09 须在新最终来源和新容量准入后完整重跑上述 Maven＋Static CI 组。本修复未涉及共享 Python cold/warm实现，因此不扩大为另一套生产路径；a08旧失败和所有Game业务边界不变。
