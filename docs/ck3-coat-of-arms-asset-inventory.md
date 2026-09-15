# CK3 1.19.0.6 家徽 DDS 完整性审计

## 结论

当前跟踪并由 GitHub Pages 部署的 `ck3-1.19.0.6` 素材包覆盖本机 exact build 的
`game/gfx/coat_of_arms/**/*.dds` **1,630/1,630 个物理源文件**。这里的“完整”严格限定为 CK3 基础游戏
1.19.0.6 该目录的 DDS 树，不外推为其他游戏版本、玩家模组、Workshop 覆盖或尚未发现的非 DDS 数据。

设计器 manifest 注册了 42 个 pattern 和 1,578 个 colored emblem；其中 42 + 1,577 个可由已实证的 ASCII 剪贴板入口
表达并进入自动拟合候选库。剩余一个注册 emblem 的文件名含高位字符，当前原生 reader 已证明会拒绝这种输入，因此只收录、
不自动生成。目录里另有 8 个未注册 colored-emblem 文件；它们同样被完整收录和标记，但在取得原生剪贴板接受证据前不由拟合器自动生成。一个
`_default.dds` textured emblem 和一个 surface mask 属于渲染支持，也不混入 colored-emblem 搜索。

这修正了此前 Alpha 裁剪包“38 个可见 pattern + 前 128 个可见 emblem”的不完整状态。旧包遗漏 1,463 个物理 DDS，
并遗漏 1,448 个可见、manifest 已注册的 emblem；它不能代表原版素材全集。

## 物理文件盘点

审计于 2026-09-15 只读本机 CK3 安装树完成，没有启动游戏。

| 原版目录/角色 | 物理 DDS | 源字节数 | Web pack 策略 |
|---|---:|---:|---|
| `patterns/` | 42 | 1,578,840 | 42 个全部收录并可拟合 |
| `colored_emblems/` | 1,586 | 136,717,436 | 1,578 个已注册（1,577 可粘贴拟合）；8 个未注册仅收录 |
| `textured_emblems/` | 1 | 49,272 | `_default.dds` 渲染支持 |
| surface mask | 1 | 43,832 | 浏览器 shader 近似预览支持 |
| 合计 | **1,630** | **138,389,380** | **1,630/1,630** |

content-addressed 去重后是 1,626 份唯一 DDS bytes；manifest 仍保留全部 1,630 个物理源路径和逻辑身份，因此重复内容不会
被误算成漏文件。

## 设计器 manifest 注册边界

| 类型 | 注册总数 | 原生网格可见 | manifest 隐藏 |
|---|---:|---:|---:|
| pattern | 42 | 38 | 4 |
| colored emblem | 1,578 | 1,576 | 2 |

隐藏 pattern 为：

- `pattern_solid.dds`
- `pattern_checkers_01.dds`
- `pattern_chief.dds`
- `pattern_horizontal_bar_01.dds`

隐藏 emblem 为 `ce_empty.dds` 与 `ce_blank.dds`。它们仍是 manifest 注册身份，完整包予以保留；空白资源不会带来实际残差
改善，正常情况下不会被贪心拟合选中。

1,578 个注册 emblem 的分类计数为：abstract 77、animals 167、chinese_seal 283、circles_spirals 73、
crosses_and_knots 138、faiths 44、figures 22、kamon 97、manmade 115、nature 99、patterns 222、
tribal_seal 169、writing 70、无分类 2。manifest 引用的 DDS 全部在磁盘存在，没有 missing-on-disk 项。

注册资源 `ce_mount_fleurdelisé.dds` 的名字包含 `é`。当前 exact-build 原生 reader 对高位 UTF-8 字节会提前退出，因此该项虽可
由原版 UI 内部选择，却不能由本项目已经证明的剪贴板输入合同可靠表达。pack 将它保留为
`registration=designer_manifest`，但标成 `fit_eligible=false`；这是“素材完整”与“可执行代码完整”之间唯一的已知注册项差异。

## 目录存在但未注册的 8 个文件

以下文件存在于 `colored_emblems/`，但不在基础游戏设计器 manifest 中：

- `ce_kamon_hole.dds`
- `ce_lentil.dds`
- `ce_question_mark.dds`
- `ce_seal_name_gui_80dc.dds`
- `ce_seal_pictorial_frame_gourd.dds`
- `ce_seal_pictorial_frame_gourd_full.dds`
- `ce_seal_pictorial_frame_tripod.dds`
- `ce_seal_pictorial_frame_tripod_full.dds`

manifest 将它们标成 `kind=auxiliary_colored_emblem`、`registration=unregistered_file`、`fit_eligible=false`。
“磁盘可读”不等于“设计器注册”或“剪贴板代码可执行”；因此它们不会被自动写进用户代码。后续若要放行，必须先通过
开发期 MCP 原生 apply → Copy/export fixed-point 实证，再修改白名单。

## 当前冻结包回执

| 字段 | 值 |
|---|---|
| pack id | `ck3-1.19.0.6-base-complete-42p-1578e-8aux` |
| manifest bytes | 1,042,018 |
| manifest SHA-256 | `AD7F0A911A2B4F002E923FEAB13716566D9A7B61447E9092504826FE6498FE91` |
| 物理资源项 | 1,630 |
| 唯一 DDS payload | 1,626 |
| fit index 条目 | 1,619（42 pattern + 1,577 可粘贴 registered emblem） |
| fit index bytes | 6,631,424（32×32 RGBA8） |

浏览器首先下载并校验 fit index，搜索完整注册库；只有选中的 pattern/emblem 才再下载全分辨率 DDS 进行预览和最终评分。
这避免首轮拟合必须同时解码约 132 MiB 压缩 DDS及其更大的 RGBA 展开数据。

## 可复现门禁

从 `coat_of_arms_editer_of_ck3` 运行：

```text
python -m pip install -r tools/requirements-pack.txt
python tools/build_web_asset_pack.py --game-root "<CK3 1.19.0.6 installation root>" --output "<new output directory>"
python tools/verify_web_asset_pack.py public/asset-packs/ck3-1.19.0.6
```

builder 默认包含隐藏注册项并拒绝覆盖既有输出。完整模式会对原版 CoA DDS 树和 manifest 项做集合闭合；少一个源路径、多一个
伪造路径或内容身份不一致都会失败。verifier 不读取或启动 CK3，会重新核对 1,630 个逻辑项、1,626 份 content-addressed
DDS、fit index 的精确长度/SHA、注册角色、物理源路径唯一性和 inventory 计数。

素材版本管理与 Pages 发布依据项目所有者 2026-09-15 的明确授权。该项目政策记录不转移 Paradox 素材所有权。
