# CK3 独立家徽编辑器 Alpha 收口

## 状态

**Alpha GREEN（source + 已跟踪 exact-build 静态 pack + GitHub Pages）**。

这里的 Alpha 是一个独立静态 Web 应用：没有安装或运行 CK3、没有 MCP、没有 Quarkus/Java 时，用户仍可上传图片、使用
静态素材包拟合、预览、继续结构化编辑并复制可粘贴的 CK3 家徽代码。CK3 原生桥只保留为仓库开发研究夹具，不属于产品运行时。

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
| PNG/JPEG/WebP 本地上传 | GREEN | Playwright 真实浏览器；16 MiB / 4096 px fail-closed 边界 |
| 图片不上传、不调用后端 | GREEN | E2E 记录完整流程 `/api/` request 数为 0 |
| 静态素材包 schema、hash、路径逃逸和重复键门禁 | GREEN | asset-pack unit tests；Python standalone verifier |
| 可取消浏览器搜索 | GREEN | 独立 Worker，可在 DDS 读取阶段使 run 失效或在搜索阶段 terminate |
| 确定性图片拟合 | GREEN | CPU reference；已知两色 pattern 和主要 emblem fixture 重复结果一致 |
| WebGL2 评估 | GREEN | Edge headless E2E 得到数值型 RGBA8 MSE；无 WebGL2 时明确 CPU fallback |
| 拟合结果回填编辑器并输出代码 | GREEN | 合成 pack E2E 与 exact-build 本地 pack E2E |
| 默认正式界面不显示 CK3/MCP 控件 | GREEN | Playwright 断言；只有显式开发开关可展示研究夹具 |
| 无 Java 的 production build | GREEN | `pnpm build`；worker 独立 chunk |
| GitHub Pages 自动发布 | GREEN | `master` 路径触发；pack → unit → browser E2E → build → deploy |

## 本机 exact-build pack 冻结结果

2026-09-15 从明确提供的 CK3 `1.19.0.6` 安装根生成 Alpha pack，全程只读游戏文件，没有启动 CK3：

| 字段 | 值 |
|---|---:|
| pack id | `ck3-1.19.0.6-base-alpha-38p-128e` |
| manifest bytes | 77,310 |
| manifest SHA-256 | `41BB03C58BCA6782F45E581188127B4186050D1FFDA777BD9027DA682C08FC03` |
| pattern | 38 |
| colored emblem | 128 |
| surface mask | 1 |
| 总资源项 | 167 |
| DDS bytes | 13,634,992 |

`verify_web_asset_pack.py` 对每项重新读取并核对路径、长度、SHA-256 和 DDS header，结果为 `status=green`。同一 pack 的真实
浏览器流程完成两色目标图片上传、DDS 加载、Worker 搜索、代码回填；没有发出 `/api/` 请求。

## 图片拟合 v1 合同

Alpha 搜索不是通用矢量化或生成式模型：

1. 将目标图在浏览器内 contain 到 96×96，再复合透明像素并缩至 40×40 搜索图；
2. 从目标得到确定性的三色量化 palette；
3. 遍历最多 64 个 pattern 与 palette 排列，使用现有正向 renderer 选择背景；
4. 对用户预算内最多 64 个 emblem 搜索目标重心/包围盒、两组颜色排列、两个中心、三个尺度、四个直角旋转和水平 flip；
5. 以 78% RGB MSE + 22% luminance edge loss 排序，稳定字符串 key 打破平局；
6. 只有 emblem 使背景损失改善至少 1% 才加入结果；
7. 输出最多一个 colored emblem 和一个 instance，随后由用户在结构化编辑器继续添加或调整；
8. CPU reference 是选择权威；WebGL2 对最终候选执行真实 RGBA8 squared-error shader 交叉评分并报告 backend。

候选只使用实机语法矩阵已接受的字段，最终仍通过同一个 validator、serializer 和 128 KiB 门禁。

## 验收命令

均从 `coat_of_arms_editer_of_ck3` 执行：

```text
pnpm test
pnpm test:e2e
pnpm build
python tools/verify_web_asset_pack.py public/asset-packs/ck3-1.19.0.6
```

Pages 正式 checkout 必须含已跟踪的 exact-build pack；verifier 或 exact-build E2E 失败都会阻断部署。开发者若有意移除 pack，
合成 fixture 仍可独立验证纯浏览器链，但这种 checkout 不满足正式 Pages 门禁。

## Alpha 已知限制

- 图片拟合当前只自动加入一个 emblem / instance；多层 beam search 属于 Beta。
- Alpha pack 为控制体积只冻结 128 个 source-ordered 可见 emblem；builder 的 `--emblem-limit 0` 可以生成全量 pack，但全量性能和部署大小尚未作为 Alpha 门禁。
- GPU 当前交叉评分最终候选，搜索权威仍是 Worker CPU reference；WebGL2 atlas 批处理属于 Beta。
- 照片、文字、渐变和高频细节通常低质量；产品明确称为“原生元素近似”。
- 浏览器 renderer 根据随附 shader 合同实现，但 FallbackColor、GPU 采样和色彩空间尚无原生 framebuffer 逐像素闭环。
- 正式平台不能知道玩家本机模组覆盖；它只声明自己绑定的 pack build 与 SHA。
- 当前线上 pack 固定于 CK3 1.19.0.6 的 38 个 pattern、128 个 source-ordered emblem 与一个 surface mask；它不是全量元素库。
- 前端主 chunk 仍约 1.03 MB（gzip 约 332 KiB），构建仅给出非阻断 code-splitting warning；Beta 应拆分 Element Plus 和编辑器面板。

## Beta 优先级

1. WebGL2 texture-array/atlas 批量 pattern/emblem 渲染和 reduction；
2. 多图层 beam search、连续 transform 局部细化、多个 Pareto 候选；
3. 基于 asset SHA 的可复用特征索引，减少首次加载和粗筛成本；
4. 输入前景/背景、对称、指定元素、颜色锁和复杂度上限控制；
5. 全量原版元素 pack 的体积、首次加载与缓存策略；
6. 前端按路由/面板拆包与移动端布局。

详细可行性和纯浏览器/WebGL2 方案见
[`ck3-coat-of-arms-image-fitting-feasibility.md`](ck3-coat-of-arms-image-fitting-feasibility.md)，
引擎语法边界见
[`ck3-coat-of-arms-clipboard-import-capability.md`](ck3-coat-of-arms-clipboard-import-capability.md)。

GitHub Pages 的触发、权限、部署路径与不依赖 CK3 的运行合同见
[`ck3-coat-of-arms-github-pages.md`](ck3-coat-of-arms-github-pages.md)。
