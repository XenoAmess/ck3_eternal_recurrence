# 二进制观察：礼仪草案、宗族 effect 与罪行理由

状态：**离线静态研究**。`machine_id: desktop-3fevhd2-1c74096080`；观察时间 `2026-10-24T06:50:05Z`。未加载游戏进程、注入、执行 EXE 内函数或生成完整反汇编。

来源为 `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101,040,248 B，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。ImageBase `0x140000000`，PE TimeDateStamp `1791204405`。文件资源的 FileVersion／ProductVersion 都是 `1.0`；实际 `1.20.0.4 (Crozier)` 来自主执行者另读的 launcher JSON，Steam build `25734779` 来自当前 appmanifest。来源清单和有限字节读回见 [source-observation.json](evidence/source-observation.json) 与 [binary-slices.json](evidence/binary-slices.json)。

下表全部地址均为该 EXE 的 **RVA**，不是其他 build 的固定地址，也不是运行时绝对地址。文件偏移需依 PE section 映射换算，不能假设整文件有同一个偏移差。

## GUI 实际登记与草案写入

| 名称 | 字符串 file offset | 字符串 RVA | 本轮实际闭合 |
| --- | --- | --- | --- |
| `RiteCreationWindow` | `0x4564e28` | `0x4566028` | 原生窗口模型名称 |
| `GetCategoryHelper` | `0x4564d18` | `0x4565f18` | 登记 thunk `0x14fb940` → 方法 `0x14f4320` |
| `SelectDoctrine` | `0x4564dd8` | `0x4565fd8` | 登记 thunk `0x14fadf0` → 方法 `0x14f46f0`，实际写草案行 |
| `CreateRite` | `0x4564ec8` | `0x45660c8` | 登记 thunk `0x14fb060` → 方法 `0x14f5130`，进入原生确认 command 管道 |
| `EditRite` | `0x4564ea8` | `0x45660a8` | 名称和相应 command 类型存在；本次未追闭完整 thunk。调用入口另有原版 GUI 依据。 |

`SelectDoctrine` 在 `0x229a49` 复制名称，`0x229ad3` 登记 callback。小段为：

```text
RVA 0x229ad3 / file 0x228ed3
4c 8d 05 16 13 2d 01 33 d2 48 8d 4d ef e8 7b 91 2d 01
lea r8, [RVA 0x14fadf0]
...
call RVA 0x1502c60

RVA 0x14fae56 / file 0x14fa256
48 8b 10 48 8b cf e8 8f 98 ff ff
mov rdx, [rax]
mov rcx, rdi
call RVA 0x14f46f0

RVA 0x14f472a / file 0x14f3b2a
48 8b 42 28 48 89 41 28
mov rax, [rdx+0x28]
mov [rcx+0x28], rax
```

最后一段在选定行的索引检查后写入选中 doctrine，随后更新派生集合。这支持复用原生选择器，而非用一个只改 UI 变量的按钮冒充草案选择。

`CreateRite` 名称在 `0x22a0e9` 复制，callback 在 `0x22a166` 登记：

```text
RVA 0x22a166 / file 0x229566
4c 8d 05 f3 0e 2d 01 33 d2 48 8d 4d ef e8 e8 8a 2d 01
lea r8, [RVA 0x14fb060]
...
call RVA 0x1502c60

RVA 0x14fb060 / file 0x14fa460
48 83 ec 28 48 85 c9 74 0c e8 c2 a0 ff ff b0 01
48 83 c4 28 c3 32 c0 48 83 c4 28 c3
```

thunk 调用 `0x14f5130`。静态链说明真实提交入口存在，不说明本轮已创建礼仪、已付款或创建钩子已触发。

**未闭合：** 本次初始化链看到 doctrine 行来自草案集合（窗口 `+0xb28`、行列表 `+0x790`），没有证明“注册一个新组后，所有没有该组的旧礼仪都会自动补齐”，也没有证明“index 最小的候选必然成为默认”。报告将其保留为后续原型问题。

## 动态宗族与 House effect

| Effect | 字符串 file / RVA | 实际登记／工厂 |
| --- | --- | --- |
| `create_dynasty` | `0x4875a98` / `0x4876c98` | 登记 `0x5dd7d0`，entry vtable `0x4878d58`；工厂 `0x2d5d900` |
| `set_house` | `0x46ca490` / `0x46cb690` | 登记 `0x5dd1a0`，entry vtable `0x4878c80`；工厂 `0x2d5d4c0` |

`create_dynasty` entry 的 RTTI COL 为 `0x4ede188`，精确类名 `.?AV?$CEffectEntry@VCCreateDynastyEffect@@@@`。工厂分配 `0x1f0` 字节对象并安装 `CCreateDynastyEffect` vtable `0x487aa38`，后者 COL `0x4ede908`，精确类名 `.?AVCCreateDynastyEffect@@`。`set_house` 的 COL `0x4ede020` 对应 `.?AV?$CEffectEntry@VCSetDynastyHouse@@@@`。

```text
RVA 0x5dd855 / file 0x5dcc55
48 8d 0d fc b4 29 04 48 89 08 48 8b cb 89 78 10
48 8b 5c 24 48 48 83 c4 30 5f e9 9c 63 18 03
```

此处安装 entry vtable 并进入共享 effect 注册函数 `0x3763c10`。只证明脚本工厂存在，不提供任意 ABI 调用资格。本轮精确 NUL 终止名称扫描未发现 `set_dynasty`，因此不在方案中编造它。

另观察到原生 on_action 名称：`on_rite_created` RVA `0x473faa0`，`on_rite_edited` `0x473f8c0`，`on_rite_updated` `0x473f8d0`，`on_rite_change` `0x473f898`。它们的覆盖范围、scope 和例外以本轮实际脚本注释为准，不从名称推导全部生命周期已覆盖。

## 监禁、处决理由的真实原生解析

| 字段 | 字符串 file / RVA | token 表 RVA | token ID |
| --- | --- | --- | --- |
| `imprisonment_reason` | `0x470ce20` / `0x470e020` | `0x46ec278` | `0x2c40` |
| `execute_reason` | `0x470cd58` / `0x470df58` | `0x46ec298` | `0x2c42` |

`COpinionFlagMask` 的精确 RTTI 对应 vtable `0x44deef0`；`slot+0x20` 在 `0x44def10`，其指针指向 parser `0x260dbf0`。parser 使用 token 跳表分派：

```text
RVA 0x260dbfa
41 81 c0 c1 d3 ff ff
add r8d, -0x2c3f

RVA 0x260df6c，8 个 uint32 跳表
260dc29 260dcae 260dd36 260ddbf
260de48 260df5a 260df5a 260ded1
```

`0x2c40` 进入 `0x260dcae`，把布尔值写入 `[mask+8]` 的 bit 1；`0x2c42` 进入 `0x260ddbf`，写 bit 3。处决分支的小段：

```text
RVA 0x260de23
0f b6 c8 ba f7 ff 00 00 0f b7 47 08 66 23 c2
66 c1 e1 03 66 0b c8 66 89 4f 08
```

另外找到 flags 持久化 parser `0x2594970`，相同 token 分别进入 `0x2594bf5`、`0x2594a79` 写 bit 1、bit 3；serializer `0x2594810` 按标志输出对应 token。这些是实际 token 绑定、parser 和序列化代码，强于孤立字符串命中。

查询触发器也有实际登记：`has_imprisonment_reason` 名称 RVA `0x47f9388`，登记 LEA `0x5aa721`，在 `0x5aa789` 安装 entry vtable `0x47f9d68`；`has_execute_reason` 名称 `0x47f92b0`，登记 LEA `0x5aa861`，在 `0x5aa8c9` 安装 `0x47f9d28`。二者进入共享注册管道 `0x372bd10`。

**本轮没有闭合的链：** 新增特质的 `triggered_opinion` 过滤结果，如何在本产品全部状态切换中进入实际监禁／处决合法性、暴政与原生赦免／消费记录。原版弑亲者脚本给出强参照，不能替代新增产品的实际验证。所有地址仅作研究来源，不是修改或绕过原生资格的实现建议。
