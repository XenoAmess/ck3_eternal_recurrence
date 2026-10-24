# CK3 存档中的零值与死亡角色变量

观察机器：`desktop-3fevhd2-1c74096080`；观察时间：`2026-10-23T17:33:10Z`。游戏为 1.20.0.4 / build 25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。

R0025 的实际 SAVE 与独立解码表明，下列状态必须分开：

| 保存形态 | 本次实际含义 | 验证方式 |
| --- | --- | --- |
| 变量条目存在，`type=value`，省略 `identity` | 数值默认 0 | 保留条目存在及省略编码的事实，再按格式解码为整数 0。 |
| 死亡角色只有 `dead_data`，没有变量条目 | 变量缺失 | 不构造 0，不要求死亡角色保留生前变量。 |
| 字段显式为 `null` 或伙伴列表为空 | 不等同于字段缺失 | JSON 合同分别编码、验证和往返比较。 |

这次证据包含 11 个在世角色的默认零值和 1 个死亡角色的缺失变量；不是对所有死亡路径或其他 build 的保证。旧夹具把死亡角色的缺失变量要求为零，导致前置检查失败，尚未执行月度业务。修正后的夹具仍保留完整前置条件，并逐项输出诊断。

精简原始角色样本与真实解析回归在 [testdata](../mod_superman_qiang/tools/testdata/natural_simulation_r0025/manifest.json)；原 SAVE、解码 SHA、角色身份和失败边界见[实际发现](../mod_superman_qiang/docs/2026-10-24-natural-fixture-native-findings.json)。读取角色块时也必须支持这次实际出现的顶层死亡记录，不能只搜索在世角色所在的嵌套层级。

本记录保留格式与夹具结论；原始证据按通用策略在 2026-11-22 复核，记录在 2027-04-21 复核。保存成功、脚本 PASS 日志和冷重载是独立证据；本次失败存档不能取得月度计次或冷重载通过资格。

2026-10-23T18:24:30Z 的后继 R0026 又证明，同一 build 的死亡角色 scope 对 `has_variable` 报 `This scope doesn't support variables`；外围 `NOT` 仍可能使后续日志打印 OK。不能把这种带脚本错误的 OK 当作变量缺失证明。死亡状态可在原生脚本检查，变量缺失继续由独立存档读回验证。R0026 仍未进入月度业务，另有不育前置条件及共享暂停读回失败。

## 2026-10-24：R5 的 Rakaly 字段路径与有界选中读回

机器 `desktop-3fevhd2-1c74096080`；实读时间 `2026-10-24T15:15:44Z–15:19:30Z`（UTC）。CK3 `1.20.0.4 / build 25734779`，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；Rakaly `0.8.19`，6,552,576 B，SHA-256 `e154af990aaed2c2f44284946772188c9749ad3f6b641b41f6c23456a6f1633d`。这是本机该 EXE、decoder 和保存对的实证，不能推广到其他 build 或 token 表。

R5 为 `desktop-3fevhd2-1c74096080--dynastic-esotericism--R0005`。[原生对应](/C:/ck3-dynastic-esotericism-20261024/common-runtime-a07/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0005/operator-evidence/root-initial-context-a01.actual.json)的 `root-initial-religion` 明确玩家 31254、Rite 0、Faith 13、Faith main Rite 0；保存中的原字段为：

| 原保存路径 | 本次值与对应 |
| --- | --- |
| `living/31254/jens_179` | `0`，与原生玩家 Rite 0 相同；选中角色 58474 的该原字段也为 0。 |
| `jens_180/database/0` | Rite 0 原块，`faith=13`、`jens_181="roman_rite"`；名称是同块原值，不据此宣布通用 ABI 字段改名。 |
| `faiths/database/13/jens_184` | `0`，与原生 Faith main Rite 0 相同。 |
| `living/31254/dynasty_house` | `174`；`dynasties/dynasty_house/174` 的 `dynasty=174`、`head_of_house=31254`；`dynasties/dynasties/174` 的 `dynasty_head=31254`。 |

这些 `jens_*` 是该 decoder 实际输出的原 token 名。保留原路径、原 key 和 AST，再做来源明确的身份 join；不能把不存在的 `rites/database` 当作 Rite 缺失，也不能静默重命名旧 AST。

变量必须分别观察 `record.variables`、角色的 `record.alive_data.variables`、Rite 的 `record.data.variables`。输出的 `des_stored` 只指 root；`des_stored_by_owner.alive_data.variables` 与 `.data.variables` 明确父块是否存在，再区分变量 owner、缺失、空 data/list。本次 actor 的 `des_test_*` 位于 alive_data；只查 root 会漏报。原 `des_test_source_rite` 条目为 `{ type=jens_179 }`，缺 `identity`：保留缺失，不把此前仅对 `type=value` 证实的默认零规则套到此 scope 类型；角色直接字段与原生 Rite 0 是另一条身份依据。

取消前后各选 6 条：角色 31254/58474、Rite 0、Faith 13、House 174、Dynasty 174。后五条原 AST SHA 相同；actor 原 SHA 不同，仅 `alive_data.variables.data` 中 20 个唯一 flag 的行顺序变化，逐 flag 完整原 row 相同。只对这个已验证唯一键的命名变量集合按 flag 排序比较，随后整 actor AST 相等；保留两份原 AST/SHA，不能推广为任意列表、重复 key 或游戏语义顺序均可排序。两档所选身份与 DES owner 读回相等，原 Rite/House/Dynasty 无绑定变量，Rite 0 的 `data.doctrine` 仍含 `des_doctrine_none`。

SDK checkpoint 原路径始终为 `attempt-a08/state/profile/save games/xar_checkpoint.ck3`。取消前 68,611,338 B / SHA `6b3c84d9baa9195ad9d156cb1818c633d13af8fff1f40895c8051f2e9cf57cea`；取消后 68,614,732 B / SHA `d0d6cedf615333a1785a9459d7a4575cd7cfd3631409ed87edeaa4515b1821a3`。先核实际 SDK producer 的 checkpoint path/size/SHA，再核 `original_SDK_pin → retained_exact_copy` custody，持副本只读锁计算 SHA，保存副本 FileID/mtime 前后一致证据。原 pin 不改成 copy 路径，copy 物理身份不冒原件；本次没有重开已覆盖的 original。用 `--save <copy> --expected-pin <原SDK-pin> --preserved-copy <custody>`；custody 含 machine_id/original_SDK_pin/retained_exact_copy，唯一可选字段 observed_at_utc 须带时区。

方法复用 `melt_projection/melt_tokens` 的 stdout 流，仅保留选中块，单块 ≤512 KiB、合计 ≤4 MiB、输出 ≤16 MiB；每档仅 17,162 B 选中 tokens，完整消费约 100 MB 解码流，decoder 均 exit0，无完整 melt 文件或 world AST。source pins（完整路径见证据索引）：`campaign_score_save_reader.py=ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e`，`i3b_checkpoint_reader.py=eb68af08c5d636e4b91caa4e0290bb889ae912ca5b7e0158f4e4d99f85958736`，`bounded_save_parser.py=12bae20f113f57e144fb422fbac2b53b8cbd5fce2ae92cb9d09f779c123f4489`，`save_fields.py=f23f4901f44c0aa015332256f9de02ede9006d66e59a2c2ec30fbdd752ab4933`。

[最终外置 a07 helper](/C:/ck3-dynastic-esotericism-20261024/observe-selected-save-a07.py) SHA `2a407ccaee4aadbadf9f9a53f7917fcb111b7e1b2eccc95532a5eaad0557e846`；[证据索引与比较 proof](/C:/ck3-dynastic-esotericism-20261024/R5-save-path-observation-a01/FINAL.actual.json) SHA `ba6795dceac10a60e768647facf6362dafac7096c32d8e6fea6f8e3a52a437ad`。[a06 原 RED](/C:/ck3-dynastic-esotericism-20261024/common-runtime-a07/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0005/operator-evidence/before-cancel-a06-decoder-tool-red.json)忠实记录 Root 观察到的 exec4984 exit1/原异常，不冒充原 subprocess receipt；原因是旧 selector 只认 rites 根。[a07 首次 after metadata RED](/C:/ck3-dynastic-esotericism-20261024/R5-save-path-observation-a01/after-cancel-a07.stderr.log)为误拒合法 observed_at_utc；v1 源保留，v2 显式允许并验该字段，解码选择逻辑未变，after 实读 exit0。

**R5 整体仍为 0/6，未合格**，见[原六项判定](/C:/ck3-dynastic-esotericism-20261024/common-runtime-a07/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0005/case-output/actual-default-cancel-and-create-ui-root-result.json)。本次只证明取消前后这六条保存记录的局部身份/无绑定后态；不能外推创建、完整功能矩阵、冷重载、正常闭场或发布通过。此次追加未重测，也未修改共享生产模块或冻结 runtime。
