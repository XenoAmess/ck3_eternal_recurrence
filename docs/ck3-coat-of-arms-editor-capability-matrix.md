# CK3 家徽编辑器 Beta 能力矩阵

> 基线：CK3 `1.19.0.6` exact asset pack；网页运行时纯浏览器。原生证据只用于开发验收，不进入生产链路。

页面“CK3 1.19.0.6 剪贴板语法能力矩阵”是本表的中英文产品投影。每一行同时显示 parser、preview、editor、serializer 与 native evidence；缺少预览能力的结构必须保留并提示或直接拒绝，不能静默消失。

| 语法/资源 | Parser | Preview | Editor | Serializer | Native evidence | Beta 边界 |
| --- | --- | --- | --- | --- | --- | --- |
| `coa = { ... }` wrapper | 完整 | 完整 | 归一化 | 归一化 | 15-case MCP Apply/Copy | 导出统一使用 `coa`。 |
| pattern、三色、`colored_emblem`、`instance`、mask、变换与 depth | 完整 | 完整 | 完整 | 完整 | R17/R18 七图原生像素与 Copy/reapply | 浏览器指标通过预声明像素门限，不声称 GPU 逐字节相同。 |
| 注释与 `hsv` | 归一化 | 完整 | 归一化 | 归一化 | 15-case MCP Apply/Copy | 注释丢弃，HSV 按原生 Copy 结果转 RGB。 |
| 静态 `@变量` | 归一化 | 完整 | 归一化 | 归一化 | 15-case MCP Apply/Copy | 只接受无循环、可静态展开的字面量引用。 |
| `_default.dds` `textured_emblem` | 完整 | 完整 | 受限 | 完整 | R35 校准 framebuffer + Copy/reapply | exact build 唯一注册 texture；其他名字保留但不伪预览。 |
| `parent` | 完整 | 受限 | 受限 | 完整 | R21 reference-free framebuffer | 原生剪贴板预览也不物化继承；页面保留引用，只画显式字段并提示。 |
| 缺失资源名 | 完整 | 缺失 | 受限 | 完整 | 15-case MCP detection | 语法接受与资源存在分开；不制造占位纹章冒充原生。 |
| 空块/缺省字段 | 受限 | 受限 | 完整 | 归一化 | 15-case MCP Apply/Copy | 载入可编辑默认值并警告，不承诺字节保真。 |
| 重复普通标量 | 归一化 | 完整 | 完整 | 归一化 | 15-case MCP Apply/Copy | 与原生一致采用后值并警告。 |
| 多 outer object | 拒绝 | 不适用 | 拒绝 | 不适用 | 15-case MCP Apply/Copy | 原生取首项；产品拒绝静默丢弃后续对象。 |
| body-only、effect/trigger/event、模板 DSL、未知字段 | 拒绝 | 不适用 | 拒绝 | 不适用 | 15-case MCP rejection | 此入口不是 CK3 脚本执行器。 |

## 资源矩阵

| 资源范围 | 状态 | 证据与限制 |
| --- | --- | --- |
| 基础 exact pack | 通过 | 1,630 项 hash-bound winner，按需 DDS/shard 加载，浏览器校验 `ck3-coa-vfs-receipt-v1`。 |
| 安装的 DLC | 通过（本 build 无额外候选） | R36 用官方 MCP 核查 29 份描述符，CoA TXT/DDS 均为 0；不外推其他 build 或 entitlement。 |
| 目录/ZIP 模组 direct DDS | 通过 scoped winner 合同 | R22/R23 证明后加载直接路径胜出；导入 `resolved_overlay` pack 必须绑定 source ID、asset hash 与 winner-set hash。 |
| `replace_path` | 不建模 | R24/R25 已反证“自动使较早/base DDS missing”的假设；导入 pack 不得据此删除资源。 |
| definition merge / 运行时 CoA registry | 未提供通用 winner API | 生产剪贴板编辑不展开 `parent`；未知 definition 仍保真导出并显示边界，不将静态 projection 冒充引擎 registry。 |
| 用户图片 | 纯浏览器 | 解码、拟合、checkpoint、保存与导出均不上传；生产流程零后端请求。 |

## 证据索引

- [剪贴板导入能力](ck3-coat-of-arms-clipboard-import-capability.md)
- [七图原生像素闭环](coat-of-arms-fit-artifacts/user-picture-corpus-v14-native-r18/README.md)
- [`textured_emblem` R35](coat-of-arms-fit-artifacts/textured-emblem-native-r35/README.md)
- [`parent` R21](coat-of-arms-fit-artifacts/parent-semantics-native-r21/README.md)
- [DLC 来源 R36](coat-of-arms-fit-artifacts/dlc-source-inventory-mcp-r36/README.md)
- [VFS direct-DDS provenance](ck3-coat-of-arms-vfs-resource-provenance-mcp.md)
- [生产运行边界](coat-of-arms-production-runtime-boundary.md)
