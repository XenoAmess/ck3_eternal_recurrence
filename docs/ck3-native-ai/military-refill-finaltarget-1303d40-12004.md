# CK3 1.20.0.4 补员开关的实际 final target：1303D40

R0180 的可见补员外层控件实际指向 `1303D40`。其完整 28 字节只做接收者非空检查并调用 `12FF8D0`；真正开关 setter 尚未跟读，未执行点击。

机器 `desktop-3fevhd2-1c74096080`；观察与原件 SHA 见[字节、分支与实际绑定记录](evidence/military-refill-finaltarget-1303d40-12004.json)。精确游戏为 1.20.0.4、EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，复用已验完整身份，没有重哈希整 EXE。

原版 `window_military.gui` SHA `4f5523d249c2e0a4d3c328d789ca375f154c2e102544782480936b4206c57eac` 的第 488/898 行，均绑定 `MilitaryView.OnMilitaryReinforcementClick`，checked 为 `MilitaryView.IsMilitaryReinforcementsEnabled`。Root R0180 打开后的 023 响应直接 `/body` 是业务 payload；SDK 镜像不重复计数。树有 595 个控件、root_available=true、truncated=false。

| 实际 outer child_path | 有名祖先 | 可见/启用 | 实际表达式 |
| --- | --- | --- | --- |
| `0/0/0/2/3/0/0/0` | `tab_your_armies` / `footer` | true / true | chain=0, kind=3, final=`1303D40` |
| `0/0/0/3/5/0/0/0` | `imperial_armies_ra_uses_this` / `footer` | false / true | chain=0, kind=3, final=`1303D40` |

两者 slot2=`3AA30E0`、object+8=`3A9F960`、final userdata present=true、receiver_type_id=635、flag=0。内层 `button_checkbox` 仍是展示子控件，业务绑定在外层。类型号 635 没有在本次研究中映射为可直接调用的 C++ 类，也没有把 callback+F0 当作 Character。

唯一、无 CHAININFO 的 `.pdata` entry 是 `[1303D40,1303D5C)`，全量 28 字节、10 条指令；原始字节与读取账本先 fsync，随后解码。新增读取为 metadata=224B、code=28B、21 次；body 阶段复用 ledger 内已有 metadata，不重复读取 EXE 元数据。

| 分支 | 实际行为 | 意义 |
| --- | --- | --- |
| RCX=0 | 跳至 `1303D55`，AL=0 后返回 | 没有调用业务函数 |
| RCX!=0 | `1303D49: call 12FF8D0`，再写 AL=1 | 原 RCX 接收者传递不变；忽略 callee 返回状态 |

`AL=1` 不能证明补员已切换；本体没有 4A9 或其他业务 flag 写入。下一源码入口唯一为这条实际 call 的 `12FF8D0`，本包严格未跟读。未来执行仍应沿有来源约束的原生 GUI dispatch，并从现有 `refill_permission_switch_v1` 独立读取同一完整代际来源 Character 的 `+1C0` military → `+4A9`；不能把 GUI ACK、玩家当前身份或 raw byte 写入当作开关动作与后验。

本记录没有授予点击、setter、actual ADD、自然父调用或完整 R06 业务资格。

后续实际业务 callee 的完整来源角色、4A9 读口与命令载荷见 [12FF8D0 专题](military-refill-toggle-command-12ff8d0-12004.md)。
