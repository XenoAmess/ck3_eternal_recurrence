# CK3 家徽编辑器 Beta 工作计划

> 状态：执行中（2026-09-16）；WP0–WP5 与 WP7 已通过，仅 WP6 仍有未闭合门禁
>
> 产品目录：`coat_of_arms_editer_of_ck3/`
>
> 目标：从 Alpha 的“可用近似器”推进到可验证、可压缩、可在大预算下稳定工作的纯浏览器 Beta。
>
> WP0 浏览器接缝修复、WP1 大载荷文本闭环、WP2 精确剪枝/压缩及压缩文本原生闭环均已通过；WP7 已删除
> Quarkus/REST 生产残留并以完整 production 请求观测闭环。当前继续处理 WP6 的 VFS/资源覆盖剩余范围。
> 128 KiB 已由真实 380,862-byte CK3 round-trip 明确证明只是旧桥合同，不是当前实测引擎上限。

机器可读状态见 [`coat-of-arms-fit-artifacts/beta-progress.json`](coat-of-arms-fit-artifacts/beta-progress.json)，WP0 完整证据见
[`xenoamess-hunter-v4/README.md`](coat-of-arms-fit-artifacts/xenoamess-hunter-v4/README.md)。旧 0.96 夹具在 96/230/512 分别稳定
泄漏 186/1,806/5,112 像素；修复后 mask 开关共六个观测点均为零。hunter v4 在共同合同下与 v3 的总损失、边缘损失完全
相同，1,000 个实例的精确 CRLF 复制与重新解析闭环通过；v4 原始文本的原生 Apply/Copy 也已通过。

WP3 第一候选现已保留原始 `File` 与 96/192/256 px 金字塔，并把语义 emblem、纯 tile 和混合残差路径放入同一候选集合。
合成夹具证明混合画笔可被搜索且能带来严格收益；hunter 实测中混合候选反而更差，选择器按预先固定的总损失/边缘损失独立门禁
拒绝晋级，保留 v4 数值基线。因此该阶段只是“搜索能力已接通”，不是“hunter 质量已提升”；机器证据见
[`xenoamess-hunter-v5-candidate`](coat-of-arms-fit-artifacts/xenoamess-hunter-v5-candidate/README.md)。下一候选继续做局部 replacement
和轮廓细化，只有边缘损失严格优于 `0.043043678580258954` 且总损失不劣化时才晋级。

WP3 第二候选 [`xenoamess-hunter-v6-edge-refined`](coat-of-arms-fit-artifacts/xenoamess-hunter-v6-edge-refined/README.md)
已越过该浏览器质量门禁：1,008 个实例的总损失为 `0.024123983862988356`、边缘损失为
`0.040769084120764576`，并且 192/256 px 两项指标也同时优于 v4。其结构压缩把块数从 1,008 降至 299，exact 固定点剪枝
又删除 2 个完全被覆盖的实例且 96/230/512 px 零像素变化。当前继续执行 Pareto 质量剪枝和 v6 原生文本闭环；在这些门禁完成前
hunter 与七图最终候选的固定点剪枝现已全部闭合，WP3 状态为 `passed`。

Pareto 质量剪枝现已通过：在 exact 固定点上继续删除 3 个可见但有害的实例，最终 1,003 个实例；96/230/512 px 的总损失与
边缘损失全部下降。完整测量见
[`xenoamess-hunter-v6-pareto-pruned`](coat-of-arms-fit-artifacts/xenoamess-hunter-v6-pareto-pruned/README.md)。
下一道晋级门禁为这份 262,138-byte 最终文本的 MCP v2 CK3 Apply/Copy；原生 framebuffer 仍是独立的像素证据缺口。

该原生文本门禁现已通过：262,138-byte / 297 blocks / 1,003 instances 输入经 6 个分块 Apply，CK3 Copy 回读
149,612 bytes / 297 blocks / 1,003 instances，九组语义字段全部一致。原生 Copy 省略显式零旋转，因此保留前后原文哈希并按
默认零语义比较，不要求格式化后的原始字节相同。CK3 已退出且 Steam 保持离线；原生 framebuffer 仍单列为待补能力。

## 1. 不变约束

- 正式 GitHub Pages 平台必须纯前端运行，不安装、启动或连接 CK3，也不依赖 Java、Quarkus、Python、Steam 或本机 MCP。
- 用户图片只在浏览器内解码和拟合；不上传服务器。拟合仍是“使用 CK3 原生 DDS 元素堆叠重建”，不是找一张最相似的 DDS。
- 图层上限由用户决定；不得再设置 12、1024 一类产品硬上限。Beta 必须至少对 `10,000` 的参数、取消、内存和失败行为建立门禁。
- 实机研究继续优先走受管 MCP；MCP 能力不足时先补 MCP，不使用 OCR 或坐标鼠标链替代结构化证据。
- 原生 MCP/CK3 只属于开发验收夹具，绝不成为正式网页的运行依赖。
- 当前 `xenoamess-hunter-v3` 结果作为历史 Alpha 证据保留，不静默覆盖。接缝修复后的结果写入新的 `v4` artifact 目录并注明取代关系。

## 2. 当前基线与问题清单

Alpha 已能解析、编辑、渲染、序列化 CK3 家徽代码，并能在浏览器内使用 exact 1.19.0.6 asset pack 做图片拟合。现有 hunter 基准在最大 1024 层时实际保留 1000 个严格改善层，总损失 `0.02590`、边缘损失 `0.04304`、相对背景改善 `86.77%`；代码为 379,666 bytes、14,006 行。

但该基准不能作为 Beta 的合格原生交付，已知缺陷如下：

| 优先级 | 缺陷 | 当前证据/影响 |
| --- | --- | --- |
| P0 | 预览出现红色规则网格/分割线 | 大预算四叉树块在 96×96 搜索平面选择 `0.96` 缩放；相邻中心仍按完整单元间距排列，于高分辨率预览暴露底层红色 `pattern_solid`。这是几何空隙，不是 `ce_block_02.dds` 的透明边：该 DDS 顶层 mip 的 65,536 个 alpha 均为 255。 |
| P0 | 原生 framebuffer 像素对照尚未完成 | 380,862-byte hunter 已完成 CK3 Apply/Copy 文本闭环；网页无缝结论仍需空间像素摘要才能提升为原生像素结论。 |
| P0 | 浏览器与原生 renderer 尚无逐像素闭环 | 浏览器 CPU reference 主要采样顶层 mip；原生 shader 使用线性 mag/min/mip、wrap 和 surface mask。接缝几何很可能也会进入游戏，但严重程度仍须 MCP 原生证据确认。 |
| P0 | 大预算路径过度依赖单一矩形画笔 | 当前大量使用 `ce_block_02.dds`；不能代表 1,577 个可粘贴 registered emblem 的混合构图能力。 |
| P0 | 输入过早缩为 96×96 | 上传图片在拟合入口即栅格为 96×96，高分辨率轮廓和细线在候选生成前已经丢失。 |
| P0 | 只保证前向追加时严格改善 | 没有最终 backward prune / leave-one-out；较早图层可能在后来覆盖后变成冗余。 |
| P1 | 代码膨胀 | v4/v6 已完成保持顺序的安全相邻合并和最终剪枝，但进一步近似压缩仍需受累计视觉损失预算约束。 |
| P1 | 大预算控制尚未完整 | 128/1024/10,000 真实拟合、跨刷新持久 checkpoint 精确暂停/恢复、取消后重启与恰好 10,000 实例文档已通过；GPU 搜索覆盖扩大与同 run WebGL2 context 重建仍待完成。 |
| P1 | 搜索仍偏贪心 | WebGL2 texture-array/atlas/reduction 已承担背景、语义晋级及 local 胜者排序并由 CPU reference 门禁；完整 transform population 与逐块残差候选仍为 CPU，尚无稳定的多候选 Pareto 自动输出。 |
| P1 | 编辑体验尚未完整 | 32 卡片虚拟窗口、撤销/重做、项目保存恢复、直接变换、三候选对比及跨刷新持久 checkpoint 恢复已通过；更多拟合阶段的恢复与配额失败恢复仍待完成。 |
| P1 | 预览合同仍不完整 | exact 1.19.0.6 唯一注册 `_default.dds` 的 `textured_emblem` shader 模型合成已通过；R21 已证明原生剪贴板路径本身不物化 `parent`，浏览器据此保留引用且只画显式字段。其他 shader/VFS 情形的原生像素对照仍待补。 |
| P2 | 输入/资产覆盖有限 | 安全 SVG、素材包目录导入、中英文、移动端、Service Worker、按需素材分片以及 Chromium/Firefox/WebKit 已通过；目录 mod 覆盖基础 DDS、后载 archive mod 覆盖目录 mod，以及两个目录 mod 冲突均已有 scoped 原生证据，但 DLC、`replace_path` 和 definition merge 仍未覆盖。Pages 的静态素材目录仍约 147 MB，运行时不会整包下载。 |

## 3. P0-1：红色分割线修复

### 3.1 已定位根因

大预算路径由 [`imageFitter.ts`](../coat_of_arms_editer_of_ck3/src/domain/imageFitter.ts) 的 `nativePaintTiles` 在 96×96 平面生成四叉树块。每块的中心和 nominal scale 按整数像素边界计算，但 `paintWithNativeTiles` 会在 `[0.96, 1, 1.04]` 中选缩放。对一个 1 像素宽单元，`0.96 / 96 = 0.01`，而相邻中心仍相距 `1 / 96`；两块之间因此留下约 `0.0004167` 的归一化空隙。

96×96 的像素中心损失无法稳定看见这条亚像素缝，平分时又固定保留先枚举的 `0.96`。230px/512px 预览会把空隙显露为底层 pattern 颜色。截图中的直线与块边界一致，因此 surface wear 可以解释块内噪声，却不能解释规则网格。

### 3.2 修复工作

1. 新增一个不依赖 CK3 的最小回归夹具：高饱和底色、1×1 完全不透明测试画笔、相邻四叉树块，并分别在 96、230、512 输出分辨率渲染。
2. 给块覆盖建立独立于目标图片总损失的 seam metric：在 nominal 内部公共边界带内统计底色泄漏像素和最大泄漏量。关闭 surface mask 时要求泄漏为零；开启 mask 时与无缝参考构图做差，避免把合法 surface detail 误判为缝。
3. 从 tile painter 移除任何小于 nominal coverage 的候选。bleed/overlap 根据输出采样足迹显式计算，候选只能保持或扩大覆盖；相邻块不得依靠 96×96 像素中心“碰巧看不见”空隙。
4. 对 tie-break 增加覆盖安全规则：总损失在容差内相同时，优先无缝覆盖，再比较较小面积/稳定序列键，禁止继续因枚举顺序选中 `0.96`。
5. 在 96×96 搜索损失之外增加至少一个高分辨率 post-check。失败候选不得进入导出，即使低分辨率总损失更小。
6. 重跑用户 hunter 图片，最大层数仍设 1024；生成 `xenoamess-hunter-v4` 的输入 receipt、参数、进度摘要、代码、浏览器渲染图、指标和 SHA-256。v3 保留并标记为“已知接缝缺陷的历史基线”。

2026-09-16 的 fit-index v2 回归补充：预计算特征曾把纹理“能量重心”直接用于铺砖位置。该值适合语义形状匹配，却不等于占用边界中心；
甚至完全不透明的 `ce_block_02.dds` 也会因 256×256 累加误差得到
`0.49999999999999634`。在特定 230/512px 像素中心上，这足以把 nominal 边界移过采样点。当前实现令语义候选继续使用能量重心，
铺砖路径则只按 `contentBounds` 的中心和跨度建立覆盖几何。带偏斜能量重心、完整占用边界的夹具在旧路径稳定失败，修复后
96/230/512 均为零泄漏；hunter v8 同门禁通过。证据见
[`xenoamess-hunter-v8-pareto-candidates`](coat-of-arms-fit-artifacts/xenoamess-hunter-v8-pareto-candidates/README.md)。

### 3.3 验收门禁

- 合成相邻块夹具在 230px 和 512px 下，关闭 surface mask 的内部公共边界 `backgroundLeakPixels = 0`。
- 开启 surface mask 后，公共边界相对无缝参考不得形成周期性误差峰；测试必须能在恢复 `0.96` 旧逻辑时稳定失败，防止空门禁。
- hunter v4 不再出现由 tile 几何造成的规则底色网格；总损失不得劣于 v3 的 `0.02590`（浮点容差只用于跨实现数值噪声），边缘损失不得劣于 `0.04304`。
- 复制代码中的 `colored_emblem`/`instance` 计数必须与结果元数据一致，不得发生 UI 截断或只复制前若干块。
- 在 WP1 的 MCP 大载荷闭环通过前，只能称“浏览器接缝修复已通过”，不得称“CK3 中已确认无缝”。

## 4. 执行工作包与依赖顺序

### WP0：接缝修复与 hunter v4（P0，0.5–1.5 工程日）

交付：上述回归夹具、几何/tie-break 修复、高分辨率门禁、1024 参数重拟合及 v4 artifact。

依赖：无 CK3、无桌面，可先纯浏览器完成。

退出条件：3.3 全部浏览器门禁通过。

### WP1：MCP v2 大载荷原生验收（P0，1–3 工程日 + 可用 CK3 槽位）

当前状态：`passed`。有界 v2 合同、官方 MCP SDK 超过 128 KiB 传输测试、native fresh build 155/155 以及真实 CK3 hunter v4
Apply/Copy 均已通过。实机输入为 380,862 bytes / 1,000 instances，8 分块；Copy 回读 240,453 bytes，九类语义字段和
1,000 层/块/实例计数完整。合同与证据见 [家徽大源码 MCP v2 传输合同](ck3-coat-of-arms-large-source-upload-v2.md)。
framebuffer 空间像素对照仍是独立待办，不影响 WP1 文本闭环的通过状态。

交付：

- 给 typed MCP 增加版本化的大文本传输，优先采用有总长度、chunk index/count、完整 SHA-256、会话/代次绑定和超时的分块合同；不得只是放大一个无界 JSON 参数。
- 原生端在组装完成、哈希一致且处于正确家徽页面后才允许 Apply；断线、重复块、越序、过期 revision、build 不匹配全部 fail closed。
- 对 hunter v4 完成 Apply → 原生 Copy 回读 → 结构/计数/哈希对照；记录耗时、内存/稳定性、CK3 是否接受以及实际边界。
- 若 CK3 拒绝，不把 128 KiB 误写成引擎限制，而通过有界二分实验定位具体失败维度：字节数、行数、block 数、instance 数或 UI clipboard 路径。
- 优先补原生 framebuffer 或稳定像素摘要能力，用结构化 MCP 证据比较网页与 CK3；不使用 OCR 或屏幕像素猜测。

退出条件：大于当前 128 KiB 合同的 round-trip 通过，或形成可复现、可归因的 CK3 实际上限报告。正式 Pages bundle 仍不得包含 MCP 控件或调用。

### WP2：最终剪枝与代码压缩（P0/P1，1–2 工程日）

当前状态：`passed`。`adjacent-equal-style-v1` 无损结构压缩已通过：hunter v4 从 1,000 块压到 293 块、实例仍为 1,000，
380,862 → 260,932 bytes，96/230/512 完整渲染逐字节零差异。`exact-leave-one-out-fixed-point-v1` 又按最终结果反向
评估全部 1,000 个实例；0 个可零像素差删除，每个单项移除都改变 96px 渲染并使总损失严格上升。完整证据见
[`xenoamess-hunter-v4-pruned`](coat-of-arms-fit-artifacts/xenoamess-hunter-v4-pruned/)。浏览器剪枝、解析和接缝门禁已经通过；
压缩后的 260,932-byte / 293-block / 1,000-instance 文本也已在 CK3 中通过 MCP v2 Apply/Copy，九类语义字段序列全部保持。

交付：

- 完整结果执行 backward prune / leave-one-out；只有移除后确会越过视觉损失容差的层才能保留。
- 将相同 texture、三色、mask 的图层合并为单个 `colored_emblem` 下的多个 `instance`；保留 depth 和渲染顺序语义。
- 对邻接、同色 tile 做矩形合并；对颜色做有界量化，但每一步都必须重新评分，不能仅按语法相似合并。
- 同时展示图层数、instance 数、代码 bytes/行数和压缩前后损失。

退出条件：最终每个保留层/实例都有必要性证据；序列化再解析后结构等价；hunter 代码显著小于 v4 原始逐块代码且不重新引入接缝。

### WP3：高分辨率、混合原生元素拟合（P0/P1，2–4 工程日）

交付：

- 保留原始输入及 96/192/256 等多尺度金字塔，不在入口不可逆地只留下 96×96。
- 低分辨率负责粗搜索，高分辨率负责轮廓、细线和最终局部替换。
- 大预算路径从单一 `ce_block_02` 扩为矩形、圆、楔形和语义 emblem shortlist 的混合画笔；加入曲线感知分区和局部 replacement。
- 预计算透明边界、轮廓、通道能量等 feature 到 fit index；输出 1–3 个质量/复杂度 Pareto 候选。

当前状态：fit-index v2 的预计算部分已实现并通过独立 pack verifier。内置 exact 1.19.0.6 pack 保持原 6,631,424-byte RGBA atlas
逐字节不变，新增 2,266,632-byte、SHA-256 `76429584EE906D7E0B2AEA4163FF2ABF690E6254571CB267CE281B402063DC26`
的定长特征 sidecar；1619 项均带透明内容边界、质心/跨度、alpha/RGB 通道能量、轮廓能量及 18×18 描述符并传入 Worker。
旧 v1 pack 继续在浏览器内确定性计算同一特征，不产生网络或后端依赖。合同与验证见
[`coat-of-arms-fit-index-v2.md`](coat-of-arms-fit-index-v2.md)。拟合器也已返回 1–3 个实际完整、同合同非支配的质量/边缘/实例数候选；
每项经 depth 编码逐像素门禁，网页自动生成独立源码、计数与预览。合成浏览器用例实际产生 2 项，详见
[`coat-of-arms-pareto-candidates.md`](coat-of-arms-pareto-candidates.md)。hunter 和七图用户语料的新合同已实跑；七图 7/7 都评估非方块 DDS，
3/7 的质量优先结果实际选中非方块元素，其中 picture-02/07 相对最佳纯方块路径同时改善总损失与边缘损失。
消融证据见七图 artifact 中的 `mixed-element-ablation.json`。最终 21 个交付候选已在
[`user-picture-corpus-v15-pruned-budget-1024`](coat-of-arms-fit-artifacts/user-picture-corpus-v15-pruned-budget-1024/README.md)
完成 96/230/512px、总损失和边缘损失零累计退化的逐实例固定点剪枝：17,234 → 16,660 实例，代码总量减少
315,551 UTF-8 bytes。该验收同时发现 v14 有 14/21 个混合候选沿用了 32px fit-index 搜索指标；产品现会在导出前用完整
DDS/mip 重新评分并重新选 Pareto 前沿，最终指标、预览和代码绑定同一素材合同。WP3 状态为 `passed`。

退出条件：hunter v4/v5 的总损失不劣化、边缘损失严格优于 `0.04304`，且资源清单证明不再退化为无条件的单一矩形铺色器。

### WP4：WebGL2 批量搜索与 10,000 层压力路径（P1，2–4 工程日）

交付：texture-array/atlas、批量渲染和 reduction；Worker checkpoint；暂停、恢复、取消；128/1024/10,000 预算 benchmark；资产分片与按需加载。

当前状态：`passed`。同一 96×96 高频压力图的 128 / 1,024 / 10,000 预算已在浏览器 Worker 中实际执行；10,000 原值未 clamp，
自然收敛到 1,824 个改善实例，评估 14,908 个候选，耗时 13,409 ms。绘制阶段取消延迟 57 ms，随后重启新 run 成功；完整复制
711,661 bytes / 25,543 行并回读 1,824 实例。`ck3-coa-fit-checkpoint-v1` 与 `ck3-coa-persisted-fit-checkpoint-v1` 已通过跨刷新暂停/恢复：
82 ms 内暂停并写入 IndexedDB，刷新、素材重载与状态恢复共 3,318 ms，继续搜索 3,239 ms；恢复结果与不中断的 128 预算结果逐字段一致，
并以 run ID/revision 拒绝旧 Worker 消息。详见[真实拟合预算压力证据](coat-of-arms-fit-budget-stress.md)。

`webgl2-texture-array-reduction-float-v1` 已在 Worker 内实测处理背景、语义晋级与 local 胜者排序；hunter 1024 为
6 batch / 354 candidates，GPU/CPU 最大指标差 `6.102908300942289e-8`，完整排序一致；真实
context loss 会 fail closed 到 CPU。背景、语义粗筛、0.1° 精筛与原生块绘制四阶段的取消延迟实测为 14.5–20.8 ms，
每次取消后均能启动新 run，无旧 revision 污染。详见[WebGL2 批量搜索证据](coat-of-arms-webgl-batch-search.md)。

GPU 目前不代替 CPU 纹章正向渲染；它批量渲染 loss contribution 并做 reduction，而 CPU reference 仍计算全候选以便逐项校验。
这满足“GPU 实际参与批量候选选择，CPU reference 保留”的门禁，不声称完整拟合已 GPU 化。JS heap 之外的 GPU/总进程内存
在当前浏览器 API 不可靠观测，因此作为证据范围限制保留，而非写成已测。

退出条件：

- 10,000 是可执行预算而非被静默 clamp；允许算法因“没有严格改善”提前停止，但 UI 必须区分“自然收敛”和“达到上限”。
- 取消在有界时间内生效，内存峰值、耗时、实际保留层数和候选评估数进入报告。
- 10,000 层文档即使不适合交互展开，也能序列化、复制、重新解析；列表通过虚拟化保持可操作。

### WP5：编辑体验与项目状态（P1，2–3 工程日）

当前状态：`in_progress`。恰有 10,000 绘制实例的独立压力文档已通过完整序列化、复制、重新解析、项目保存恢复和尾部编辑；
页面只物化 32 个实例卡，完整模型为 1,653,890 UTF-8 bytes / 70,014 行。首次同步整图预览令尾部编辑耗时 4,683 ms、越过
预先冻结的 1,000 ms 门禁；延后超大文档实时预览后降至 724 ms。证据见
[10,000 实例完整文档压力证据](coat-of-arms-large-document-stress.md)。`d265503e` 又通过有界撤销/重做、IndexedDB 单槽自动保存及
刷新后 SHA-256/计数校验恢复；10,000 实例自动保存 1,096 ms、恢复 5,899 ms，非 GET 请求为 0。`39e18a9d` 已加入直接画布位置拖拽、
等比缩放和连续旋转，并通过每手势单步撤销回归；证据见[可视化实例编辑证据](coat-of-arms-visual-instance-editor.md)。`cb59fa06`
又完成 1–3 项完整源码候选对比；仅在输入 SHA、评分器、renderer、分辨率和 mask 合同相同的情况下计算三维支配，证据见
[候选对比证据](coat-of-arms-candidate-comparison.md)。拟合 checkpoint 已通过 IndexedDB 跨刷新精确恢复；未知版本与输入、素材、预算或
游标不一致会 fail closed。浏览器清站点数据、配额拒绝或设备丢失不在持久保证范围内。

交付：图层/实例虚拟列表、撤销/重做、直接拖拽/缩放/旋转、项目导入导出、自动保存恢复、候选对比、长拟合暂停/恢复，以及更清楚的近似/原生未验提示。

退出条件：不依赖后端即可恢复项目；1024+ instance 编辑不会冻结页面；复制始终来自当前完整模型而非可视列表窗口。

### WP6：预览、输入、资产与浏览器覆盖（P1/P2，2–4 工程日）

交付：`parent`/`textured_emblem` 合成；安全 SVG 栅格化；asset-pack 版本选择/导入；DLC/mod VFS receipt；Firefox/WebKit E2E；主 bundle code splitting；移动端退化策略；Service Worker/asset shard 缓存。

当前状态：`in_progress`。安全 SVG、唯一注册 `_default.dds` 的 `textured_emblem` 浏览器 shader 模型、简体中文/英文、素材包目录
导入、移动端退化、Service Worker 离线恢复、主 bundle code splitting 以及 Chromium/Firefox/WebKit 核心流程已经通过自动化门禁。
Pages 已由 workflow `35000503958` 部署到 `/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/`，公网 canonical URL 与入口资源均
回读 `200`；无尾斜杠地址为预期 `301`。部署证据见 `ck3-coat-of-arms-github-pages.md`。`parent` 引用现在会在预览区就地显示中英文边界、仍完整保留导出，不再静默冒充已合成。R21 的 MCP-only
原生 framebuffer 矩阵已证明角色设计器剪贴板路径同样不物化有效 `parent` definition，而显式 child 正常渲染；因此生产浏览器维持
“保留 parent、只画显式字段”的行为。

页面顶栏版本合同已经通过：每个 production build 显示 ISO 8601 构建时间戳与 Actions 从 `github.sha` 注入的 8 位 Git hash；
`6eade3ab` 的 workflow `35076612146` 全部 build/deploy GREEN，随后公网 Playwright 从嵌套 canonical URL 精确回读
`6eade3ab` 和 ISO 8601 时间戳。这个短标识用于定位线上字节来源，不替代完整 commit、asset-pack manifest SHA 或证据 SHA。

R22 又以 MCP-only、零 OCR/键鼠的 reference-free framebuffer 矩阵证明：两个启用的目录模组注册并提供同名直接 DDS 路径时，
后一个 `enabled_mods` 项胜出。基础静态 pack 现在带 `ck3-coa-vfs-receipt-v1`，浏览器会校验 1,630 项胜者清单 SHA-256，
并明确显示 `base_game_only`；导入包可以携带 `resolved_overlay` 收据。overlay 中每个胜者必须声明已登记的 `source_id`，胜者集
SHA-256 同时绑定 source、逻辑资源、资源 hash 和源相对路径；缺失或引用 receipt 外来源会 fail closed。R23 在独立夹具中进一步证明：
启用目录 mod 的直接 DDS 覆盖基础游戏同路径 DDS，较晚启用的 ZIP archive mod 覆盖较早目录 mod 同路径 DDS。两组各自都有唯一名
byte-twin reference，6/6 Apply/Copy/capture 和 6 个预登记像素 pair gate 全部通过。R24 首次运行 `replace_path` 原生矩阵，
3/3 Apply/Copy/capture 与清理正常，但“后载 replace_path 会让较早模组独有 pattern 等价于 missing control”的预登记假设 RED：
该 pair 的 `46,518/46,518` 个共同可见像素不同，MAE `0.3960397086`。R24 已冻结为反例，不能事后改门禁；R25 将新增基础游戏独有
pattern 对照，分别验证基础目录是否被屏蔽、较早启用模组是否保留。现仍未覆盖 DLC mount、闭合后的 `replace_path` 结论和
definition merge，不能据此把 WP6 宣称为全部完成。证据见
[`vfs-winner-native-r22`](coat-of-arms-fit-artifacts/vfs-winner-native-r22/README.md) 与
[`vfs-extended-native-r23`](coat-of-arms-fit-artifacts/vfs-extended-native-r23/README.md)、
[`vfs-replace-path-native-r24`](coat-of-arms-fit-artifacts/vfs-replace-path-native-r24/README.md)。asset delivery 已由浏览器门禁闭合：1,630 项
manifest 载入后首屏只请求当前构图所需的 4 个 DDS，不请求 6,631,424-byte RGBA index 或 2,266,632-byte shape-feature shard；首次拟合才请求
这两个内容寻址 shard，并只把本例 DDS 请求增加到 5 个。Service Worker 会按 build version 隔离 cache，两个 shard 在线填充后在
完全离线状态逐字节回读相同 SHA-256。该结论证明运行时按需加载与缓存，不改变 Pages artifact 本身约 147 MB 的静态授权素材规模。

MCP 优先补完已新增 exact-build 家徽定义索引/读取工具：可分页读取基础游戏 block、完整源码、别名链和来源 SHA-256，
重复定义、循环或缺失目标全部 fail closed。真实 1.19.0.6 安装上的 `k_england` 和 `d_agder → c_agder` 已通过；
详见 [`ck3-coat-of-arms-parent-definition-mcp.md`](ck3-coat-of-arms-parent-definition-mcp.md)。R21 又新增 reference-free capture MCP，并用预先登记的量化噪声门限
闭合 `parent` 剪贴板预览语义；证据见 [`parent-semantics-native-r21`](coat-of-arms-fit-artifacts/parent-semantics-native-r21/README.md)。
这仍不冒充 title/dynasty 其他加载路径的继承语义或 DLC/mod VFS 胜者。

退出条件：能力矩阵明确每种语法/资源在 parser、preview、editor、serializer、native evidence 五列的状态；不能预览的结构不得静默消失。

### WP7：开发后端退役（P1，1–2 工程日，依赖 WP1）

当前状态：`passed`（`0b8c6733`）。Quarkus backend、浏览器 REST client 与生产界面的本机桥控件已删除；原生开发验收继续
直接使用 WP1 已通过合同测试和实机 round-trip 的受管 typed MCP/native bridge。production bundle 字节扫描没有发现五类旧后端标识；
完整浏览器流程观测到 13 个 HTTP 请求，全部是同源 GET，backend 与用户内容请求均为 0。证据见
[生产运行边界](coat-of-arms-production-runtime-boundary.md)。

退出条件：所有仍有价值的原生开发验收都有 MCP 等价路径；独立浏览器 E2E 继续断言图片拟合期间零 `/api/` 请求；生产构建中不存在 Java/本机服务依赖。

## 5. 里程碑与停止条件

| 里程碑 | 包含 | Go 条件 | Stop 条件 |
| --- | --- | --- | --- |
| B0 无缝浏览器基线 | WP0 | 合成 seam gate + hunter v4 通过 | 接缝仍可复现，或为了消缝明显恶化总/边缘损失 |
| B1 原生可证 | WP1 | 大载荷 Copy/Apply/Copy 闭环或确认实际引擎边界 | 需要重新启动 CK3 但没有可用槽位；此时保存证据并通知，不改走 OCR |
| B2 结构有效 | WP2 | 剪枝、合并、round-trip 通过 | 压缩改变渲染顺序或结构语义 |
| B3 质量提升 | WP3 | 高分辨率与混合画笔指标通过 | 只是增加层数而没有边缘/感知收益 |
| B4 大预算可控 | WP4–WP5 | 10,000 压力、取消、恢复、编辑通过 | 内存无界、取消失效或复制截断 |
| Beta 收口 | WP6–WP7 | Pages CI、跨浏览器和能力矩阵通过；生产零本机依赖 | 任何生产路径依赖 CK3/MCP/Java，或将未验证近似标作原生一致 |

## 6. Beta 完成定义

Beta 只有同时满足下列条件才收口：

1. 红色规则分割线的旧实现有稳定失败用例，修复后在低/高分辨率均通过；hunter 新 artifact 可追溯且不覆盖历史证据。
2. 1024 参数结果在代码、解析模型、元数据和原生回读之间没有截断；大于 128 KiB 的真实边界由 MCP/CK3 证据而非猜测给出。
3. 最终结果经过反向剪枝；同配置实例完成安全合并；每个保留项都对最终质量有可量化贡献。
4. 高分辨率边缘与混合原生元素路径相对 Alpha 有实测提升，不再把“堆更多矩形”冒充完整素材组合拟合。
5. 10,000 层预算的运行、提前收敛、取消、恢复、序列化和编辑行为都有自动化压力证据。
6. GitHub Pages 从干净 checkout 可构建、测试和部署；用户上传、拟合、预览、编辑、保存与复制全程纯浏览器、零后端请求。
7. 原生一致性仍按证据分级：没有 framebuffer/像素摘要闭环的部分继续标“近似”，不因肉眼看起来接近而升级结论。

## 7. 预计工期与优先顺序

按单人连续工程时间粗估，WP0–WP3（解决接缝、原生大载荷、冗余和主要质量问题）约 `4.5–10.5` 工程日；完整 WP0–WP7 约 `11.5–21.5` 工程日。CK3 槽位、MCP 原生扩展复杂度和 10,000 层性能结果会影响日历时间。

严格顺序为：

`WP0 接缝` → `WP1 原生边界` → `WP2 剪枝压缩` → `WP3 质量` → `WP4 性能` → `WP5 编辑体验` → `WP6 覆盖` → `WP7 后端退役`。

其中 WP0 可完全静默执行；WP1 才申请 CK3 共享槽位。若 WP1 需要重新启动 CK3 而槽位不可用，应停止原生操作、保留当前 MCP 证据并通知用户，其他纯前端工作可继续。

## 8. 关联文档

- [家徽编辑器 Alpha 收口](ck3-coat-of-arms-editor-alpha.md)
- [图片拟合可行性与架构](ck3-coat-of-arms-image-fitting-feasibility.md)
- [剪贴板导入能力报告](ck3-coat-of-arms-clipboard-import-capability.md)
- [大源码 MCP v2 传输合同](ck3-coat-of-arms-large-source-upload-v2.md)
- [真实 10,000 拟合预算与持久恢复证据](coat-of-arms-fit-budget-stress.md)
- [WebGL2 texture-array/reduction 批量搜索证据](coat-of-arms-webgl-batch-search.md)
- [hunter v3 历史拟合证据](coat-of-arms-fit-artifacts/xenoamess-hunter-v3/README.md)
