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

## 首次实际资格及明确委派后继

2026-10-10 本机 QOL R0038/a138 原 prison_payment 已实际run0/verify0，公共自动路线在原期限内完成菜单、未勾选自动存档的退出对话框和退出桌面。独立 retained HANDLE exit0、完整 native0、managed thread、cleanup与无host error齐备，`normal_close_qualified=true`；Root人工退出回执保持NULL，未冒写human review。原始路线、每次mapped click及独立进程证据保存在[本场case-output](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0038/case-output/normal-close-result.json)，[小型verify回执](C:/workspace/ck3-upgrade-20261010/qol-prison-payment-bound13-live-01/actual-common-verify-01.json)保留产品release=false。keeper随后实际exit0，CAS7867 done/resources=[]。此资格限于实际模板尺寸、同公共文件pins与已观察窗口，不将任意未知对话框视为可自动导航。

下一场R0039/a139已真实绑定[七字段委派原件](C:/workspace/ck3-upgrade-20261010/qol-ui25-delegated-live-01/actual-ui-delegation-01.json)，Root在亲审Steam离线证据并启动后明确移交唯一UI/checkpoint操作权给`/root/qol_ui_operator`。该操作者以自己身份记录原UI25，Root不并发输入。委派已实际成立；UI业务仍需该场真实结果，不能由委派成立或R38正常退出推出。

共享接点及隔离MSVC NOMINMAX修复提交`03c65a80954da5d68cad87e8a8ff74d7fcb326df`对应[官方CI37976493582](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37976493582)已实际completed/success，64步骤全部成功，包含17项接点及原local-launch等共享测试。原37973418218失败保留，不由后继成功改写。
