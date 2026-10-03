# CK3 1.20.0.3：运行中语言切换的 R0004 实机边界

2026-10-03，地产类型转换维护版的 R0004 中，直接输入 `switchlanguage french` 和点击原版调试 Language 菜单的 French 按钮，两条路线都没有把可见 HUD／Decisions 切换为法语。**本次运行中的法语渲染检查为 FAIL。** 命令出现在 console、返回空白或原版 GUI 中定义了该按钮，都不能记为语言切换成功。

这项失败只限定本次运行中的语言切换路线，不改变产品的九语格式认证，也不能归因于产品本地化脚本、某个原生 bug 或某种未证明的加载原因。现有证据没有确认 `switchlanguage` 的编译实现，也没有证明该命令的必要条件一定是重启。后续验收采用每语独立冷启动和相同 checkpoint；各语实际渲染结果另行记录。

## 本次真实画面

原始 attempt：`C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0004/`。以下均为已保存的真实 PNG，本次归档只读打开文件，没有重新采屏或操作游戏；五张图真实尺寸均为 1920×1080，不构成后续点击坐标的默认尺寸。

| PNG | 可直接看到的内容 | SHA-256 |
|---|---|---|
| [console-french-physical-input-01.png](C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0004/session/screens/console-french-physical-input-01.png) | console 输入框完整显示 `switchlanguage french`。 | `e2d0adc3328d8305c7b190ec12436f2950c617fb928a5f74303768b1564bf40b` |
| [console-french-executed-02.png](C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0004/session/screens/console-french-executed-02.png) | console 输出有 `> switchlanguage french`；HUD 仍为英文 `Paused`、`Political Map` 和英文日期。黄色人物年龄提示不能当作法语切换结果。 | `609e56fe4805aa893e480886863e4e0c07ef9a40ceedd4efc122b69bb5478d6f` |
| [french-console-closed-01.png](C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0004/session/screens/french-console-closed-01.png) | 关闭 console 后，`Paused`、`Political Map` 与英文日期仍未改变。 | `a0584f9403ea64a93fdba13300a55b02ec52d5bfb96d2a3bb21fedd582dddc9b` |
| [language-menu-open-01.png](C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0004/session/screens/language-menu-open-01.png) | 实际原版 `Switch Languages` 窗口出现 English、Latin、German、French 四个按钮；背景 Decisions 是英文。 | `7c86014614129b72c26b621caa1a5fd7448863a3b5225f486ef7aa73563e7cc4` |
| [language-menu-french-result-02.png](C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0004/session/screens/language-menu-french-result-02.png) | 点击 French 后，console 增加第二条 `> switchlanguage french`；`Decisions`、`Found a New Kingdom`、`Consecrate a New Kingdom` 与 HUD 仍是英文。 | `fe355e94563333f5552ffdc3e33bcb61ee71bddc756ab13b8efbd9971b1bbc19` |

这些画面只支持“可见英文界面没有切换成法语”。它们不包含某个 mod 法语窗口的成功渲染，也不证明游戏内部语言变量曾改变、命令被拒绝或未来重启会自动生效。

## 当前安装的一手文本定义

来源均为本机 Steam 管理的 CK3 安装树：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/`。`launcher/launcher-settings.json:6–7` 声明当前安装为 `1.20.0.3 (Crozier)`。本次保存了下表文件的精确字节及行号摘录。

| 原版文件与行号 | 实际定义与边界 | 整文件 SHA-256 |
|---|---|---|
| `launcher/launcher-settings.json:6–7` | 当前安装版本声明为 1.20.0.3。 | `9cd6ff96f8092f2d21e1491b37e8344aa287faf69850563128ca1b117244a214` |
| `launcher/settings-layout.json:92–108` | `language` 为 select，九个设置值是 `l_english`、`l_french`、`l_german`、`l_polish`、`l_japanese`、`l_spanish`、`l_simp_chinese`、`l_russian`、`l_korean`。这里只定义 launcher 的设置值。 | `649319eebff6212e1993e54bd0dc652c35e2158f77909ed9fb8bd840f2648eb9` |
| `game/gui/console.gui:582–583` | Language 按钮执行 `gui.CreateDockable gui/debug/debug_menus.gui language_window`，打开本次实际出现的调试窗口。 | `67b9468576c392598cb801464830feca1979f7b50be672c30866bd76961c403d` |
| `game/gui/debug/debug_menus.gui:43–64` | 四个按钮分别调用 `switchlanguage english`、`latin`、`german`、`french`。这证明 GUI 配置中的命令字符串；其文件没有语言切换的编译实现。Latin 按钮也不能扩充 launcher 的九语支持声明。 | `780fe45933c0b65050714cefe9bd2c3c918dec7caeeb8f0cd86a30b1ff5091b6` |
| `game/gui/settings/setting_types.gui:197–198`、`:108–116`、`:252–255` | 每项设置的星号由 `PdxSetting.GetSettingPromoted.RequireRestart` 控制，底部提示由 `JominiSettingsWindow.RequireRestart` 控制，星号 tooltip 为 `REQUIRES_RESTART`。实际 language 项的 native flag 未在这些文本定义中给出。 | `8ab3b396e3010fdc527833061170c3df1e846174f80327a5e3a3e65b3665632b` |
| `jomini/localization/settings/settings_l_english.yml:31–32` | 提供通用的重启提示文本。该文本不声明具体哪些设置需要重启。 | `aaf6d2f24261d6873f6e9ca06e9be75cd280b73b3713bdf60be3c4595bef1338` |

普通 Settings 是否要求重启，需要读取当时实际 language 项的星号或重启提示；此处没有操作 Settings，也没有把通用提示外推为 `switchlanguage` 的合同。官方 Paradox 网站检索未取得 CK3 1.20.0.3 对该命令与重启要求的说明；本次访问官方 CK3 wiki Console／Localization 页面返回 401。未用其他游戏的命令说明推断 CK3 行为。

读取 R0004 的 `state/profile/pdx_settings.txt:412–415` 时，语言仍为 `value="l_english"`；观察时间为 `2026-10-03T01:32:19.722654+00:00`，该次文件 SHA-256 为 `2eb45f6ec70bddf7b57492b0218413eef35bef794daa5465d2b46d8eade665e0`。这是文件观察，不是 live 本地化查询，不能独立证明运行中的设置值或切换失败原因。

## 后续可复用验收方式

主执行者已停止继续猜测运行中命令，改用每种语言独立 run：在该 run 的外置 profile 中设置上述精确 `l_*` 值，冷启动同一已保存 checkpoint；进入地图后读取真实原版界面和重新打开的产品界面。每语保存自己的输入身份、实际 PNG、完整可见文案／tooltip 与 PASS／FAIL。文本格式通过、选项存在、启动成功或英文界面仍能操作，都不能代替该语种的实际渲染验收。

语言视觉检查复用相同存档和现有转换状态；不为检查文本重复执行地产转换。后续冷启动若通过，只声明对应 run 的成功，不改写 R0004 的失败或把它推广为整个 CK3 1.20 系列的能力结论。

## 保全位置

本次外置归档：`C:/workspace/two-mod-maintenance-20261003/ck3-language-runtime-boundary-R0002/`。其中 [evidence.json](C:/workspace/two-mod-maintenance-20261003/ck3-language-runtime-boundary-R0002/evidence.json) 保存 PNG/原版源文件 bytes、size、SHA、真实尺寸和源码摘录，SHA-256 为 `1ffb0ce5cedeb95b8a940cade76ea53d54b6f5a870156a39616a4ccba48b254b`；`installed-sources/` 保留六份原版完整文本，`screens/` 保留本次复制的已有 PNG。

`console-french-physical-input-01.png` 原始输入图以本页表中的实际原片路径和 SHA 绑定，也已逐字节保全到 `screens/`；补充收据 [physical-input-supplement.json](C:/workspace/two-mod-maintenance-20261003/ck3-language-runtime-boundary-R0002/physical-input-supplement.json) 记录真实尺寸和输入全文，SHA-256 为 `91718888e732e412ddac5f5e3bf656da8779058f5ada56e7ba06ca91e4b8ae21`，没有改写原 `evidence.json`。`evidence.json` 中另保存的 `console-french-input-02.png` 输入框为空，不作为全文输入成功证据。本页仅引用实际查看过的画面。既有来源研究保留在 `ck3-language-primary-R0001/`，其中静态命令路线始终只有 source-level 证据；R0004 添加的是该候选路线本次未能切换可见语言的实机事实。
