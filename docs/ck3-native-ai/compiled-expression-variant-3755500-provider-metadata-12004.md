# 编译表达式正 count provider 原始元数据

`ProjectCompiledExpressionVariant3755500ProviderMetadata12004` 投影既有
`ReadCompiledExpressionVariant3755500Readonly12004` 的 owned witness。
只有已复制的 list+C 有符号 count 大于零时才返回 optional record；缺少 count、
零 count 和负 count 不要求此 provider 元数据。正 count 的缺失字段保持 nullable，
并保留具体 unavailable reason。

来源是固定 CK3 1.20.0.4 的实际 `3755500` 完整 842B，源码 SHA-256
`76665f652651c1163f17a684ff8ada07d2b037fa3ef25e1c88cdcbce91089115`。
实际父调用 `A0F2D6` 传 expression+8、原始 variant16 输出、复制的父 pack、
原始 R9 named tuple，以及 stack5 BYTE0/stack6 DWORD0。

正 count 的第一个 16B row 提供 receiver；`3755600` 调用 receiver vtable+30
类型掩码方法。源码随后检查返回的掩码与当前 root WORD，条件满足时才在
`3755638/375563B` 重读 receiver/vptr，并于 `3755646` 调用 vtable+20。
投影保留已有 receiver/vptr、+30 raw VA 和 +20 raw VA，既有复制未见证这些
目标的前后相等，也未见证类型掩码返回、后续实际 dispatch target 或 provider 返回值。
因此 record 的实际调用路径、实际调用目标与返回 variant 全部保持 nullable unknown。

`37555D5..37555E7` 使用 inline list+70 的首 QWORD：非零选择 inline32，
零选择原始 R9 tuple32。这份所选 tuple 被复制到数值 producer context；
选择 R9 时它是数值输入。record 保留 inline 首 QWORD、原始 R9、所选 identity
和既有 tuple32 前后字节，不制造物理 stack context 地址。

目标 RVA 字段只是 raw VA 减 module base、可容纳于 uint32 的候选差值。
它不证明地址落在固定 image 内，不证明该地址上的实际函数体，也不触发任何源码采集。
完整 revision 只原样携带，不成为数值 prerequisite；角色、日期、时钟和 prisoner
descriptor 合同不进入此入口。

owner40 在实际 compiled-positive 数值路径消费 optional record。投影不增加
guarded read、不再次调用既有 reader、不调用任何 provider，record 永不提供数值结果；
正 count 返回值未知时父级继续保持 unknown，不能转换为 tag0 或选择 fallback98。
本工作包未新增或运行 QA、构建、native entry 或游戏验收。旧 64b/64d 与已验静态报价
夹具保持原字节；外置 `SOURCE-INPUT-FREEZE.json`、`SOURCE-CONTRACT.json` 和
`DELIVERY.json` 固定来源、候选与实际 consumer 交接。
