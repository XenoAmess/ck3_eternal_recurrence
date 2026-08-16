# 琉焰卿的永恒轮回（AGENTS 指南）

## 项目结构

- `XenoAmess_s_Eternal_Recurrence/` — CK3 mod 本体（唯一发布内容）
- `Crusader Kings III/` — 游戏本体目录（仅作参考/逆向用，已被 .gitignore 排除）
- `docs/` — 知识库（跨存档存储机制、GUI 系统、语法踩坑），改机制前先读
- mod 通过用户目录的 `mod/XenoAmess_s_Eternal_Recurrence.mod`（path 指向本仓库）注册

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

## Git 约定

- **每次任务执行完成后，默认 `git commit` + `git push`**（无需另行确认，也不要等人工验证，直接提交推送）
- 提交信息用英文，简明描述改动

## 硬性约束（血泪教训，详见 docs/）

- 所有脚本文件 **UTF-8 BOM**；yml 缺 BOM 直接不加载
- script values 目录是 `common/script_values`（**不是** scripted_values）
- `is_tutorial_lesson_completed` 是 interface trigger，只能用于 customizable_localization / GUI，游戏状态脚本禁用
- on_action 同名键**覆盖不合并**，扩展用 `on_actions = { 自定义钩子 }` 模式
- 自定义顶层窗口必须在 `gui/scripted_widgets/` 注册才会实例化
- `Tutorial` 数据上下文只存在于 tutorial_window 本体
- 教程课程自动完成用 `trigger_transition`（课程文件内），不要试图从外部点按钮
- 游戏语言非英语时，customizable_localization 的 key 必须在**当前语言**的 yml 里存在（不吃英文回退）
