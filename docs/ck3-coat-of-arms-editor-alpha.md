# CK3 独立家徽编辑器 Alpha 收口

## 状态

**Alpha v3 GREEN（source + 完整 exact-build 静态 pack + GitHub Pages workflow）**。

这里的 Alpha 是独立静态 Web 应用：没有安装或运行 CK3、没有 MCP、没有 Quarkus/Java 时，用户仍可上传图片、使用原生
DDS 多层拟合、预览、继续结构化编辑并复制可粘贴的 CK3 家徽代码。CK3 原生桥只保留为仓库开发研究夹具，不属于产品运行时。

项目所有者已于 2026-09-15 明确要求把原版 DDS 素材包视为本仓库版本管理与 GitHub Pages 发布所授权的素材。当前 exact
1.19.0.6 `ck3-coa-web-asset-pack-v1` 因此与源码一同跟踪，并由 Pages Actions 在部署前逐文件校验；该项目政策记录不转移
Paradox 素材的所有权，也不自动授权其他 build 或仓库。

## Alpha 交付面

| 能力 | 状态 | 证据 |
|---|---|---|
| CK3 剪贴板 render-description 解析、诊断、CRLF 序列化 | GREEN | Vitest；原生正反例矩阵 |
| pattern、三底色、colored emblem、mask、instance 结构化编辑 | GREEN | Vue UI；parser/serializer/validation tests |
| DXT1、DXT5、BGRA8 DDS 浏览器解码 | GREEN | decoder tests；静态 pack E2E |
| shader 合同近似预览 | GREEN with declared limits | renderer tests；不声称逐像素 CK3 一致 |
| PNG/JPEG/WebP 本地上传 | GREEN | Playwright；16 MiB / 4096 px fail-closed 边界 |
| 图片不上传、不调用后端 | GREEN | E2E 记录完整流程 `/api/` request 数为 0 |
| 原版 CoA DDS 树完整收录 | GREEN | 1,630/1,630 物理源文件集合闭合 |
| 静态包 schema、hash、路径、注册角色和 fit-index 门禁 | GREEN | asset-pack unit tests；Python standalone verifier |
| 可取消浏览器搜索 | GREEN | 独立 Worker；读取阶段 run invalidation；搜索阶段 terminate |
| 确定性多层图片拟合 | GREEN | 双分离目标、透明留白/非等比旋转和原生块严格递减 fixture；真实 hunter 图 1024 上限回归 |
| WebGL2 评估 | GREEN | Chromium headless E2E 得到数值 RGBA8 MSE；无 WebGL2 时明确 CPU fallback |
| 拟合结果回填编辑器并输出代码 | GREEN | 合成 pack E2E 与 exact-build 完整 pack E2E |
| 默认正式界面不显示 CK3/MCP 控件 | GREEN | Playwright 断言；只有显式开发开关可展示研究夹具 |
| 无 Java 的 production build | GREEN | `pnpm build`；worker 独立 chunk |
| GitHub Pages 自动发布 | GREEN | `master` 路径触发；pack → unit → browser E2E → build → deploy |

## exact-build 完整素材包

下表保留 Alpha v1 的历史冻结回执。Beta 工作线已在 2026-09-16 将同一批 RGBA atlas 无损升级为 fit-index v2；当前部署 pack 的
manifest 为 1,042,792 bytes、SHA-256 `F5BB089884F864ED5DF88DCF3C8CB2C8966E3E541284AE691C6EBC1A282FD36E`，并新增
2,266,632-byte 的哈希绑定特征 sidecar。当前回执以[素材清单](ck3-coat-of-arms-asset-inventory.md)为准，历史 Alpha 数字不据此改写。

2026-09-15 从明确提供的 CK3 `1.19.0.6` 安装根生成，全程只读游戏文件，没有启动 CK3：

| 字段 | 值 |
|---|---:|
| pack id | `ck3-1.19.0.6-base-complete-42p-1578e-8aux` |
| manifest bytes | 1,042,018 |
| manifest SHA-256 | `AD7F0A911A2B4F002E923FEAB13716566D9A7B61447E9092504826FE6498FE91` |
| registered pattern | 42（38 visible + 4 hidden） |
| registered colored emblem | 1,578（1,576 visible + 2 hidden） |
| 可粘贴自动拟合 registered emblem | 1,577 |
| unregistered auxiliary colored DDS | 8（只收录，不自动生成） |
| textured emblem / surface mask | 1 / 1 |
| 总物理 DDS 资源项 | 1,630/1,630 |
| 物理 DDS bytes | 138,389,380 |
| 32×32 RGBA fit index | 1,619 项 / 6,631,424 bytes |

Alpha 时的 `verify_web_asset_pack.py` 对源路径角色、长度、SHA-256、DDS header、完整 inventory 和 fit index 重新核对，结果为
`status=green`。1,619 项索引是 42 个 pattern 加 1,577 个可由已实证 ASCII reader 表达的 emblem。另一个注册资源
`ce_mount_fleurdelisé.dds` 含高位字符；原生 reader 已知会拒绝高位 UTF-8，因此完整收录但不由拟合器生成。8 个未注册文件也
只收录、不冒充可执行资源。完整盘点见
[`ck3-coat-of-arms-asset-inventory.md`](ck3-coat-of-arms-asset-inventory.md)。

## 图片拟合 v3 合同

Alpha 搜索不是“从库里选一张最像图片的徽记”，而是受 CK3 原生构图模型约束的两条确定性候选路径：

1. 目标 RGBA 使用 alpha-aware 双线性缩放；透明像素不再被复合成白色，也不参与颜色/边缘损失。小预算使用 56×56，大于等于
   128 层的重建预算使用 96×96；
2. 从不透明目标得到确定性的三色 palette，遍历全部 42 个注册 pattern 与排列。背景 beam 除当前最低损失候选外，强制保留
   最佳 `pattern_solid.dds`，防止复杂 pattern 的短期优势堵死后续重建；
3. 语义路径从当前残差的最大连通区域计算轮廓、重心和非等比尺度。1,577 个可生成 emblem 先按 18×18 透明内容轮廓、30°
   旋转和 flip 粗筛，再用真实渲染选出 shortlist；
4. DDS 自带透明留白不再算作图案尺寸：每项记录实际内容边界和重心，求解旋转后的内容包围盒，补偿 position 与 X/Y scale；
5. 精筛覆盖整圆旋转种子，并对 position、X/Y scale、颜色、flip 做多轮 coordinate descent；角度先精扫到 1°，再按
   `0.5° → 0.25° → 0.125°` 二分，最终残余角误差尺度小于 0.1°。导出角度不是 45° 离散值；
6. 前六层保持背景路径多样性的 beam；每个追加层都必须令同一正向 renderer 的总损失严格下降，`provenance.layerLosses` 保存
   背景及每次接受后的完整递减序列；
7. 大预算另走原生块重建：从纯色背景开始重复使用原生 `ce_block_02.dds`，将目标自适应四叉树分区，每个叶片分别拟合颜色、
   position 和非等比 scale。它通过堆叠原生 DDS 逐块拼图，不从库中只选一张“最像的图”；
8. 用户值是最大改善图层数，不是目标层数。默认 6；UI 可输入 1024、10000 或更大安全整数。默认最小相对改善阈值为零，但候选
   仍须满足严格绝对损失下降；没有改善便停止，serializer 对所有已接受层完整输出；
9. 损失为 62% alpha-weighted RGB MSE + 38% alpha-weighted luminance edge loss，稳定 key 打破平局；WebGL2 最终评分同样忽略
   透明目标像素；
10. CPU reference 是选择权威；WebGL2 对最终多层候选执行 RGBA8 交叉评分。页面分别展示无盾面材质的拟合平面和带
    surface-mask 的 shader 预览；
11. fit index 承担全库搜索；结果确定后重新校验并下载入选完整 DDS。Worker 对背景、轮廓粗筛、连续精筛和原生块阶段回传真实
    完成量，页面进度条显示当前阶段百分比和累计候选数。

真实用户图门禁见 [`coat-of-arms-fit-artifacts/xenoamess-hunter-v3/README.md`](coat-of-arms-fit-artifacts/xenoamess-hunter-v3/README.md)：
1024 上限实际保留 1,000 个严格改善层，输出 1,000 个 `colored_emblem` 块，总损失 0.02590，相对背景改善 86.77%。

输出只使用实机语法矩阵允许的字段，并继续经过 validator 与 serializer。128 KiB 只作为当前开发期 MCP probe/export 的传输合同：
网页对更大代码显示证据说明和警告但仍允许复制；开发期 MCP 检测/应用按钮会禁用。它不是已证明的 CK3 原生粘贴上限。

## 验收命令

均从 `coat_of_arms_editer_of_ck3` 执行：

```text
pnpm test
pnpm test:e2e
pnpm build
python tools/verify_web_asset_pack.py public/asset-packs/ck3-1.19.0.6
```

Pages checkout 必须含已跟踪的 exact-build 完整包；verifier 或 exact-build E2E 失败都会阻断部署。正式 E2E 同时证明图片拟合
过程中没有调用 CK3、MCP、Java 或任何 `/api/` 后端。

## Alpha 已知限制

- 大预算四叉树块路径当前会在 `[0.96, 1, 1.04]` 中选择缩放；96×96 损失可能看不见 `0.96` 块之间的亚像素空隙，而较高分辨率预览会把底层 pattern 显示成规则分割线。该问题已列为 Beta 的第一阻断项，根因、回归门禁和 hunter v4 重跑要求见 [`ck3-coat-of-arms-editor-beta-plan.md`](ck3-coat-of-arms-editor-beta-plan.md)。
- v3 仍不是组合全局最优；小预算语义路径只保留宽度有限的 background/layer beam，大预算原生块路径是确定性四叉树近似。
- 每个自动图层当前生成一个 instance；同一 DDS 的重复使用表现为多个可独立编辑的 `colored_emblem` 块。
- CPU 仍承担全库搜索，WebGL2 当前只交叉评分最终候选；WebGL2 atlas/reduction 批处理属于 Beta。
- 照片、文字、渐变和高频细节通常质量较差；原生块重建在曲线边缘会出现与 96×96 搜索平面相应的台阶，产品明确称为“原生元素近似重建”。
- 浏览器 renderer 根据随附 shader 合同实现，但 FallbackColor、GPU 采样和色彩空间尚无原生 framebuffer 逐像素闭环。
- “完整”只指 CK3 1.19.0.6 基础游戏 `game/gfx/coat_of_arms/**/*.dds`；不包含玩家模组或其他 build。
- 1 个含高位文件名的注册资源和 8 个未注册辅助 DDS 不参与拟合；磁盘存在或 UI 可选不能替代剪贴板 reader 证据。
- 前端主 chunk 仍约 1 MiB，构建只有非阻断 code-splitting warning；Beta 应拆分 Element Plus 和编辑器面板。

## Beta 优先级

1. 修复大预算块的覆盖空隙，建立 230/512px 接缝回归门禁并重跑 1024 参数 hunter 基准；
2. 扩展版本化 MCP 大文本合同，完成超过 128 KiB 家徽代码的原生 Copy/Apply/Copy 边界验证；
3. 做最终 backward prune、同配置多 instance 合并和代码体积门禁；
4. WebGL2 texture-array/atlas 批量 pattern/emblem 渲染和 reduction；
5. 更宽的 beam、原生圆/矩形混合画笔、曲线感知分区与多个 Pareto 候选；
6. 将当前运行时轮廓、透明边界和通道能量特征预计算进 fit index，进一步减少精渲染 shortlist；
7. 输入前景/背景、对称、指定元素、颜色锁和复杂度上限控制；
8. 完整原版包的分片、Service Worker 缓存、前端拆包与移动端布局。

完整执行顺序、验收条件、停止条件与粗略工期见 [`ck3-coat-of-arms-editor-beta-plan.md`](ck3-coat-of-arms-editor-beta-plan.md)。
设计方案见 [`ck3-coat-of-arms-image-fitting-feasibility.md`](ck3-coat-of-arms-image-fitting-feasibility.md)，引擎语法边界见
[`ck3-coat-of-arms-clipboard-import-capability.md`](ck3-coat-of-arms-clipboard-import-capability.md)，Pages 合同见
[`ck3-coat-of-arms-github-pages.md`](ck3-coat-of-arms-github-pages.md)。
