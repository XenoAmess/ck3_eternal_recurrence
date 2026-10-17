# CK3 圣地研究的安装源码来源核查

**结论：撤回“发现本地改写痕迹”的判断。** 本次检查的 46 个文件，与声明为 CK3 **1.20.0.4** 的同版本公开资源镜像逐字节一致；其中包含最初引起怀疑的 `Empire Faith Gate` 模块。当前证据不能将这些内容归因为本机后加的修改。

这不是对整个游戏目录的完整性认证，而是对下列明确文件范围的实际比较结果。完整文件清单、两侧 SHA-256、版本来源和当前机器读回保存在 [source-lock.json](source-lock.json)。

## 当前机器与证据

- `machine_id: xenoamess-full-tower-eb9d2c1186`。
- 实际版本读回开始于 2026-10-17 04:36:30 UTC；最后一次来源收据时间见 `source-lock.json` 的 `observed_at_utc`。
- 检查根目录：`Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/`。
- 版本依据：实际读取 `Z:/SteamLibrary/steamapps/appmanifest_1158310.acf`，`buildid=25734779`；游戏资源 depot `1158311` 的 manifest 为 `5078208590259867811`，Windows depot `1158312` 为 `8895371403079420353`。
- 上述两个 depot manifest 都与同版本镜像的 [版本元数据](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/.ck3-version.json)一致，该元数据声明版本为 `1.20.0.4`。
- 没有启动或操作 CK3，没有修改安装文件，没有执行 Steam 文件验证或版本切换。本次没有查询正在运行的游戏所绑定 EXE 或存档规则。

读取 `ck3.exe` 的 Windows 文件版本资源得到 `1.0.0.0`，它不足以识别游戏补丁版本，因此没有拿它替代上述 build/depot 证据，也没有把磁盘安装状态当作某个运行会话的资格证明。

## 最初看到的内容

在安装树的 `common/scripted_triggers/00_religious_triggers.txt` 中读到了以下内容：

| 本地行号 | 内容与用途 |
| --- | --- |
| 1480 | `empire_faith_gate_hof_temporal_is_hof`，世俗宗教领袖创建检查的一段提示 |
| 3091–3124 | `Empire Faith Gate: easier reformation path`，编辑礼仪时针对未改革信仰的分支 |
| 3204–3237 | 同类分支，位于创建礼仪的检查中 |

安装目录还有独立的 `01_empire_faith_gate_rules.txt`、`00_empire_faith_gate_triggers.txt`、事件、修正、宣战理由、GUI 与本地化文件。因此这是一组完整功能代码，确实不只是注释。

**错误发生在归因上：自定义风格的标识符、模块化文件名和 `Vanilla` 注释，都不能证明它们是本机后来注入的。** 最初没有先对齐补丁版本就使用了“本地改写”这一表述，证据不足。

## 同版本比较的实际结果

比较基准为第三方资源镜像仓库 `jesec/ck3-mod-base` 的固定提交：

`074429b3f6d9352a3cf4c5671725fee2f41267ba`，提交说明为 `Version 1.20.0.4 (Crozier)`。

镜像的 [仓库说明](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/README.md)明确其保存基础游戏资源，并以元数据替代二进制文件。它是第三方资源镜像，不是 Paradox 官方签发的全盘校验回执。

| 比较范围 | 实际结果 |
| --- | --- |
| 在 `common/`、`events/`、`gui/` 和英／简中本地化中引用 `empire_faith_gate`、`efg_`、`multi_empire_same_faith` 的 20 个文件 | 20/20 原始字节一致 |
| 采用、效果类型、动态类型、信仰配置、圣物槽、供奉规则、朝圣、建筑、相关触发器等 27 个圣地研究文件 | 27/27 原始字节一致 |
| 两组去重后 | **46/46 原始字节一致** |

20 与 27 相加后需要去掉共有的 `00_religious_triggers.txt`，因此总数是 46。模块引用文件的 20 项计数明确只包含上述目录和两种语言，不代表所有语言版本的文件总数。

关键文件身份：

| 文件 | 本地与同版本镜像共同的 SHA-256 |
| --- | --- |
| `common/scripted_triggers/00_religious_triggers.txt` | `e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2` |
| `common/game_rules/01_empire_faith_gate_rules.txt` | `c04dc35c7d3cd4a0c414a1b61435d013d8601014d378cbed102e7b12733d64a9` |
| `common/decisions/50_holy_site_decisions.txt` | `80ad6a6045bdafdce514cbccf59a9cd1370eaef6749d510adcec759468065fb4` |

宗教触发器文件对同版本镜像的逐行 diff 为空，不只是几个被挑出的片段相同。

另外，较新的 `1.20.1.1` 镜像中仍可读到 `empire_faith_gate_enabled_trigger` 及其礼仪创建分支；不能把这次调查改写为“该模块已被新版本删除”。

## Empire Faith Gate 实际是什么

它的中文游戏规则名为 **“帝国头衔受组织化信仰限制”**。同版本代码可直接查看 [规则定义](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/game_rules/01_empire_faith_gate_rules.txt)、[触发器](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/common/scripted_triggers/00_empire_faith_gate_triggers.txt)和[中文说明](https://github.com/jesec/ck3-mod-base/blob/074429b3f6d9352a3cf4c5671725fee2f41267ba/base/game/localization/simp_chinese/empire_faith_gate_l_simp_chinese.yml)。

| 项目 | 源码中实际写的内容 |
| --- | --- |
| 选项 | 启用；启用且豁免无宗教领袖信仰；禁用 |
| 默认值 | `empire_faith_gate_off`，即禁用 |
| 启用检查 | 只有前两个选项使 `empire_faith_gate_enabled_trigger` 为真 |
| 帝国创建 | 启用时，对封建、氏族、部落、日本封建等适用政体加入组织化信仰和批准检查；还限制已有更强同信仰帝国时 AI 新建帝国 |
| 批准要求 | 精神领袖分支要求领袖意见大于 0、至少半数强力封臣意见大于 0；世俗领袖分支检查本人为领袖或领袖的正面意见，并另核封臣；无领袖豁免选项另走分支 |
| 未改革信仰的礼仪创建／编辑 | 启用分支检查奉献等级至少 2、`tribal_authority_3`，以及至少 3 个由本信仰角色持有的圣地；未启用分支继续使用本人的领地圣地计数检查 |
| 同信仰竞争帝国 | 三档“正统对立／争端／分裂”修正的每月正统性分别为 −1、−2、−3；事件还可能影响 AI 宿敌关系 |
| 绝罚与战争 | 竞争帝国参与绝罚请求的意愿和接受度；“解散帝国”宣战理由要求规则启用及绝罚等条件，竞争状态会改变 AI 评分 |

这里有一个与影片有关的细节：上述启用分支遍历的是信仰的圣地及其县持有者，没有在那段遍历中要求它们全部在操作者自己的领地内；未启用分支调用的却是带 `CHARACTER = root` 的领地检查。**两种规则配置会改变改革的资格，拍摄时须记录实际存档选项。** `1.20.0.4` 的该段部落权威检查也不能未经版本核对就照搬到其他补丁。

默认禁用只说明新开局配置的默认值。本次未读正在运行的存档，因此没有声称用户当前这一局启用了或关闭了它。

此外，`empire_faith_gate_hof_temporal_is_hof` 也是被其他原版检查复用的本地化键。仅出现这个名字，不代表整段检查都受 EFG 开关控制。对此必须读条件和调用者，不能只按键名判断。

## 为什么较新版本的差异容易造成误判

本次还将 27 个研究文件与声明为 `1.20.1.1` 的固定镜像提交 `9a5d0ff6e105297755e19d574cbf4eacdd972709` 比较：10 个文件字节相同，17 个不同。这组跨补丁差异不能用作本地篡改证据。

圣地采用资格、法理王国检查、综摄关系的四个命名触发器块，在这两侧按换行归一化后仍完全相同；但有些其他圣地规则确实随版本变化。例如 [1.20.1 官方更新说明](https://store.steampowered.com/news/posts/?appids=1158310&feed=steam_community_announcements)增加了符合虔诚、县信仰及宗教领袖好感要求的独立国王／皇帝创建圣地路线，并修正了放弃圣地的圣物返还行为。

因此导演案需要标注研究版本，并在拍摄时将源码与实际加载版本对齐。它不需要因为本次已撤回的怀疑去恢复或重装游戏。

## 历史记录能证明什么

仓库的 `docs/ck3-upgrade-native-startup-2026-10-03.md:91` 已记录同一游戏规则文件及同一个 SHA，并明确写了当次没有修改该文件。`artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/` 的历史资源中也可读到 EFG 规则和宗教触发器分支。

这些历史记录缺少可核验的机器身份，按项目规则记为 **`machine_id: unknown`，所属机器未核实**。它们可证明项目曾保存这些内容，不能据此认定本机的安装时间、修改者或当前运行状态。此次当前机器的同版本文件比较，是独立取得的新证据。

## 对导演案的处理

撤回“安装树已被本地改写”的前提；保存此次纠正与比较回执。圣地研究继续按明确版本的脚本定义、调用链和 GUI 进行。采用后的默认等级、共享库存的实际行为、引擎内的激活判定等仍以对应版本的实机读回补齐，不用文件比较替代运行时结果。
