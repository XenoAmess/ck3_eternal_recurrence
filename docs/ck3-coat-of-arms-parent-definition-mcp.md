# CK3 家徽 `parent` 定义：MCP 静态来源合同

更新时间：2026-09-16（Asia/Shanghai）

## 结论

开发侧 MCP 现在可以在**不启动 CK3**的情况下，对 exact 1.19.0.6 基础游戏
`game/common/coat_of_arms/coat_of_arms/**/*.txt` 建立有界、可分页、SHA-256 绑定的定义索引，并读取某个 key 的完整原始定义。新增工具：

- `ck3_query_coat_of_arms_definition_catalog_v1`
- `ck3_read_coat_of_arms_definition_v1`

这补上了此前 MCP 只能读设计器 DDS manifest、启动配置候选和 DLC 物理文件、却不能结构化取得 `parent` 目标定义的缺口。它是开发/研究输入，
不进入 Pages 生产运行链路；正式网页仍只消费仓库冻结的静态 asset pack。后续 R21 原生矩阵进一步证明：角色设计器剪贴板路径虽然保留
`parent` 文本，却不会在预览里物化该 definition，因此静态读取能力不能直接用于冒充原生剪贴板预览。

## 已实现合同

查询工具按稳定 key 排序返回分页结果，逐项包含：

- key、候选数、`block / alias / scalar` 分类与别名目标；
- 相对游戏目录的来源路径、起止行、文件内序号；
- 定义源码和来源文件的 UTF-8 bytes 与 SHA-256；
- 整组 source file 数量、bytes 和 content manifest SHA-256；
- exact `ck3.exe` SHA-256/build 绑定。

读取工具保留直接候选完整源码，并且只在每一跳都唯一时解析静态别名链。以下情况 fail closed 并返回显式状态，不挑一个“看起来合理”的来源：

- 同一 key 有多个静态候选：`ambiguous_source_candidates`；
- 别名循环：`alias_cycle`；
- 缺少 key 或别名目标：`missing / alias_target_missing`；
- 非标量别名值：`unsupported_scalar`；
- 超过 32 跳、单文件 8 MiB、全集 64 MiB 或单定义 256 KiB 的有界资源合同。

词法扫描器专门允许 CK3 家徽中的匿名向量/列表块，例如
`position = { @x 0.5 }`，不会拿只适用于 `key = value` manifest 的严格 parser 错判真实定义。字符串内 `#`、注释、嵌套块和 UTF-8 BOM
均有测试覆盖。

## exact-build 实测

在本机冻结的 CK3 1.19.0.6 安装上，集成用例通过：

- `k_england` 唯一解析为完整 block，源码包含 `pattern_solid.dds`；
- `d_agder` 唯一解析别名链 `d_agder → c_agder → block`；
- 目录分页查询可找到 England 相关定义；
- 全程没有启动 CK3、Steam、桌面输入或 OCR。

MCP SDK 合同测试同时证明两个新工具的输入 schema 都拒绝未知字段；fixture 覆盖分页、匿名向量、两文件重复 key、别名链、循环、缺失和非法路径式 key。

复现命令：

```bat
set PYTHONPATH=ck3_autonomous_player\src
tools\.venv\Scripts\python.exe -m unittest ck3_autonomous_player.tests.unit.test_coat_of_arms_definition_catalog_v1 ck3_autonomous_player.tests.unit.test_coat_of_arms_resource_catalog_v1 ck3_autonomous_player.tests.unit.test_coat_of_arms_load_configuration_v1 ck3_autonomous_player.tests.unit.test_coat_of_arms_dlc_sources_v1 ck3_autonomous_player.tests.unit.test_coat_of_arms_configured_resources_v1 -v

set CK3_GAME_DIRECTORY=C:\SteamLibrary\steamapps\common\CRUSAD~1
tools\.venv\Scripts\python.exe -m unittest ck3_autonomous_player.tests.unit.test_coat_of_arms_definition_catalog_v1.CoatOfArmsDefinitionCatalogV1Tests.test_exact_build_indexes_and_resolves_real_base_definitions -v
```

## 原生剪贴板预览语义（R21）

`parent` 的运行时语义已经通过新增的 reference-free framebuffer MCP 做了独立矩阵。R21 在 CK3 启动前预先登记 8-bit 捕获噪声门限，
随后在同一受管会话中完成七个 Apply → 原生 Copy → capture case：

- `parent=k_england` 与不存在的 `parent=c_england` 在门限内等价；
- `parent=k_england color1=blue` 与 `parent=k_england` 在门限内等价；
- 添加显式 `ce_block_02.dds` child 后明显不等价；
- 将 `k_england` 静态 definition 显式写成 `pattern_solid.dds + ce_wyvern.dds` 后，与 parent case 明显不等价。

三项正式诊断门禁均通过，完整紧凑证据见
[`parent-semantics-native-r21`](coat-of-arms-fit-artifacts/parent-semantics-native-r21/README.md)。这证明 exact 1.19.0.6 的角色设计器剪贴板路径只保存引用、
不物化继承图案；它不证明其他数据库加载路径也忽略 `parent`。

为取得该证据，开发 MCP 新增 `ck3_capture_frontend_coat_of_arms_framebuffer_v1`：它必须消费同一 native process/route/generation 的 v3 calibration，
只返回有界的对齐 PNG、尺寸和 SHA-256，不接受参考图、屏幕坐标、OCR 或输入动作。这样测试数据无法反向参与定位或配准。

## 证据边界与下一接点

这份合同证明的是**基础游戏静态来源与无歧义别名**，不是 CK3 运行时已经完成的继承合成：

- 不展开 `@变量` 或 `@[表达式]`；
- 不声称 `parent` 与子对象字段的覆盖/追加规则；
- 不声称 DLC、mod、replace_path 或同名文件的实际 VFS 胜者；
- 不声称来源 definition 一定是当前 native 会话中的注册对象；
- 不提供生产网页对本机游戏目录的访问。

因此生产网页继续保真解析/编辑/导出 `parent`，并显式说明只预览 source 中直接写出的 pattern/child，不自动展开静态数据库 definition。
如果未来提供“解析数据库定义”的辅助视图，必须与“CK3 剪贴板预览”分开命名和展示。DLC/mod 胜者仍须由后续 MCP 运行时 mount/VFS
证据确认，不能仅按文件顺序猜测。
