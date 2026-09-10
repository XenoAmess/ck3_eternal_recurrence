# CK3 家徽编辑器

Vue 3 + Element Plus + TypeScript 实现的 CK3 静态纹章代码编辑器。它只覆盖原版“从剪贴板粘贴”所读取的
coat-of-arms render description，不把该入口描述成任意 CK3 脚本执行器。

## 当前能力

- 解析 `name = { ... }`、注释、紧凑/多行排版和 `rgb` / `hsv` typed block；
- 编辑 pattern、三通道颜色、重复 `colored_emblem`、mask 和重复 instance；
- 编辑 position、scale、rotation、depth，并生成稳定 CRLF CK3 文本；
- 展开简单静态 `@变量`，诊断多顶层、重复标量、`parent` 与未知字段；
- 通过本机 Quarkus 伴随服务调用 typed MCP：读取基础游戏资源目录、单个 DDS、渲染支撑数据、当前 `dlc_load.json` 以及目录/ZIP 模组 manifest 与 DDS 候选，获取 session revision，执行原生检测/应用和 Copy/export；
- 在浏览器解码原版 DXT1 pattern / DXT5 colored emblem 与 `coa_mask_texture.dds` 的顶层 mip；
- 按 CK3 随附的 Clausewitz/Jomini shader 源码翻译三通道调色、pattern mask、flip→rotate→scale→translate、surface detail 和 alpha blend；GPU 采样/色彩空间及引擎未公开的 `FallbackColor` 绑定仍不冒充逐像素一致。

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
`ck3_take_snapshot` 和八项 CoA MCP 工具，不实现第二套后端解析器，也不触碰 OCR、鼠标或屏幕。

## 启动伴随服务

需要 JDK 17+、Maven，以及已经安装 Python MCP SDK 的 Python 环境。以下路径按本机 checkout 修改；state 目录必须是专用目录：

```powershell
$env:COA_MCP_PYTHON='D:\path\to\python.exe'
$env:COA_MCP_PYTHONPATH='D:\path\to\repo\ck3_autonomous_player\src'
$env:COA_MCP_STATE_DIR='D:\path\to\coa-companion-state'
$env:XAR_CK3_GAME_DIR='D:\path\to\Crusader Kings III'
$env:XAR_CK3_USER_DIR='C:\Users\name\Documents\Paradox Interactive\Crusader Kings III'
mvn -f backend/pom.xml quarkus:dev
```

前端默认访问 `http://localhost:8080`；需要改变地址时设置 `VITE_CK3_COMPANION_URL`。伴随服务公开：

| REST | MCP | 是否需要已运行的 CK3 |
|---|---|---:|
| `GET /api/ck3/coat-of-arms/resources` | `ck3_query_coat_of_arms_resource_catalog_v1` | 否，只读安装目录 |
| `GET /api/ck3/coat-of-arms/asset` | `ck3_read_coat_of_arms_resource_asset_v1` | 否，只读 manifest 内的精确 DDS |
| `GET /api/ck3/coat-of-arms/render-support` | `ck3_read_coat_of_arms_render_support_v1` | 否，只读 shader、命名颜色与 surface mask |
| `GET /api/ck3/coat-of-arms/load-configuration` | `ck3_query_coat_of_arms_load_configuration_v1` | 否，只读 `dlc_load.json`、描述符与目录模组候选 |
| `GET /api/ck3/coat-of-arms/configured-resources` | `ck3_query_coat_of_arms_configured_resource_catalog_v1` | 否，分页读取目录/ZIP 模组 manifest 候选与同名冲突 |
| `GET /api/ck3/coat-of-arms/configured-asset` | `ck3_read_coat_of_arms_configured_resource_asset_v1` | 否，以绑定当前配置的 opaque ID 读取模组 DDS |
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
DLC/mod 覆盖或运行时资源注册状态。`ck3_read_coat_of_arms_render_support_v1` 另行绑定五份 Clausewitz/Jomini/game
shader 源文件、15 个原版命名颜色和 256×256 DXT1 surface mask；本机后台 REST→Java SDK→Python MCP 贯通后，mask
的 43,832 bytes 与 SHA-256 `5FA2A49DC59AEEBA19709B6BB3F9D0B017ACDE7DC576793705EAF85C7F33691E` 解码复核一致。

`ck3_query_coat_of_arms_load_configuration_v1` 只把当前 `dlc_load.json` 的有序 `enabled_mods` 映射到 `.mod`
描述符，并枚举目录模组九类 `common/gfx/coat_of_arms` 直接候选文件。它不读取启动器 SQLite，不解压 archive，不执行
资源覆盖/merge，也不把启动配置冒充为引擎已经 mount 的运行时状态。

configured-resource catalog 在此基础上解析目录模组及 ZIP archive 内的 designer manifest，标出同名候选并保留配置顺序；
archive 通过中央目录有界直读，不解压到磁盘。asset reader
只能接受 catalog 返回且仍属于当前配置的 opaque candidate ID。前端目前显示候选计数，但在引擎 precedence/merge 尚未取得
原生证据前，不会擅自把某个同名候选选成 effective winner，也不会把这些候选混入基础游戏下拉框。
