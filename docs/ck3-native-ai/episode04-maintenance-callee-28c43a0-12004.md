# 战争四期 R08：current 费率 callee 28C43A0 的实际来源（1.20.0.4）

**新增的是军队对象到费率输出缓冲区的数据流，已付维护费归因仍未闭合。** 在已有 current getter 的真实调用边 `2C141D7→28C43A0` 后，本次取得这个具名 callee 的完整直接函数体；没有将费率当成付款，没有新增实机通过格。

来源机器 `machine_id=desktop-3fevhd2-1c74096080`，观察时间 `2026-10-16T09:57:32.599613+00:00`，基线 `20c7319b6964c80fa419540cf4e30852feff4810`。新鲜流式核对本机 `ck3.exe` 的 SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；来源 build 身份为 1.20.0.4 / Steam 25734779。本次只读取离线映像，不证明本机运行、Steam 状态或安装验收。精确 bytes、全部指令、PE 边界和输入 pins 保存在[小型 source JSON](episode04-maintenance-callee-28c43a0-12004.sources.json)。

## 完整直接函数边界

通过 PE exception directory 的二分定位，唯一 entry 精确命中 `28C43A0`，区间为 **`[28C43A0,28C4532)`，402 bytes，95 条完整解码指令**，末尾 `28C4531: ret`。函数 bytes SHA 为 `47a076981a8f92c4ae53c2da28c81b44a8ed90ffca55b593dfa17108c97a9a81`。直接条件跳转均留在区间内；唯一直接 CALL 是末尾的 `24E1E80`，本次不展开它。

复用现有 bounded PE mapper 的 `sections` / `read_rva`，不调用其历史 1.19 main 或历史 anchors。源代码/metadata 原始读取含两次小 header 共 **5,750 bytes**，低于本 lane 8 KiB 上限；另对 EXE 101,040,248 bytes 做流式 SHA 身份核验，没有导出或复制整个 EXE。输出采用单份小 JSON 和本文，不生成全图/xref/邻域扫描。容量观察见 JSON；这是小型 record 写入，没有续期已过期的重型写入例外。

## 新证实的数据流

调用 ABI 复用已持有 current getter 的真实来源：`RCX=Character`、`RDX=out80`。函数入口保存 `Character` 到 RSI、`out80` 到 RBX，并清零输出的全部 80 bytes。

| 指令区间 | 直接证据与边界 |
| --- | --- |
| `28C43CB..28C43EE` | 读取 `context=*(Character+1C0)`；非空使用 `context+278`，空则使用 RVA `545A918` 的 fallback 描述符。从描述符 `+0` 取 ID 数组，`+C` 取有符号 DWORD count，构造 `begin+count*4`。此处没有读取 settlement 的 `context+28/+30`。 |
| `28C4410..28C4444` | 依次解析数组中的完整 32-bit UnitID：低 24 bits 做 index，unsigned capacity `+2C`，rows `+20` / stride 16 / pointer `+8`，对象 `+10` 必须等于完整 ID；否则使用 `5D1E378` fallback。实际 registry 为 `5D1E380`。 |
| `28C4444..28C4483` | 仅 selected Unit 的 DWORD `+18 == 0` 分支继续；非零跳过本次对象。registry 非空时，从这个 Unit 的 `+178` 取完整内部 ArmyID，以相同 generation 检查方式通过 `5D1DE48` 解析 CArmy，失败或 null registry 使用 `5D1DE50` fallback。`Unit+18` 的枚举名称不由本次函数自行命名。 |
| `28C4490..28C44F9` | 将 selected CArmy 的 QWORD `+130,+138,…,+178` 十槽，分别 ADD 到 `out80+0,+8,…,+48`。没有在这里计算或刷新这些缓存槽。 |
| `28C4504..28C450B` | 数组地址每次加 4；按原顺序访问至预先构造的 end，不自行去重。重复 UnitID 将重复经过同样分支；这不是按 ID 集合求和。 |
| `28C4511..28C451A` | 随后调用 **`24E1E80(RCX=out80,RDX=Character,R8=0)`**。helper body/effects 未读；最终输出不能被写成“严格等于上面十槽的和”。 |
| `28C451F..28C4531` | 返回最初的 `out80` 指针并恢复寄存器。 |

Unit / Army 类型角色复用同一 exact4 的[army-world source proof](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_4_army_world.json)及[Character suffix 的 generation selector 合同](army-character-detachment-suffix-12004.md)，不因地址相同就把旧版本通过数迁移过来。这里新读取的 RIP operands 独立匹配了这些 registry/fallback 槽。

```text
Character → *(+1C0) → +278 的 UnitID occurrences
  → full-generation CUnit（+18 == 0）
  → +178 full-generation CArmy
  → CArmy+130..178 十槽 ADD 到 out80
  → 24E1E80(out80, Character, 0) [未展开]
  → 返回 out80 → 已持有的 current getter 再累加
```

## 类别、对象、付款与周期分开

- **类别/对象：** 已定位 current 军事费率查询第一分量经过哪些 Unit/Army 对象和物理槽。`CArmy+130..178` 的每槽 producer、刷新和具体业务构成仍未证；此处只保留原始向量命名。资源槽含义复用已有 public reader 合同，不从内存 offset 猜费用类别。
- **付款：** 直接 body 没有 settlement `context+28/+30` 的读写，也没有 wallet ADD/SUB。当前 getter 的父链位于 settlement 之后；本函数不能倒推同次已付军事金额。`maintenance_attribution=unclosed`，`paid_military_amount_raw=null`。
- **周期：** 费率查询输出沿用既有 monthly-rate 消费口径；本次没有实际 scheduler、缓存刷新或交易周期证据。不得把这次 getter 调用时间命名为每日/月结付款。
- **副作用：** 自身的非栈写只直接落在 caller 输出 80 bytes；transitive helper 的作用未闭合。因此不能据此宣称整条函数纯只读，也不能安装新 native invocation。

## 下一份最小来源

第一分量的具体未展开边已缩为 `28C451A→24E1E80(out80,Character,0)`，缓存 producer 仍为 `CArmy+130..178` 的真实 writer。若研究目标是补齐 current rate 的组成，下一次需独立声明这个具名 helper 的有限 source 计划；本次不自动展开。另一个分量 `2C142B0` 由并行 lane 负责，不能用本函数覆盖它。

若目标仍是“已付军事维护费”，优先消费新的 source-qualified settlement `context+28/+30` writer，继续按[既有 R08 最小证据计划](episode04-r08-next-maintenance-attribution-12004.md)关闭类别、同次应用与 payer store。仅取得更多费率函数依然不抵扣这条业务缺口。

智能体可把本记录作为 exact4 current-rate 的来源依赖图；视频可说“已追到实际 Army 缓存向量及后续 helper”，不能配“这里就是本次已扣军费”的结论。知识可跨机器复用；本机映像、容量和执行事实不跨机外推。record 复核期限为 `2027-04-14T09:57:32.599613+00:00`，不产生新的实机资格或研究完成百分比。
