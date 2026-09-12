# “自动升级建筑”二期开发清单与验收记录

状态：**二期实现、静态全量验收与抽样 CK3 实机验收已完成；Workshop 发布尚未开始**

候选版本：`2.0.0`

产品目录：`mod_auto_upgrade_buildings/`

Steam Workshop item：`3800124956`

研究基线：CK3 `1.19.0.6 (Scribe)`、当前维护版 `1.19.0`

## 1. 二期唯一目标

玩家直接持有的所有**已有且存在下一等级**的原版省份地产建筑都可以自动升级，包括：

- 城堡、城市、神殿、部落和曼荼罗神殿城塞的地产主建筑；
- 普通封建建筑、普通部落建筑和神殿城塞独有建筑；
- 公国建筑；
- 仍使用普通建筑升级流程的特殊建筑。

二期继续采用一期的即时升级语义：定期扫描符合条件的已有建筑，成功时扣费一次并立即升级一级。**不实现原版施工队列、施工进度条、取消或退款流程。**

## 2. 明确排除范围

- **所有住所系统**：冒险者营地、行政庄园、游牧毡帐、东亚庄园和日本庄园。
- **曼荼罗都城 `mandala_capital_01 → 05`**：这四条边属于 Great Project，不走普通建筑升级流程。
- 自动填充空建筑槽；二期只升级已经存在的建筑。
- 没有 `next_building` 的终级建筑。
- 任意第三方 Mod 新增建筑；以后只能通过显式兼容适配另行支持。

原版 `nomad_holding` 与 `herder_holding` 带 `no_buildings` 参数，其主建筑也没有下一等级，因此二期在这两类省份地产中没有可升级对象。正确行为是 N/A 和零副作用，不能用住所建筑替代，也不能凭空添加省份建筑。

## 3. 可行性结论

| 子目标 | 结论 | 依据 |
| --- | --- | --- |
| 全量发现普通省份建筑升级边 | **可行性高** | 原版定义可以在构建时完整解析并冻结 |
| 主建筑、部落、神殿城塞、公国和特殊建筑即时升级 | **已实现并实机通过** | 普通／主／公国建筑使用原生 `upgrade_building_effect`；特殊槽使用显式替换与失败回滚；均在成功后扣费 |
| 纯 Workshop 数据 Mod 交付 | **可行性高** | 不再依赖真人玩家施工 command、native bridge 或外置 companion |
| 与未来 CK3 版本同步 | **可控** | 生成器绑定游戏版本和输入哈希，版本变化时以 inventory diff 阻止静默漂移 |

总体判断：二期已完成为一个**全量数据提取、确定性生成和分类验收项目**。资格门槛由生成器从 exact 原版定义投影；普通槽使用引擎原生的即时升级 effect，避免直接添加目标建筑时丢失原版完成上下文。

## 4. CK3 1.19.0.6 冻结清单

本机原版 `game/common/buildings/*.txt` 包含 981 个建筑定义和 609 条 `next_building` 边：

| 类型 | 原版边数 | 二期状态 |
| --- | ---: | --- |
| 普通 `regular` | 370 | 包含 |
| 特殊 `special` | 205 | 包含 |
| 公国首府 `duchy_capital` | 30 | 包含 |
| Great Building／Great Project | 4 | 排除 |
| **合计** | **609** | **包含 605，排除 4** |

605 条二期目标边中包括：

- 13 条地产主建筑边：城堡、城市、神殿和神殿城塞各 3 条，部落 1 条；
- 神殿城塞的 `citadel_shrine`、`sacred_pool`、`vihara_halls` 共 21 条独有普通升级边；
- 费用形状为 588 条 `cost_gold`、5 条 `cost_gold + cost_prestige`、3 条 `cost_gold + cost_piety`、9 条完整 `scripted cost`；
- 601 个目标带至少一种原版建造资格门槛，另外 4 个目标没有同类 gate。

一期基线只冻结 43 条建筑链、生成 301 条升级边。二期已替换为 165 条链、605 条适用边，并取消只接受城堡／城市／神殿地产的范围限制。

## 5. 实现原则

1. **构建时生成，运行时不猜。** 生成器解析 exact CK3 建筑定义，产出带来源、类型、费用和门槛元数据的 605 边清单，再生成 Clausewitz dispatcher。
2. **仍然即时升级。** 400 条普通／主／公国边使用 `upgrade_building_effect = <source tier>`；205 条特殊边使用“移除源建筑、添加目标特殊建筑、失败则恢复源建筑”。两条路径都只在目标出现后扣费，不建立施工对象。
3. **一次轮询每条建筑链最多一级。** 继续使用互斥 `if/else_if`，不允许一轮跨越多个等级。
4. **与人工施工互不覆盖。** province 已有 ongoing construction 时整地产跳过，即使二期本身不创建施工队列。
5. **Great Project 硬排除。** 任何 `type = great_building` 或通过 `great_project_type` 升级的目标都不得进入 dispatcher。
6. **费用按原版定义分类。** 不再把所有目标压成 cheap/normal/expensive 三档；金币、威望、虔诚和 scripted cost 分别生成并验证。
7. **资格条件必须有证据。** 生成器投影 601 个目标的原版 gate，另外 4 个目标按原版无 gate；不依靠一期 43 链的手写近似表。
8. **旧存档入口保持稳定。** 保留 `enable_auto_build`、`auto_build.0003/.0004` 和唯一全局循环合同。

## 6. 二期开发清单

### P0：即时升级语义原型

- [x] 冻结 exact CK3 1.19.0.6 的建筑 schema、21 个原版建筑文件、holding 定义和版本哈希。
- [x] 用普通建筑、主建筑、公国建筑和特殊建筑验证即时升级路径；普通槽最终采用原生 `upgrade_building_effect`，特殊槽采用替换与回滚。
- [x] 验证合法目标升级一级、原版 gate 拒绝非法目标、成功后只扣一次、资金不足时零副作用。
- [x] 验证金币、金币加威望、金币加虔诚和 scripted cost 四种费用形状的支付路径。
- [x] 验证 `type = great_building` 的四条边不会进入候选或扣费。
- [x] 冻结 P0 结论：完整 gate 由生成器显式投影，实际替换仍交给对应的引擎建筑 effect。

### P1：建筑图谱和生成器

- [x] 新增嵌套 Clausewitz 建筑定义解析器；不使用正则逐行近似识别顶层节点。
- [x] 生成 981 定义／609 原版边 inventory，并投影二期 605 边 allowlist 与 4 边 exclusion list。
- [x] 校验所有源和目标存在、升级图无环、类型已知、费用形状已知、Great Project 零泄漏。
- [x] 按 regular、special、duchy-capital 和 primary-building 标签生成 dispatcher。
- [x] 保存 23 个 exact 输入的 SHA-256 和 CK3 版本；版本升级时强制审阅 inventory diff。
- [x] `tools/auto_upgrade_buildings_data.py` 改为读取冻结 inventory，43 链手写表不再是第二权威源。
- [x] 生成文件保留 `GENERATED FILE. DO NOT EDIT.` 标记，并由 `--check` 验证逐字节一致。

### P2：运行时 dispatcher

- [x] 放开 `auto_build.0004` 对部落和神殿城塞的合理遍历，同时保留未出租、玩家直辖和无在建项目门槛。
- [x] 覆盖五种有可升级主建筑的 holding：castle、city、church、tribal、temple-citadel。
- [x] 覆盖 370 条 regular、30 条 duchy-capital 和 205 条 special 边。
- [x] 对 nomad/herder holding 明确零候选、零扣费，不把 Domicile 纳入扫描。
- [x] 每条链一次轮询最多升级一级；不同建筑链继续按冻结顺序独立判断。
- [x] 先验证目标升级成功，再执行一次对应费用扣除；失败分支不得改变任何资源。
- [x] 国库／个人金钱选择保持一期兼容；威望、虔诚和 scripted cost 使用冻结的付款人资源路径。
- [x] 保留启用、禁用、读档和循环去重语义。

### P3：设置、反馈与兼容

- [x] 默认启用主建筑、普通、部落、公国和特殊建筑升级；本期不增加分类开关。
- [ ] 玩家查看最近一次升级／拒绝原因的 UI：本期未实现，也不是最小二期目标；验收 marker 不进入 production staging。
- [x] 旧存档无需重新点击启用；升级前后的公开 flag/event ID 保持兼容。
- [x] 其他 Mod 增加未知建筑时安全跳过，不对未知费用或类型猜测扣款。

### P4：静态全量验收

- [x] 对 **全部 605 条二期边**逐条校验：源、目标、类型、费用、dispatcher 分支和一级升级关系。
- [x] 对全部 4 条 Great Project 边逐条校验：只存在于 exclusion list，生产 dispatcher 中为零。
- [x] 校验 13 条主建筑边、21 条神殿城塞独有边、30 条公国边、205 条特殊边计数不漂移。
- [x] 校验四种费用形状的总数为 `588 + 5 + 3 + 9 = 605`。
- [x] 校验生成可重复、未定义 key、括号／作用域、本地化、15 文件 release allowlist、manifest 和 deterministic ZIP。
- [x] 静态拒绝 production 中的 Domicile effect、Great Project 自动推进逻辑和原版施工队列／native companion 依赖。

### P5：抽样实机验收

实机不逐条运行 605 个建筑 key。所有边的完整性由 P4 保证；P5 只验证不同运行机制的代表样本，并尽量在同一 CK3 进程中串行完成。

- [x] 五种主建筑各取一条：castle、city、church、tribal、temple-citadel。
- [x] 普通封建、普通部落和神殿城塞独有建筑各取一条。
- [x] 公国建筑成功样本一条，并以普通建筑地形 gate 拒绝样本验证生成 gate 的负路径。
- [x] 特殊建筑覆盖普通金币和 scripted cost；复合资源覆盖金币加威望、金币加虔诚和 scripted cost。
- [x] 全部 4 条 Great Project 以生产 dispatcher 零存在的静态证据验收，不伪造普通建筑实机场景。
- [x] nomad/herder 组合 N/A 样本证明无候选、无扣费。
- [x] 横切实机验证资金不足、同轮最多一级、禁用／重新启用、国库优先和个人金币回退；无在建项目门槛、终级边不存在及旧公开循环合同由静态门禁和一期回归证据覆盖。
- [x] 使用 exact 15 文件 production projection、外置 fixture 和一次性 `-userdir`；正式轮次为 `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0024`。

最终在一次 R0024 受控矩阵中完成 17 个功能断言。所有 605 条边的完整性由静态全量检查承担，不为名称不同但逻辑相同的建筑重复启动游戏。

### P6：发布收口

- [x] 更新 README、Workshop BBCode 和九语玩家可见范围说明，明确即时升级、住所排除和 Great Project 排除。
- [x] 构建 release-candidate staging、manifest 和 deterministic ZIP；canonical `descriptor.mod` 不含 `remote_file_id`。
- [ ] 更新同一 Workshop item `3800124956`，下载订阅缓存并逐字节复核。
- [ ] 上传成功后写入 `docs/release-changelogs/auto-upgrade-buildings/<version>.md`。
- [ ] 提交并推送 exact release commit/tag/changelog；恢复 Steam 离线模式。

## 7. 工时评估

以下是开工前估算，保留用于复盘；实际实现发现直接 `add_building` 会丢失部分原版完成上下文，因此切换到原生 `upgrade_building_effect`，没有把原版施工进度纳入范围：

| 工作包 | 预计工时 |
| --- | ---: |
| P0 语义原型与费用路径 | 1.5–2 小时 |
| P1 图谱解析与生成器 | 2.5–3.5 小时 |
| P2/P3 运行时与兼容 | 1.5–2 小时 |
| P4 静态全量验收与构建 | 1–1.5 小时 |
| P5 抽样实机矩阵 | 1.5–2.5 小时 |
| 文档与 release candidate 收口 | 0.5–1 小时 |
| **合计** | **约 8–12 小时** |

最终生成器完整投影了 601 组资格条件，并以冻结 inventory 和生成校验控制复杂度。Workshop 正式上传仍不计入上述开发工时；取得明确发布授权且 Steam 可以上线后，发布、fresh-cache 复核和 changelog 另行执行。

## 8. 完成标准

“实现与验收完成”和“公开发布完成”分开记账：

1. 605 条适用边静态全量通过，4 条 Great Project 边生产零泄漏。
2. 抽样实机覆盖五种适用 holding、三类建筑、四类费用路径和代表性拒绝条件，而不是逐建筑 key 重复跑。
3. 每个成功目标只升一级、只扣一次；原版 gate、资金不足和 nomad/herder 均零副作用；在建、终级与 Great Project 由静态生产边界保证。
4. 住所、原版施工进度和 native companion 均不进入二期实现或公开声明。
5. 保存／重载、禁用／启用和重复轮询不产生双扣款、重复循环或瞬间跨级。
6. 前五项已完成，因此二期代码为 implementation-complete；正式 staging、Workshop 更新、订阅缓存复核与相对上一版本 changelog 全部完成后，才算 release-complete。

## 9. 证据来源与边界

静态权威输入与实现：

- 当前 Mod：`tools/auto_upgrade_buildings_data.py`、`tools/gen_auto_upgrade_buildings.py`、`mod_auto_upgrade_buildings/events/auto_build.txt`。
- 原版 schema：`game/common/buildings/_buildings.info`、`game/common/holdings/_holdings.info`。
- 原版数据：`game/common/buildings/*.txt`、`game/common/holdings/00_holdings.txt`。

- 静态检查：`extract_auto_upgrade_buildings.py --check`、`validate_auto_upgrade_buildings_static.py`、构建器 7 个单测和 `build_auto_upgrade_buildings_release.py --check` 均 GREEN。
- 正式实机：`desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0024`，artifact 为 `D:\workspace\ck3_auto_upgrade_runtime\phase2-live-r10-20260912`。
- R0024 在 CK3 1.19.0.6 中通过 17 个功能断言；34 条 fixture marker、项目诊断 0、生产树 SHA-256 `116795FA60632F0ED247B2D3B88D162F2E37A1EBF9E92DEC109A76E1D539FDAF`，运行树、源树和真实用户存储均未变化，一次性 userdir 已删除，CK3 受控退出。
- 报告 SHA-256 `BCE9485277FADBB507C83998824FC346E7EEBB737B459A19F358E71BC59F49BB`；最终暂停画面 SHA-256 `34EBFA20155014FF537FEB02243D72CD75FF7259F54C421B1A852AD676BE388C`。
- R0023 已先证明 17/17 产品断言与零项目诊断，最终 RED 仅来自旧的暂停文字 OCR；R0024 改用 HUD 日期稳定性验证后正式 GREEN。更早 RED 轮次均保留，未改写为 GREEN。
- Open Kaishek 的 Java environment RED 已于 2026-09-12 解除：适配器自动解析 workspace sibling checkout 与 `JAVA_HOME`，受支持的 `synthetic-361-014` 完整 preflight 在 `0.959s` 内 GREEN。对本产品全量 source 的 parser 为 GREEN；validator/fixture 仍因未覆盖 opcode／未知 fixture 返回语义 RED，不能冒充产品语义 GREEN，也不改变 R0024 的 CK3 正式结论。
- 本轮没有上传或更新 Workshop；Steam 保持离线。
