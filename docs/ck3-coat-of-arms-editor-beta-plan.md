# CK3 家徽编辑器 Beta 工作计划

> 状态：执行中（2026-09-15）；WP0–WP2 已通过，当前推进 WP3 高分辨率与混合原生元素
>
> 产品目录：`coat_of_arms_editer_of_ck3/`
>
> 目标：从 Alpha 的“可用近似器”推进到可验证、可压缩、可在大预算下稳定工作的纯浏览器 Beta。
>
> WP0 浏览器接缝修复、WP1 大载荷文本闭环、WP2 精确剪枝/压缩及压缩文本原生闭环均已通过；当前工作项为 WP3。
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
WP3 仍保持 `in_progress`。

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
| P1 | 代码膨胀 | 当前每个自动图层输出一个 `colored_emblem` 块，尚未把同 texture/colors/mask 的多实例合并。 |
| P1 | 10,000 层缺少真实压力证据 | UI 接受大数字不等于搜索、序列化、编辑和取消路径能稳定处理。 |
| P1 | 搜索仍偏贪心 | WebGL2 只交叉评分最终候选，尚未承担 atlas/reduction 批量搜索；没有稳定的多候选 Pareto 输出。 |
| P1 | 大文档编辑体验不足 | 图层列表未虚拟化；缺少撤销/重做、项目保存、直接拖拽、暂停/恢复和候选对比。 |
| P1 | 预览合同仍不完整 | `parent` 与 `textured_emblem` 尚未完整合成到浏览器预览。 |
| P2 | 输入/资产/浏览器覆盖有限 | 安全 SVG 输入已通过浏览器门禁；仍只有 1.19.0.6 基础包，没有自动解析 DLC/mod VFS 胜者；Pages asset pack 较大；E2E 仅覆盖 Chromium；主 JS chunk 仍约 1 MiB。 |

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

退出条件：hunter v4/v5 的总损失不劣化、边缘损失严格优于 `0.04304`，且资源清单证明不再退化为无条件的单一矩形铺色器。

### WP4：WebGL2 批量搜索与 10,000 层压力路径（P1，2–4 工程日）

交付：texture-array/atlas、批量渲染和 reduction；Worker checkpoint；暂停、恢复、取消；128/1024/10,000 预算 benchmark；资产分片与按需加载。

当前状态：`in_progress`。页面输入已确认不截断 10,000，但这不构成真实拟合压力通过；下一门禁会实际运行预算 10,000 的拟合，
记录候选评估数、实际实例、停止原因、耗时与可取得的内存证据。完整文档压力已在 WP5 单独通过，不能拿来代替本项。

该子门禁现已通过：同一 96×96 高频压力图的 128 / 1,024 / 10,000 预算在浏览器 Worker 中实际执行；10,000 原值未 clamp，
自然收敛到 1,824 个改善实例，评估 15,640 个候选，耗时 14,644 ms。绘制阶段取消延迟 52 ms，随后重启新 run 成功；完整复制
711,661 bytes / 25,543 行并回读 1,824 实例。详见[真实拟合预算压力证据](coat-of-arms-fit-budget-stress.md)。WP4 仍因暂停/恢复、
checkpoint 与 GPU 批量搜索未完成而保持 `in_progress`。

退出条件：

- 10,000 是可执行预算而非被静默 clamp；允许算法因“没有严格改善”提前停止，但 UI 必须区分“自然收敛”和“达到上限”。
- 取消在有界时间内生效，内存峰值、耗时、实际保留层数和候选评估数进入报告。
- 10,000 层文档即使不适合交互展开，也能序列化、复制、重新解析；列表通过虚拟化保持可操作。

### WP5：编辑体验与项目状态（P1，2–3 工程日）

当前状态：`in_progress`。恰有 10,000 绘制实例的独立压力文档已通过完整序列化、复制、重新解析、项目保存恢复和尾部编辑；
页面只物化 32 个实例卡，完整模型为 1,653,890 UTF-8 bytes / 70,014 行。首次同步整图预览令尾部编辑耗时 4,683 ms、越过
预先冻结的 1,000 ms 门禁；延后超大文档实时预览后降至 724 ms。证据见
[10,000 实例完整文档压力证据](coat-of-arms-large-document-stress.md)。`d265503e` 又通过有界撤销/重做、IndexedDB 单槽自动保存及
刷新后 SHA-256/计数校验恢复；10,000 实例自动保存 1,096 ms、恢复 5,899 ms，非 GET 请求为 0。拟合 pause/resume/checkpoint、
`39e18a9d` 已加入直接画布位置拖拽、等比缩放和连续旋转，并通过每手势单步撤销回归；证据见
[可视化实例编辑证据](coat-of-arms-visual-instance-editor.md)。`cb59fa06` 又完成 1–3 项完整源码候选对比；仅在输入 SHA、评分器、renderer、
分辨率和 mask 合同相同的情况下计算三维支配，证据见[候选对比证据](coat-of-arms-candidate-comparison.md)。拟合
pause/resume/checkpoint 仍未完成。

交付：图层/实例虚拟列表、撤销/重做、直接拖拽/缩放/旋转、项目导入导出、自动保存恢复、候选对比、长拟合暂停/恢复，以及更清楚的近似/原生未验提示。

退出条件：不依赖后端即可恢复项目；1024+ instance 编辑不会冻结页面；复制始终来自当前完整模型而非可视列表窗口。

### WP6：预览、输入、资产与浏览器覆盖（P1/P2，2–4 工程日）

交付：`parent`/`textured_emblem` 合成；安全 SVG 栅格化；asset-pack 版本选择/导入；DLC/mod VFS receipt；Firefox/WebKit E2E；主 bundle code splitting；移动端退化策略；Service Worker/asset shard 缓存。

退出条件：能力矩阵明确每种语法/资源在 parser、preview、editor、serializer、native evidence 五列的状态；不能预览的结构不得静默消失。

### WP7：开发后端退役（P1，1–2 工程日，依赖 WP1）

当前 Quarkus 只把本机 REST 请求转成 Java MCP SDK，再转给 Python stdio MCP/原生桥；正式平台本来就不使用它。WP1 的版本化传输稳定后，将开发期连接能力直接收敛到 MCP 的可选 loopback/受管 transport，迁移对应合同测试，随后删除 Quarkus backend 和浏览器 REST client。

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
- [hunter v3 历史拟合证据](coat-of-arms-fit-artifacts/xenoamess-hunter-v3/README.md)
