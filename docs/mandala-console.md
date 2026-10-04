# 曼荼罗相位的控制台设置

2026-10-03：静态核对本机原版脚本，未在游戏内执行本条命令。

开启 debug mode 后，在控制台输入以下一整行，可将当前玩家家族的创造之相直接设为 5 级：

```text
effect house = { set_house_aspiration = { type = aspect_of_creation level = 5 } }
```

2026-10-04 语法复核：`effect` 是控制台命令前缀，后面直接接脚本，不写成 `effect =`。`house = { ... }` 切换到家族作用域；`type` 和 `level` 用空格分隔即可，不需要逗号。控制台前缀的公开示例可见 [CK3 Wiki 控制台文档镜像的 Scripting commands](https://github.com/jesec/ck3-modding-wiki/blob/master/wiki_pages/Console_commands.md#scripting-commands)，其中 `effect root = { ... }`、`effect root.culture = { ... }` 使用同一种结构。该复核仍为文档与原版脚本核对，不代表本命令已经实机执行。

`type` 必须对应要保留或切换到的相位：

| 相位 | type |
|---|---|
| 创造之相 | `aspect_of_creation` |
| 宁和之相 | `aspect_of_serenity` |
| 毁灭之相 | `aspect_of_destruction` |
| 欺诈之相 | `aspect_of_trickery` |

相位属于 house scope；不能把 `set_house_aspiration` 直接放在角色 scope。指定其他 `type` 会同时更换相位。原版调试交互要求接收者为曼荼罗统治者、家族族长且存在家族。

原版证据：`Crusader Kings III/game/common/character_interactions/00_debug_interactions.txt` 的 `debug_set_mandala_aspect`（第 4201 行）在 `on_accept` 中进入 `scope:recipient.house`，分别调用四种 `set_house_aspiration = { type = ... level = 5 }`；创造之相的 5 级分支位于第 4492 行。中文名称来自 `game/localization/simp_chinese/dlc/tgp/tgp_mandala_devaraja_aspects_l_simp_chinese.yml`。

也可以在 debug mode 下右键自己的角色，使用“设置曼荼罗相位”调试交互，直接选择相位的第 5 级。
