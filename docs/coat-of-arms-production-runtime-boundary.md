# CK3 家徽编辑器生产运行边界

状态：`passed`（Beta WP7，2026-09-16）  
实现 commit：`0b8c6733`  
适用入口：`/ck3_eternal_recurrence/coat_of_arms_editer_of_ck3/`

## 结论

生产网页已删除 Quarkus backend、Java MCP SDK 转接层和浏览器 REST client。Vue 应用只从同源静态资源或用户明确选择的
本地文件读取输入；原生 Apply/Copy、分块大文本和 framebuffer 研究继续留在仓库受管 typed MCP/native bridge 的开发验收链，
不进入浏览器 bundle。

这次删除的是已退役的 `coat_of_arms_editer_of_ck3/backend/` 和 `src/api/ck3Companion*`。历史文档中的
`Vue → Quarkus → MCP` 记录仍作为当时版本的冻结证据保留，不代表当前架构，也不应被改写为从未存在。

## 两级门禁

### 1. 构建产物静态门禁

`tools/verify_production_boundary.mjs` 递归扫描实际 `dist` 字节，拒绝以下五类标识：

- `/api/ck3/coat-of-arms`
- `http://localhost:8080`
- `http://127.0.0.1:8080`
- `VITE_ENABLE_CK3_COMPANION`
- `VITE_CK3_COMPANION_URL`

本次结果：`passed`，扫描到的命中数为 `0`。Pages workflow 在 production acceptance build 后固定执行该门禁。

### 2. 完整请求行为门禁

`e2e/production-no-backend.spec.ts` 针对 `vite preview` 的真实 production build 完成：

1. 载入 exact 1.19.0.6 静态素材包；
2. 选择一张只存在于浏览器内的 PNG；
3. 执行一次原生 DDS 拟合；
4. 把完整 CK3 代码写入浏览器剪贴板；
5. 下载完整项目；
6. 重置页面并从下载文件恢复项目。

本次浏览器观测到 `13` 个 HTTP 请求，method 集为 `GET`，origin 集仅为 `http://127.0.0.1:4173`；
backend 请求 `0`，用户内容请求 `0`。测试同时拒绝用户文件名进入任何请求 URL。该证据验证运行行为，不以字符串扫描代替。

## 复现

```text
cd coat_of_arms_editer_of_ck3
pnpm test
pnpm build
pnpm verify:production-boundary
set COA_E2E_USE_PREVIEW=true&& pnpm exec playwright test e2e/production-no-backend.spec.ts --reporter=line
```

本报告中的 `set` 是 Windows `cmd.exe` 语法。

## 证据边界

- 静态资源请求会正常访问部署站点；“不外传”指用户图片、缩略图、像素、拟合模型和本地项目内容不进入请求。
- 浏览器扩展、浏览器自身遥测和用户主动另存后的外部操作不属于应用网络行为。
- 原生 MCP 的现有实机证据仍由 `ck3-coat-of-arms-clipboard-import-capability.md` 与 WP1 artifacts 约束；删除 REST
  转接层不会把尚未取得的原生 framebuffer 像素对照变成已完成。
