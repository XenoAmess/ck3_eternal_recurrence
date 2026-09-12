# “自动升级建筑”二期可行性预研与开发清单

状态：**范围已冻结；开发尚未开始；未执行二期 CK3 实机验证**

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
| 主建筑、部落、神殿城塞、公国和特殊建筑即时升级 | **可行性高** | 沿用已在一期实机验证的 `add_building` + 成功后扣费模型，扩展生成范围 |
| 纯 Workshop 数据 Mod 交付 | **可行性高** | 不再依赖真人玩家施工 command、native bridge 或外置 companion |
| 与未来 CK3 版本同步 | **可控** | 生成器绑定游戏版本和输入哈希，版本变化时以 inventory diff 阻止静默漂移 |

总体判断：二期已从“需要逆向原版施工命令”的高不确定项目，收敛为一个**全量数据提取、生成和分类验收项目**。主要风险是特殊费用、复杂资格条件和类型排除，不是引擎接口。

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

现版只冻结 43 条建筑链、生成 301 条升级边。二期需要新增 304 条普通流程升级边，并取消现版只接受城堡／城市／神殿地产的范围限制。

## 5. 实现原则

1. **构建时生成，运行时不猜。** 生成器解析 exact CK3 建筑定义，产出带来源、类型、费用和门槛元数据的 605 边清单，再生成 Clausewitz dispatcher。
2. **仍然即时升级。** 每个成功分支继续使用 `add_building = <next tier>`；确认目标建筑出现后才扣费，不建立施工对象。
3. **一次轮询每条建筑链最多一级。** 继续使用互斥 `if/else_if`，不允许一轮跨越多个等级。
4. **与人工施工互不覆盖。** province 已有 ongoing construction 时整地产跳过，即使二期本身不创建施工队列。
5. **Great Project 硬排除。** 任何 `type = great_building` 或通过 `great_project_type` 升级的目标都不得进入 dispatcher。
6. **费用按原版定义分类。** 不再把所有目标压成 cheap/normal/expensive 三档；金币、威望、虔诚和 scripted cost 分别生成并验证。
7. **资格条件必须有证据。** 先用最小原型确认 `add_building` 是否自行拒绝非法升级；若会绕过 gate，则由生成器投影必要条件，不能继续依靠 43 链的手写近似表。
8. **旧存档入口保持稳定。** 保留 `enable_auto_build`、`auto_build.0003/.0004` 和唯一全局循环合同。

## 6. 二期开发清单

### P0：即时升级语义原型

- [ ] 冻结 exact CK3 1.19.0.6 的建筑 schema、21 个原版建筑文件和版本哈希。
- [ ] 用普通建筑、主建筑、公国建筑和特殊建筑各做一条最小 `add_building` 原型。
- [ ] 验证合法目标能升级一级、非法目标是否被引擎拒绝、成功后只扣一次、失败时零扣费。
- [ ] 验证金币、金币加威望、金币加虔诚和 scripted cost 四种费用形状的支付路径。
- [ ] 验证 `type = great_building` 的四条边不会进入候选或扣费。
- [ ] 冻结 P0 结论：哪些 gate 由引擎执行，哪些必须由生成器显式投影。

### P1：建筑图谱和生成器

- [ ] 新增嵌套 Clausewitz 建筑定义解析器；禁止用正则逐行近似识别顶层节点。
- [ ] 生成 981 定义／609 原版边 inventory，并投影二期 605 边 allowlist 与 4 边 exclusion list。
- [ ] 校验所有源和目标存在、升级图无环、类型已知、费用形状已知、Great Project 零泄漏。
- [ ] 按 regular、special、duchy-capital 和 primary-building 标签生成 dispatcher。
- [ ] 保存输入文件哈希和 CK3 版本；版本升级时强制审阅新增、删除和变更边。
- [ ] 将 `tools/auto_upgrade_buildings_data.py` 的 43 链手写表迁移为生成结果或明确废弃，禁止两个权威来源并存。
- [ ] 生成文件保留 `GENERATED FILE. DO NOT EDIT.` 标记，并由 `--check` 验证逐字节一致。

### P2：运行时 dispatcher

- [ ] 放开 `auto_build.0004` 对部落和神殿城塞的合理遍历，同时保留未出租、玩家直辖和无在建项目门槛。
- [ ] 覆盖五种有可升级主建筑的 holding：castle、city、church、tribal、temple-citadel。
- [ ] 覆盖 370 条 regular、30 条 duchy-capital 和 205 条 special 边。
- [ ] 对 nomad/herder holding 明确零候选、零扣费，不把 Domicile 纳入扫描。
- [ ] 每条链一次轮询最多升级一级；不同建筑链继续按冻结顺序独立判断。
- [ ] 先验证目标升级成功，再执行一次对应费用扣除；失败分支不得改变任何资源。
- [ ] 国库／个人金钱选择保持一期兼容，威望、虔诚和 scripted cost 的付款人及资源来源另行冻结。
- [ ] 保留启用、禁用、读档和循环去重语义。

### P3：设置、反馈与兼容

- [ ] 默认启用主建筑、普通、部落、公国和特殊建筑升级；是否需要分类开关以最小实现为准，不为本期强行增加复杂 UI。
- [ ] 玩家可查看最近一次升级或拒绝的简要原因；验收 marker 不进入 production staging。
- [ ] 旧存档无需重新点击启用；升级前后的公开 flag/event ID 保持兼容。
- [ ] 其他 Mod 增加未知建筑时安全跳过，不对未知费用或类型猜测扣款。

### P4：静态全量验收

- [ ] 对 **全部 605 条二期边**逐条校验：源、目标、类型、费用、dispatcher 分支和一级升级关系。
- [ ] 对全部 4 条 Great Project 边逐条校验：只存在于 exclusion list，生产 dispatcher 中为零。
- [ ] 校验 13 条主建筑边、21 条神殿城塞独有边、30 条公国边、205 条特殊边计数不漂移。
- [ ] 校验四种费用形状的总数为 `588 + 5 + 3 + 9 = 605`。
- [ ] 校验生成可重复、未定义 key、括号／作用域、本地化、release allowlist、manifest 和 deterministic ZIP。
- [ ] 静态拒绝 production 中的 Domicile effect、Great Project 自动推进逻辑和原版施工队列／native companion 依赖。

### P5：抽样实机验收

实机不逐条运行 605 个建筑 key。所有边的完整性由 P4 保证；P5 只验证不同运行机制的代表样本，并尽量在同一 CK3 进程中串行完成。

- [ ] 五种主建筑各取一条：castle、city、church、tribal、temple-citadel。
- [ ] 普通封建建筑取一条，验证一期兼容路径。
- [ ] 普通部落建筑取一条，验证部落 holding 与复合资源。
- [ ] 神殿城塞独有建筑取一条。
- [ ] 公国建筑取一条成功样本和一条非公国首府拒绝样本。
- [ ] 特殊建筑至少取三条，覆盖普通金币、金币加虔诚和特殊地点／文化门槛；scripted cost 另取一条。
- [ ] Great Project 取一条排除样本，证明无升级、无扣费。
- [ ] nomad/herder 各取一个 N/A 样本，证明无候选、无扣费。
- [ ] 横切验证资金不足、已有施工、终级建筑、同轮最多一级、禁用／重新启用和保存／重载。
- [ ] 使用 production projection、外置 fixture 和一次性 `-userdir`；启动前按机器／mod 分配新实机编号。

预计约 14–18 个实机场景，但不是 14–18 次 CK3 启动；目标是在一轮受控矩阵中批量完成。只有新的机制分支或失败证据才增加样本，不为名称不同但逻辑相同的建筑重复验收。

### P6：发布收口

- [ ] 更新 README、Workshop BBCode 和九语玩家可见范围说明，明确即时升级、住所排除和 Great Project 排除。
- [ ] 构建正式 staging、manifest 和 ZIP；canonical `descriptor.mod` 不含 `remote_file_id`。
- [ ] 更新同一 Workshop item `3800124956`，下载订阅缓存并逐字节复核。
- [ ] 上传成功后写入 `docs/release-changelogs/auto-upgrade-buildings/<version>.md`。
- [ ] 提交并推送 exact release commit/tag/changelog；恢复 Steam 离线模式。

## 7. 工时评估

在 CK3 1.19.0.6 不再变化、无需兼容第三方建筑、P0 未发现 `add_building` 绕过关键 gate 的新问题时：

| 工作包 | 预计工时 |
| --- | ---: |
| P0 语义原型与费用路径 | 1.5–2 小时 |
| P1 图谱解析与生成器 | 2.5–3.5 小时 |
| P2/P3 运行时与兼容 | 1.5–2 小时 |
| P4 静态全量验收与构建 | 1–1.5 小时 |
| P5 抽样实机矩阵 | 1.5–2.5 小时 |
| 文档与 release candidate 收口 | 0.5–1 小时 |
| **合计** | **约 8–12 小时** |

如果 P0 证明 `add_building` 会绕过大量复杂原版 gate，需要生成器完整投影 601 组资格条件，则增加约 4–8 小时。Workshop 正式上传不计入上述开发工时；取得明确发布授权且 Steam 可以上线后，发布、fresh-cache 复核和 changelog 预计另需 1–2 小时。

## 8. 完成标准

二期只有同时满足以下条件才能标记完成：

1. 605 条适用边静态全量通过，4 条 Great Project 边生产零泄漏。
2. 抽样实机覆盖每种 holding、建筑类别、费用形状和关键拒绝条件，而不是逐建筑 key 重复跑。
3. 每个成功目标只升一级、只扣一次；非法目标、资金不足、在建、终级、nomad/herder 和 Great Project 均零副作用。
4. 住所、原版施工进度和 native companion 均不进入二期实现或公开声明。
5. 保存／重载、禁用／启用和重复轮询不产生双扣款、重复循环或瞬间跨级。
6. 正式 staging、Workshop 更新、订阅缓存复核与相对上一版本 changelog 全部完成后，才算发布完成。

## 9. 证据来源与边界

本次预研和范围修订只使用本地静态证据，没有启动 CK3，也没有改变 Steam 离线状态：

- 当前 Mod：`tools/auto_upgrade_buildings_data.py`、`tools/gen_auto_upgrade_buildings.py`、`mod_auto_upgrade_buildings/events/auto_build.txt`。
- 原版 schema：`game/common/buildings/_buildings.info`、`game/common/holdings/_holdings.info`。
- 原版数据：`game/common/buildings/*.txt`、`game/common/holdings/00_holdings.txt`。

清单计数是 CK3 1.19.0.6 的静态冻结基线，不代表二期已经实现，也不代表 P0 或抽样实机矩阵已经 GREEN。
