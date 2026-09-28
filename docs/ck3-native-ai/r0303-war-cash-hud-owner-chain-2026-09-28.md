# R0303 战时现金：顶栏对象静态持有链

状态：**精确 EXE 的静态持有边已证；当前暂停帧的 live 实例、缓存自然刷新和现金扣款账期未证，正式战争现金仍不可填。**本轮只读取 CK3 1.19.0.6 `ck3.exe`，SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；未附着或启动游戏，未读取游戏内存。可复核入口是 [`verify_war_cash_hud_owner_chain.py`](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_hud_owner_chain.py)；普通和 `-O` 运行均给 `static_constructor_and_holder_edges_proven=true`、`war_cash_formal_eligible=false`。有界反汇编定位工具为 [`inspect_war_cash_hud_ctor_owner.py`](../../ck3_autonomous_player/native_bridge/research/inspect_war_cash_hud_ctor_owner.py)，默认仅扫描 RVA `0x900000..0xF00000` 的直接 `CALL` 候选；RTTI/指令结论由前述固定锚点校验器给出。

## 精确静态边

| 边 | 可复核证据 |
| --- | --- |
| 全局槽至 idler 候选 | `0xAA43C8` 从模块基址加 `0x570F7B8` 读取指针 `G`；`0xAA43D8` 读取 `*(G+0x10)`，`0xAA43DC/0xAA43E3` 将 `CIngameInterfaceIdlerGfx` / `CIdlerGfxBase` 两个 RTTI descriptor 传给 `0x143E631F4` 动态转换；成功后 `0xAA43FE` 读取转换对象 `+0x88`。`G` 的类型、生命周期、当前暂停帧唯一性还未从静态代码证明。 |
| `CIngameInterfaceIdlerGfx+0x88` 至 handler | idler 主 COL `0x45F5BC0`、虚表 `0x40B1D30`、type descriptor `0x501EF50`；虚表第二槽 `0xAA4350` 分配 `0x16CE8`，于 `0xAA4381` 调 handler 构造 `0xA71E00`，于 `0xAA43A0` 保存返回对象到 idler `+0x88`，并在此前释放旧指针。 |
| `CIngameInterfaceHandler+0x470` 至顶栏 | handler 主 COL `0x45F3F28`、虚表 `0x40AF630`、type descriptor `0x5191068`；次 COL `0x45F3F00`、虚表 `0x40AF6A8` 在对象 `+0x58`。主虚表第二槽 `0xA734B0` 入口把 `RCX` 存为 `R14`，于 `0xA73800` 调 `CHudTopBar` 构造 `0xD465A0`，于 `0xA7380D` 存返回对象到 handler `+0x470`，随后释放旧指针。 |
| 顶栏返回校验 | handler 初始化把 `RDX=*(handler+0x40)`、`R8=handler` 传入顶栏构造；该构造分别保存于顶栏 `+0xC8/+0xD0`。顶栏主/次虚表 RVA `0x40E6F68/0x40E7038`，次表在对象 `+0x10`；对象大小候选 `0xFA0`，见[原有类型指纹](r0303-war-cash-passive-instance-gate-2026-09-28.md)。 |

## 下一最小纯读 live 门

只在有独占 CK3 实机的受管暂停帧，使用精确 EXE/DLL/injector 组合，从模块基址 `B` 读取有限个地址，不作堆扫描、不调用 getter、不让游戏推进日期：

```text
G = read_ptr(B + 0x570F7B8)
I = read_ptr(G + 0x10)
H = read_ptr(I + 0x88)
T = read_ptr(H + 0x470)
```

逐个指针先检查规范地址、对齐、可读页和固定读取上限；空值、读失败、生命周期切换一律可恢复拒绝。检查 `*(I+0)==B+0x40B1D30`，`*(H+0)==B+0x40AF630`，`*(H+0x58)==B+0x40AF6A8`，`*(T+0)==B+0x40E6F68`，`*(T+0x10)==B+0x40E7038`。再检查 `*(T+0xC8)==*(H+0x40)`、`*(T+0xD0)==H` 和 holder 指针回读一致。上述类型门故意只接受无指针偏移的 idler 主对象；若 RTTI 转换需要调整基址，拒绝并补证，不能猜测偏移。顶栏行解码仍走既有[被动布局诊断](../../ck3_autonomous_player/native_bridge/research/war_cash_topbar_passive_layout.py)，不能据此发现金值。

同一探针需在读取前后各取原生 `paused`、played CharacterID、WarID、date、episode、snapshot/public/native revision、treasury 及顶栏 `+0xF88` 渲染帧；两次快照及全部指针相同才允许将结果标为**稳定的候选缓存**。还需独立证明本次自然 GUI 渲染确已把该玩家该原生修订的费用写入这些行，并与可观察费用分项对照。渲染帧计数不是 native revision。`CIngameInterfaceHandler+0x40` 的上下文类型仍待核；本轮仅能把它用于构造器回指一致性。

即使顶栏月费率获得同帧证明，它也不是实际金币扣款。`committed_war_spend_raw`、即时费用、Robert 的最低战争储备及有限期 `future_war_cost_upper_raw` 仍需实际余额写入/扣款节奏、正式动作报价与有来源的策略上界。缺任一边时保持五项未证读数为 `null`、`formal_eligible=false`，不得把普通 GUI 显示值或一日月费率冒充现金占款。
