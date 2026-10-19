# M7：LandState +3A0 的 bounded source 结果

`machine_id: xenoamess-full-tower-eb9d2c1186`，本轮实际观察时间为
`2026-10-19T07:52:20.029846Z` 至 `07:56:13.322717Z`。
本轮把现有 raw-cache 消费者与两个局部谓词绑定到当前 exact 1.20.0.4 文件。
**缓存 writer、刷新触发、generation boundary 和完整 player-eligible backup 域仍未知**；
H 继续 unknown/interval，M7 继续 `in_progress`。没有实现 provider 或取得运行时资格。

来源和精确字节见
[小来源索引](evidence/g2-m7-landstate-3a0-source-2026-10-19.json)、
[独立 micro 计划](research-plans/g2-m7-landstate-3a0-20261019/source-discovery-plan01.json)、
[当前 consumer 小窗](research-plans/g2-m7-landstate-3a0-20261019/consumer-windows01.json)和
[两个 reached 谓词](research-plans/g2-m7-landstate-3a0-20261019/reached-predicates02.json)。

先读了原 player-heir anchors、现有完整数组 reader，以及 M3 共享的 source cache。
原 `ACTUAL4-CACHED-CANDIDATE-CONSUMER.actual.json` 的 73146-byte blob 未重定位，
其历史机器仍为 unknown；不能由旧 header 注释追认本机 writer。
shared-span-cache 的精确同名 span 不存在，CORE map 也无该 consumer entry。
只检查了三个邻近既存 cached body：没有 `+1C0/+3A0` operand 或对 consumer 的 direct call；
地址相邻不构成 constructor、writer 或 caller 证据。一次更宽的外置文件名枚举已中断，
没有从中取得可采用源事实，也不把它描述成完整搜索。

随后按 Root 已准 micro 范围先写计划，再通过结构/文件完整性检查。
复用 M3 在本机实际流式核出的 EXE SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，
每次读前后均核 size/mtime/file ID 与该原件相同，未重复全文件 hash。
实际只读三个已到达入口：consumer 累计512字节，两个谓词16和128字节；
连 PE 元数据和一次失败的 pdata 查询在内，当前文件读取上界3700字节。
没有复制 EXE、进程读取、游戏/MCP 调用或构建。

当前文件的 `2C0B66F/67B/687/6AE/6B4/6D7` 确认原
actor `+1C0` → LandState `+3A0` → count `+C` / data `+0` →
DWORD full ID stride4 → candidate 自身 full ID `+18` 的读链。
这是原 raw-array reader 的源锚，不增加 eligibility 含义。
第二 consumer 窗起始 `2C0B660` 的前8字节未独立取得指令对齐证明，
不参与语义判断；只采用既有字段锚从 `2C0B668` 起的序列。
没有声称跨省略区域完成线性反汇编或完整 CFG。

本轮新增两个有用限制：

- `2C0B68D` 另载一个 global DWORD，`2C0B6A0/6A3` 在数组索引达到它时跳出。
  该 global 的名称和值未读取。消费者扫描受原 count 和独立上限共同限制，
  不能把其扫描范围等同完整 raw array，更不能把它当全部合法备选域。
- `2494B30` 的实际 leaf 只有
  `cmp DWORD[RCX+8], EDX; sete AL; ret`。
  `2494B40` 已见前缀遍历 receiver `+8` 指针数组、`+14` count，
  对各元素调用这个等值谓词，并生成 found 标志。
  consumer 把 actor/candidate `+1B0` → `+288` 指针中的 DWORD 交给它。
  这是未知字段的泛型 membership 链，未闭合 living/player-continuation 资格检查。
  不猜该字段是宗教、宗族或其他对象 ID。

`2494B30` 没有 pdata envelope，首次查询如实失败；后续固定入口窗显示了7字节 leaf
和 padding，不能把缺少 unwind 误作函数不存在。
`2494B40` 当前只读128字节，pdata 范围为130字节，末2字节未读；
上述结论限于已见搜索与 AL 标志，不宣称整函数等价。
M3 的另一路 serializer 已证 receiver 在 parent `+268`、DWORD 在 parent `+270`，
本轮未发现其对象类型联系；不能因两边都出现 `+8` 就拼接。

本轮额度已用完，停止新的 EXE 遍历。下一必要源是**receiver 已证明属于同一 LandState 的
`+3A0` mutation/vector-refresh 路径及其确切 constructor/update caller**，
随后才是该 producer 的完整枚举域与逐候选原生 player-continuation filter。
普通 `0x3A0` 命中、泛型 membership、title heirs、alive 和固定 D0 检查都不能单独补齐。
当前没有可实施的 complete-backup provider，不把 unknown 当0，也不改变 H 或运行中计分。

存储遵循统一策略1.0.0，本批全部新增记录峰值限64KiB、每个回执小于32KiB，
record 于180天后复核，未删除资产。索引记录本机实际容量及观察UTC；不据此准入重写入。
