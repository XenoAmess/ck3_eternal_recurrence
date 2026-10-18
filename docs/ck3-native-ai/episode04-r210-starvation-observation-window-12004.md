# R210：零库存后，30 个自然日能证明什么

库存已经为 0，不会自动每日扣兵。对当前这条普通供给损耗链，首先要轮到该军队的真实调度桶，再通过 updater 准入，更新后的库存仍处于有损耗分量的档位，产生正整数预算，最后真正写减物理 DATA。**30 日是最多覆盖一轮桶相位的观察上限，不是必定出现饥饿扣兵的承诺。**

本页是离线来源复核和观察判据，没有执行 SDK、游戏、构建或新的 EXE 读取。机器相关复核绑定 `machine_id: desktop-3fevhd2-1c74096080`；实际观察时间、文档原件 SHA 与来源提交见同包 `ROOT-DELIVERY.actual-a01.json`。R210 当前结果尚未在本包读取，不把本页写成实机正例。R209“初始化后两天没有目标扣兵”保留原事实，不据此推断机制不存在。

## 实际调用时钟

`.4` dispatcher `2A9A570..2A9AB73` 读取 GameState `+9C` 的 **stored D**，以 `uint32(D) % 30` 选择原始 CArmy 指针桶。`2A9AB46` 对桶中每个指针 occurrence 调用 `24E3410`，返回地址 `2A9AB4B`。重复指针是不同调用，不能去重后计算机会，也不能将一次预算复制成多次。

同一支 manager 先做 cleanup、gathering/due、月首 regular refill、assault 和 late Army 工作，再进入这个桶。因此它既不是“每天每支军队一次”，也不是“全军固定每月一号扣兵”。月首补员还可能抵消同窗净人数变化，净人数差不能替代物理扣兵账本。

下一正常日期的已闭合 source pair 是：

```text
nextRaw = signed32(uint32(currentRaw) + 24)
nextD   = trunc0(signed32(uint32(nextRaw) - 43800000) / 24)
phase   = uint32(nextD) % 30
```

不能一般地用当前 stored D 加 1；日期和 D 是独立读取的字段。普通、不跨 DWORD 有符号边界且每天实际推进 +24 的区间，后继 source pair 的相位逐日走过全部 30 个值。**只有该军队仍在已读取的真实桶里、membership 未变且实际日期阶段确实发生时**，30 日才覆盖其一轮调度机会。并不保证该机会准入，也不保证损耗。

## 为什么刚归零仍可能暂时不扣兵

`24E3430` 调 updater `24E4CF0`，`24E3437` 检查实际 AL；只有 true 才由 `24E343E` 调供给人数预算 `24E32C0`。AL false 时供给预算为 0。

updater 拒绝 Unit `+170 == 3`、原生 combat、gathering、Army `+5C != 0`，以及以下年龄条件：

```text
trunc0(signed32(uint32(passedDate.low32) - uint32(Army+190)) / 24)
    <= loadedGrace
```

因此等于 grace 仍拒绝。`+190` 是 gathering 完成锚点，`+188` 是成功供给更新日期；updater 不把 `+188` 当 30 日冷却门，也不写 `+190`。如果本轮唯一匹配桶的机会发生在 grace 内，30 日内可以始终没有成功供给更新。下一次同桶机会可能再等 30 日；本页不授权延长当前场次。

成功后 updater 一次性加整笔原生 rate，再 floor 到 0、cap 到当时容量；不除 30，也不乘经过天数。stock 0 加负 rate 后仍为 0、或者 0 加 0，都可能是成功更新。若正 rate 先把库存补回到无损耗档位，同次预算会读补回后的库存。

标准表在实际加载为 `[60,10,0] / [0,0,5000]` 时，0 与 9.99999 同属低库存档，exact 10 不属于该档；0 没有额外倍率。实际 loaded 表、将领分量和 fleet suppression 必须使用本次读回。普通无溢出域的整军预算是 `min(E, floor(E*F/100000))`；标准 F=5000 时，E=19 得 0、E=20 得 1，没有“至少扣一人”或小数 carry 的补偿。画面显示兵数不自动等于合格人数 E。

## 本轮可直接采用的判据

1. 优先消费现有同帧 full-history 原件中的 `future_daily_supply_schedule_inputs_v1`、`source_derived_next_daily_supply_frame_inputs_v1`、`army_update_clock_v1`。`observed_army_bucket_phase` 只是首次 pointer-match，不能代替全部 30 桶及 positions。用已发布 `same_input_conditional_future_daily_supply_schedule_v1` 和 `source_derived_next_updater_writes_v1.next_admission` 确定最近条件机会；不为找相位额外盲推进 30 天。
2. 在既有逐日观察中，每次只按实际完成的 +24 日期和双 FullID、进程/连接代取独立后验。必须保留两个 journal 各自的 fence、gap/overwrite/capture failure；stock 0→0 或 drain 0 时仍读取 callback/writer，不能跳过。
3. 命中最小物理正例即可结束 R05 这部分研究：自然 callback `2A9AB4B`，同 parent token/thread/date/双 FullID，writer 当时库存为 0，供给 preferred return `24E35FF`，完整 unique physical DATA 的有符号 debit 总和 > 0。供给 residual 则另核外 return `24E3638`、flags 2；不能只凭 inner `2A958E8` 归因。围城 `24E377C`、combined residual `24E37B3/flags0`、县进入 `24E2630/flags0` 分列。
4. 若看到了 callback 但无供给 writer，先区分：准入未知或拒绝、更新后 stock 变正、loaded/component/fleet 抑制、整数预算 0、writer 自身跳过、capture 不完整。当前 callback entry/return 不直接记录 updater AL；库存没变不能证明 AL false。若已部署的 mixed writer budget leaf 真有样本，可用其原供给预算区分，缺样本不补 0。
5. 到当前 30 日上限仍无正例时，输出实际覆盖的桶机会、已知准入/库存档位与 capture 完整性；不报告“零库存不会扣兵”。若唯一机会受 grace 阻断，下一工作包应选择已经过 grace 且下一真实桶含该军的合法现存 checkpoint；若预算确为 0，应先解释实际 fraction、eligible E 或 suppression。若正预算/请求已见但 physical debit 为 0，则转查同一 writer 的 physical target/skip，而非继续盲耗日期。

## 可复用原始来源

- [零库存时钟及采样](episode04-zero-stock-clock-and-capture-12004.md)：`.4` dispatcher 完整 1539 B，SHA `60520f156b0b4c3a9f0846d67f322f620ac0ed9e946052e7cf328f4f2a4ca4a7`；原 raw SHA 是既有证据，本包未重新读 EXE。
- [当前 callback 的供给风险](army-current-callback-supply-risk-12004.md)、[updater 写入与准入](army-source-derived-next-updater-writes-12004.md)：`24E4CF0..24E4EBF` 463 B；callback `24E3410..24E3A3C` 1580 B。
- [下一 source pair](army-next-admitted-supply-tick-input-12004.md)：既有 `.4` 两次有限读取 155 B，真实日期/D 写入公式；不是新增反汇编。
- [零供给整数分配](episode04-zero-supply-loss-source-12004.md)、[首次归零与正预算](episode04-first-zero-positive-budget-decision-12004.md)：0 无额外 early return，同 callback 可首次归零后立即计算预算。
- [共同调用与物理 writer](army-actual-supply-parent-join-observation-12004.md)：stock、budget、request、physical debit 分层；DATA alias 不重复计数。

本页可用于视频解释和智能体选择观察窗口；它不授予 R05 实机通过、完整 30 相位总损失、固定每月百分比、自然未初始化样本或拍摄签核。
