# CK3 家徽编辑器

Vue 3 + Element Plus + TypeScript 实现的 CK3 静态纹章代码编辑器。它只覆盖原版“从剪贴板粘贴”所读取的
coat-of-arms render description，不把该入口描述成任意 CK3 脚本执行器。

## 当前能力

- 解析 `name = { ... }`、注释、紧凑/多行排版和 `rgb` / `hsv` typed block；
- 编辑 pattern、三通道颜色、重复 `colored_emblem`、mask 和重复 instance；
- 编辑 position、scale、rotation、depth，并生成稳定 CRLF CK3 文本；
- 展开简单静态 `@变量`，诊断多顶层、重复标量、`parent` 与未知字段；
- 浏览器构图近似预览，明确不冒充 CK3 最终渲染。

引擎证据与完整正反例矩阵见
[`../docs/ck3-coat-of-arms-clipboard-import-capability.md`](../docs/ck3-coat-of-arms-clipboard-import-capability.md)。

## 开发

```powershell
pnpm install
pnpm test
pnpm build
pnpm dev
```

当前不需要后端。未来只有在索引用户选择的 CK3/DLC/mod 资源、转换 DDS 或连接本机 MCP 会话时，才考虑增加
Maven + Java + Quarkus 伴随服务。

仓库内的原生 `ck3_export_coat_of_arms_source_v1` MCP Copy/export primitive 已完成静态构建与 closed-schema 测试，
尚未在真实 CK3 进程中验收，也尚未接入这个浏览器界面。浏览器不会用 OCR 或屏幕自动化冒充该能力。

`ck3_query_coat_of_arms_resource_catalog_v1` 已能在不启动 CK3 的情况下分页读取 exact 1.19.0.6 基础游戏 designer manifest；
它尚未接入前端，并明确不声称包含 DLC/mod 覆盖或运行时资源注册状态。
