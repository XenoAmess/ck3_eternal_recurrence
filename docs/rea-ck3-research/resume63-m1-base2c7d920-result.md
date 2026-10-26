# Resume63：2C7D920 的 flags、原始返回字节与副作用

machine_id: `xenoamess-full-tower-eb9d2c1186`。离线 PE 观察；无 CK3/Steam 动作、无 live actor。完整原件位于 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-m1-base2c7d920-01/`。本题接 [上一层 Gate](resume63-m1-gate2c7ded0-result.md) 的实际 `2C7DF4C` 调用，**不能据此命名 join/persistent 或新增已知资格字段**。

## 问题与读取边界

caller 传 member RCX、已解析 target RDX、五 flags 指针 R8、type 指针 R9、nullable 输出对象作为第五 stack 参数。问题是这些输入如何产生 P0、五 flags 如何选择检查、type 的字段/loader/slot 能否闭合；允许原始 AL 不归一、输出改变执行、调用 opaque 等反例。自然继承/实际 runtime producer 仍 UNKNOWN。

先查两个已声明 cache 根8879/333文件名，无覆盖完整 body；不宣称全盘不存在。复用上一题 fresh probe153795 raw12 `20d9c70272dcc70204872b05` 定位；当前 PE 全 hash 后只重核已知 pdata 一行12 B，确认 `[2C7D920,2C7DC72,52B8704]`、文件偏移98684196，再读固定850 B，没有重做204 B二分。PE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`、101040248 B、base `0x140000000`；1.20.0.4/build25734779 是来源合同，不是 loaded 资格。无 callee/globaldata/incoming/vtable 跟随，无全 PE 导入或 Ghidra。

raw `raw/new-02C7D920-02C7DC72.bin`850 B，SHA `52c9887141468aa8b9ba0ad76fd3a6afc27191aed13915ccb0f4b94878545649`。原件覆盖与正常流程必须分开：

| 范围 | 指令/字节 | CFG |
| --- | --- | --- |
| Capstone 完整 RF | 207 / 850 | 36块，包含不可达尾块 |
| 入口可达正常流程、Rizin pdf | 206 / 849 | 35块57边，逐边相同 |
| RF最后 `2C7DC71` | 1 B `CC` | 不可达，无新正常边 |

206条 pdf 指令逐 VA/size/bytes 相等；26 branch、20 direct call 的 signed target 独算一致，另1 virtual call。唯一 RET `2C7DC18`，尾部初始化分支仍可跳回主体，不能把第一个 RET 后所有字节都排除。provider 未列尾 CC 不等于原 raw 缺失，也不能写成207条全部匹配。portable单 record 与 flat按 JSON 值/类型/数组序 deepEqual。opaque callee 正常返回和 Win64 保存 nonvolatile 是局部 CFG/寄存器分析前提，异常/unwind未闭。

## 有限数据流

- entry 保存 member R14、target RDI、flags R15、type R13。target 先检查 `+1C == 0x43686172`、`+18 != FFFFFFFF`，不满足时清 DIL。该 raw tag 不能单独代替完整领域类型合同。
- 首 `2C7D7E0(member,target,collector)` 的 AL 记作 Q，以 `MOVZX EDI,AL` 保存。Q为0且 collector为空时走失败；有 collector 时可继续收集后继结果。首调用未显式拿到 flags 指针，callee 内部作用仍 opaque。
- 实际读取 flags `+4` 非零才调用 `2C7E860(member,type,collector)`；该调用 AL=0 清 DIL。flags `+3` 非零才调用 `28CB780(member)`；其 AL非零清 DIL，并在有 collector 时进入输出构造链。分析相对实际读取值，不假定外部调用后所有输入不变。
- Gate直接读 `+2`，Base直接读 `+3/+4`；Base没有再向上述 helper 显式转发完整 flags。不能据此称 `+0/+1` 在全局未使用。type 本体在这里没有取 slot 字段，只继续传给 `2C7E860`，loader→field→原生 evaluator 名称仍未闭合。
- 正常返回都经 `2C7DBF4 MOVZX EAX,DIL`：Q只被保留或清0，EAX/RAX零扩展为0..255的原始字节；**不归一为布尔1**。这收紧了上一题首 helper 的返回宽度，不能外推上一题其他 opaque call 的 EAX高位。
- nullable输出不只是文本开关：非空时可在 target检查之前分配/构造 collector，显式写 `collector+D0` 为0/1，再经 `375DCA0` 合成输出。`[RBP+7F]` 是第五参数的本地 stack 存储，写入它不等同直接写 `*out`。该链的外部副作用未知。
- RF中还明确出现 `2C7DC3F`/`2C7DC4D` 的 RIP-relative全局指针写，以及 TLS/初始化守卫。这里没有另读 global值；只根据已采 instruction确认存在写。纯函数、frame不可变、输出不影响资格都未证明。自动字符串注释/反编译签名不能补出正式业务名。

Java消费继续使用来源绑定的观测与 UNKNOWN，不因 Q/flags存在就构造“已知 persistent=true”。`AL!=0` 与“返回值必为1”是不同合同。本题没有授 Game、ABI、native dossier、Shared 或 replay资格。

## 方法、成本和原始记录

Root另授新300s work+60s close卡，slot1/provider1 GiB/30s、decoder256 MiB/20s、Node heap128 MiB，最多4 provider是上限。原6 MiB净分为 Gate保留2 MiB/Base4 MiB，未删除文件/未产生物理释放。普通 research-plan check0，`--for-observation`2 的 offline-only无 live window拒绝原样保存。已安装官方service/OwnedProcess，独立TMP/export/stdout，没有重用旧180秒卡。

decoder459ms、job peak25325568 B；REA4911ms、Rizin job peak592150528 B，close17:45:35.562Z，service.close无错误。850 B为新语义范围，Rizin再次分析同850 B边界、实际列849 B；header/全 hash/PE加载 I/O另计。outer/joint peak、outer Job0未测，无速度或token收益结论。

`CASE-CLOSED01.json`2091 B / `1189197fc98b1182513928013b3890d88f0fba4cff75057c6bc1c61b6c0063a8`，17:45:58.324Z，T0→68.940s，在17:50:49.384562Z deadline内，4个实际 owned PID均缺席、0owned/MCP/business exec。原 `PAYLOAD_UNASSESSED` 保留，先关闭再独审。

M1独审 `INDEPENDENT-M1-BASE-REVIEW01.json`8020 B / `fb5f406652df7edd4696ab2e0a9e4c9ae8565ba0d9d980e183d7e6e2f228d7cb`，17:54:05.130Z；机械 `CROSSCHECK01.json`3362 B / `3d2d073457ebc032d205063dec1e0cd3e475a33eb53d1f1bba74d4da624d82ac`。富 `CASE-RECEIPT01.json`11073 B / `db1a3c247809f4195890bcafd9a371dddd241824e0ff14d92be2416a619d3edb` 在T0后909.895s封存，包含独审/其他岗复核/协调/记录；最初准备未完整计时，完整研究总耗时未测。一次 functions.store 对运行中 exec 的未定义退出码报错，随后只恢复原session84420，实际exit0/close后封最小回执，没有重跑provider。详见原件与 [sources.json](sources.json)。

下一真实类型边为 `2C7E860`，其 RF/loader绑定未知。仅列候选问题，不自动取样或扩展本case。
