# 574c 真实 CI RED 的检查器修复

ROOT 的实际 GitHub Actions run `37702997797` / job `113070638610` 在 `Check product builder` 失败：`test_c3_i3b_preview_scope.py:135` 拒绝 `common/scripted_triggers/lyd_i3b_institution_triggers.txt` 的旧 AST 指纹。原始 CI 输出由该 run 保留；本包不制造原始日志副本。

574c 修复了正式活跃 rite 授权条件，使用 `NOT { AND { total > 0; quorum >= 0; signed = 1; exists delegate } }`。旧检查器仅撤销九类 optional-target guards，没有撤销这一项已审议的AND包装，因此拒绝新增节点。此失败来自旧逆投影未适配，不说明原指纹应被刷新。

唯一候选修改是原检查器的精确有限逆投影：只识别 `lyd_i3b_ready_trigger` 下、`lyd_i3b_rites` 且 `dormant=0` 列表上下文的唯一完整AND节点。四项原语、顺序、operator及路径必须精确符合，才能去掉这一层包装。缺失或变动明确拒绝；随后原C3 `e9836265a7371777dca0d784fcd614a85d689267cbdf3f5e614412eb30f1dc0e`、I3 `45b2043addbc812e2e7b41426f1451187d159708ec2df14f30a7d7bc659e8284` 继续绑定其余完整表达式。

M3入口／说明／helper、宗主工厂不是此检查器的输入，未新增忽略规则。业务源码、69／87保护合同均未改动。

外置候选原脚本一次验证 exit0：50个既有案例与19个 guard-removal mutant通过。另11个有界错误变化检查 exit0：9个错误phase2形状被有限逆投影拒绝，2个无关I3/C3条件修改被原指纹拒绝。上述均SOURCE_ONLY，不是实际CI重跑或实机能力通过。

原件及候选为：

- `SOURCE.actual.json`：2621 bytes，SHA `360a09b277ab0622d4dfbb58e65c37fb6745ac338d3d5b818258b9f6feadf354`。
- 候选检查器：18913 bytes，SHA `1625a63e6324a83f393bcbf5577920c0286e2b3cc5344efd3d7acc3ba870a5e6`。
- `candidate.patch`：3608 bytes，SHA `fb3fdad95e295afbf27274f81166d8b91b77145185ddb28e0379d1abb1577849`。
- `PREVIEW.actual.json`：9828 bytes，SHA `3dce164bf853a9abf7afd6e295c3ebde094e30b5945bff2d066ebee16d7762c7`。
- `BOUNDED-MUTANTS.actual.json`：1926 bytes，SHA `a9bb5f47111fcd5017d424d82dccd2245ebfa23aa9b9d0722aac850111562221`。
- `INTEGRATION-MANIFEST.json`：2579 bytes，SHA `0916caf227ae20fc720e52d4142f1f0bc8062e2bf6b6354408d07ed59fe27f18`。

包根目录是 `C:/workspace/ck3_lyd_runtime_20261004/preview-phase2-finite-inverse-ci-fix-20261008-001`。ROOT 已审阅该patch，选复用50／19回执，不重复同结论验证；后续只由ROOT应用一个test文件、保全永久事实文档并commit/push。应用、下一canonical HEAD、CI重跑和实机结果在作者封存时均未发生，保持NULL。没有main、SDK、body、游戏、进程、桌面或总线操作。
