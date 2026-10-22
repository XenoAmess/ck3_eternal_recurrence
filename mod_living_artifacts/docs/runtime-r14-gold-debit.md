# R14 金币扣款故障与修复候选

`machine_id: pc-20260924rtuf-f11af23c08`；观察时间 `2026-10-22T19:57:08Z`。
场次 `pc-20260924rtuf-f11af23c08--living-artifacts--R0014` 加载旧冻结候选 `c16`。
本文记录故障与离线修复，不授予新版实机或正式发布通过。

R14 训练后 L11/XP25，金币 747；首次镇压后金币仍为 747，威望由 2350 降为 2300，压力由 25 升为 33，期限 389453、连续次数 1、计时序号 1、饥渴 2 已写入。SAVE 与原生钱包一致；压力受角色倍率影响，不据它否认动作发生。金币应扣 75，验收预期保持 747→672。

独立读回来源为该场外置 `case-output/threshold-checkpoint-03.json`（SHA-256 `5c4a7f0b4a8562d47d2531f5dba0343e5c14ce0cc206767f8fb0b00dce0f3c93`）及 `threshold-checkpoint-04.json`（SHA-256 `f4c3a53d338879f7b022225172b4a2c6d13fd8c7621fd9ec24f93e917337abd8`），均位于 `D:/workspace/ck3-living-artifacts-20261022/live/pc-20260924rtuf-f11af23c08--living-artifacts--R0014/`。两份 `saved_vitals` 与 `native_vitals` 的 `gold_raw_decimal` 均为 `74700000`、`scale=100000`。

实际日志源为 `D:/workspace/ck3-living-artifacts-20261022/runtime/profiles/living-threshold-a18/state/profile/logs/error.log`。本次读取的完整小型日志快照保存在 [evidence/r14-negative-add-gold-error.snapshot.log](evidence/r14-negative-add-gold-error.snapshot.log)，SHA-256 `2a13ec95e78e377a5aee97380a066f564300d31032a66afe019dbe7ee1a1cc22`。这是闭场前快照，后续原日志可继续增长；原件未修改。关键行 24–27：

```text
[03:43:07][E][jomini_script_system.cpp:304]: Script system error!
  Error: add_gold effect [ Trying to add add_gold with negative value to Robert 德· 欧特维尔 of d_apulia (Internal ID: 31254 - Historical ID 1128)! ]
  Script location: file: common/scripted_effects/xalw_core_03.txt line: 31 (xalw_suppress_effect)
    file: events/xalw_core_events.txt line: 111 (xalw.10:option)
```

原因是引擎拒绝负数 `add_gold`，但继续执行后续威望、压力与状态操作。此条日志明确报负值，不是神器报价 scope 未解析。实际原版 `events/artifacts/artifact_events.txt:1821,1848` 使用 `remove_short_term_gold = scope:this_artifact.reforge_artifact_cost`；该原版文件本次 SHA-256 为 `aab135e64c2586b7315f0ab2e7ab14bb35801ffbbb6368649305a8d5379bfbb5`。

修复仅改两个共享生成器的四处付款模板：镇压、安抚、共用有限钱包付款、宴会酒款。生成后实际覆盖 10 个扣款点：镇压及安抚各 1、借款还款 1、贵族胃口三级 3、锈蚀修复三级 3、酒款 1。全部使用正数报价的 `remove_short_term_gold`，奖励 `add_gold`、报价、破产代价和状态计时保持原值。生成结果仅变更 `xalw_core_03.txt` 与 `xalw_content_01.txt`，未直接编辑它们，未改冻结场次、原始证据、descriptor 或公共 host。

回归接入现有 `static-ci.yml` 的完整 mod unittest discovery 与目录 strict step，检查实际生成树中的付款与资格共用报价、扣款先于状态、有限钱包 clamp 与短款记账、酒款资格及后续收益顺序。首次中间版本完整 suite 在 catalog 尚保留旧 core 来源 SHA 时实际 exit 1：215 项、330.642 秒，`test_real_source_bindings_and_changed_hash` 报 `ValueError: Catalog source changed: mod_living_artifacts/tools/living_artifacts_core.py`，其余无失败。该失败保留，不算通过。随后同步 catalog 的 core/content 来源 Pin，重新执行完整同一命令。生成结构和类型检查仅属于离线范围。

Catalog 原 core Pin 为 `8265d274716711234fcf66147f885abe61428bf2f8da9074338f50b68dde644c`，原 content Pin 为 `126cedc1c65db6b8d93db139aca994c17948623c5e92c83c26080875dec5f64d`；本候选分别为 `848c0abed02183daae4084c9fbc8baa695ac9efa0433467223c91cd0de8225b0`、`1720fbf0150646ccfee248e21b253b2d44b9184d110c115293b67d54f358c3b4`。共更新 25 个来源引用，原 anchor 全部仍存在，没有放宽来源守卫。

同机新候选离线终态：`generate.py` 生成 49 文件，随后 `--check` 与 `validate_static.py` 均实际 exit 0；CI 原命令 `python -B -X utf8 -m unittest discover -s mod_living_artifacts/tools -p test_*.py` 实际 218 项、312.577 秒、exit 0，无失败或跳过。全量日志保存在 `D:/workspace/ck3-living-artifacts-20261022/environment/r14-gold-debit-offline-a01/unit-{stdout,stderr}.log`。按 CI 配置 `MYPYPATH=tools;mod_living_artifacts/tools;ck3_autonomous_player/src` 执行 `python -B -X utf8 -m mypy --strict --follow-imports=silent mod_living_artifacts/tools`，实际 53 文件、exit 0；`git diff --check` 通过。新增测试由现有 CI discovery 自动覆盖，无新增编排入口。

新版仍须新候选重载：threshold 首次镇压扣 75；既有 timer 代表首次 25、续镇 45；贵族胃口实际扣款及破产代价；管理流程补一次安抚正扣款。沿用各代表场次，不新增整套实机矩阵，不将 R14 旧加载结果改记为新版成功。R14 由原 owner 完成既定保存与正常退出。
