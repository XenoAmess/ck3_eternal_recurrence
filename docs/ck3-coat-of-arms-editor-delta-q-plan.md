# CK3 家徽编辑器 Delta-Q / 拟合质量 2.0 计划

> 状态：`in-progress`（2026-09-21）
>
> 起始基线：`master` `4b90191c9e47680378c4d7a200aa2b389df0f1f6`
>
> 产品目录：`coat_of_arms_editer_of_ck3/`
>
> 前置阶段：[Gamma / 1.0 收口计划](ck3-coat-of-arms-editor-gamma-plan.md)的 G0–G5 已全部通过。

## 1. 唯一目标

Delta-Q 只优化图片到 CK3 家徽的拟合质量：在相同实例预算和可比时间预算下，让浏览器完整 DDS 预览与 CK3 原生 framebuffer 更接近输入图。战役内编辑、角色/头衔家徽、后端、账号、云同步和其他外围能力不进入本期。

本期不把“提高搜索预算”“更换一个自我偏好的评分公式”或“浏览器预览更好看”单独视为质量提升。通过声明必须同时绑定输入、素材包、算法 revision、完整 DDS、候选源码、浏览器指标和原生证据。

## 2. 已知基线与瓶颈

- v14 七图在 1,024 实例预算下的质量优先结果为 `0.006149..0.047678` total loss，其中五图使用 1,024 或接近 1,024 个实例，源码约 355–404 KiB。
- 当前搜索损失是 alpha 加权的 RGB 均方误差与相邻亮度梯度误差，固定组合为 `0.62 * color + 0.38 * edge`。它没有直接度量轮廓距离、连通结构、主体重心或多尺度布局。
- 语义候选使用 18 维形状描述符和很窄的 beam；v14 只有三张质量优先结果实际选择了非 tile 原生 DDS。
- 语义路径不够好时，单前向 tile painter 会消费大部分实例预算修补残差。v15 的事后固定点剪枝只能删除 3.33% 实例，不能代替更好的搜索。
- 完整 DDS/mip 复评发生在候选尾端；v15 发现 21 个候选中 14 个历史搜索指标与完整 DDS 重渲染存在漂移。

权威基线：

- [v14 七图 1,024 预算与 Pareto 候选](coat-of-arms-fit-artifacts/user-picture-corpus-v14-pareto-budget-1024/README.md)
- [v14 CK3 原生 A/B](coat-of-arms-fit-artifacts/user-picture-corpus-v14-native-r18/README.md)
- [v15 完整 DDS 零退化剪枝](coat-of-arms-fit-artifacts/user-picture-corpus-v15-pruned-budget-1024/README.md)

## 3. 不变约束

- 正式站点继续是纯前端；图片、项目和拟合状态不上传，不连接 CK3、MCP、Java、Python 或本地后端。
- 所有新搜索保持确定性；相同输入、素材包、配置和算法 revision 必须产生相同候选源码与报告 hash。
- 旧 color/edge/total 指标永久保留为回归维度。新感知指标在完成校准前只运行 shadow mode，不参与选优。
- 搜索质量、结构复杂度、源码体积和运行时间分别报告；不得把复杂度惩罚混进视觉分数后隐藏取舍。
- 调优集和 holdout 严格分开。holdout 的目标、期望和 hash 冻结后，不得为消除 RED 修改样本或门限。
- CK3 原生验收继续使用 Steam 离线、exact `1.19.0.6`、结构化 MCP、无 OCR/键鼠/固定坐标路径。

## 4. 质量基准与通过门限

### 4.1 数据集

1. 真实集：现有七张用户图片，固定执行 128 与 1,024 实例预算；10,000 只做压力与收益饱和分析。
2. 合成集：以冻结 seed 从已授权的 exact-build 素材包生成 256 个已知源码样本；192 个用于开发，64 个作为 hash-frozen holdout。
3. 扰动集：对 holdout 真值执行有序的颜色、位置、缩放、旋转、层序、缺层和错误素材扰动，用于验证新指标的单调性与素材召回率。

### 4.2 总体验收

- 七图 1,024 预算的旧 total loss 与 edge loss 7/7 不劣于 v14 质量优先基线。
- 校准后的感知指标中位数相对 v14 改善至少 15%；任何单图不得退化超过 2%。
- 合成 holdout 的正确素材 Top-8 recall 至少 85%，Top-32 recall 至少 95%。
- 1,024 预算仍是硬上限；实例数和源码体积作为 Pareto 维度公开，不允许通过越界换质量。
- 七图总运行时间不超过 v14 同机基线 14.1 分钟的 1.25 倍；更换机器时同时报告绝对时间与候选数，不伪造横向速度结论。
- 七图质量优先候选全部通过完整 DDS、parse/serialize、Apply/Copy、浏览器→CK3 与 Copy→re-Apply 原生空间像素门限。
- 生成新旧候选的匿名 A/B contact sheet；它是人工判断材料，不由自动化工具伪造“人工通过”。

## 5. 工作包

### Q0：冻结 benchmark-v1（P0，1–2 工程日）

状态：`browser-passed / v15-native-pending`（2026-09-21；[benchmark-v1](coat-of-arms-fit-artifacts/delta-q-benchmark-v1/README.md)）。

- 把七图 v14/v15 基线投影成机器可读 manifest，记录输入、候选源码、预览、指标、实例数和 SHA-256。
- 新增确定性合成语料生成器，生成 192/64 dev/holdout manifest 与扰动阶梯，不提交重复的大体积像素副本。
- 为 benchmark manifest、划分不可变性、源码往返和确定性添加单元测试。
- 补齐 v15 质量优先候选的 MCP 原生状态，不能把浏览器剪枝 GREEN 外推成 CK3 GREEN。

退出条件：benchmark 可从干净 checkout 重建；两次生成逐字节一致；所有输入和现有基线 hash 可回读。

### Q1：感知评分 v2 shadow calibration（P0，3–4 工程日，依赖 Q0）

状态：`shadow-passed`（2026-09-21；[R001–R005 与七图追加式证据](coat-of-arms-fit-artifacts/delta-q-perceptual-shadow-v1/README.md)）。

- 新增线性光颜色差异、多尺度颜色布局、双向边缘距离、主体面积/重心、连通域与孔洞结构等独立指标。
- 保持 legacy 指标不变；v2 shadow 只走确定性 CPU reference，未实现的 WebGL v2 不得伪装成一致。后续若新增 GPU v2，必须先执行 CPU 数值和排序 fail-closed 门禁。
- 在扰动阶梯上验证严重扰动不得优于轻微扰动，在真实七图上生成 shadow 报告。
- 门限和权重在允许它参与搜索前冻结；不得在真实结果出来后追调门限。

退出条件：CPU 确定性、扰动单调性和七图 shadow 报告 GREEN；搜索结果仍与基线逐字节一致。v2 晋升搜索时先在 bounded frontier 上以 CPU 完整 DDS 评分；GPU v2 不是本阶段的虚假前置条件。

实证：

- R001–R004 保留三级严格单调、语义参数扰动、周期位移和硬阈值结构权重暴露的 RED，不覆盖失败 attempt。
- R005 在 64 个 hash-frozen holdout 上 GREEN：颜色 100%、固定终点平移 96.875%、缩放 100%、旋转 100%，分别超过 98% / 90% / 85% / 75% 门限。
- 七张真实 v14 首选候选均完成 96/230/512 px 精确 DDS shadow 重算，所有维度有限、非负且重复计算逐值一致。
- 最终 v2 合同以连续的线性颜色、多尺度颜色和梯度差为主；双向轮廓、连通分量和封闭区域继续作为独立诊断。
- v2 明确保持 `shadow-only + cpu-reference`，不参与 legacy 搜索排序，也不把未实现的 GPU v2 计算冒充一致；现有 WebGL legacy scorer 继续执行 CPU 数值与排序 fail-closed。

### Q2：原生素材检索 v2（P0，3–5 工程日，依赖 Q1）

状态：`passed`（2026-09-21；[64 例 holdout 检索证据](coat-of-arms-fit-artifacts/delta-q-asset-retrieval-v2/README.md)）。

- 为 colored/textured emblem 建立离线确定性索引：alpha 距离场、Hu moments、径向/方向直方图、对称性、孔洞、连通域、长宽比和 mask 通道形状。
- 将目标残差分割为显著区域，按区域查询 Top-K；旋转、镜像和 mask 选择作为显式变换，不污染素材身份。
- 永久保留矩形、圆、菱形和楔形 primitive fallback，避免召回失败后失去安全路径。

退出条件：64 个 holdout 达到 Top-8/Top-32 门限；索引逐字节可重建；未降低现有 primitive 覆盖。

实证：

- R001 的 96 项纯不变量 shortlist 为 43.75% / 43.75%，R002 扩到 512 项仍只有 68.75% / 68.75%；失败报告追加保留。
- 最终以 6×6 旋转/镜像稀疏网格加不变量粗筛 128 项，再以 18×18 网格和有符号距离场精排，Top-8 为 93.75%，Top-32 为 96.875%。
- 检索 v2 已接入语义层与 paint 后原生形状 refinement；矩形、圆、菱形和楔形 primitive 仍由独立保留合同覆盖。

### Q3：结构感知联合搜索（P0，5–8 工程日，依赖 Q2）

状态：`structure-passed / real-corpus-performance-red`（2026-09-21；[结构门禁与真实图 RED](coat-of-arms-fit-artifacts/delta-q-structure-search-v1/README.md)）。

- 先估计 pattern、主色和大面积分区，再为各显著区域生成素材、颜色、mask、位置、缩放、旋转和层序假设。
- 使用确定性多起点局部优化；同时保留视觉质量、边缘质量和低复杂度 Pareto 前沿。
- 图层顺序进入搜索；每个阶段在 230px 完整 DDS 上复评 bounded frontier，提前淘汰低分辨率假优解。
- checkpoint schema 升级并提供旧 checkpoint 的明确拒绝/迁移信息；取消、暂停、恢复和 revision 隔离继续有效。

退出条件：合成 holdout 的结构恢复与七图 128/1,024 对照达到冻结门限；恢复前后候选逐字节相同。

阶段实证：64 例复合 holdout 的主素材锚点覆盖率为 92.1875%，有界 512 候选前沿召回率为 51.5625%，均通过冻结门限；四次错误地要求被遮挡底层素材 Top-32 身份命中的 RED 已追加保留。checkpoint 已升级为 v2，旧 v1 fail closed。首张真实图在 128 预算下超过 180 秒且停在尾端高分辨率细化之后，因此 Q3 尚未冒充整体通过；该可复现性能 RED 直接进入 Q4 修复。

### Q4：稀疏残差修复（P1，3–5 工程日，依赖 Q3）

- 用残差连通域与四叉树区域替代近似逐块填色；优先覆盖大面积同色区域。
- 每轮接受后合并同纹理、同色、同深度的相邻实例，并执行 bounded necessity pruning。
- tile painter 降为最后 fallback；其增益、实例成本和停止理由单独记录。
- 不以牺牲视觉质量为代价强制压缩，复杂度仍通过 Pareto 暴露。

退出条件：七图视觉门禁通过且实例/源码没有隐性越界；所有删除都有可回放 necessity receipt。

### Q5：完整 DDS、CK3 与 Pages 收口（P0，2–3 工程日 + CK3 槽位，依赖 Q0–Q4）

- 在干净 checkout 重跑 pack、Vitest、128/1,024 benchmark、生产浏览器、跨浏览器、WebGL fallback、离线 Service Worker 和 production-boundary。
- 对七图质量优先候选执行完整 DDS 96/230/512 复评和 CK3 MCP-only Apply/Copy/framebuffer/re-Apply。
- RED attempt 追加保留；不得覆盖、删改或通过移动门限追结果。
- 推送同一 release commit，等待 Pages workflow GREEN，并从 canonical URL 回读 commit/time、素材包身份和零后端请求。

退出条件：第 4.2 节全部满足，公开页面、能力说明、证据和 release commit 一致。

## 6. 执行顺序与停止条件

执行顺序固定为 `Q0 → Q1 → Q2 → Q3 → Q4 → Q5`。每个工作包只执行一次与风险相称的验证，形成 GREEN 或可复现 RED 后立即提交、rebase、推送，再进入下一包。

出现以下情况必须 fail closed：

- 新评分无法在扰动阶梯上保持单调，或 GPU/CPU 排序不一致；
- holdout 被用于调参、样本或门限在结果产生后变化；
- 新搜索靠超过实例预算、遗漏完整 DDS 复评或降低原生门限取得“提升”；
- checkpoint 恢复改变候选、WebGL context loss 没有显式 CPU fallback；
- 生产 bundle 出现后端、上传、CK3、MCP、localhost API 或未授权素材路径。

## 7. Delta-Q 完成定义

1. Q0–Q5 全部达到各自退出条件并更新为 `passed`。
2. 七图与 holdout 的提升均由冻结合同证明，不用新指标掩盖 legacy 退化。
3. 浏览器完整 DDS 与 CK3 原生证据分别存在且互不冒充。
4. 搜索仍可确定性暂停、恢复、取消和重启，生产站点仍为零后端纯前端。
5. `master`、公开 Pages 版本、benchmark manifest、原生证据和能力说明指向同一 release commit。
