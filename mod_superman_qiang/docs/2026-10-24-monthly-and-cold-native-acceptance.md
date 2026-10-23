# 月度夫妻生活与冷重载实机验收

本记录的执行机器为 `machine_id: desktop-3fevhd2-1c74096080`。实际观察截至 **2026-10-23T22:13:55Z**，来源为以下公共场次、独立存档读回、原生关闭回执和 Steam 状态回执。两场源码均固定在 `2d810e442d28ade91df09052ca72fa4f4f56cb6f`，游戏为 **1.20.0.4 / Steam build25734779**，EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。使用的公共 runtime JSON SHA-256 为 `2afce59cd300fa7ecdb30e076e28c361c307810a4e583d6198a4139a548223f6`；原生工具仅用于开发验收，不是玩家运行依赖。

R0030 的公共 `natural-simulation` case 与 R0031 的 `natural-cold-reload` case，实际 run、verify 命令均返回 0，`case_acceptance_pass` 与 `qualified_boundary_pass` 为 true。这是两个限定源码 case 的验收，不代表整个产品或 Workshop 发布完成。历史失败和 [R0029 超时](2026-10-24-natural-fixture-r29-findings.json)保持原样。

## 月度计数：R0030

实际玩家为 31254，十二角色引用依次为：夫妻 65831/65832、妾主/妾侍 65833/65834、孕中配对 65835/65836、不育配对 65837/65838、未成年边界 65839/65840、死亡边界 65841/65842。夫妻的 Catholic/Roman 与 Orthodox/Byzantine 身份保持不同；原生基线同时核对关系、年龄、生死、怀孕及有效生育力。

| 独立保存阶段 | 实际日期 | 八名合格角色 | 三名在世排除角色 | 死亡角色 65842 |
| --- | --- | --- | --- | --- |
| 基线 | 1066.9.17 | XP0，月份与名单缺失 | XP0 | XP缺失 |
| 同月重复调用后 | 1066.9.17 | XP1，M12801，四对名单双向唯一 | XP0 | XP缺失 |
| 实际跨月后 | 1066.10.19 | XP2，M12802，四对名单双向唯一 | XP0 | XP缺失 |

游戏从 1066.9.15 推进了 34 个自然日，在 35 日上限内完成。七个预期 PASS marker 各出现一次，没有 fixture FAIL。原生观察器实际记录一次月度回调，保存的 `sxanf_native_pulse_count=1`，其月份与 `sxanf_before_explicit_month` 均为12802。**夫妻双方在显式补充回调之前的经验快照已是2，最终仍为2**，因此该配对的新月经验可归于真实月度回调；其余六名合格角色证明的是最终总数，没有额外声称逐对独立归因。

最终 `sxanf.10` 的实际原生 context 为实例3、revision147，唯一显示项为 native index0。实际加载的定义 SHA 为 `8dfeff3ddcf6c5965d29d62962fb581bcd06513a7263d2e78482228966c4d172`，该选项没有游戏效果。Root 先经原生接口关闭一次，确认 event 为 null、日期未变，再保存唯一终态。因此终态证据是**关闭后保存**，没有声称存在关闭前的另一份存档；此文件同时成为下一场冷重载来源。

| 保存原件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| R0030 baseline | 68453670 | `fd6e64b0bb2337b2ec355b2b1e7d36831f610866019110daf06d609d877cc7f5` |
| R0030 same-month | 68623373 | `f03bdad82c2d2e882daa3484397f2fe25c41d3f5e0eddd2680cd1a970f2b1454` |
| R0030 final | 69409184 | `dddf14a6d837642623e24f3596d479190918e6808ce97c6d0f0127f6891cf1b0` |

## 独立冷重载：R0031

R0030 的原游戏进程为 PID22980，实际创建 FILETIME 为十进制字符串 `134372645551159774`。R0031 为新的 PID2800，实际 Win32 `GetProcessTimes` 读回的 FILETIME 为 `134372664876344364`。没有从浮点时间反推 FILETIME。

R0031 通过公共 saved-campaign 入口载入上述终态，保持玩家31254、1066.10.19及暂停状态；实际 restore 回执的 new_game、start、fixture_setup 请求均为 false。被动夹具仅含六个既有定义/本地化文件，没有启动注册器；未推进日期、重放行为或重置变量。冷加载后只提交了一次新的原生 SAVE。

独立解码后，通过既有强类型 `TwelveCharacters` 与原始 `SavedReadbackOrigin` 比较，十二个完整ID、生死状态、经验的缺失/零值、月份及双向伙伴名单双方完全相等。冷 SAVE 为 **69411031 B**，SHA-256 `3ba9d6ef2ee20212b37e7ca6f831dd62f60710505fc1b47b44e67fdb9d88c76e`；完整文件因保存元数据而不要求与来源字节相同，比较基于约定字段，未放松身份或源文件守卫。

冷加载的非空 error.log 另行保留，其中包含原版位置 `slander_scheme.txt:50` 的 `is_valid_agent_standard_trigger [Owner not defined]` 等诊断。没有声称全部日志无错误，也没有仅凭文件位置断定其因果归属。所检查的 SXAD/夹具错误子集为空，十二角色状态精确比较通过。

## 关闭、证据与边界

两场均由 Root 查看新原始截图中的“保存游戏”未勾选状态，再通过原版 GUI 退出桌面。独立保留的 OS 句柄实际返回0，原生 process exit 为0、Job关闭前/最终进程数均为0、cleanup为true；keeper 实际退出0。R0030 的 CAS释放序号为8510，R0031为8517，闭场 Steam 原生状态均为 offline。

证据根目录为 `C:/ck3-superman-validation-20261023`，以下是本次实际来源：

- `runs/desktop-3fevhd2-1c74096080--superman-qiang--R0030/`：冻结参数、原生报告、三个 Root 阶段、case结果、正常关闭及 keeper 原始等待结果。
- `ops/R0030-baseline-readback-a01/`、`ops/R0030-samemonth-readback-a01/`、`ops/R0030-final-readback-a01/`：三份不可变原件及独立读回。最终 raw readback SHA 为 `8918abff2b935f50f8fcbceb3f71509538a30e27aa9eb3296a982b0e628112d3`，最终 assessment SHA 为 `d88a7b1f0285a4b9b931427195ea6e8ad856644399c7cd8bd164622578b0d7d4`。
- `runs/desktop-3fevhd2-1c74096080--superman-qiang--R0031/` 及 `natural-cold-scene-a01/public-verify.actual.json`：独立公共冷重载及 verify 原件。
- `ops/R0031-cold-readback-a01/`：不可变冷 SAVE、raw readback、强类型比较及加载诊断。raw readback SHA 为 `102c4d97b45ba17e355025e3c346417977868819390a66af9565b966e67b43d5`，assessment SHA 为 `c7715f21bbc62eef86414c4f1ab1af4ce4300326bdbb493f2acc3f6c44fea1b6`。
- `ops/R0030-screen-release.actual.json`、`ops/R0031-screen-release.actual.json` 及同序号 `steam-background-*-closed-a01.json`：实际释放与离线读回。

原始证据依通用策略于 **2026-11-22** 复核，必要活跃来源在该日前保护以供本轮整合；小型记录于 **2027-04-21** 复核，不授权永久续存大文件。当前仍未证明的内容包括通知重复的根因、同性婚姻的独立引擎设置、全部第三方兼容，以及对引擎每次自然受孕随机判定的精确观测。本方案按原生月度频率模拟夫妻生活；显式脚本受孕尝试的失败计数覆盖另见来源审计，不能把本矩阵外推成全部剧情分支的实机通过。本候选未上传。
