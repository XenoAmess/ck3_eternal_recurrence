# CK3 独立家徽编辑器 Alpha 收口

## 状态

**Alpha v2 GREEN（source + 完整 exact-build 静态 pack + GitHub Pages workflow）**。

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
| 确定性多层图片拟合 | GREEN | 双分离目标 fixture 证明同一 DDS 可重复选择并堆叠两层以上 |
| WebGL2 评估 | GREEN | Chromium headless E2E 得到数值 RGBA8 MSE；无 WebGL2 时明确 CPU fallback |
| 拟合结果回填编辑器并输出代码 | GREEN | 合成 pack E2E 与 exact-build 完整 pack E2E |
| 默认正式界面不显示 CK3/MCP 控件 | GREEN | Playwright 断言；只有显式开发开关可展示研究夹具 |
| 无 Java 的 production build | GREEN | `pnpm build`；worker 独立 chunk |
| GitHub Pages 自动发布 | GREEN | `master` 路径触发；pack → unit → browser E2E → build → deploy |

## exact-build 完整素材包

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

`verify_web_asset_pack.py` 对源路径角色、长度、SHA-256、DDS header、完整 inventory 和 fit index 重新核对，结果为
`status=green`。1,619 项索引是 42 个 pattern 加 1,577 个可由已实证 ASCII reader 表达的 emblem。另一个注册资源
`ce_mount_fleurdelisé.dds` 含高位字符；原生 reader 已知会拒绝高位 UTF-8，因此完整收录但不由拟合器生成。8 个未注册文件也
只收录、不冒充可执行资源。完整盘点见
[`ck3-coat-of-arms-asset-inventory.md`](ck3-coat-of-arms-asset-inventory.md)。

## 图片拟合 v2 合同

Alpha 搜索不是“从库里选一张最像图片的徽记”，而是受 CK3 原生构图模型约束的多层 matching pursuit：

1. 将目标图在浏览器内 contain 到 96×96，再复合透明像素并缩至 40×40 搜索图；
2. 从目标得到确定性的三色量化 palette；
3. 遍历全部 42 个注册 pattern 与 palette 排列，使用正向 renderer 选择初始背景；
4. 计算目标相对当前构图的逐像素残差，以最大连通残差区域求下一层的重心和尺度；
5. 对 1,577 个可粘贴注册 emblem 全库粗评分，再对低损失 shortlist 搜索残差颜色排列、残差/画布中心、三个尺度、八个
   45° 旋转和水平 flip；
6. 将本轮最佳 DDS 作为新的 `colored_emblem` 块追加，然后重新计算残差；同一 DDS 可在不同位置、颜色和变换下重复入选；
7. 每层相对改善低于 0.5%、达到用户图层预算或没有改善候选时停止；默认最多 6 层，UI 可设 1..12；
8. 以 78% RGB MSE + 22% luminance edge loss 排序，并用稳定字符串 key 打破平局；
9. CPU reference 是选择权威；WebGL2 对最终多层候选执行 RGBA8 squared-error shader 交叉评分；
10. fit index 只承担全库搜索；结果确定后重新校验并下载入选元素的完整 DDS，供编辑和预览。

输出只使用实机语法矩阵允许的字段，并继续经过 validator、serializer 和 128 KiB 门禁。

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

- v2 是逐层贪心残差分解，不是全局最优 beam search；早期错误图层可能影响后续选择。
- 每个自动图层当前生成一个 instance；同一 DDS 的重复使用表现为多个可独立编辑的 `colored_emblem` 块。
- CPU 仍承担全库搜索，WebGL2 当前只交叉评分最终候选；WebGL2 atlas/reduction 批处理属于 Beta。
- 照片、文字、渐变和高频细节通常质量较差；产品明确称为“原生元素近似重建”。
- 浏览器 renderer 根据随附 shader 合同实现，但 FallbackColor、GPU 采样和色彩空间尚无原生 framebuffer 逐像素闭环。
- “完整”只指 CK3 1.19.0.6 基础游戏 `game/gfx/coat_of_arms/**/*.dds`；不包含玩家模组或其他 build。
- 1 个含高位文件名的注册资源和 8 个未注册辅助 DDS 不参与拟合；磁盘存在或 UI 可选不能替代剪贴板 reader 证据。
- 前端主 chunk 仍约 1 MiB，构建只有非阻断 code-splitting warning；Beta 应拆分 Element Plus 和编辑器面板。

## Beta 优先级

1. WebGL2 texture-array/atlas 批量 pattern/emblem 渲染和 reduction；
2. beam search、连续 transform 局部细化、同块多 instance 合并与多个 Pareto 候选；
3. 为当前 RGBA fit index 增加轮廓、方向和通道能量特征，进一步减少精渲染 shortlist；
4. 输入前景/背景、对称、指定元素、颜色锁和复杂度上限控制；
5. 完整原版包的分片、Service Worker 缓存和增量 build 更新策略；
6. 前端按路由/面板拆包与移动端布局。

详细方案见 [`ck3-coat-of-arms-image-fitting-feasibility.md`](ck3-coat-of-arms-image-fitting-feasibility.md)，引擎语法边界见
[`ck3-coat-of-arms-clipboard-import-capability.md`](ck3-coat-of-arms-clipboard-import-capability.md)，Pages 合同见
[`ck3-coat-of-arms-github-pages.md`](ck3-coat-of-arms-github-pages.md)。
