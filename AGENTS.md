# 琉焰卿的永恒轮回（AGENTS 指南）

## 项目结构

- `XenoAmess_s_Eternal_Recurrence/` — CK3 mod 本体（唯一发布内容）
- `Crusader Kings III/` — 游戏本体目录（仅作参考/逆向用，已被 .gitignore 排除）
- `docs/` — 知识库（跨存档存储机制、GUI 系统、语法踩坑），改机制前先读
- mod 通过用户目录的 `mod/XenoAmess_s_Eternal_Recurrence.mod`（path 指向本仓库）注册
- Steam 创意工坊物品 id：**3784706360**（首次上传后启动器把 `remote_file_id` 写回用户目录 .mod）。
  注意：`remote_file_id` **只能留在用户目录外层 .mod，不要同步进仓库内层 descriptor.mod**——
  更新上传时启动器要回写内层 descriptor，带此字段会导致 "Mod descriptor validation failed" 上传失败。
  更新工坊 = 改仓库内容 → 启动器 Mods → 上传 Mod 选同一物品再传一次。预览图用 mod 根目录的 `thumbnail.png`
  （启动器约定俗成按 mod 根目录找此文件名，同其他 dev mod）；descriptor 里 `picture="thumbnail.png"`
- 工坊描述维护在 `workshop/description.bbcode`（BBCode，内嵌 4 张截图的 steamusercontent 直链）；改完描述到物品页「编辑标题与描述」整段替换

## 构建/生成

```powershell
py XenoAmess_s_Eternal_Recurrence/tools/gen_highscore.py
```

位阈值体系（教程课程位）由生成器产出，**不要手改 `GENERATED FILE` 标记的文件**：
`common/tutorial_lessons/xar_highscore.txt`、`common/customizable_localization/xar_generated_loc.txt`、
`common/scripted_guis/xar_generated_guis.txt`、`common/scripted_effects/xar_generated_effects.txt`、
`gui/xar_meta.gui`、`localization/*/xar_generated_*.yml`。

要扩上限：改生成器里的 `TIERS` 列表再跑一遍即可，旧纪录不丢（位是只增的）。

## 测试流程

1. `Start-Process binaries/ck3.exe -ArgumentList "-debug_mode"` 启动
2. 日志：`Documents\Paradox Interactive\Crusader Kings III\logs\error.log`（解析/运行时错误）、
   `debug.log`（`debug_log` 标记，本项目用 `XAR:` 前缀）
3. 全局存储落盘文件：`Documents\Paradox Interactive\Crusader Kings III\tutorial.txt`
4. 流程性验证：新开局看商店事件 → 控制台 `die` → 结算事件 → 教程通知自动完成 → 再开新局看导入

## 文案人格（琉焰卿）

所有琉焰卿的台词/事件文案必须贴合此设定：

- **风格**：中二 + 奇幻，具有诱惑力、诱导性；从容不迫，永远像在等一笔迟早成交的生意
- **设定**：以人类的情感为食的咒间仲魔；**不会刻意告诉玩家自己的恶劣性**——恶意只藏在措辞的阴影里，表面永远温柔有礼
- 称玩家"旅人"，第一人称"我"；自称"琉焰卿"；把分数说成"分量/余烬"，把交易说成"典当/垂青/咒痕"
- 祝福诅咒奖池的权威定义在 `docs/blessing-curse-pools.md`，改池必须五处同步（表内列明）

## Git 约定

- **每次任务执行完成后，默认 `git commit` + `git push`**（无需另行确认，也不要等人工验证，直接提交推送）
- 提交信息用英文，简明描述改动

## 硬性约束（血泪教训，详见 docs/）

- **一切内容只对玩家生效，AI 永远不得触发**。现有屏障：开局走 `every_player`（不含 AI）；死亡链要求
  `has_character_flag = xa_enabled`（该 flag 只能由玩家点契约获得）**且** `is_ai = no` 双闸门；GUI 桥走
  `GetPlayer`。今后新增任何事件/决议/互动/钩子，都必须挂在上述玩家限定链上（或自带等价闸门），
  禁止给 AI 留入口；新增 on_action 钩子时注意其本身对全场角色触发，effect 必须包 limit
- 所有脚本文件 **UTF-8 BOM**；yml 缺 BOM 直接不加载
- script values 目录是 `common/script_values`（**不是** scripted_values）
- `is_tutorial_lesson_completed` 是 interface trigger，只能用于 customizable_localization / GUI，游戏状态脚本禁用
- on_action 同名键**覆盖不合并**，扩展用 `on_actions = { 自定义钩子 }` 模式
- 自定义顶层窗口必须在 `gui/scripted_widgets/` 注册才会实例化
- `Tutorial` 数据上下文只存在于 tutorial_window 本体
- 教程课程自动完成用 `trigger_transition`（课程文件内），不要试图从外部点按钮
- 游戏语言非英语时，customizable_localization 的 key 必须在**当前语言**的 yml 里存在（不吃英文回退）
