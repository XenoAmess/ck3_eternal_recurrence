# 原生财政目标的保存与账户通知：1.20.0.4

`machine_id: xenoamess-full-tower-eb9d2c1186`；本轮静态审阅时间2026-10-25T22:59:02Z。EXE绑定为1.20.0.4/build25734779/SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本篇复用已有239字节原件，没有新增EXE读取、哈希、Game、SDK、构建或生产改动。

已有 `19EAD90` 确实调用[新闭合的997字节目标计算](finance-native-budget-target-12004-2026-10-26.md)，并将80字节复制到strategy+1E0..22F。它先清原始selector0或3对应的四个tracker槽，再按已有账户参数的正、负、零分支通知。**这建立目标计算到保存字段的来源边，仍未建立两个war_chest脚本getter，也不是一笔钱包收付款。**

## 复用原件而非再次采样

原件是仓库 `evidence/declaration-upstream-reuse-boundary-2026-10-19.json` 的 `new_bounded_source`，15401字节，SHA `634700bdcdc0fc64810a5ecab37bb8922afff81b111e9791ddde3c2583874697`。其中raw_hex精确覆盖 `[19EAD90,19EAE7F)` 239字节，SHA `dc9df24089a568667f3823a3758b30025472cda5f3f059feee741c7aaf7da56b`，64条指令完整连续。

b64的 `WAR-CHEST-HELD-REUSE04.json`（1290字节，SHA `2d1b5399ae12fc594e28973719778d810b123ec326da283ef6238ad0225a6dda`）重新核对原件hex、哈希和64条拼接，已在batch04 financial/take前取消该239字节重采。本岗没有制造替代raw。原件2026-10-19的机器与静态build身份保留；不是当前加载状态。

本岗 `AI-CHEST-STORAGE26.json` 保存新连接，`AI-CHEST-PLAN26.json` 绑定10份来源及[同源图](finance-native-budget-storage-12004-2026-10-26-graph.md)。实际check/render均exit0；仅结构与来源完整性通过，3个业务case仍pending。

## 真正的计算、保存和符号分支

记C为RCX输入context、S为[C+20]，mode为EDX，A为原始signed R8。

| 路径 | 当前字节可证事实 |
|---|---|
| 初次S为null | 19EADAE直接跳返回，不清槽、不重算、不通知 |
| mode=0 | 选择S+160；mode=3选择S+1A0 |
| 其他mode | 选择字面global5D218B0；不把它改成我方拒绝分支 |
| 19EADD6..19EADE1 | 清选中块的四个连续qword，共32字节 |
| 再查[C+20]非null | 19EADF3调用19EA9A0(local80B,C) |
| 19EAE0B..19EAE2B | 重读S，五次16字节复制至S+1E0、1F0、200、210、220 |
| A>0 | 19EAE50尾跳19EAE80(C,mode,A) |
| A<0 | NEG64后19EAE68调用19EB5C0(C,mode,负号后的A,R9D=3) |
| A=0 | 不调用上述正、负helper |

第二次context检查失败只跳过重算，后续仍按A分派。不能把初次与后续指针读强行合并为一次原子快照。INT64_MIN取负按机器位保留，不能偷换成无限精度绝对值。

目标计算25只有输出槽0、槽6可能非零，因此它们在这次实际复制后对应S+1E0、S+210，其他八槽复制零；这不是war_chest getter字段命名。两次mode初始化各可重新计算整个80字节目标，不能说mode3只更新一项。

正分支本体还未取得；该尾跳没有在本体明确设置第四参数，不授予R9业务语义。函数也没有构造跨分支aggregate success；返回、尾跳或目标已复制都不能当付款成功。

## 初始化caller和实际credit通知是两种输入

既有current initializer在19E7D1E传mode0，A取Character+1B0对象的+100或0；19E7D9D传mode3，A取通过已有Land守卫的Land+318或0。它们是读取已有账户字段来初始化tracker，没有创建新金币。

既有 `resume60/native_war_cash/RESOURCE-APPLICATION17.json`（57165字节，SHA `8a3cdf78c028271fdbb5452e99aa50eff3493e73c6ee6dbe6041ea6f5517ca3d`）另有两个真实入边：

- 310D6C5在原resource0 credit分支通知19EAE80，EDX=0。
- 310D9FD在原resource6 credit分支通知同一helper，EDX=3。

这两处RCX来自 `*(*(Character+1B0)+278)`，并检查context+20；R8保留原分支金额。它们不是当前静态审阅中的真实收款记录。初始化已有余额与credit后通知不能合并为两次钱包ADD；同一角色也不能代替整段callback两端账户身份证明。

## 正分支缺口与已有负分支知识

已保留pdata为 `[19EAE80,19EAEAA)`、42字节、row84855/unwind51BFD04。b64对shared-span-cache及相关repo来源作有界检查后，未取得这42字节原件；不把该查找扩大为全域不存在。后继只请求这42字节，追实际callee/字段和参数，不开全image扫描。

负分支155字节pool扣减叶的既有exact4知识见[被动付款专题](war-payment-passive-12004.md)：按selector0/3选择+160/+1A0，优先component后3..0，最后pool3可负。来源机器为desktop-3fevhd2-1c74096080，原160字节含5字节padding；本轮只复用静态知识，没有重读该机器原件或外推其安装/运行资格。literal3保持原值，不能命名为军事维护费component。

当前保存目标、四槽pool和脚本war_chest/current maximum的注册、读取与失效关系均需独立证据；不能根据旧版+168形似或余额相同授予getter别名。此处无termination报价、雇佣到场、借款退款credit、可支付性或政策调整，也不增加首场新前置。

本岗仍在D≤2MiB、Z独立docs≤128KiB额度内；复核2026-10-26T08:00:00Z，不自动续期。新增游戏日0，M0–M7实机状态不变。
