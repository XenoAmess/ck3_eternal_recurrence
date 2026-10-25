# 薪酬与考核条件的实际界面验证

`machine_id: pc-20260924rtuf-f11af23c08`，2026-10-25 UTC，场次 `pc-20260924rtuf-f11af23c08--zhongguo-style--R0004`。实际 CK3 1.20.0.4/build25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。启动前后台原生确认 Steam 离线；本场 PID 12132、generation 1，玩家 31254，受款封臣 33946。

这是明确准备前提的零日历日专项测试，不是自然年度考核：1066 罗贝尔改为天朝制，给予两库测试资金，使用已有直属有地封臣，准备已交付考绩，再调用生产 AE opener 和 AE1 消费者。实际界面、选择、付款均继续使用原生产事件；fixture 不直接写 AE2 支付结果。公共入口是 `ck3_mod_acceptance.py` 的 `zhongguo-361 / ae2-ui-payment`，没有调用旧独立 runner。

已实际观察：

- `zg361comp.1` 实例 1 展示三项中文选项。原生 context 读回其 authored index 15/16/17、受款人 saved scope 和可用性；本场实际立即支付使用 MCP `option_number=16`，没有把显示第一项误当 authored 第一项。
- 三项原版 hover 均可显示，动态应付为 21。立即付清显示总额 25、国库 18、私库 7；90 日承认补发显示欠款 25、信用 -15 和资金不足后不自动重试；180 日驳回补发显示欠款 21、国库 15、私库 6，以及多周转 90 日、少付 4 和相同信用代价。实际没有 raw localization key。
- 选择立即付清后，真实原生个人金币由 1244 变为 1237，事件关闭。fixture 的只读 verifier 在同一暂停日期核对国库 1000→982、受款人 +25、生产 paid=25/owed=0、两本 journal 已结算，并记录 `TEST PASS actual_pay_now_wallets_and_statement`。
- 打开“提前启动本年度考核”，亲见四条中文条件，内部 flag、重复展开和“总是”均未显示。没有执行这项考核决议。
- 前后日期均为原生 `53144328`（1066.9.15），玩家未变且存活。未推进 90/180 日期限；其结算语义由生成脚本有限执行回归覆盖，不冒充本场延期实测。

现有原生事件 context 明确将完整 `effect_preview` 标为 unavailable，不能把它当作 hover 证明。本场仅为呈现检查使用 `desktop_coordinate_map.py --move`，逐次绑定实际 1920×1080 原图、独立坐标换算、可见选项区域及指针读回；没有 OCR。游戏内决议与事件选择均为原生 MCP。原图分别为外置 `ae2-hover-now-r3.png`、`ae2-defer90-hover-r2.png`、`ae2-defer180-hover.png`、`review-localized-actual.png`。

本场发现 AE opener 直接读取缺失的可选 L 历史变量，产生两组 unset-variable 运行诊断。正式源码随后改为先检查存在性，新增两项回归先在旧生产源码上失败，修后共 44 项通过；本场已加载输入没有热改。这处补丁没有在本场取得加载或执行信用。正式 1034 文件与实测 candidate 仅这一个 foundation 文件的两处 guard 不同，其余 1033 文件逐字节相同；外置 `formal-vs-live-candidate.json` 保存精确比较。fixture 自身的日期条件还触发 `current_date_trigger` 显示诊断，fixture 不进入正式包。既有未使用变量与孤立事件加载诊断不由本场清除。

产品 GUI 条件和 source case 条件均实际满足，但完整公共报告保留 **RED**：执行者误查询未为该场配置固定 managed-source inventory 的原生退出接口，接口明确拒绝。随后使用原版退出确认、取消自动存档并点“退出到桌面”；保留句柄实际读回 OS exit 0，原 session 的 Job/tree/control/watchdog 清理完成。failure lifecycle 和原退出码 2 保留，不追认为公共 normal-close GREEN。keeper 原退出码为 0，实际 CAS 释放序号 1329。

证据根为 `D:/workspace/ck3-361-ui-20261025`；关键原件在 `r4-evidence/`、场次 `case-output/`、`r4-screen-release.json` 和各 mapped-action 回执。源码模型、静态检查与这份专项实测分别记录，均不授予完整二期、旧存档、多人或重新一年运行的验收信用。过程原件按通用策略限期保留；本文件与发布摘要永久入库。
