# R14 闭合后源码整合与离线验证附录

本附录记录 R14 原游戏、Client、keeper 句柄 exit0 及 CAS3429 释放后，root 对实际主仓工作树的源码整合。R14 loaded/export/build 永久绑定 `19e660105e05395caa6cc95e76c299312ee89d51`；本附录不能把原 B4/B5 STATE38/47、保护80/87 RED 改成成功。整体产品 NOT_GREEN；new committed source HEAD、新冷构建/新实机、Workshop 发布信用仍为 NULL。

root 顺序应用 numeric6、preview5、factory7、reader3九目标增量，运行 gen_runtime 退出0。原四份 manifest 和候选源字节逐个保全在 [source_inputs INDEX](source_inputs/INDEX.json)，原 manifest 的 not-applied/null 字段作为当时冻结事实保持；当前应用结果另以本附录的工作树读回表示。源目标共有 26 个唯一文件，实际读回与对应最终候选一致，仅三项新 fixture/test source 使用 root 的[CRLF→LF 原回执](source_inputs/originals/92769f96c20c11e85cf38572bb89bf780f30b45197d18b066f2d266bc61ae779.json)规范化；历史 raw、生成文件没有因此改写。

| root 实际检查 | 实际结果 | 原件 |
| --- | --- | --- |
| 全 reader tests | 112 tests，exit0、无 skip | [receipt](source_inputs/originals/f5af37df9b830c7e0c359f399c26e28a48a10279af457840c4e573c6f4a218bf.json) |
| factory law protection | 11 tests，exit0、无 skip | [receipt](source_inputs/originals/abead694db25f282d41300541415b6ce7af539b9114975aa0bbb1c30b21da19c.json) |
| event bind preview | 6 tests，exit0、无 skip，SOURCE_ONLY | [corrected invocation](source_inputs/originals/92b6745103366dea08490fa91508ec22c7341d5ebe9ec36a55df223939091421.json)、[checks](source_inputs/originals/b2918730a2ceeb554c692384406e1384bf1b2f434f5b3dbe7cbcf38835836199.json) |
| static | L0 GREEN，70 runtime files、errors=[]、live=NOT_RUN | [receipt](source_inputs/originals/a7b95092720d85f020b13f2904adf6759e546bb9fb8dc0ba354c81c1f72edf54.json) |
| gen_runtime | 实际 exit0 | [receipt](source_inputs/originals/42bb6fa015b80e2a88876c594fd5be274e320e44904db24086c994e85a56a406.json) |

[首次 preview CLI exit2](source_inputs/originals/3967cd746c0b4e33c021ba37542600a176dfcf30e5b21f3e1fd09a4b291aebcb.json)因缺少 --report 保留原 stderr，随后 corrected invocation 单独记录，没有把旧失败改写。以上 counts 来自实际 stdout/stderr/JSON，报告代理没有重跑测试或生成器。

factory 源码拟在 title factory 中保存/恢复既有 same_faith_succession_law 状态，reader3 使用显式 saved-Faith semantics v2；原 raw doctrine_no_head 与 native predicate UNKNOWN 保留，政治/actor 全 AST 保护不放宽。fixture 测试不授予新实际 checkpoint 成功资格，engine law re-add 与 preview native 效果仍需下一次 cold 实机。

工作树读回时 HEAD `1a09b47d352e0a93243e9f12420ec6948dac2e8c` 是已提交基线，源码修改尚不构成新的 commit HEAD。原既有网络失败与之后 HTTP1.1 fetch 成功由执行者另存原回执，本附录不猜最新远端或合并完成。后续提交/合并与正式 build 双检查未纳入本 cutoff，必须以新的实际回执追加；不同 Z 机器的1.20.0.4迁移不替代当前 C 机器1.20.0.3版本资格。


## 2026-10-07 追加：finalfactory004 最终源码补证

[final004增量、gen0、law11、static70 files及实际双构建原件](FINAL004-INTEGRATION.md)已另附来源。原R14 runtime19、B4/B5 RED及所有历史raw保持，新native/cold实机资格尚无信用。
