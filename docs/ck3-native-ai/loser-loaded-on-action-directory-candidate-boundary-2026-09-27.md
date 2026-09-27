# 败方 loaded child：原版 on-action 目录候选已收窄，实例行级来源仍未绑定

本页接续[parser 父链审计](loser-loaded-parser-source-attribution-boundary-2026-09-27.md)。结论分两层：**exact-build 静态 loader 的直接输入目录确定为 `common/on_action`；在本机原版该目录的 165 个 `.txt` 文件里，败方根名称和 `combat = { warscore_value >= 15 }` 都只出现在 `combat_on_actions.txt` 的第 519／563 行。** 但尚未取得正在运行的 VFS bytes、parser 子对象父链或 loaded trigger 指针，因此不能写成“实际 loaded child 已唯一来自第 563 行”。没有启动或附加 CK3，没有触碰 080 collector。

只读的[目录与候选 verifier](../../ck3_autonomous_player/native_bridge/research/audit_loser_loader_directory_static.py)核对：EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；原版 `combat_on_actions.txt` SHA-256 `B35D696F472E801BB332D7204AA46008349E8AFBFDB38985C781EB099BBFB233`；原版 `combat_events.txt` SHA-256 `CF4E7F43786477DF43319638138232086CFD477FEE0F2951B34DD41BE265CADD`。165 个 on-action `.txt` 按仓库相对路径排序，将每个 `path UTF-8 + NUL + raw-file-SHA256` 串接后求 SHA-256，得到目录指纹 `7A94B27129485C068333303CFF0872C23788F0B6A6E0B7006A4ACF19888C3ED7`；verifier 固定这个指纹，不能只靠两份单文件哈希推断其余 164 个文件未变。

| exact EXE 位置 | 只读字节及传递 | 可证事实 |
| --- | --- | --- |
| `0x2506B7C → 0x4080A4C`，`0x2506B88` | `.txt`，长度 `4` | loader 枚举参数的扩展名。 |
| `0x2506B95 → 0x4081118`，`0x2506BA0` | `common/on_action`，长度 `16` | loader 枚举参数的目录。 |
| `0x2506BC5` | 两个参数和输出缓冲区传给 `0x3B55190` | 该调用返回的目录项供下段循环使用；其运行时 VFS 内容未被静态取得。 |
| `0x2506C2B → 0x4084340`，`0x2506C3C–0x2506C56` | `/` 与当前目录项拼接 | 每次循环构造 path；不是 EXE 预存固定文件名。 |
| `0x2506C99–0x2506CA5` | path view 与同一数据库主实例传给 `0x33F75C0` | 接回此前已证的根 factory／parser 链。 |

源文件等价性因此可以更精确地区分。[原版 `combat_on_actions.txt:519–563`](loser-effect-root-gate-and-child-dispatch-static-2026-09-27.md) 是**这个 on-action loader 目录中的唯一同文字直接源候选**；`events/war_events/combat_events.txt:2173` 的 `combat_event.3000` 在 `trigger` 内也有第 2238 行同文字比较，但它**不属于该 loader 的直接目录输入**。它仍是独立事件 parser 可能加载的同型 `CCombatWarscoreTrigger` 候选：若只在求值期看见类型、`>=` 与 `1,500,000` raw，仍无法把该指针归给败方 on-action。实际 VFS 若叠加 mod 文件、覆盖/`replace_path` 或其他 on-action 文件，当前磁盘指纹也不能代表实际读入 bytes。

目前未观察到的关键边是：序号 76 的实际根 `R13` 接收哪份 VFS 内容；第 563 行的 `if.limit.combat` 在 `0x33F3660` callback 中编译为哪个 child/trigger 指针；这个指针是否沿根 `+0x338` 门、`+0x2B0/+0x2F8` 两数组或 `+0x348` 递归进入终局执行；事件 `combat_event.3000.trigger` 的同文实例是否同时存在。即使原版目录只有一个文字命中，解析器仍可能复制或展开子节点，不能把“唯一文字”冒充“唯一 loaded 实例”。

下一次最小被动读口先在加载期记录 `0x2506CA5` 的逻辑 path view、实际 VFS 解析来源和**同一次打开**的文件 bytes/SHA；只处理 `on_combat_end_loser` 名称序号 76 与同一 `COnActionDataBase` 的 `R13` 根。随后在该根的 `0x33F3660` callback／`0x334B490` trigger parser 记录当前 parser 节点来源、父指针/字段槽及 trigger 指针，并与另一路 `combat_event.3000` parser 身份区分。终局时用 `0x230B0EE` 根指针核对对象延续，再被动遍历执行父链。VFS bytes、父子指针、复制映射或同线程身份任一缺失，就保持“候选”；只有唯一闭合后才按[ABI 门](loser-warscore-trigger-passive-probe-abi-preflight-2026-09-27.md)读同一实例的操作码与 RHS。探针不得调用 parser、evaluator 或 effect。Steam 离线画面新鲜度门当前 RED，故本页没有新实机 attempt。

离线复核命令如下，使用有 `pefile` 的已验证解释器，仅读取 exact EXE 与原版 game 目录：

```text
<verified-python> ck3_autonomous_player/native_bridge/research/audit_loser_loader_directory_static.py --exe <exact-1.19.0.6-ck3.exe> --game-root <exact-1.19.0.6-game-directory>
```

其成功输出仍明确为 `actual_vfs_path_and_bytes_verified=false`、`loaded_child_to_source_line_563_unique=false`。
