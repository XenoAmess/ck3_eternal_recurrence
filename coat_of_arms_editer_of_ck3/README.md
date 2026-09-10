# CK3 家徽编辑器

Vue 3 + Element Plus + TypeScript 实现的 CK3 静态纹章代码编辑器。它只覆盖原版“从剪贴板粘贴”所读取的
coat-of-arms render description，不把该入口描述成任意 CK3 脚本执行器。

## 当前能力

- 解析 `name = { ... }`、注释、紧凑/多行排版和 `rgb` / `hsv` typed block；
- 编辑 pattern、三通道颜色、重复 `colored_emblem`、mask 和重复 instance；
- 编辑 position、scale、rotation、depth，并生成稳定 CRLF CK3 文本；
- 展开简单静态 `@变量`，诊断多顶层、重复标量、`parent` 与未知字段；
- 浏览器构图近似预览，明确不冒充 CK3 最终渲染；
- 通过本机 Quarkus 伴随服务调用 typed MCP：读取基础游戏资源目录与单个 DDS、获取 session revision、原生检测/应用和 Copy/export；
- 在浏览器解码原版 DXT1 pattern / DXT5 colored emblem 的顶层 mip，显示真实纹理通道近似；调色、mask 与 CK3 shader 仍不冒充逐像像素一致。

引擎证据与完整正反例矩阵见
[`../docs/ck3-coat-of-arms-clipboard-import-capability.md`](../docs/ck3-coat-of-arms-clipboard-import-capability.md)。

## 开发

```powershell
pnpm install
pnpm test
pnpm build
pnpm dev
```

浏览器不能直接启动本机 stdio MCP，所以 `backend/` 提供必要且很薄的 Maven + Java + Quarkus 伴随服务。它只允许调用
`ck3_take_snapshot` 和四项 CoA MCP 工具，不实现第二套解析器，也不触碰 OCR、鼠标或屏幕。

## 启动伴随服务

需要 JDK 17+、Maven，以及已经安装 Python MCP SDK 的 Python 环境。以下路径按本机 checkout 修改；state 目录必须是专用目录：

```powershell
$env:COA_MCP_PYTHON='D:\path\to\python.exe'
$env:COA_MCP_PYTHONPATH='D:\path\to\repo\ck3_autonomous_player\src'
$env:COA_MCP_STATE_DIR='D:\path\to\coa-companion-state'
$env:XAR_CK3_GAME_DIR='D:\path\to\Crusader Kings III'
mvn -f backend/pom.xml quarkus:dev
```

前端默认访问 `http://localhost:8080`；需要改变地址时设置 `VITE_CK3_COMPANION_URL`。伴随服务公开：

| REST | MCP | 是否需要已运行的 CK3 |
|---|---|---:|
| `GET /api/ck3/coat-of-arms/resources` | `ck3_query_coat_of_arms_resource_catalog_v1` | 否，只读安装目录 |
| `GET /api/ck3/coat-of-arms/asset` | `ck3_read_coat_of_arms_resource_asset_v1` | 否，只读 manifest 内的精确 DDS |
| `GET /api/ck3/coat-of-arms/session` | `ck3_take_snapshot` | 是 |
| `POST /api/ck3/coat-of-arms/probe` | `ck3_probe_coat_of_arms_source_v1` | 是，且需打开纹章设计器 |
| `POST /api/ck3/coat-of-arms/export` | `ck3_export_coat_of_arms_source_v1` | 是，且需打开纹章设计器 |

后端测试与可运行包：

```powershell
mvn -f backend/pom.xml test
mvn -f backend/pom.xml package
java -jar backend/target/quarkus-app/quarkus-run.jar
```

实现依据为 [Quarkus REST Jackson](https://quarkus.io/extensions/io.quarkus/quarkus-rest-jackson/) 和
[MCP Java SDK stdio client](https://java.sdk.modelcontextprotocol.io/latest/client/)。

仓库内的原生 `ck3_export_coat_of_arms_source_v1` MCP Copy/export primitive 已完成静态构建与 closed-schema 测试，
尚未在真实 CK3 进程中验收；浏览器与伴随服务接线已经完成，但不会用 REST mock、OCR 或屏幕自动化冒充 live 能力。

`ck3_query_coat_of_arms_resource_catalog_v1` 已能在不启动 CK3 的情况下分页读取 exact 1.19.0.6 基础游戏 designer manifest；
它已经接入前端，并通过 `REST → Java MCP SDK → Python stdio MCP` 对本机安装完成后台贯通；结果明确不声称包含
DLC/mod 覆盖或运行时资源注册状态。
