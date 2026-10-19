# Driver 历史编码：有界 C 编码片段

本次在完整 JSON 字节不变的条件下，减少查询历史 sidecar 写入与 combat 历史摘要的 Python 逐标量编码开销。它是离线源码资格；当前 Game/frozen SDK 未采用，尚无新局每游戏日收益结论。

执行机器 `machine_id: xenoamess-full-tower-eb9d2c1186`。实际资格时间为 `2026-10-19T03:27:25.337506Z` 至 `03:27:34.948889Z`。原始结果、源码 SHA、输入 SHA 与输出清单见 [小回执](evidence/bounded-json-chunks-performance-2026-10-19.json)。基线函数从 `b000c9a6` 精确提取，不读旧或活跃 Driver/SAVE，不调用游戏/native/RPC。

改动只接入两个已有热编码边：`army_query_history_store.write_json_exclusive` 和 `combat_history_superseded_v1._digest`。新增 `bounded_json_chunks_v1` 对字符串键的平坦标量字典，以及列表中连续的标量小段使用标准库 C encoder；嵌套结构仍流式遍历，陌生类型与非紧凑 encoder 回原路径。每个新组合片段的保守上界为 256 KiB / 4096 项，临时列表只持有引用，不复制子树。单个超大字符串保留标准 encoder 原有的单字符串分配行为。

| 一次受控工作负载 | 原实现 | 新实现 |
| --- | ---: | ---: |
| 3,175,802B create-only 实际写入，含编码/预算/SHA/fsync | 0.407363s | 0.234781s |
| 相同 canonical 摘要，3 组交替次序的 median | 0.174150s | 0.148219s |
| 编码器输出片段数 | 712,205 | 16,397 |
| traced 编码/UTF-8/hash 额外峰值 | 3,472B | 172,140B |

实际写入减少 0.172582s（42.4%）；摘要 median 减少 0.025932s（14.9%）。这是包含大整型数组和 6144 个平坦字典的合成数据，其结构与实机查询体不完全相同，不能按字节数线性外推。实际新片段最大 9,129B；输入对象与预先生成的期望字节在 tracemalloc 开始前已分配，峰值不是进程 RSS。

成功文件的完整字节、顺序、SHA 和预算计数相同；1.5 MiB 配额耗尽时，两者抛出同一预算错误，均保留同一份 1 MiB partial 与相同 SHA/预算。4 项合同测试覆盖 Unicode、数字、嵌套别名、tuple、排序、非标准键 fallback、NaN/Infinity、循环拒绝、片段上界与非紧凑 encoder fallback。完整历史、sidecar 引用、create-only、缓冲阈值、fsync、摘要上限及恢复语义沿用原实现。没有新增全规划缓存，也没有改变候选、决策或战争处理。

在 `2026-10-19T03:29:07Z` 的收口检查中，5 个修改/新增 Python 源编译通过；新 verifier AST 的 Assert 节点为 0；`python -O` 对未获准 work-root 在创建文件前显式 ValueError 拒绝（exit 1）。这些源码检查没有重复性能工作负载。

历史 P49 `5104-5165` 的 118 日完整 wall 为 134.924610s，即 1.143429s/day；1s/day 阶段还需减少 16.924610s。full persistence 21 次合计 10.448259s，其中 `temp_stream_write` 为 9.954374s。这次修改不接入该 full-state byte write，因此不能把 P49 的整段落盘收益归给此补丁。即使全免该 persistence，旧窗口仍约 1.054884s/day；还要审完整规划、推进与查询开销。P49 两份小来源没有机器 ID，均保持 `machine_id: unknown`，不能当作当前机器实测。

P67 AUTO77 的 87.814358s 与大 combat 包只证明一个完整 AUTO 的总成本，缺少 native/normalize/archive/MCP 的互斥分解，不能认定全是编码。下一步只消费 runtime owner 自然闭合的 compact/stage 数据确认真实占比。

首个当前局 sealed compact 在本次资格完成之后到达：`CLOSED-BATCH-0008-COMPACT29.json`，SHA `4ff6d54429ce62464b7831cf6783602ab233022c0cc43b4760aa16ff74c4f452`，机器 ID 与本机相同。该批只有一次 war-results 查询 AUTO（0.418585s）与原有 MET（0.009883s），未进日；从首请求到末请求 0.497070s，s/day 仍为 null。runtime 另报之后约 79s feeder ledger 修复间隔，它必须留在首 AUTO 之后的活跃运行 wall，待后继 closed 边界精确计入，不能划回此前录制排障。此次新样本不改写早先合成资格回执。

存储登记为 `SERIALIZATION-RESEARCH-CHILD01`，根 `D:/codex-ck3-demos/2026-10-19-robert-v20261019-serialization01`。保留 4 个输出 8,448,756B，加 `QUALIFICATION.json` 6,765B，合计逻辑 8,455,521B；allocated 未核，不据此宣布物理释放。producer closed、future writes 0，无删除。16 MiB 上限计入原共享研究预算，WAL 包保持 closed，不新领容量。

后继自然闭批及 V3 复制优化
-------------------------

同机 `CLOSED-BATCH-0011-COMPACT30.json` 的精确 SHA 为 `fb2415b1cbc179a78e8d013c7417c2fefaf65e65d3670e5aa435cbae1cfea06f`。首 10 日批次 wall 61.535486s；从首 AUTO 起累计 110.445645s，含首个 0 日 window 和 48.413089s 跨批间隔，为 **11.0445645s/day，未达标**。原位来源与每类已知 RPC 的总耗时见 [累计账本](evidence/robert-v20261019-closed-wall-ledger01.json)。单个 oversized 响应只有 stat，不读其正文，未知 RPC 耗时与间隙保持混合剩余项。口报约 79s 修复时间不与这段 48.413089s 可见间隔强行等同；最新 closed 之后的修复仍待后继边界计入。聚合工具首次因 UTC 与 monotonic 的 32.6μs 差值拒绝过紧的 10μs 检查，修为 1ms 后保留原始值；另一次 8KiB 大小守卫写前拒绝，经缩短 docstring 收口，没有跑游戏或性能负载。

AUTO74 整体 30.314162s 只进 2 日，最终有原生事件，native clock 尚为 armed，随后合法取消；AUTO50 正常推进 8 日为 3.000531s。该反差已交 clock owner；单凭整体 AUTO 不能拆出等待、规划或落盘时间。clock owner 已针对普通 active_event 被旧等待谓词漏检提供后继补丁及独立软件证据，此处不冒充已经实机部署或已回收 30s。

Root 随后批准 `combat_phase_contract.normalize_combat_simulation_inputs_v3` 的 canonical-enriched 分支仅修改剔派生字段前的复制：由复制整份输入改为 root/phase 两层浅拷贝。v2 normalizer 原有 detached 返回、phase raw 的新值构建及 advantage 的先复制后适配已审；完整递归 normalizer、`recomputed != value` 与最终返回隔离均保留。没有复用未经重算的派生结果。

实际 `2026-10-19T03:41:04.060411Z` 至 `03:41:09.310761Z`，同机完成 [V3 离线资格](evidence/combat-v3-revalidation-copy-performance-2026-10-19.json)：2,892,696B 有效 canonical fixture 的 3 组交替 CPU median 从 0.210316s 降至 0.166886s（20.6%），traced 额外峰值从 14,265,354B 降至 13,152,122B。成功 wire/enriched/unavailable 的完整 JSON 字节与顺序相同；5 种篡改保留相同异常和消息；成功与拒绝均不改输入，输出可变对象图与输入完全分离。原构造的 32 个合成 knight event 在 CPU 采样前触发 canonical 4MiB 守卫，缩为 8 个后完成唯一一组资格，无正文落盘。verifier AST Assert=0、源编译与一个 `-O` 显式拒绝分支通过。

该 V3 结果仍是有效生产 schema 的合成数据，不能按大小推算 25MB 包收益，也不能折算当前 s/day；非常规对象子类与校验过程中并发改写输入不在本资格范围。新源等待下次 SDK 合法维护采用，当前运行的 frozen SDK 未被本支线热改。V3 verifier/小回执合 15,748B，累计 wall tool/小回执合 15,284B，均登记在原其它共享研究预算、外置写 0，旧 D 包与 WAL 保持 closed。
