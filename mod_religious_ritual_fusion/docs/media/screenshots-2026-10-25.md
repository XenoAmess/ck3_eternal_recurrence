# R0007 原始截图与商店候选

本清单于 `2026-10-24T23:57:14Z` 在机器 `4-8e1c2f1861` 逐图核对原始 PNG、现有 sidecar 并实际查看画面。机器身份由本轮 `python tools/ck3_live_run_id.py machine` 读回。原图根目录为 `C:/workspace/rrf-development-20261024/screenshots/R0007`，场次为 `4-8e1c2f1861--religious-ritual-fusion--R0007`，场次源码为 `ef195f23393bc83a1b4cfc711734639b359771c7`。

本节保留 R0007 的 **13 张原图，其中 01–09 为业务画面**，合计 58,579,696 B；逐一读取 PNG IHDR 均为 **2560×1440**。没有复制大图、裁切、重命名、AI 修改或发布。后附 R0008 增量；当前29张总索引见[素材入口](README.md)，没有宗教融合模式新图。

## 建议用途

成功结果候选优先顺序为 **09 → 08 → 07**：09 同时显示三个结果核心及“允许离婚”，08 的大卡片适合展示结果核心，07 适合展示实际“融合完成”通知。01／02 可作来源选择流程的辅助图。最终商店排序和上传尚未执行。

03–06 保留为真实业务与 GUI 缺陷参考，**不选作主图**：该场旧 GUI 的教义 radio 没有选中点；选中核心后 footer 越出底边。不能用后续修正后的源码为这些旧图重新标注版本。10–13 明确排除商店用途；13 虽名为 confirmation，实际画面是 Windows 资源管理器。

| 图 | 原文件名 | 可见内容／用途 | 当前选择 |
| --- | --- | --- | --- |
| 01 | `01-rite-source-selector.png` | 原版来源选择器，尚未选 B。 | 辅助候选 |
| 02 | `02-rite-source-selected.png` | 来源 B 的诺曼礼行已高亮。 | 辅助候选 |
| 03 | `03-rite-fusion-draft.png` | 零核心草稿，左右来源及候选列表。 | 缺陷参考，不选主图 |
| 04 | `04-two-cores-require-third.png` | 仅选两核心，确认按钮禁用；footer 已下移。 | 缺陷参考，不选主图 |
| 05 | `05-one-source-contribution-refused.png` | 三核心但 A 独有贡献不足；左右贡献状态可见。 | 缺陷参考，不选主图 |
| 06 | `06-legal-mixed-selection.png` | 两来源均贡献的混合草稿，确认可用；旧 footer／radio 缺陷仍在。 | 缺陷参考，不选主图 |
| 07 | `07-fusion-result-after-confirmation.png` | 实际“融合完成”通知及地图。 | 成功结果候选；建议配文“融合完成，采用结果并记录来源” |
| 08 | `08-result-rite-beliefs.png` | 原版信仰面板展示采用的结果礼仪及天主子民／秘传／占星术。 | 成功结果候选；建议配文“在原版面板查看融合后的核心信条” |
| 09 | `09-result-expanded-doctrines.png` | 展开的原版面板，同时可见三个核心及“允许离婚”。 | 成功结果优先候选；建议配文“融合后的核心与教义” |
| 10 | `10-normal-quit-current.png` | 虽仍显示结果面板，但为退出故障诊断补图。 | **exclude：退出诊断** |
| 11 | `11-normal-quit-menu.png` | 游戏菜单。 | **exclude：退出过程** |
| 12 | `12-normal-quit-confirmation.png` | 退出确认对话框。 | **exclude：退出过程** |
| 13 | `13-confirmation-refreshed.png` | 实际是 Windows 资源管理器，非游戏确认画面。 | **exclude：桌面／文件管理器** |

本清单的视觉选图不替代[该场实机报告](../acceptance/R0007-2026-10-25.md)中的原生结果、存档与闭场结论。结果画面存在不表示整场退出通过；该场的失败闭场记录保持原义。

## 逐图身份与时间

以下时间均为 UTC，日期均为 `2026-10-24`。01–09 的 machine／run／source／捕获 UTC 均来自各自 `.png.json` 并核对 bytes／SHA／桌面尺寸与当前原图一致。10 的 sidecar 有 machine／run／UTC，但没有 source；表内源码只能引用上述场次上下文。11／12 是坐标映射回执，没有捕获 UTC 和源码；13 没有 sidecar。清单不补造这些字段的直接捕获证据。

11–13 的时间标 `mtime`，仅为本轮读取的文件修改时间，**不作为精确捕获时间**；JSON 的 `capture_utc` 保持 `null`。其 machine／run／source 只作场次归档上下文，`identity_basis` 已明确标注，尤其不能把 Explorer 图认定为该源码的产品画面。所有项目的 SHA 与 bytes 均重新读取原图计算。

| 图 | UTC 时间及来源 | bytes | PNG SHA-256 |
| --- | --- | ---: | --- |
| 01 | 23:05:42.888674，capture sidecar | 4,982,657 | `9752144d1c793bd6b138bb83c18c510bb2b9e9256c3206d02ce947396b9ec63e` |
| 02 | 23:06:07.552589，capture sidecar | 4,984,864 | `93107ed2c55eb0f7a75ff7dc2a489a182ac09f2e9611e3743e2a364d296b14cd` |
| 03 | 23:07:35.948329，capture sidecar | 4,541,925 | `ac6e661732def18b4db55fb98a4ed007ce69fe4a30556bc1b1eb43a7cd99603f` |
| 04 | 23:08:44.021067，capture sidecar | 4,525,262 | `fb7a198ea4f55942746346ac00c3146554ad9e4862a8d23f885b0e0bb6419cb5` |
| 05 | 23:09:59.415677，capture sidecar | 4,527,550 | `bc42b010cd4f0c1caaf85547b7f8b86a49c1041dae3e6464a45123e926a3c82a` |
| 06 | 23:12:21.176991，capture sidecar | 4,525,272 | `4ba08660aa3efa35400d17c9f76919f6b0ed40bbb69a1eb3010160fd4135bb54` |
| 07 | 23:14:07.469729，capture sidecar | 5,579,890 | `9e8d1fb732de1fc20d123e9f34b3c9cd9bfc54587d9ca11dd9811dfd311cca82` |
| 08 | 23:16:55.306486，capture sidecar | 5,374,166 | `45da3ce5b50ecdb1e3603561378ee675df516c8e0f2fac3518df660cc2888b55` |
| 09 | 23:20:36.419536，capture sidecar | 5,341,433 | `374777b60c3444d8a78148d5ce20e55352a80c64c187255674c4d75d9d6d7867` |
| 10 | 23:30:50.691218，capture sidecar | 5,338,240 | `d9165fc60c00e18c580d97649e64ea2dc63e3dabb7767343fa0f3394f117f7e1` |
| 11 | 23:32:17.031872，mtime only | 4,813,038 | `4d1e2ba7cb502e2aed141d947f91871a076ca9e6c3fdad8dfb1de2a72128b9cf` |
| 12 | 23:33:29.112102，mtime only | 3,778,911 | `474433d0819654826cba0ac8b179a67aa5a08aae01033260f3c3f133c79ab5d5` |
| 13 | 23:37:15.779552，mtime only | 266,488 | `d7664bd5e653ce29de64543c1a2c4b341dc51a52419af6678a222c9ae40c1ffd` |

JSON 同时保存原图根目录、逐图尺寸、完整 machine／run／source、元数据来源级别、sidecar SHA、文件 mtime 的纳秒十进制字符串及用途。追加未来场次时应另列实际 run、源码与 UTC，不将本场元数据跨场继承。

## R0008 新增13张原图

`machine_id: 4-8e1c2f1861`；实际来源 `cb7369d3775a8e77c32220bf4806f0af500054bd`，场次 `4-8e1c2f1861--religious-ritual-fusion--R0008`。原件在 `C:/workspace/rrf-development-20261024/screenshots/R0008/`，合计64,383,153 bytes，均2560×1440，13份捕获侧车逐一绑定。完整SHA／UTC／用途见[独立R0008清单](screenshots-R0008-2026-10-25.json)，不覆盖R0007身份。

优先候选为08合法三核心与允许离婚、13展开结果教义、12原版结果核心卡片、09真实成功通知；03／05展示修复后的窗口，01／02为来源选择辅助。04／06／07是过程与拒绝条件参考，后继已由Root逐图复核，保留为过程图。没有复制、裁切、AI修改或发布原图。

10是实际隐藏只读fixture完成后的诊断画面，没有可见事件窗口，排除商店。11只拍到历史操作后的地图，没有可读历史吐司，不能当作历史展示；其sidecar标签不替代画面真值。原调用至截图约19秒，过期仅是可能原因，未证明吐司曾显示。闭场日志未发现来源变量或localization读取错误，另一条 `_CanQueueMapChange` 断言不据此归因。

现有历史决策的详情desc已含结果、来源A、来源B三条动态名称。下一cold场可直接选中详情并拍摄，不必先确认后等待吐司；当前不增加新界面或改脚本。原13图均保留，整场正常退出仍未通过，详见[R0008实机记录](../acceptance/R0008-2026-10-25.md)。
