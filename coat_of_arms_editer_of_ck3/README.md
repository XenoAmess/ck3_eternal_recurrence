# CK3 家徽编辑器

Vue 3 + Element Plus + TypeScript 实现的 CK3 静态纹章代码编辑器。它只覆盖原版“从剪贴板粘贴”所读取的
coat-of-arms render description，不把该入口描述成任意 CK3 脚本执行器。

## 当前能力

- 解析 `name = { ... }`、注释、紧凑/多行排版和 `rgb` / `hsv` typed block；拒绝 wrapper 外杂项及未声明、循环或重复的静态 `@变量`；
- 通过浏览器 Clipboard API 一键读取剪贴板文本并立即进入同一解析/诊断流程；浏览器权限或安全上下文不满足时明确报错；
- 编辑 pattern、三通道颜色、重复 `colored_emblem`、mask 和重复 instance；
- 对唯一已由原生 MCP 应用并 Copy 保留的 `textured_emblem = { texture = "_default.dds" }` 提供明确标限的解析、编辑、原始纹理预览和导出；不生成未验证字段，也暂不把该层合成进最终家徽；
- 编辑 position、scale、rotation、depth，并生成稳定 CRLF CK3 文本；
- 导入后继续对表单模型执行确定性校验：颜色语法、可打印 ASCII 资源名、有限数值和原生 128 KiB 上限不合格时，禁止复制或发送 MCP；
- 内置 exact 1.19.0.6 的机器可读语法能力矩阵，逐项展示例子、原生 `detected/applied/not_detected` 结果、编辑器策略与证据边界；
- 展开简单静态 `@变量`；保留已证实可应用/Copy 的受限 `parent` 数据库引用；重复标量按 CK3 后值优先并警告，多顶层仍阻止静默丢数据；
- 通过本机 Quarkus 伴随服务调用 typed MCP：读取基础游戏资源目录、单个 DDS、渲染支撑数据、当前 `dlc_load.json`、目录/ZIP 模组 manifest 与 DDS 候选，以及运行中 CK3 的 effective feature / script `has_dlc` truth；获取 session revision，执行原生检测/应用、Copy/export，并以固定的原生王朝 Finish 动作提交回角色设计器；
- 在浏览器解码原版 DXT1 pattern、DXT5 colored emblem、`coa_mask_texture.dds` 以及 `_default.dds` 使用的无压缩 BGRA8 顶层 mip；
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
`ck3_take_snapshot`、九项 CoA MCP 工具、一项原生 runtime-feature 查询和两项固定 CoA 页面动作，不实现第二套后端解析器，也不触碰 OCR、鼠标或屏幕。

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
| `POST /api/ck3/coat-of-arms/open-native-designer` | `ck3_activate_frontend_coat_of_arms_designer_v1` | 是，且需停在角色设计器；只接受固定王朝家徽按钮 |
| `POST /api/ck3/coat-of-arms/commit-native-design` | `ck3_commit_frontend_dynasty_coat_of_arms_v1` | 是，且需停在王朝家徽页；只接受固定 `dynasty_finish_button`，成功后验证返回角色设计器 |
| `GET /api/ck3/coat-of-arms/resources` | `ck3_query_coat_of_arms_resource_catalog_v1` | 否，只读安装目录 |
| `GET /api/ck3/coat-of-arms/asset` | `ck3_read_coat_of_arms_resource_asset_v1` | 否，只读 manifest 内的精确 DDS |
| `GET /api/ck3/coat-of-arms/render-support` | `ck3_read_coat_of_arms_render_support_v1` | 否，只读 shader、命名颜色、surface mask 与 `_default.dds` |
| `GET /api/ck3/coat-of-arms/load-configuration` | `ck3_query_coat_of_arms_load_configuration_v1` | 否，只读 `dlc_load.json`、描述符与目录模组候选 |
| `GET /api/ck3/coat-of-arms/dlc-sources` | `ck3_query_coat_of_arms_installed_dlc_sources_v1` | 否，只读安装树 `.dlc` 描述符与九类 CoA 目录；不证明授权或 mount |
| `GET /api/ck3/coat-of-arms/runtime-features` | `ck3_query_loaded_feature_manifest_v1` | 是，同一 snapshot 读取 44 项 effective feature 与 script `has_dlc` key；不证明 entitlement 或 CoA 资源胜者 |
| `GET /api/ck3/coat-of-arms/configured-resources` | `ck3_query_coat_of_arms_configured_resource_catalog_v1` | 否，分页读取目录/ZIP 模组 manifest 候选与同名冲突 |
| `GET /api/ck3/coat-of-arms/configured-asset` | `ck3_read_coat_of_arms_configured_resource_asset_v1` | 否，以绑定当前配置的 opaque ID 读取模组 DDS |
| `GET /api/ck3/coat-of-arms/session` | `ck3_take_snapshot` | 是 |
| `GET /api/ck3/coat-of-arms/binding` | `ck3_get_capabilities`，有 snapshot 时再调用 `ck3_take_snapshot` | 是；返回 probe/export 可用的 snapshot revision 或精确 frontend `revision=0` |
| `POST /api/ck3/coat-of-arms/probe` | `ck3_probe_coat_of_arms_source_v1` | 是，且需打开纹章设计器 |
| `POST /api/ck3/coat-of-arms/export` | `ck3_export_coat_of_arms_source_v1` | 是，且需打开纹章设计器 |

后端测试与可运行包：

```powershell
mvn -f backend/pom.xml test
mvn -f backend/pom.xml package
java -jar backend/target/quarkus-app/quarkus-run.jar
```

当前基线：Vitest `40/40`、Vite production build、Quarkus REST `15/15` 与 Maven test 均 GREEN。
“打开原生家徽页”和“提交回角色设计器”都只调用固定、零参数的王朝家徽 MCP，并要求独立 route 后置条件；它们不会接受浏览器传入的控件名、路径、指针或桌面输入。提交动作已经完成静态实现与定向测试，真实 CK3 往返证据将在受管实机验收后单独记录。

probe/export 不再错误地假设家徽页必有 gameplay snapshot。binding 端点先验证 native-headless、named-pipe、exact
CK3 `1.19.0.6`/EXE SHA、连接代次/PID 及 probe/export capability；有 snapshot 时返回其正 revision，没有 snapshot
时返回原生合同允许的 frontend `revision=0`。断线、build 不匹配或 capability 缺失都会 fail closed。

底层动作已由受管实机 artifact `mcp-frontend-route-coa-page-live5.json` 闭合为 `production-live primitive`：官方 MCP
独立观察到 `coat_of_arms_designer` 以及可见、enabled 的 `coat_of_arms_page`，Steam 离线与 cleanup 均为 GREEN。
该证据不覆盖角色设计器上层 Finish。

Mask 编辑只接受整数分区索引 1、2、3。exact 原版语料实际使用 `{ 1 }`、`{ 2 }`、`{ 2 3 }`；MCP 进一步实际应用了
`{ 1 2 3 }`，且原生 Copy 将它作为默认全通道省略。随附 shader 对应 R/G/B 三通道。其他值会形成阻止导出的诊断，不会被输入框静默丢弃。

15 例受管实机矩阵进一步证明：重复标量取最后值、多 outer 取第一个、静态变量在 Copy 时展开、
`parent` 原样保留、注释丢弃、HSV 规范化为 RGB、空块与受限 textured emblem 均可应用。该轮全程只使用官方 MCP，
artifact SHA-256 为 `0C5F2F88765224219F7F824DD9F1215E4D2B9EBAB024F0677B5F7506D8F5F84A`。

实现依据为 [Quarkus REST Jackson](https://quarkus.io/extensions/io.quarkus/quarkus-rest-jackson/) 和
[MCP Java SDK stdio client](https://java.sdk.modelcontextprotocol.io/latest/client/)。

仓库内的原生 `ck3_export_coat_of_arms_source_v1` MCP Copy/export primitive 已在 CK3 `1.19.0.6` 真实进程完成同会话
apply → export → reapply → export。两次引擎 canonical 输出均为 327 bytes、SHA-256
`9F84F667B413D2BA24FA101A28D6F455AD93B638F90D9C2A21A91EF264B93C93`，证明该实测字段组合已形成原生 fixed point。
真实浏览器 live UI 随后完成“连接 → 应用到设计器 → 从 CK3 读取”：Vue 实际发出的 3 次 session GET、1 次 probe POST 和
1 次 export POST 全部 HTTP 200，并经 `Quarkus REST → MCP Java SDK → Python stdio MCP → native bridge` 到达同一 CK3
designer。probe 为 `applied`，原生 Copy/export 返回 483-byte CRLF canonical 源码，前端重新解析后诊断为空。该闭环仍只证明
designer working state；上层 Finish/持久化、运行时 DLC/mod effective registry 和 CK3 原生像素回读尚未完成。

`ck3_query_coat_of_arms_resource_catalog_v1` 已能在不启动 CK3 的情况下分页读取 exact 1.19.0.6 基础游戏 designer manifest；
它已经接入前端，并通过 `REST → Java MCP SDK → Python stdio MCP` 对本机安装完成后台贯通；结果明确不声称包含
DLC/mod 覆盖或运行时资源注册状态。`ck3_read_coat_of_arms_render_support_v1` 另行绑定五份 Clausewitz/Jomini/game
shader 源文件、15 个原版命名颜色、256×256 DXT1 surface mask，以及唯一原版 textured-emblem 素材 `_default.dds`。
后者经离线官方 MCP SDK 读取为 96×96、7 mip、49,272 bytes 的无压缩 BGRA8，SHA-256 为
`697430F86ABD26B5056A8779E4BF78C7CB526A57B5AD13F02898BA64B89526CC`。浏览器当前只显示其原始纹理，不声称这是最终合成像素。

`ck3_query_coat_of_arms_load_configuration_v1` 只把当前 `dlc_load.json` 的有序 `enabled_mods` 映射到 `.mod`
描述符，并枚举目录模组九类 `common/gfx/coat_of_arms` 直接候选文件。它不读取启动器 SQLite，不解压 archive，不执行
资源覆盖/merge，也不把启动配置冒充为引擎已经 mount 的运行时状态。

`ck3_query_coat_of_arms_installed_dlc_sources_v1` 另行扫描 exact 安装树的 `.dlc` 描述符及其内容根。本机 29 份描述符中，
九类 `common/gfx/coat_of_arms` 直接目录候选为 0 个 TXT、0 个 DDS；这说明当前 CoA designer 素材不由这些 DLC 内容树追加，
但不证明用户商店授权，也不证明引擎是否 mount 某个 DLC。

configured-resource catalog 在此基础上解析目录模组及 ZIP archive 内的 designer manifest，标出同名候选并保留配置顺序；
archive 通过中央目录有界直读，不解压到磁盘。asset reader
只能接受 catalog 返回且仍属于当前配置的 opaque candidate ID。前端用独立候选表显示来源与同名冲突，并允许用户显式选择
某个候选做精确 DDS 预览；在引擎 precedence/merge 尚未取得原生证据前，它不会擅自选 effective winner，也不会把候选
混入基础游戏下拉框。

运行态按钮另行调用既有的 exact-build `loaded-feature-manifest-v1` 原生 reader：成功时显示当前进程 44 个 feature 中为真的数量和
script `has_dlc` key 数量；不可用时保留 typed reason。该结果比磁盘 DLC 描述符更接近当前进程实际 gameplay gate，但仍不把
feature key 推导成商店 entitlement，也不声称已经找到 DLC/mod 家徽 DDS 的最终 VFS/registry 胜者。
