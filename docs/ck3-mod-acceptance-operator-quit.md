# 公共验收的正常退出与单一 GUI 操作者

本功能由 QOL R37 的实际工具调用间隔耗尽 hold1800 触发。它复用同一公共 Selection、CaseClient、host 和 native，不为产品建立另一套运行时。源码与定向测试完成不等于 GUI 实机通过。

## 普通 GUI 自动退出

本机 runtime 可选配置 `normal_quit_automation`，包含 `helper`、`matcher`、`templates` 三份文件的完整 `path / bytes / sha256`。公共代码为：

- `tools/ck3_mod_acceptance_normal_quit.py`：一次菜单、退出对话框与桌面退出路线。
- `tools/ck3_mod_acceptance_gui_template.py`：仅定位已审模板，不生成业务结果或人工签核。
- `tools/ck3_mod_acceptance_client.py`：调用一次路线并独立核实进程退出。

helper 与 matcher 路径由本机配置提供；模板包引用本机保留的原始截图及其精确 pin。另一台机器使用自己的模板配置，不复制操作者、PID、会话或账户路径。helper 从模板读取其支持尺寸，同时读取当前截图和桌面真实尺寸；不猜缩放倍率。

默认未配置时保留人工退出。配置后，CaseClient 写当次 `normal-quit-awaiting.json`，在原 hold 期限内仅调用一次公共 helper。每次点击使用新的原始截图、唯一模板匹配、实际 PID/create_time/HWND/focus 和 `desktop_coordinate_map` 回执；未知窗口或失败停止该路线并保留记录，不自动重放。

路线依次打开菜单、退出对话框、确认取消退出自动存档，再点击退出桌面。独立回执 `normal-quit-automation-result.json` 明确记录 `automation_actor=template-automation`、`human_review_claimed=false`。它不写 Root 人工回执、不发 finish_hold、不授 OS0/native0 或业务 PASS。

CaseClient 仍要求 helper 实际 exit0、同场精确来源与最终 mapped click 回执，再核实 retained HANDLE OS0、原完整 native0、managed 完成、线程结束、cleanup 和 host 无错误。原预算与产品业务合同保持。awaiting 的 `/root` 是原请求授权者，不表示自动动作经过人工审图。

## 明确委派一个实际 GUI 操作者

默认 `operator_reviewer=/root`。Root 可在实际 run context 中提供 `operator_delegation` 文件 pin；授权文件固定使用以下字段：

```json
{
  "schema": "ck3-mod-acceptance-operator-delegation-v1",
  "run_id": "<本场实际编号>",
  "screen_task": "<本场实际屏幕任务>",
  "frozen_argv": {"path": "<本场实际 frozen-argv.json>", "bytes": 123, "sha256": "<实际 SHA256>"},
  "delegated_by": "/root",
  "delegate_reviewer": "<被明确委派的实际 agent 名称>",
  "scopes": ["ui", "checkpoint"]
}
```

以上占位示例不能执行。CaseClient 将真实授权文件绑定本场 run、屏幕任务与 frozen argv，只接受该实际操作者的 UI/checkpoint 回执。委派不授权启动游戏、改变租约或结束 host；同一时刻只允许一名实际 GUI 操作者，Root 在交接期间不并行输入。

公共 `tools/ck3_mod_acceptance_ui_mailbox.py --inspect` 显示最新 await、原始截图和实际 `operator_reviewer`。操作者直接审阅当次原图后，通过 `--reviewer <实际名称>` 提交一个请求；Root 不能替子线程冒写亲审，子线程不能借用 `/root` 身份。原 source、sequence、一次请求、PID/create_time、期限与业务断言保持。

## 本机首轮接入记录

2026-10-10：Source10 / FINAL11 / d1d4 native 保持原冻结。新机器映射 `runtime.local-entry-bound13.json` 只增加公共自动退出三 pins，SHA256 `a7f20631fd99395a8e509246850ac7ef47da841352abd0e6db00d48ca6070e2d`。

旧 normal-close 测试补齐实际新增的 synthetic live/keeper/screen 字段及独立导入路径后，正常退出、操作者接点和 mailbox 合计 17 项定向测试实际通过（2.098s）。官方 CI 已接入这些检查，静态环境补 `psutil==7.2.2`。此截止尚无自动退出或明确委派后的新实机资格；R37 原 entry2、UI0/25 和 normal-close 未资格保持。
