# 第一期 A 冷载与 F→B 的公共入口

本页是冷载操作卡，**尚未启动 R2/R3**。原生缺 mod 确认的已有能力与未知边界见
[saved campaign / missing mods](saved-campaign-vanilla-and-missing-mods-12004.md)。
它不要求重开 867，不修改保存内容，不用旧 Start 的 ACK 追认冷载通过。

## 本次已冻结的输入

`machine_id: 4-8e1c2f1861`；2026-10-17 08:58:03 UTC 独立只读计算整文件 SHA：

| 输入 | 字节数 | SHA-256 |
| --- | ---: | --- |
| A：已选择保留 Hanafi | 50,214,831 | `8cadd902d3360995ecfb1541013a72b80408ff041e25b9627592553e2cf9f662` |
| F：准备事件尚未选择 | 50,308,970 | `786afb9eb40e8952d8aeade35eebd869ad7c7383fc28894389e2859451f750f1` |

证据为外置 `episode01/frontend-save-input-summary.json`，A 来源为
`runtime/state-ep01-a02/profile/save games/xar_checkpoint.ck3`，F 为
`scenario/saves/F-pending-prepare.ck3`。两者是 `SAV0101` 二进制，开头含 `1.20.0.4`；
本次没有解析其二进制 mod 元数据，不能据此声称移除 mod 一定不会产生提示。
原件保持 exact SHA；不能通过删改 mod 元数据或重新编码保存来消除提示。
两份输入是当前 A/B 实验活跃基线，复核期限 2026-10-24；届时按通用存储策略结合使用情况复核。

## R2：A 加载到明确的 vanilla profile

1. R1 正常闭场、keeper/CAS 释放后，整合新的 shared host/native 并冻结一个公共 manifest。
2. 公共 adapter 调 `materialize_product_profile(context, None, plain_configuration)`，再调
   `finish_product_profile`。四份普通配置原字节固定；`dlc_load.json` 明确
   `enabled_mods=[]`。inventory schema 为 `ck3-saved-campaign-vanilla-profile-v1`，
   `enabled_mods=[]` 与 `product_files=[]` 成对，不制造占位 mod。
3. case `startup.mode="saved_campaign"`，`saved_campaign` 声明
   `save=<A原件>`、上述 `bytes/sha256`、`player_id=15893`、`date_raw=51394920`、
   `product_inventory=<公共prepare输出saved-product-inventory.json>`，初始 plan 仅只读。
4. 公共 host 自动复制 exact A 到新 profile 的 `save games/restored_campaign.ck3`，
   单次 `-loadsave=restored_campaign`。不带 frontend bootstrap/fixture-start-policy、
   不 NewGame/Start，不使用 `-continuelastsave`。历史 `--fixture-profile` 参数仅选择隔离 userdir。
5. 原生读回实际新 PID/connection、玩家 fullref、暂停日期、campaign root；再读 religion/rite、
   圣地状态，记录 A 仍为 Hanafi，且本 run 没加载准备 mod。实际冷载前均为 NOT_RUN。

代码门槛为 host commit `76c6168ea` 与公共 prepare commit `46b1f7a28`；前者 7 项、后者
4 项聚焦测试通过。旧 product-only 的非空 mod、完整文件 SHA、无 cold registrar 守卫保留。
`saved_campaign_inject_after_load=true` 会等 In Game 才注入；若缺 mod modal 阻挡更早阶段，
此模式不能提供已注入的 MCP。不能把已有 ruler-designer Accept 复用成 load-confirm。
先做实际 CLI 读回；只有真实出现阻点时才采集并补精确 typed route。

## R3：从 F 选择 B，然后再保存并移除准备定义

F 还含未选的准备事件，所以第一次从 F 恢复不能直接删除该事件定义。使用原 bootstrap 的
**四文件 event-only 投影**作为 product：`descriptor.mod`、原事件文件和中英两份 localization。
全部四文件字节与 R1 原件相同；省去 bookmarks 与 `on_game_start_after_lobby`，因此没有二次
初始化/加虔诚入口，也满足原 saved product-only 禁止 cold registrar 的守卫。
descriptor 的名称/版本保持，但不因此保证引擎不会报 mod 差异。

保存开局的观察合同应固定 `event_definition_key=xar_faith_h01_prepare.1`、actual saved actor/root、
日期 `51394920` 与显示顺序对应 native options `[0,1]`，**不把旧进程 event instance `1`
当作新进程前提**。使用明确的 saved-startup v2 profile，输入
`expected.event_instance_id=null`，由新进程两个实际 owner 帧后的 active event 绑定当前 instance，
然后复用原严格 definition/root/date/options/fresh 保持校验。旧 v1 fixed-instance 合同不变。
本页的 actor `15893` 是本次 F 实际保存输入的期望 fullref，不能换写为历史 ID `34014`。

纯 proof handler 为 `tools/ck3_mod_acceptance_cases/faith_e01_saved_startup.py` 的
`qualify_prepare_event_from_save`，只消费已绑定 actual instance 的上下文，检查四文件 exact SHA，
不查询/选择/改游戏。contract 的 handler 与 dependencies 均按公共 case 机制冻结 size/SHA。
动态实例合同的 host 实现/聚焦结果由对应候选追加，不以本文替代其运行。

R3 原生观察到该双选事件后，先留完整帧/实际选项，再由操作者一次调用
`ck3_select_event_option(option_number=2,event_instance_id=<本进程actual>,expected_revision=<fresh>)`。
独立读回原事件消失、rite=Maliki、日期未变及 piety 未再次增加，再保存 exact B。
B 后续 coldload 可复用 R2 vanilla 路线。A、F、B 不覆盖彼此；选项 ACK 不替代上述后验。
