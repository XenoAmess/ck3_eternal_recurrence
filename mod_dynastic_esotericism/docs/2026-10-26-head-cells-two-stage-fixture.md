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

原 `des_acceptance_read_head_cells_effect` 观察段逐字保留，原 `.81 days=2`、`des_deferred_binding_date == des_test_*_creation_date`、新旧 House/Dynasty 真实头衔、singleton 中间真实 NPC 与 Root 身份守卫不放宽。H1/H2 继续以第二段实际 factory H0 为锚，不以准备日替换，也不顺延观察。13 fixture 文件、25 必需 marker、6 公共 phase 不变。

生产 binding、on_action、native UNKNOWN/barrier 不改。普通 setter 的实际回调时序仍须新场 H0/H1/H2 原生和独立 Save 证明，源码或 marker 不授予修复通过。

## 共享回归与实际命令组

Java 真实 emitter 的既有 AST 回归增加针对重复 stage、同日启动、来源/恢复 scope 漂移、同帧生成、自动转换、错误 override、history setter、产品变量写入、日期换锚和延迟读回的独立反例。原失败回归保留。

SharedRuntimeComposerTest 将实际 CORE emission 接入现有公共 registry/import、Selection.prepare、generic profile、Prepared 和冻结 source pins；同时验证实际装载13文件、25 markers、6 phases。合并 empire/transfer 后 source count 仍为34，不另加公共 case 或私有 runner。新9个 CK3 资产源统一 UTF-8 BOM，真实 emitter 的 packaged/current 资源比对仍须通过；a07不能追认新源。

容量准入及干净最终 HEAD 后，在仓库根按现有 Static CI 组完整执行，使用命令行默认 Maven；下面输出根是本机本工作包路径记录：

```bat
mvn --version
mvn --batch-mode --no-transfer-progress -f mod_dynastic_esotericism/tools/pom.xml -Ddes.build.root=C:/ck3-dynastic-esotericism-20261024/resume-builder-a20/attempt-a08/java-build -Djava.io.tmpdir=C:/ck3-dynastic-esotericism-20261024/shared-temp-a20/attempt-a08 verify
python -B -X utf8 tools/test_prebuilt_fixture_prepare.py
python -B -X utf8 tools/test_canonical_host_successor.py
python -B -X utf8 tools/test_product_acceptance_purpose.py
python -B -X utf8 tools/test_preserved_failure_native_os0.py
python -B -X utf8 tools/test_ck3_mod_acceptance_offline_ttl_unrun.py
python -B -X utf8 -m mypy --strict --strict-equality --follow-imports=silent --no-incremental --cache-dir=C:/ck3-dynastic-esotericism-20261024/shared-temp-a20/attempt-a08/mypy tools/test_prebuilt_fixture_prepare.py tools/test_canonical_host_successor.py tools/test_product_acceptance_purpose.py tools/test_preserved_failure_native_os0.py tools/test_ck3_mod_acceptance_offline_ttl_unrun.py tools/ck3_mod_acceptance_launcher_protocol_v1.py tools/ck3_mod_acceptance_background_types.py
```

沿用 CI 环境 `PYTHONPATH=ck3_autonomous_player/src`、`MYPYPATH=tools;ck3_autonomous_player/src`，在导入会冻结配置的模块前设置。未执行的命令不能写为 PASS。完成静态构建后走同一正式生产链和新公共 Core 场，不复用 R0019 原 request 或热改其 runtime。
