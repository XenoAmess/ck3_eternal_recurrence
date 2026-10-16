# CK3 1.20.0.4 补员 OnClick：来源角色、开关读口与命令载荷

实际 `1303D40` 包装函数的唯一业务 callee `12FF8D0` 已完整读取。它从原生接收者 `+218` 解析来源 Character，读取 `Character+1C0` military 的 `+4A9`，构造相反的布尔值并提交命令；本体没有直接写回 4A9。命令执行器尚未读取，未执行点击。

机器 `desktop-3fevhd2-1c74096080`，精确 1.20.0.4 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。观察时间、完整 346B hex、90 条指令、12 个分支与 4 个 call 见[来源合同](evidence/military-refill-toggle-command-12ff8d0-12004.json)。`.pdata` 为唯一无 CHAININFO 的 `[12FF8D0,12FFA2A)`；新读取 metadata=80B/code=346B/9次。原字节和 I/O 账本先 fsync，随后解码；元数据在 body 阶段从账本复用，没有重读。

上游[实际控件与包装函数](military-refill-finaltarget-1303d40-12004.md)来自 R0180 打开后的 Military 树。这里保持原 RCX 来源，不把 callback+F0、当前玩家或 persistent Regi 的来源字段直接当作 GUI 接收者。

| 源码边 | 实际规则 |
| --- | --- |
| 接收者 `+218` | 完整 Character ID，取低24位查 registry global `5C67568`，count `+2C` / table `+20`，槽宽16、对象指针+8 |
| 对象资格 | 对象 `+18` 必须等于完整 ID；失配、越界、空槽或空 registry 走 global `5C67570` fallback。本函数没有独立检查 Character magic |
| 状态读取 | 对象 `+1C0` military 非空则读 byte `+4A9`；空 military 在原生函数中按0处理 |
| desired | `sete r11b`：旧字节为0得到1，任意非零字节（包括2）得到0 |
| 命令 owner | 重新解析接收者 `+218`，将选中对象的完整 ID `+18` 写 stack `+4C` |
| 命令 desired | 写 stack `+50`，值严格0或1 |

未来只读状态接口应保留“实际 owner 完整 ID / 是否 fallback / military 是否可读 / raw4A9 / enabled”。读取不可用不应被严格消费者压成 false。typed toggle 的准入应拒绝 fallback，并验证 GUI 实际 owner 与独立后验 Character 的完整代际一致；不能套玩家身份替代来源角色。

原生函数将 `476A520` 和 `476A4F0` 的静态地址放入 stack descriptor，在 `12FF9C0` 调用 global `476A560` 中的 factory 指针。随后 `12FF9F3` 调用 `37F06D0`，RCX 为 `&module[5CC1240]`、RDX 为 unique command holder、R8D=14（0xE）。这些是实际指令解出的静态地址；本包没有读取对应 data、factory、通用 queue 或命令执行器，也没有给命令猜业务类名。

这解释了为什么 `1303D40` 的 AL=1 不能证明开关已变：它忽略此 callee 的结果；callee 只构造并提交带 owner+desired 的命令。即使未来原生 dispatch 返回 ACK，仍需独立读取同来源 Character 的 raw4A9，验证预期值实际出现，不能立即或重复点击一个结果未知的动作。

下一最小源码入口是本体精确使用的 global `476A560` 的8B实际 factory 指针，并在独立有限计划中识别 command descriptor `476A4F0` 的执行入口。不能把通用 `37F06D0` 直接命名为补员 setter。本包严格没有跟读 callee。

原生布尔读取 `4A9!=0`、desired 取反，与 Regi `+138==1` 的补员拒绝门及费用 `+138!=0` 的门各自独立，不合并为一个谓词。本记录不授点击、状态转移、actual ADD 或完整 R06 资格。

勘误：上文“factory / command / queue”的角色名称来自对象布局与调用形态的结构推断。已直接证明的是 owner+desired 的字节载荷、间接调用 global476A560，以及向37F06D0传递 holder 和常量0xE。两个 callee 本体均未读，不能据此断言它一定异步排队、也不能排除同步执行。执行时机与实际4A9写入仍未知；独立后验要求不变。
