# R08：SubC递归scalar与实际付款的语义边界审查（1.20.0.4）

2026-10-16，审查及勘误机器 `machine_id: desktop-3fevhd2-1c74096080`；只读审查基线 `c743520929d4f9a82c17c908b218075018598e2d`，原审查实际完成 `2026-10-16T14:40:02.008819+00:00`。精确来源为CK3 1.20.0.4 / Steam25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本次只消费已封原件、仓库typed profile与便携bundle，不读EXE、不接游戏/SDK/桌面、不构建；勘误只改说明文字并追加来源现状。

[小型derived provenance摘要](evidence/episode04-r08-rate-application-12004/semantic-audit-a05.json)保存15条直接CALL的5B原指令、rel32目标、对应仓库bundle及必要SHA。原始RAW/SOURCE/archive沿用已有相对路径，不复制外部大输入；原外置审查的delivery SHA与时间单独保留。它支持其他机器重新核对知识，不转移来源机器的安装、部署、权限或现场资格。

## 已证关系与业务缺口

[应用链](episode04-r08-rate-resource4-application-12004.md)和[合同单项贡献链](episode04-r08-contract-contributions-12004.md)现已接成以下静态依赖：

1. 父函数持有原始角色A，`28F7C20→2BD3320(A)`取得scalar B，`28F7C30→2C13F60(A)`取得当前十槽向量，取零基slot9为M。
2. B的第二/三加数分别使用A的context+218/+248，经过`2BC76C0→2BD47E0`转换FullID occurrences。exact4 typed profile将registry5D1EB88/fallback5D1EB40识别为subject/vassal contracts；converter仍保留重复与fallback，没有自己的SubC magic或active过滤。
3. 已证serial链`2BD5530→2BD58E0`按对象+20选择关联角色X，经本体显式门后递归调用`2BD3320(X)`。X与父函数角色A是两个来源位置，不能自动合并为payer或player。
4. `24C7BB0`正常返回local88在0..100000；`24C18F0`写`max_signed(0,nativeMulQ(local88,recursiveRaw))`。raw量纲未知，保留机器fast/slow/wrap；`2BD36D0`选择已有64B槽，随后首QWORD ADD贡献。六叶专题保留24B参数span、192B capture/190B logical和缺失首metadata ledger的明确纠正。
5. 结果返回外层scalar，后段形成`D=wrap64(B-M)`，条件通过才对context+4A0加减，SUB通过resourceRaw4网关。B的正式业务名/单位及其与M的业务同量纲尚未建立；resource4/context+4A0没有取得个人金币或军事账户业务名。

这15条直接CALL可从保存字节独立重算。参数、身份和返回传播来自作者逐指令人工合同；source校验PASS不自动证明业务语义。registry类型、函数连接与军事类别应分别保留，不用“军费”代填原始标量、合同、modifier key或未知资源名。

同一父函数更早的`28F7934→28A6D10`已消费四raw形成NET并调用钱包。后段scalar返回不能成为同次更早ADD的直接输入；未知callee副作用与跨轮刷新仍未建立或排除。`maintenance_attribution=unclosed`、`paid_military_amount_raw=null`、`cadence=null`、`resource4_business_name=null`保持不变，R08整卡与动态分子不增加。

## 可复用成果的范围

| 来源 | 可使用的事实 | 保留边界 |
| --- | --- | --- |
| exact4 typed cash binder与[getter清单](war-payment-maintenance-cache-source-12004.md) | current/all-raised是两个独立情景的军事月费率；gold槽0、treasury槽6分开；总收入减完整支出的月NET含军事 | 不是累计付款；两种情景不相加，不从NET重复扣军事；未来总额与风险预算保持原readiness |
| [R0174实际父链](war-payment-r0174-actual-parent-source-12004.md) | 唯一seq12的kind2 ADD282364、四raw算式及个人账户25166043→25448407；整原callback边界 | day17/day21保留同一条记录只计一次；其军事子分量、指令局部store和周期未闭 |
| [R0173登船实付](episode04-r0173-boarding-halt-12004.md) | source-qualified登船SUB300000，即该次3金币扣款 | 不扩展成持续维护费、任意兵力通用价格或月结周期；同T0无登船对照仍缺 |
| [R0168月净率历史](war-cash-net-live-r0168-2026-10-05.md) | `.3`的数值与净率合同可按其历史范围阅读，知识和代码可复用 | 来源`machine_id: unknown`；不能推认当前机器或`.4` live通过 |

目前没有现成来源可以授予`.4`已付军事维护的日/月周期。一次callback日期、调度器父栈、monthly getter或旧版本`on_army_monthly`均不能替代该证据。下一条有效证据仍按[现有归因路线](episode04-r08-next-maintenance-attribution-12004.md)，需要军事类别writer、同次应用、真实payer及独立刷新/周期；本审查不新增任意地址读取。

## 2026-10-16措辞与历史状态勘误

应用专题的标题、开头、图标签和视频许可句已收窄为“角色scalar／当前向量slot9差额”；transport首docstring明确为当前军事月费率和尚未应用的send quote。生产guard、API和金额合同均不改变。原始“未展开”描述保留原封包时点，并追加首/第二向量、合同递归与单项贡献的现有来源链接；不把已持有body继续列为待重复读取。R0168历史机器补注为unknown，不按路径猜认。

以下已有stdlib命令分别核旧来源、五叶链、六叶贡献链；不启动游戏、不访问原记录中的来源C盘、不授实机或自动语义信用：

```text
<project-python> -B -O docs/ck3-native-ai/evidence/episode04-r08-rate-application-12004/verify_r08_portable.py
<project-python> -B -O docs/ck3-native-ai/evidence/episode04-r08-rate-application-12004/verify_r08_descriptor_chain.py
<project-python> -B -O docs/ck3-native-ai/evidence/episode04-r08-rate-application-12004/verify_r08_contract_contributions.py
```

历史source封包及纠正保持精确原字节；新增摘要仅保存必要pins和derived CALL清单，合计小于64KiB。其复核期限与实际生成时间见JSON，按通用存储策略的record类别管理。
