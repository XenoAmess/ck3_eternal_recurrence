# 二进制观察：文化融合、动态礼仪与精确核心组合

状态：**本机离线静态研究；无游戏执行或功能实测**。

`machine_id: 4-8e1c2f1861`；初次二进制观察时间为 `2026-10-24T14:32:39.308399Z`，核心集合补充观察为 `2026-10-24T14:37:28.023485Z`。机器身份使用 `tools/ck3_live_run_id.py machine` 独立读回。用户已确认包含 Empire Faith Gate 的版本为原版版本，本研究按该基线取证。

本机文件：`C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101,040,248 B；SHA-256 **`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`**。PE ImageBase `0x140000000`，TimeDateStamp `1791204405`。launcher 版本为 1.20.0.4，Steam build 为 25734779；版本来源和文件摘要见[来源记录](evidence/source-observation.json)。

完整的小型研究证据在 [binary-observations.json](evidence/binary-observations.json)。以下地址均为这个 EXE 的 **RVA**；file offset 须按 PE section 映射，不能把这里的地址用于其他 build，也不构成注入或直接调用 ABI 的资格。

## GUI 不是名称占位：四条真实 callback 链

| 原生模型／方法 | callback 登记 RVA | thunk RVA | 实际方法 RVA |
| --- | --- | --- | --- |
| `HybridizationWindow.HybridizeCulture` | `0x233746` | `0x15330c0` | `0x1530620` |
| `RiteCreationWindow.CreateRite` | `0x22a166` | `0x14fb060` | `0x14f5130` |
| `RiteCreationWindow.SelectDoctrine` | `0x229ad3` | `0x14fadf0` | `0x14f46f0` |
| `RiteCreationWindow.EditRite` | `0x229d9c` | `0x14faed0` | `0x14f49c0` |

文化融合登记的最小片段：

```text
RVA 0x233746 / file 0x232b46
4c 8d 05 73 f9 2f 01 33 d2 48 8d 4d ef e8 18 23 30 01
lea r8, [RVA 0x15330c0]
...
call RVA 0x1535a70

RVA 0x15330c9
e8 52 d5 ff ff
call RVA 0x1530620
```

`SelectDoctrine` 的真实方法在索引检查后，把选中对象写入草案行：

```text
RVA 0x14f472a / file 0x14f3b2a
48 8b 42 28 48 89 41 28
mov rax, [rdx+0x28]
mov [rcx+0x28], rax
```

这证明选择能进入真实草案，以及文化融合、礼仪创建、礼仪编辑各有实际原生方法。不能据此推导任意 TenetType／DoctrineType 都能直接当作 `TenetItem`／`DoctrineItem` 传入，也不能证明原生礼仪草案已经支持第二来源。

**ACK 界限也有实码依据。** 例如文化融合 thunk 在 window 指针非空时调用方法，随后直接返回 `al=1`；它不在此处读回文化是否已创建、费用是否扣除。礼仪 callback 的返回也不能替代最终对象与保存结果。

## `create_dynamic_rite` 的真实 effect 登记

| 项目 | RVA／身份 |
| --- | --- |
| 精确 effect 名称 | `0x481fb98`，file `0x481e998` |
| 原生帮助文本 | `0x481fbb0`，file `0x481e9b0` |
| 登记引用 | `0x5bd181` |
| entry vtable | `0x48219a0`，RTTI `CEffectEntry<CCreateDynamicRiteEffect>` |
| 工厂 | `0x2c95380` |
| 真实 effect vtable | `0x48219d0`，RTTI `CCreateDynamicRiteEffect` |
| parser | `0x2c91b10` |

登记不仅有字符串引用，还安装真实 entry vtable 并进入共享 effect 注册 `0x3763c10`；工厂随后安装实际 effect 类型。完整帮助文本保存在 JSON，关键合同为：在 Character 的当前 Faith 内创建 Rite；继承其当前 Rite；显式覆盖先于名字与图标生成；支持多个 `core_tenet_override_entry` 和 `doctrine_override_entry`。

帮助直接给出 `core_tenet_override_entry = tenet:some_tenet` 与 `= scope:saved_tenet` 两类示例。parser 的两个数组分支分别在 `0x2c91b48`、`0x2c91b97` 追加 scope expression，再进入共享 scope parser `0x376c380`。所以显式覆盖不是仅接受散落的字面字符串；完整 token 归一化的每个分支没有在本轮全部逆向。

`target_divergence=0` 是默认且被忽略；只有主动指定分歧目标且显式覆盖不够时，才随机补齐。将该 effect 归类成“只能随机生成”与原生帮助及实际构造路径不符。

## 精确核心集合：追到新 Rite 字段写入

执行链已经闭合为：

```text
CCreateDynamicRiteEffect vtable +0xb0
  slot RVA 0x4821a80 / file 0x4820880
  -> Execute 0x2c91810
  -> 解析覆盖 scope 0x2c91c80
  -> 创建 manager 0x29c8770
  -> 共享组合函数 0x2be0200
  -> 新 Rite 的 tenet-state vector +0x788
```

slot 实际指针字节为 `10 18 c9 42 01 00 00 00`，即 ImageBase 加 `0x2c91810`。其余有限切片见 JSON 的 `bounded_core_override_followup`。

实际观察到的算法：

1. 执行前解析有效的目标 Tenet scope，受核心上限约束。
2. 组合函数先遍历并去重全部目标指针，形成共同的目标集合。
3. 仅当集合数量不足核心上限，才从排序后的旧核心补足；旧核心排序内部未继续追踪。
4. 原有条目若在目标集合中，设为状态 `4`；原状态为 `4` 而未选中的，保留但降为状态 `3`。
5. 新目标的剩余条目以状态 `4` 追加。
6. manager 把组合后的 16 B 状态记录复制到新 Rite 的实际字段。

核心判断函数 `0x25907c0` 比较状态字节是否等于 `4`：

```text
80 79 08 04 0f 94 c0 c3
cmp byte ptr [rcx+8], 4
sete al
ret
```

目标集合达到上限时，`0x2be058e` 跳过旧核心补足；`0x2be08ca` 处理原条目的 `4 → 3` 降级；`0x2be0940` 追加新核心。`0x29c8b18` 将最终记录复制到新 Rite 的 tenet vector。

随机补齐也核到实际分支：`0x2c920df` 读取目标分歧，`<=0` 时跳过随机补充分支。原版 defines 的当前核心上限为 `3`，但是本轮没有读取运行期全局初始化值。

**可提升的结论：** 在核心上限为 3、传入三个有效且不同的 Tenet scope、目标分歧为 0 等前提下，静态构造路径支持“最终核心恰为这三项”；后传入项不会因逐次替换而把先前所选覆盖掉。这已经追到新 Rite 的真实字段写入。

**仍未获得的结论：** 创建后的所有脚本钩子、知识与互斥规则、任意组合、保存／冷重载和玩家实际创建结果全部正确。旧核心降级后仍在集合，不能把“不是核心”说成“已从礼仪彻底删除”。

## 独立 Faith 与后续修改入口

| effect | 登记 RVA | 已核身份／语义边界 |
| --- | --- | --- |
| `detach_rite_to_new_faith` | `0x5bd391` | `CEffectEntry<CDetachRiteToNewFaith>`；原生帮助支持分离指定 Rite、创建 Faith、保存结果 scope。 |
| `set_parent_faith` | `0x5bd5a1` | `CEffectEntry<CSetParentFaithEffect>`；本轮未继续闭合任意跨 Religion 的合法性、清理与所有后态。 |
| `set_tenet_status` | `0x5cdba1` | `CEffectEntry<CSetFaithTenetStatusEffect>`；不能把 Faith 层的 setter 无条件当作只改某一个 Rite。 |

补充读取了 `change_rite_doctrine` 和 `set_rite_name` 的精确名称及相邻原生帮助：前者对同组教义覆盖；后者支持名称、描述、形容词和信徒单复数名称。该补充只记录名称／帮助文本，不将其升级为本轮已闭合的执行链。

## 否定查询只说明查了什么

本轮对这个 EXE 的精确 NUL 终止 ASCII 名称扫描，没有命中 `create_dynamic_religion`、`create_dynamic_faith`、`create_religion`、`set_religion`、`parent_rites`、`parent_rite`、`GetParentRites`、`GetParentRite`。此结果不证明所有替代名称、内部路径或其他版本都不存在。

因此报告采用“当前未找到动态 Religion／原生双父 Rite 的公开合同证据”，没有把没有命中名称写成绝对不可能。全部切片只用于版本绑定的研究，不需要把 EXE、完整反汇编或游戏资产复制进仓库。
