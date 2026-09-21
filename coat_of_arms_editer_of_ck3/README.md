# CK3 家徽编辑器

Vue 3 + Element Plus + TypeScript 实现的独立 CK3 静态纹章代码编辑器和图片拟合器。生产网页不安装、启动或连接 CK3，
不依赖 MCP、Java、Python 或任何本机服务；它只生成原版“从剪贴板粘贴”读取的 coat-of-arms render description，
不把该入口描述成任意 CK3 脚本执行器。

## 当前能力

- 解析 `name = { ... }`、注释、紧凑/多行排版和 `rgb` / `hsv` typed block，并确定性输出 CRLF CK3 文本；
- 从 Clipboard API 读取源码，编辑 pattern、三通道颜色、`colored_emblem`、mask、instance、受限
  `textured_emblem`，以及已由原生证据覆盖的 `parent`；
- 在浏览器内解码 PNG/JPEG/WebP，使用 CK3 原生 DDS 元素进行多层重建。用户图片、缩略图、像素和拟合内容不上传；
- 使用版本化的 `ck3-coa-web-asset-pack-v1` 静态素材包。manifest 与每个 DDS 均校验 SHA-256、字节数、尺寸和格式；
  exact 1.19.0.6 pack 覆盖基础游戏 CoA 目录 1,630/1,630 个 DDS，自动拟合只使用 1,577 个可粘贴 registered emblem；
- 用户决定搜索预算，产品不设置 12、1,024 或 10,000 等硬上限，也不静默 clamp。预算是最大候选数，不承诺无贡献层；
- Web Worker 提供运行、暂停、刷新后恢复、取消、自然收敛和失败隔离；checkpoint 绑定输入 SHA-256、素材包及搜索游标；
- 安全 checkpoint 可导出为 `ck3-coa-portable-fit-checkpoint-v1` 文件，payload 由 SHA-256 绑定；导入会重新检查文件大小、
  RGBA 编码、输入/素材包身份、预算、算法和搜索游标，为 IndexedDB 配额失败或站点数据丢失提供人工恢复路径；
- WebGL2 texture-array 与 GPU reduction 批量排序背景和原生图形候选，并以 CPU reference 检查指标及完整稳定排序；
  WebGL2 不可用、上下文丢失或超出误差门禁时 fail closed 到 CPU；
- 大预算原生 tile 路径使用覆盖安全和高分辨率接缝门禁，避免旧 0.96 缩放暴露底色规则网格；
- 支持固定点 leave-one-out 剪枝、安全相邻块合并、候选质量/复杂度对比、虚拟化大文档编辑、撤销/重做、
  项目导入导出和 IndexedDB 自动保存；复制与保存始终读取完整模型，不读取可视窗口；
- 简体中文/英文界面切换保存在浏览器本地；Element Plus、页面标题、状态和能力矩阵同步切换；
- 内置 exact 1.19.0.6 语法能力矩阵，区分 parser、preview、editor、serializer 与 native evidence；
- 代码超过旧版单请求 MCP v1 的 128 KiB 合同时只显示历史运输边界说明，仍可完整复制。该数字不是 CK3 引擎上限；
- renderer 翻译 Clausewitz/Jomini 的三通道调色、pattern mask、transform、surface detail 与 alpha blend；仍未覆盖的
  GPU 采样、色彩空间和原生 framebuffer 对照不会冒充逐像素一致。

引擎语法和真实正反例见
[`../docs/ck3-coat-of-arms-clipboard-import-capability.md`](../docs/ck3-coat-of-arms-clipboard-import-capability.md)，
图片拟合架构和隐私边界见
[`../docs/ck3-coat-of-arms-image-fitting-feasibility.md`](../docs/ck3-coat-of-arms-image-fitting-feasibility.md)，
Alpha 基线见
[`../docs/ck3-coat-of-arms-editor-alpha.md`](../docs/ck3-coat-of-arms-editor-alpha.md)，
Beta 工作包和机器可读状态见
[`../docs/ck3-coat-of-arms-editor-beta-plan.md`](../docs/ck3-coat-of-arms-editor-beta-plan.md)。

下一轮拟合质量技术规划见
[`docs/fitting-quality-epsilon-q-plan.md`](docs/fitting-quality-epsilon-q-plan.md)：以已发布的 Delta-Q v9 为基线，
优先推进多分辨率选优、固定实例预算下的联合优化与轮廓细节重建；质量相同时再减少游戏内绘制实例和输出大小。
该文档是后续实施规划，不代表所列新能力已经实现。

## 在线版本

GitHub Pages 正式入口：
<https://xenoamess.github.io/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/>。

[`coat-of-arms-editor-pages.yml`](../.github/workflows/coat-of-arms-editor-pages.yml) 在 `master` 的本目录内容变化后自动执行
素材包校验、Vitest、Playwright 独立浏览器验收和 production build，全部通过后部署到上述子路径。线上包含项目已授权的
exact CK3 1.19.0.6 DDS pack，但运行时不读取游戏目录，也不连接 CK3。

部署合同与故障边界见
[`../docs/ck3-coat-of-arms-github-pages.md`](../docs/ck3-coat-of-arms-github-pages.md)。

## 开发

```text
pnpm install
pnpm test
pnpm test:e2e
pnpm build
pnpm dev
```

从明确给出的 exact-build 安装目录冻结静态 pack：

```text
python -m pip install -r tools/requirements-pack.txt
python tools/build_web_asset_pack.py --game-root "<CK3 installation root>" --output public/asset-packs/ck3-1.19.0.6
python tools/verify_web_asset_pack.py public/asset-packs/ck3-1.19.0.6
```

浏览器不执行这些 Python 命令。Vite 只把已准备的静态 pack 复制到 `dist`。

## 原生开发验收边界

Quarkus backend 与浏览器 REST client 已在 Beta WP7 退役。原生研究、Apply/Copy round-trip、大文本分块运输和 framebuffer
对照继续使用仓库受管的 typed MCP、Python official-MCP client 与 native bridge 测试工具；这些工具只属于开发验收，
不进入生产网页运行链路。历史文档中的 `Vue → Quarkus → MCP` 记录是当时有效的冻结证据，不代表当前产品架构。

已完成的原生 Apply/Copy、王朝 Finish、15 例语法矩阵和大于 128 KiB 的分块 MCP v2 证据均保留在
[`../docs/ck3-coat-of-arms-clipboard-import-capability.md`](../docs/ck3-coat-of-arms-clipboard-import-capability.md)。
当前最终 1,024 实例 Pareto 候选的 CK3 Apply、校准 framebuffer 与 Copy/reapply 已在
[`../docs/coat-of-arms-fit-artifacts/xenoamess-hunter-v8-native-r38/README.md`](../docs/coat-of-arms-fit-artifacts/xenoamess-hunter-v8-native-r38/README.md)
通过预冻结门限；该证据不声称 GPU 逐字节一致。
角色设计器王朝家徽的 Finish、开局、保存、存档内语义记录和新进程冷重载闭环见
[`../docs/coat-of-arms-fit-artifacts/xenoamess-hunter-v8-campaign-r49-r52/README.md`](../docs/coat-of-arms-fit-artifacts/xenoamess-hunter-v8-campaign-r49-r52/README.md)。
当前尚未覆盖的 shader/VFS 组合原生 framebuffer 与通用 DLC/mod runtime definition winner 继续按证据范围标为受限；
战役内重新打开王朝编辑器为 `limited`，角色个人家徽和头衔家徽为 `not-supported`，不得从王朝路径外推；
Gamma/1.0 收口顺序见 [`../docs/ck3-coat-of-arms-editor-gamma-plan.md`](../docs/ck3-coat-of-arms-editor-gamma-plan.md)。
