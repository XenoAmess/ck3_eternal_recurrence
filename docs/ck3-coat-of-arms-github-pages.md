# CK3 家徽编辑器 GitHub Pages 发布合同

## 结论

纯前端编辑器部署到本项目 GitHub Pages 的独立子路径：

<https://xenoamess.github.io/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/>

正式发布只由 [`.github/workflows/coat-of-arms-editor-pages.yml`](../.github/workflows/coat-of-arms-editor-pages.yml)
生成。它不会部署 `backend/`、启动 CK3、调用 MCP、访问玩家游戏目录或要求 Java/Quarkus。浏览器只下载静态 HTML、JS、CSS
和仓库内已冻结的 DDS pack；用户图片仅在浏览器内解码、拟合。

## 2026-09-16 首次嵌套路径部署证据

- 官方 workflow run：[`35000503958`](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/35000503958)，
  head `a35b0edde036ebfe636f0f71b051008e1f27e41a`；build `14m10s`、deploy `50s`，两项均为 `success`。
- 该 run 从干净 checkout 通过 80 项 Vitest、独立浏览器验收、hunter/剪枝源码研究验收、Chromium/Firefox/WebKit
  核心验收、Service Worker 离线验收、嵌套目录 staging 校验及 artifact 上传后才部署。
- 公网回读：无尾斜杠 URL 返回 `301` 并跳转到本文开头的 canonical URL；canonical URL 返回 `200 OK`、
  `Content-Type: text/html; charset=utf-8`；HTML 引用的嵌套入口 JS 返回 `200 OK` 和
  `Content-Type: application/javascript; charset=utf-8`。
- 发布产物的资源 URL 均以 `/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/` 开头，没有覆盖仓库 Pages 根入口。
- 正式简体中文/英文切换与持久化在同一 run 中通过；该结论不代表七种其他语言已翻译。

## 自动触发与发布门禁

工作流在以下情况运行：

- `master` 中 `coat_of_arms_editer_of_ck3/**` 发生变化；
- 工作流本身发生变化；
- 维护者从 Actions 手动触发 `workflow_dispatch`。

构建必须按顺序通过：

1. `verify_web_asset_pack.py` 对 manifest、完整 inventory、fit index/feature sidecar 和全部 DDS 的路径、角色、字节数、SHA-256、
   二进制 header 与容器头重新校验；
2. `pnpm install --frozen-lockfile`，禁止 CI 静默改 lockfile；
3. 运行全部 Vitest；
4. 安装 Actions runner 的 Playwright Chromium，先让大预算拟合与完整图片拟合各自在独立 Playwright 进程执行，再运行其余无 CK3
   浏览器 E2E；进程隔离释放重型用例的浏览器/Worker 状态，但不跳过任何 spec；
5. 在 GitHub Pages 返回的真实仓库 `base_path` 后追加固定的 `/coat_of_arms_editer_of_ck3/`，以该嵌套路径执行 Vite production build；
6. 对 `dist` 中复制后的 pack 再校验一次，将完整产物装入 Pages artifact 的 `coat_of_arms_editer_of_ck3/` 子目录并复核；
7. 仅在上述步骤全部 GREEN 后，由 `github-pages` environment 发布。

工作流权限限定为 `contents: read`、`pages: write`、`id-token: write`。并发组为 `pages`，在途正式部署不会被新的 push 强制取消。

## 已授权静态素材包

项目所有者于 2026-09-15 明确要求将原版 DDS 素材包视为本项目已授权内容。因此当前 Pages artifact 包含：

| 字段 | 值 |
|---|---:|
| 路径 | `asset-packs/ck3-1.19.0.6/` |
| pack id | `ck3-1.19.0.6-base-complete-42p-1578e-8aux` |
| manifest SHA-256 | `F5BB089884F864ED5DF88DCF3C8CB2C8966E3E541284AE691C6EBC1A282FD36E` |
| registered pattern / emblem | 42 / 1,578 |
| auxiliary / textured / surface mask | 8 / 1 / 1 |
| 原版物理 DDS 覆盖 | 1,630 / 1,630；138,389,380 bytes |
| 32×32 RGBA fit index | 1,619 个可粘贴注册项；6,631,424 bytes |
| v2 shape feature sidecar | 1,619 项；2,266,632 bytes；SHA-256 `76429584…DC26` |

该授权记录只适用于本仓库当前 pack 的版本管理与 Pages 发布，不冒充所有权转移，也不自动放行以后从其他 CK3 build、DLC 或
mod 提取的资源。其他 `ck3-*` 生成目录继续由 `.gitignore` 排除，只有显式审阅并添加精确 unignore 后才能进入发布树。
完整性定义、隐藏项及 8 个未注册辅助文件清单见
[`ck3-coat-of-arms-asset-inventory.md`](ck3-coat-of-arms-asset-inventory.md)。

## 子路径与运行边界

Vite 本地开发默认 `base=/`。Actions 从 `actions/configure-pages` 取得实际 Pages `base_path`，追加固定页面段
`/coat_of_arms_editer_of_ck3/` 后注入 `VITE_BASE_PATH`。因此脚本、Worker 和默认素材 manifest 都从
`/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/` 解析，不会错误请求域名根目录或仓库 Pages 根目录。Pages artifact
本身也保持同样的子目录层级；该工作流不在 `/ck3_eternal_recurrence/` 根入口生成编辑器副本或自动跳转。

页面顶栏始终显示 production build 的 ISO 8601 时间戳与 8 位 Git hash。Actions 从部署目标 `github.sha` 注入 hash，时间戳在每次
Vite build 时生成；该标识只用于定位静态页面版本，不替代 asset-pack manifest SHA 或证据 artifact 的完整 commit。

Pages 是静态托管，不能也不应直接“执行 CK3”：

- 线上产物不包含 Maven/Quarkus backend；
- 正式构建不设置 `VITE_ENABLE_CK3_COMPANION`，MCP/CK3 开发控件不会显示；
- E2E 记录完整图片拟合流程并断言没有 `/api/` 请求；
- 输出是 CK3 原生设计器可从剪贴板读取的 render-description 文本，用户自行复制进游戏；
- HTTPS 安全上下文允许浏览器剪贴板 API，但浏览器仍可能要求一次明确的用户权限或交互。

## 仓库设置与维护

仓库 Pages 的 build type 必须为 `workflow`。首次启用后，后续编辑器提交不需要人工复制 `dist`、维护 `gh-pages` 分支或提交构建
产物。`dist/` 继续忽略，Actions artifact 是唯一线上构建结果。

若发布失败，先按失败阶段定位：pack verifier RED 表示素材 bytes/manifest 不一致；Vitest/Playwright RED 表示产品行为退化；
build RED 表示类型或 bundling 问题；deploy RED 才检查 Pages 设置、environment 和 GitHub 服务状态。禁止通过跳过前四个门禁来
“修复”部署。
