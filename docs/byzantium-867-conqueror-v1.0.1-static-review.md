# Byzantium 867 - Conqueror v1.0.1：不生效的静态排查

分析日期：2026-10-06（Asia/Shanghai）。用户要求仅做代码静态分析。目标目录为 `D:\Download\Byzantium_867_Conqueror_v1.0.1`；未修改目标 mod、用户配置、存档或游戏安装，未启动游戏，未读取运行日志。

## 结论与边界

**没有发现使该包在原版默认规则、正确安装并新开 867 年游戏时必然失效的脚本错误。** 不能仅凭这份发布包断言某次实际失败是加载失败、规则关闭或脚本未执行；这些需要安装配置或既有运行日志才能区分。

静态确认的条件如下，条件成立时可以解释“不生效”：

| 条件 | 代码行为 | 证据 |
|---|---|---|
| 征服者出现频率为“无” | 在创建故事之前跳过 | mod 脚本第 19、53–55 行；原版 `story_cycle_conqueror.txt:18` 也会终止该规则下的新故事 |
| 征服者加成为“无” | 故事可以创建，但原版主动移除 `conqueror` 特质，改用 `ai_weak_conqueror_modifier` | 原版 `story_cycle_conqueror.txt:98`；mod 第 40–41 行只解释这个结果，没有覆盖规则 |
| 在选人界面检查，或为旧存档启用 | 唯一授予入口是 `on_game_start_after_lobby`，没有读档补发入口，也没有角色历史修改 | mod 第 3–7 行；原版 `game_start.txt:2509` 对入口时机的说明 |
| 非 867 年新开局 | 年份条件拦截 | mod 第 14–15、57–58 行 |
| 仅把包留在下载目录，或者安装时保留额外外层目录 | 外层 `.mod` 的 `path="mod/byzantium_867_conqueror"` 指向 CK3 用户目录下的 mod 文件夹，不指向下载目录 | 外层 `.mod:7`；安装说明第 15–21 行 |

上述是确定的条件分支，不代表已经知道用户那次运行采用了其中某个条件。相对 `path` 本身不是错误；按说明复制文件夹和外层 `.mod` 后，层级是正常的。中文 Windows 用户名导致该用户环境挂载失败的说法也不能由本次包内源码独立证实。

## 源码核对

实际核对的原版安装为 `Z:\SteamLibrary\steamapps\common\Crusader Kings III`，`launcher/launcher-settings.json:6`、`:7` 声明 `1.20.0.3 (Crozier)` / `1.20.0.3`。仓库内 `Crusader Kings III/` 的启动器声明为 `1.19.0.6`，不能代替当前安装作为版本依据。

以下原版路径均相对于实际安装的 `game/`。

1. **文件结构与编码正常。** 包内包含一个外层 `.mod`、一个内层 `descriptor.mod` 和一个 `common/on_action/*.txt`；三个文件均为 UTF-8 BOM。没有 `replace_path` 或 `remote_file_id`，没有自定义特质/本地化需要另外注册。
2. **追加钩子方式正确。** mod 第 3–7 行通过 `on_actions` 引入独立 effect，没有为原版 hook 再定义一个 effect。原版 `common/on_action/_on_actions.info:102` 明确给出了这个扩展方式，文件名改为 `zzz_` 不是修复重复 effect 所必需的条件。
3. **头衔与历史持有者存在。** `common/landed_titles/00_landed_titles.txt:9001` 定义 `e_byzantium`；`history/titles/00_other_titles.txt:4127` 开始其历史，`:4514` 在 866.9.24 指定 `holder = 1700`，下一次更换在 886.8.29。不能因为版本新增了霸权级头衔，就推断 867 年的 `e_byzantium` 没有皇帝。
4. **授予入口与原版一致。** mod 第 33 行为当前头衔持有者执行 `create_story = story_conqueror`；原版 `common/on_action/game_start.txt:7028` 起也通过此 effect 初始化历史征服者，而非必须直接 `add_trait`。
5. **默认规则下故事授予特质。** `common/story_cycles/story_cycle_conqueror.txt:18` 的 `on_setup` 进入 `story_owner`，`:98`–`:110` 在加成非“无”且不走 AI 极端加成分支时执行 `add_trait = conqueror`。初始化没有要求故事持有者是 AI，也没有行政政体排除条件。其后部分 AI 专属效果不等于玩家不能获得特质。
6. **默认规则不是关闭。** `common/game_rules/00_game_rules.txt:130`、`:175` 分别定义频率与加成，默认项在 `:136`、`:181`，均不是对应的 `no_*` 项。
7. **自建替换角色没有硬编码障碍。** mod 使用 `title:e_byzantium.holder`，没有绑定 `character:1700`。原版 `common/on_action/ruler_designer.txt` 文件头明确说明，普通领地角色在该设计器完成 hook 时已经接收头衔。是否实际采用该替换方式不能由发布包证明。

## 诊断标记如何区分失败层

这只是对现有代码的解释，本次没有读取或生成日志：

- `startup hook reached`：自定义 hook 已经执行；没有这一行只能说明没有找到执行证据，不能仅据此断定 mod 未挂载（也可能日志未采集或未到该时机）。
- `skipped - conquerors disabled by game rule` / `bonuses disabled by game rule`：对应上表两条游戏规则分支。
- `skipped - start date is not in 867` / `Byzantine Empire has no holder`：对应日期/头衔分支。
- `ERROR - emperor is missing conqueror trait after initialization`：在该检查时点缺特质；不能仅靠这行区分故事是否新建、是否原先已有故事，或是否原版机制被其他 mod 改写。
- `SUCCESS - emperor has conqueror trait`：该时点已持有特质；不证明后续征服、继承或整个故事周期已经实测。

原版 `_story_cycles.info:5` 描述 `on_setup` 为故事刚创建时执行。未发现需要为了本次问题直接添加重复 `add_trait`、延迟一天或覆盖原版 `game_start.txt` 的静态依据。若原版默认规则且新开局仍无效，下一份有区分力的输入是实际安装的外层 `.mod`、启用配置和既有 `BYZ867`/加载错误，而不是继续猜测修改脚本。

## 目标文件指纹

SHA-256：

| 文件（相对目标目录） | SHA-256 |
|---|---|
| `byzantium_867_conqueror.mod` | `847E459132BB44AEBB893323AF1C72FC1B100D9469DA438347E67D9FEDECF0F3` |
| `byzantium_867_conqueror/descriptor.mod` | `2F5A607CEFF81A124BBBE1300FE51E23427A73A1534D1DA3758DBC1E33D957B9` |
| `byzantium_867_conqueror/common/on_action/zzz_byz867_conqueror_on_actions.txt` | `601E626B667542821BCDDA6015E0D0DE3FEBDA5C54CD431156E2ACB225417A5B` |

验证等级仅为源码静态分析（`research` / `static-confirmed`），不是游戏验收。此次变更仅增加排查文档，不需要运行主项目的构建或实机验收。
