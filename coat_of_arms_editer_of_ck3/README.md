# CK3 家徽编辑器

Vue 3 + Element Plus + TypeScript 实现的独立 CK3 静态纹章代码编辑器和图片拟合器。正式 Web 平台不安装、启动或连接
CK3，不依赖 MCP、Quarkus 或 Java；它只生成原版“从剪贴板粘贴”所读取的 coat-of-arms render description，
不把该入口描述成任意 CK3 脚本执行器。

## 当前能力

- 解析 `name = { ... }`、注释、紧凑/多行排版和 `rgb` / `hsv` typed block；拒绝 wrapper 外杂项及未声明、循环或重复的静态 `@变量`；
- 通过浏览器 Clipboard API 一键读取剪贴板文本并立即进入同一解析/诊断流程；浏览器权限或安全上下文不满足时明确报错；
- 在浏览器内解码用户选择的 PNG/JPEG/WebP，以可取消 Web Worker 对完整的 42 pattern / 1,577 个可粘贴 registered emblem 索引执行
  双路径重建：小预算做透明轮廓粗筛、background/layer beam 与连续 transform 精化；大预算从纯色背景重复堆叠原生
  `ce_block_02.dds`，以自适应四叉树叶片拼出目标。图片不上传；
- DDS 透明留白、内容重心和旋转后包围盒进入 position/X/Y scale 求解；旋转由整圆种子细化到 1°，再按
  `0.5° → 0.25° → 0.125°` 二分到 0.1° 量级，不再锁死 45°；
- 图层搜索预算默认 6，UI 不设固定产品上限并回归验证 1024 与 10000；预算是最大值而非承诺产出层数。每层必须严格降低
  实际渲染损失，`layerLosses` 保存递减证据；没有改善或用户取消时提前停止，serializer 完整输出全部接受层；
- CPU reference 决定候选，WebGL2 RGBA8 对最终候选做 alpha-weighted 交叉评分；Worker 按背景、轮廓粗筛、连续精筛和原生块重建
  回传真实计数，页面显示阶段进度、无盾面材质拟合平面和 shader/surface-mask 预览；
- 使用 `ck3-coa-web-asset-pack-v1` 静态素材包：manifest 与每个 DDS 都经 SHA-256、字节数、尺寸和格式绑定，正式运行时不读取
  用户的游戏目录；当前 1.19.0.6 pack 覆盖原版 CoA 目录 1,630/1,630 个 DDS，并将 8 个未注册辅助文件明确排除在自动拟合外；
- 编辑 pattern、三通道颜色、重复 `colored_emblem`、mask 和重复 instance；
- 对唯一已由原生 MCP 应用并 Copy 保留的 `textured_emblem = { texture = "_default.dds" }` 提供明确标限的解析、编辑、原始纹理预览和导出；不生成未验证字段，也暂不把该层合成进最终家徽；
- 编辑 position、scale、rotation、depth，并生成稳定 CRLF CK3 文本；
- 导入后继续对表单模型执行确定性校验：颜色语法、可打印 ASCII 资源名和有限数值不合格时禁止复制；超过 128 KiB 只产生警告并
  仍允许浏览器复制，但会禁用当前开发期 MCP probe/apply，因为 128 KiB 是桥接层安全合同，不是已证明的 CK3 原生粘贴上限；
- 内置 exact 1.19.0.6 的机器可读语法能力矩阵，逐项展示例子、原生 `detected/applied/not_detected` 结果、编辑器策略与证据边界；
- 展开简单静态 `@变量`；保留已证实可应用/Copy 的受限 `parent` 数据库引用；重复标量按 CK3 后值优先并警告，多顶层仍阻止静默丢数据；
- 仓库保留本机 Quarkus → typed MCP → CK3 原生桥作为开发期研究/验收夹具；默认正式界面不显示这些控件，独立浏览器 E2E
  断言完整图片拟合过程中没有任何 `/api/` 请求；
- 在浏览器解码原版 DXT1 pattern、DXT5 colored emblem、`coa_mask_texture.dds` 以及 `_default.dds` 使用的无压缩 BGRA8 顶层 mip；
- 按 CK3 随附的 Clausewitz/Jomini shader 源码翻译三通道调色、pattern mask、flip→rotate→scale→translate、surface detail 和 alpha blend；GPU 采样/色彩空间及引擎未公开的 `FallbackColor` 绑定仍不冒充逐像素一致。

引擎证据与完整正反例矩阵见
[`../docs/ck3-coat-of-arms-clipboard-import-capability.md`](../docs/ck3-coat-of-arms-clipboard-import-capability.md)。
用户图片只在浏览器内使用原生元素做近似重建的可行性、WebGL2/CPU 架构、隐私边界和 Alpha 门禁见
[`../docs/ck3-coat-of-arms-image-fitting-feasibility.md`](../docs/ck3-coat-of-arms-image-fitting-feasibility.md)。
当前 Alpha 的逐项交付状态、exact-build 本地素材包 receipt、验收命令与已知限制见
[`../docs/ck3-coat-of-arms-editor-alpha.md`](../docs/ck3-coat-of-arms-editor-alpha.md)。
红色规则分割线修复、MCP 大载荷原生闭环、剪枝压缩、10,000 层压力门禁与完整 Beta 顺序见
[`../docs/ck3-coat-of-arms-editor-beta-plan.md`](../docs/ck3-coat-of-arms-editor-beta-plan.md)。

## 在线版本

GitHub Pages 正式入口为 <https://xenoamess.github.io/ck3_eternal_recurrence/>。仓库中的
[`coat-of-arms-editor-pages.yml`](../.github/workflows/coat-of-arms-editor-pages.yml) 在 `master` 的本目录内容变化后自动执行
素材包校验、Vitest、Playwright 独立浏览器验收和 production build，全部通过后才部署。线上页面包含已获项目授权的 exact
CK3 1.19.0.6 DDS pack，但运行时仍不安装、启动或连接 CK3。

部署合同、GitHub Pages 设置和故障边界见
[`../docs/ck3-coat-of-arms-github-pages.md`](../docs/ck3-coat-of-arms-github-pages.md)。

## 开发

```text
pnpm install
pnpm test
pnpm test:e2e
pnpm build
pnpm dev
```

本地开发者可以从明确给出的 exact-build 安装目录冻结一份部署用静态 pack。项目所有者已于 2026-09-15 明确将当前
CK3 1.19.0.6 pack 视为本仓库版本管理与 GitHub Pages 发布所授权的素材；其他 build 的生成目录仍默认忽略，需逐项审阅后再纳入：

```text
python -m pip install -r tools/requirements-pack.txt
python tools/build_web_asset_pack.py --game-root "<CK3 installation root>" --output public/asset-packs/ck3-1.19.0.6
python tools/verify_web_asset_pack.py public/asset-packs/ck3-1.19.0.6
```

浏览器本身不执行这些 Python 命令。Vite 只把已经准备好的静态 pack 复制到 `dist`，部署后的页面不再读取游戏目录。

`backend/` 是开发期研究夹具，不属于最终平台。它提供很薄的 Maven + Java + Quarkus 伴随服务，只允许调用
`ck3_get_capabilities`、`ck3_take_snapshot`、十四项 CoA 专用 MCP 工具和一项原生 runtime-feature 查询，共 17 项；不实现第二套后端解析器，也不触碰 OCR、鼠标或屏幕。

## 仅开发期：伴随服务

需要 JDK 17+、Maven，以及已经安装 Python MCP SDK 的 Python 环境。以下路径按本机 checkout 修改；state 目录必须是专用目录：

```python
import os
import subprocess

environment = os.environ.copy()
environment.update({
    "COA_MCP_PYTHON": r"D:\path\to\python.exe",
    "COA_MCP_PYTHONPATH": r"D:\path\to\repo\ck3_autonomous_player\src",
    "COA_MCP_STATE_DIR": r"D:\path\to\coa-companion-state",
    "XAR_CK3_GAME_DIR": r"D:\path\to\Crusader Kings III",
    "XAR_CK3_USER_DIR": r"C:\Users\name\Documents\Paradox Interactive\Crusader Kings III",
})
subprocess.run(
    ["mvn", "-f", "backend/pom.xml", "quarkus:dev"],
    check=True,
    env=environment,
)
```

最终平台不得启用这一模式。仓库内开发夹具可显式设置 `VITE_ENABLE_CK3_COMPANION=true`；此时前端访问
`http://localhost:8080`，需要改变地址时设置 `VITE_CK3_COMPANION_URL`。伴随服务公开：

| REST | MCP | 是否需要已运行的 CK3 |
|---|---|---:|
| `POST /api/ck3/coat-of-arms/open-native-designer` | `ck3_activate_frontend_coat_of_arms_designer_v1` | 是，且需停在角色设计器；只接受固定王朝家徽按钮 |
| `POST /api/ck3/coat-of-arms/commit-native-design` | `ck3_commit_frontend_dynasty_coat_of_arms_v1` | 是，且需停在王朝家徽页；只接受固定 `dynasty_finish_button`，成功后验证返回角色设计器 |
| `GET /api/ck3/coat-of-arms/native-designer-tree` | `ck3_inspect_frontend_coat_of_arms_tree_v1` | 是；只读检查当前可见的 `coat_of_arms_page` 子树，不接受控件名、路径或指针 |
| `GET /api/ck3/coat-of-arms/native-pattern-grid` | `ck3_inspect_frontend_coat_of_arms_pattern_grid_v1` | 是，且需停在已打开的背景图案页；只读检查编译期固定的无名网格根并要求直接子项完整，不接受控件名、路径、指针或遍历上限 |
| `POST /api/ck3/coat-of-arms/enter-native-custom-mode` | `ck3_activate_frontend_coat_of_arms_custom_mode_v1` | 是，且需停在王朝家徽模式选择页；只接受原版两个互斥固定按钮，并验证背景图案网格可见 |
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

```text
mvn -f backend/pom.xml test
mvn -f backend/pom.xml package
java -jar backend/target/quarkus-app/quarkus-run.jar
```

当前 Alpha v3 基线：Vitest 覆盖多层残差重建、透明输入、透明 DDS 留白、非等比/0.1° 旋转、严格递减原生块路径与完整 fit-index
合同；Playwright 除合成/exact-pack E2E 外固定运行用户 hunter 图的 1024 上限质量门禁；Vite production build、静态 pack verifier、
Quarkus REST `18/18` 与 Maven test 均 GREEN。E2E 同时覆盖合成 pack 和本机生成的 exact 1.19.0.6 pack；
两者都进入 Pages Actions 门禁；缺少已跟踪的 exact-build pack 会直接使部署失败。
“打开原生家徽页”和“提交回角色设计器”都只调用固定、零参数的王朝家徽 MCP，并要求独立 route 后置条件；它们不会接受浏览器传入的控件名、路径、指针或桌面输入。提交动作已在 exact CK3 `1.19.0.6` 完成受管实机往返：Finish 前后重开家徽页的原生 Copy 均为 330 bytes，SHA-256 均为 `4769FD42836E68FA35DC07FBA23BEABCC589E5A33087314F1D6287E5C53C305A`；该结论仍不覆盖完成整个角色创建或战役/存档持久化。

probe/export 不再错误地假设家徽页必有 gameplay snapshot。binding 端点先验证 native-headless、named-pipe、exact
CK3 `1.19.0.6`/EXE SHA、连接代次/PID 及 probe/export capability；有 snapshot 时返回其正 revision，没有 snapshot
时返回原生合同允许的 frontend `revision=0`。断线、build 不匹配或 capability 缺失都会 fail closed。

打开动作已由受管实机 artifact `mcp-frontend-route-coa-page-live5.json` 闭合为 `production-live primitive`：官方 MCP
独立观察到 `coat_of_arms_designer` 以及可见、enabled 的 `coat_of_arms_page`。固定王朝 Finish 则由
`mcp-frontend-dynasty-finish-roundtrip-live7.json` 闭合：动作前精确观察 `dynasty_finish_button`，动作后验证返回
`ruler_designer`，重开后的原生 Copy 与提交前逐字节一致；Steam 离线与 cleanup 均为 GREEN。

`coat_of_arms_page` 专用树检查与固定自定义模式动作已经达到 `production-live primitive`：Python official-MCP/contract 回归、
原生 Release、adapter/mailbox CTest、Quarkus、Vue 和一次受管真实 CK3 official-MCP 路由均已通过。live census 证明 custom mode
背景网格容器实际存在并报告 38 个 child；不过 512 项页面级遍历在进入这些 child 前截断。为此新增的零输入
`ck3_inspect_frontend_coat_of_arms_pattern_grid_v1` 从 `ruler_designer` 经编译期固定路径解析该无名网格，并要求四级有名祖先、
可见性、enabled 状态以及全部直接子项同时成立。它已通过原生 127/127 CTest、Python official-MCP、Quarkus 与 Vue 回归，当前状态为
`mcp-static-ready / live=false`；在新一轮受管 CK3 实机运行完成前，不能声称已由该新工具枚举 38 项，更不能把 GUI 子项外推成
具体 pattern 资源名或同名 DDS 的最终 VFS 胜者。

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
designer working state；王朝 Finish 的后续 MCP 往返已完成，但整个角色创建/战役持久化、运行时 DLC/mod effective registry
和 CK3 原生像素回读尚未完成。

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
