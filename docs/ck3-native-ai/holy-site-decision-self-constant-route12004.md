# 圣地快捷决议的常量与动态参数

本节补充[四种圣地决议接口](holy-site-management-native12004.md)的 R6 实际开窗故障。`machine_id: 4-8e1c2f1861`；CK3 `1.20.0.4`，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。实机来源为 `4-8e1c2f1861--faith-and-power--R0006`，PID `21920`、creation `1792244644.324554`。物理指针、class ID 的观测值和这些身份只属于该次进程，不能成为其他机器的协议常量。

## 实际故障与原因

`2026-10-17T14:03:30.826879Z` 的 `ck3_open_holy_site_decision_v1(action='promote', holy_site_id=32)` 返回 `entry_parameter_self_declaration_unavailable`；实际 `native_dispatch_attempted=false`，尚未调用原版开窗。随后详情不可用不能解释为原版 `CanConfirm=false`，R6 没有发送晋升、降级或放弃 Confirm。

Root 在相同 PID 内经 MCP 重开 HolySite32，保存新鲜 GUI 原件，随后于 `2026-10-17T14:31:51.974852Z` 完成一次只读参数采样。两个实际可见、启用且符合完整原版回调签名的按钮均呈现下列结构：

| 字段 | 两个按钮的实际值 |
|---|---|
| 动态描述符数量 `block+0` / `+0xC` | 1 |
| 常量行数量 `block+0x80` / `+0x8C` | 1 |
| 最终调用首输出槽 `block+0x30` | 0 |
| 常量内容、输出槽 | CString `decision_detail`，size/capacity=15，slot0 |
| 动态 Self | ordinal0，chain空，kind2，原 getter `CAB1C0`，output slot1 |
| 动态 receiver indices | `[0, -1]` |
| 声明与当前 runtime class ID | 均168；声明 flag1 |
| Self 原始 return type 字段 | 0，不重新命名其含义 |

旧 reader 把“输出第二槽”混同为“动态描述符的第二项”，强制动态数量2并读取 `indices[1]`。实际动态数量1，且 `indices[1]` 为−1；因此在聚合声明守卫处提前拒绝。声明行本身的8字节步长、`+0x98` 指针与 `+0xA4` count 均与原版一致，无须修改宽度。

## 原版来源与最小修正

原版 `3E4BC50` 先把 `block+0x80` 的常量 Any 行复制到指定输出槽，再求值 `block+0` 的动态描述符。常量行 stride `0x30`、输出槽 DWORD `+0x28`；动态描述符 stride `0x40`、输出槽 `+0x38`。`3AC38C0` 为两类输出分配总槽数，动态 receiver index 仍按动态描述符的 ordinal 取值。`3E4C090` 把 `block+0x30` 交给最终调用者。

原 `A79540` 从该首输出槽提取视图名 CString，并把紧邻的下一槽 Any 交给 view dispatcher。因此有限 reader 修正为：

- 只接收已闭合的常量1＋动态1形状，并要求首输出槽0。
- 常量须唯一写slot0；类型为原 CString32 singleton `542FD20`，核其 VTable/COL/type descriptor 与 `876E00` accessor，再借读完整 `decision_detail\0`。SSO 与已闭合的 heap CString 均按原布局读取，不构造、求值或析构游戏对象。
- 唯一动态描述符须为已闭合 Self getter、空chain、kind2、当前实际 runtime class、output slot1；用其 ordinal0 读取自己的 `indices[0]` 与8字节声明。
- 继续验证同源 owner/context、原生 typed cache、固定决议 key、完整 selected_item/site generation，保持双读及原 dispatcher 守卫。

未验证视图名的旧“动态2、常量0”合成形状明确返回 unknown；不能为了保留合成正例而授权另一视图。仍只支持固定四动作，不增加任意 key、指针、child path 或 bypass 参数。class ID168只是本次样本值，生产 reader 每次读取实际 runtime class，未把168硬编码为通用条件。

## 验证边界

修正只涉及 `holy_site_decision_entry_parameters12004.hpp/.cpp` 与对应原生测试，无 MCP、wire、CMake 或部署开关变化。新夹具正例复现实际数量、输出槽、`indices=[0,-1]`、type/flag与raw return type0，并保留同签名动作区分、完整ID、缓存与双读检查；另有错误视图名、Any类型、输出槽及未闭形状的定向拒绝断言。

截至 a38 源码冻结，这些修改尚未实际编译、运行新夹具或在新进程开窗。旧17份详情/冷却回包的生产 MCP 资格属于其原来范围，不证明这次 parser 修正已经 live 成功。下一步只构建 bridge 与受影响 entry-parameter fixture；实际原版开窗、详情合法性和业务后验须由后续受管场次独立读取。

采样仅 `ReadProcessMemory`：2个按钮、2211次读取、24,200字节、进程写入0、原版函数调用0。第一次 a35 采样在全局树 traversal guard 失败，没有参数输出；成功 a37 使用实际 mailbox jomini→gfx→typed handler→registered HolySite window→GUI root，只遍历该窗口子树，重复节点正常跳过。child path 仅作为诊断位置，未用于选择动作。

## 原件

以下路径相对外置根 `C:/workspace/ck3-faith-and-power-20261017/episode01/`；原件含机器身份与实际 UTC，不复制大份 raw 到仓库。

| 原件 | SHA-256 |
|---|---|
| `native-candidate/r6-self-declarations-actual-a37.json` | `70fa4e4c628d17478deb6c90856ea318d2e1438b36bcb5446634a61dcd9eef88` |
| `live/4-8e1c2f1861--faith-and-power--R0006/root-native-receipts/r6-fresh-window32-sample-a37.json` | `3132762dd16d2102b12a87039a601eee9f97144874505d3a0044f6970961ee88` |
| `native-candidate/management-self-source/self-declaration-r6-source.json` | `1cc684a290333d084ca4e4c5be64d32fd8af61fd873c078900b9bce66366070e` |
| `native-candidate/management-self-source/constant-decision-detail-route-source.json` | `b22a6330fb30b9093e38c04bd515d96940421dbc86ebb0a64ce1770599c41e92` |
| `native-candidate/management-self-fix-a38-freeze.json` | `b5870a9d3ad98988e258eeaf05383574227489b03a42df09e6413e5aeacfd673` |

新采样前已执行 `native_research_plan.py check --for-observation` 并生成图；`research-plan-r6-self-a37-check.json` 记录 plan-consistent。这只证明计划结构与引用文件一致，不授予游戏操作权限，也不证明语义或实机业务成功。
