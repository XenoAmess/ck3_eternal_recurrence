# R188：两条 post-PC 与已持 copy source 的精确连接（1.20.0.4）

本次不重读 EXE：两个实际 post-PC 都属于已持普通函数 `[28A63E0,28A6697)`，原件695B SHA `ffebf7d960edb76b71d2456b7f8722cc09092952b41c565f648410b42a47dede`。新工作是将 R188 保存的两条 qualified physical write 对到确切 store 结束边界；+28/+30 producer、payer、币种、military paid amount 与 cadence 继续 unknown，业务整卡分子不变。

## 实际来源与独立窗口边界

机器 `desktop-3fevhd2-1c74096080`；R188 PID12060/create134366470385086412、generation1、actor FullID31254、episode `native-31254-0a8ceff1be59`；代码来源提交仍为 `d05b0c780b615faa714fdf0535403bb2e6941faf`。EXE 身份复用本窗口 Root admission：CK3 **1.20.0.4 / Steam25734779**，SHA：

`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`

原严格projection recorded UTC为 `2026-10-16T18:21:53.177885+00:00`。它的状态 `ACTUAL_WRITERS_SOURCE_UNKNOWN`、两条source_status=unknown、writer_instruction_start=null和known_copy_caller_v1=null原样保留；本包另附source join，不回写旧结果。保存的完整projection6891B SHA `05575043e9ca43c0469bbbfe9d3ec74e902daf62d6778e4ce010fd1db754262d`；完整raw34982B SHA `d20028e2596ea585939c033cde5ace26f804e51c7bcb8b0ccec11d06478f9a0b`。

Root独立 `NATURAL-DAY.actual.json` 证明g12从date53149056到53149080，completed_daily_ticks1、overshoot0、pause observed；Root将其标作 Apr1 月界。trap本身**没有native date或trigger phase**，不能把这个独立exact day直接填作每条write的发生日，更不能据两条命中命名月结cadence。

观察器实际ready armed_thread_count108；raw包含108 arm、1 thread exit和107 restore readback。它以30秒自然timeout、实际exit1结束；projection证实restored/detached/cleanup_complete为true、pending_event=false，full_window_all_writes_covered=false。cleanup已完成与全窗口写覆盖是两个结论；不是zero fullcoverage。

## post-PC 指向下一条指令，不是store起点

| actual slot/field | source load | source store | actual post-PC | source RAX / after |
|---|---|---|---|---|
| 0 / +2C0 | 28A6450: RAX=[R9+18] | 28A6454: [R9+2C0]=RAX | 28A645B | 469493 / same-value |
| 1 / +2C8 | 28A645B: RAX=[R9+20] | 28A645F: [R9+2C8]=RAX | 28A6466 | 0 / same-value |

精确字节：`28A6450 49 8B 41 18`，`28A6454 49 89 81 C0 02 00 00`；其7B store结束于28A645B。随后 `28A645B 49 8B 41 20`，`28A645F 49 89 81 C8 02 00 00`，结束于28A6466。因此 post-PC28A645B本身已是下一条load20，不能把它当第一store的起点。

两条actual的R9都等于Root context1779091018144，有效地址分别为1779091018848/1779091018856，正好context+2C0/+2C8；RAX/after分别469493/0，thread1396/lifecycle1。before是last observed sample，**不是atomic pre-instruction value**；same-value仍是物理write，不证明整个窗口的字段从未变化。

695B源于2026-10-15T22:14:02.913163+00:00的同机器既有R0178有限读取。保留全部147条原ASM与bytes、原receipt/readledger和PE mapping；原.pdata row139546对应上述唯一已定位普通extent，flags2、无chain。source join只处理普通指令和原边界，未扩异常handler，不扫描其他函数或callee。原源字节本轮新增读取为0。

## incoming caller 仍未取得

已持prologue有5个push（共28h），`RBP=postpushRSP-50h`，随后sub RSP,150h，故entry return-slot地址为 **RBP+78h = RSP+178h**。两条trap保存的RBP58900609952/RSP58900609696符合关系，推得候选slot地址58900610072。它是source-derived地址，不是已经读出的return address。

本次raw没有known_copy_caller_v1字段，projection补为null；没有该slot的实际两读值，incoming caller RVA必须null。不要把后来静态 `28A6535→28D6170` 当作进入28A63E0的caller或本轮实际callee执行证明。

当前仓库observer代码只有选择`--capture-known-copy-caller`（argc15）才输出该附加叶；本次保存argv argc14，没有此选项。**没有核对所运行build-a07 binary是否含这个feature**，因此这里只是source接口与实际argv对照，不能把当前源码能力当现已安装，也不把缺叶诊断夸成已证单一故障原因。未改argv、未热重启/重attach或额外读进程。

## 可复用结论与剩余缺口

智能体可以将这两条既有实际write标为“精确源匹配的+18→2C0、+20→2C8 copy”，不将它们标为+28/+30的原始producer。视频可以展示post-PC为何需要回到前一条store边界及同值write的区别；不能说观察到付费、月结扣费、没有军费producer或+28/+30永不写。

现有两条qualified trap都不属于+28/+30，仅能说明有限、明确非全覆盖区间中没有保留对应qualified trap。入场当前value_28=216342也不能替代其生产源。下一有信息的输入仍须是+28/+30实际qualified write，或与已证copy frame绑定的真实两读return-slot值；由Root另行授权窗口，本包不制造新动作/采样。

## 离线移机复核

```text
python -B -O docs/ck3-native-ai/evidence/episode04-r08-r188-copy-writers-12004/verify_r188_copy_source.py
```

[便携JSON](evidence/episode04-r08-r188-copy-writers-12004/postpc-source.actual.json)嵌入完整小raw/projection、Root admission/meta/ready、day/finalize/start、原窗口plan/check、旧source ZIP及d05 observer source Git blob。默认标准库、不依赖C/D盘历史路径、EXE、SDK或网络；可加`--extract-originals <不存在的新目录>`恢复exact原件。绝对路径仅是provenance。机器PID、context和运行资格始终machine-bound；可移植的是来源、算法关系与代码。

新verifier只验证保存的字节/边界、实际post-PC与EA/value/source frame的组合及未升级的timeout/caller/date范围，不独立证明全部语义，也不重新执行strict collector或原19/18项矩阵。旧原件及unknown/失败语义保留，不授业务或human approval。
