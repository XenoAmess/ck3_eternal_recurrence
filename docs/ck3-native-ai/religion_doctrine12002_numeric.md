# CK3 1.20.0.2 当前宗教 special_parameters 数值缓存

状态：原生字段与读取树 static-confirmed，实际只读 provider / serializer static-ready；没有 CK3 进程访问或 live 证据。

**1.20.0.2 的普通 `parameters` 与 `personal_tenet_parameters` 是布尔 token 集合，不是通用数值 map。** 冻结 stock 的 199 个普通参数块、95 个个人参数块没有数值赋值。旧 `STokenParameter` 数字反射 getter `0x22C81A0` 不能冒充本版本当前 effective 数值查询。`Faith.HasParameterByKey` 同样只转到 main Rite `+0x7B8` 布尔 membership。数值 authoring 位于独立 `special_parameters`。

冻结游戏 CK3 1.20.0.2 Crozier / Steam 25588574，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`，大小 101039736 bytes。本包不涉及战争、holy order、宗教动作或我方策略；只读取同一 paused owner frame 的实际 played Character。

```mermaid
flowchart TD
    C[实际 played Character] --> R[actor current Rite]
    R --> F[原生 Faith identity]
    F --> M[Faith main Rite]
    T[独立 Tenet definition special +1240] --> B[container rebuild 2591180]
    D[Doctrine definition special +9F8] --> B
    B --> V[merge 32908F0: max 字段与 additive heresy threshold]
    V --> RC[Rite special cache +7D0]
    R --> RC
    M --> MC[main Rite special cache +7D0]
    RC --> Q[复制实际 raw integer / Q100000 与 native unset]
    MC --> Q
    M --> H[Faith.GetHeresyThreshold 2440920]
    H --> HT[main Rite +7F8 + native define; 最终阈值]
    Q -. 本包未实现 .-> U[其他 special 字段与 authored 历史来源]
```

原生 constructor `0x14F27B0` 初始化特殊参数结构；container `+0x80` 为该结构，即 Rite `+0x7D0`。rebuild `0x2591180` 将 Core Tenet definition `+0x1240` 与 effective Doctrine definition `+0x9F8` 合并到该结构。`0x32908F0` 对多个字段取 max，对 `+0x28` 加法合并。当前最小输入目标为 `minimum_fervor`、`fervor_per_holy_site`、`bonus_fervor_gain`、`bonus_heresy_protection`、`heresy_threshold`。

`heresy_threshold` 特殊参数是 additive adjustment，不能等同于 Faith 的最终阈值；后者已由 `0x2440920..0x2440974` 证明只读取 Faith main Rite `+0x7F8` 加原生 define。actor current Rite 与 Faith main Rite 必须保留独立来源。

constructor 默认零的合并字段不保留“显式 authored 零”与“未 authored”的历史区别。输出必须称为实际 effective cache 值，不能从零反推 definition 缺失。`minimum_fervor` 的原生 `-1` sentinel 则可明确表示 unset，不能当成零；读取失败与合法无 Rite 另外区分。

| 原生 key | special / Rite offset | payload 与 scale | 默认 / 合并 | 实际 Faith consumer |
| --- | --- | --- | --- | --- |
| `minimum_fervor` | `+C` / `+7DC` | signed int32，scale 1，热忱点数 | -1 unset / max | setter `243EBC0..243EC59` 将主 Rite 整数乘 100000 作为热忱下限 |
| `fervor_per_holy_site` | `+10` / `+7E0` | signed int64，Q100000，每个受控圣地的年度热忱增量 | 0 / max | Faith calc `243EF4B..243EFA2` 从主 Rite 读取，在圣地遍历中使用 |
| `bonus_fervor_gain` | `+18` / `+7E8` | signed int64，Q100000，年度热忱增量 | 0 / max | Faith calc `243EE24..243EE7D` 从主 Rite 读取并加原生基础增量 |
| `bonus_heresy_protection` | `+20` / `+7F0` | signed int32，scale 1，保护名额增量 | 0 / max | Faith calc `243F626..243F685` 读取主 Rite 整数并加原生基础保护数 |
| `heresy_threshold` | `+28` / `+7F8` | signed int64，Q100000，热忱阈值 adjustment | 0 / addition | final getter `2440920..2440974` 读取主 Rite adjustment 并加原生 define |

`32901B0..3290557` 为特殊参数 field parser；五个 key 的 builtin table/CString 字节及实际 token 分派冻结在 [ABI JSON](../../research/religion_doctrine12002_numeric_abi.json)。`minimum_fervor` 分支 `329021A` 传 `+C` 给 int parser；holy-site gain 分支 `32902AD` 传 `+10` 给 fixedpoint parser；bonus gain `3290530` 传 `+18` 给同一 fixedpoint parser；protection `3290525` 传 `+20` 给 int parser；threshold `3290519` 传 `+28` 给 fixedpoint parser。原生 fixedpoint parser `3F840C0..3F841A1` 写 signed 64-bit；Faith consumer 的乘 100000 与同一 Q 原生基础值闭合单位。

Stock 证据为 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-doctrines/tenet/numeric-stock-dependencies/result.json`，SHA `b51ff93b66ed96128c3047c2d455490c82f0c92e09dfbc7e1bf959214339e683`。`_doctrine_types.info` 134–168 行明写这五项默认和合并规则；`20_doctrines.txt` 的无领袖教义提供最低热忱 45、bonus gain 0.5、保护 1、threshold +5；fundamentalist adjustment -5；Pentarchy Tenet 的 holy-site gain 为 0.05。

离线 ABI 已冻结 10 个完整函数 / 明确 scalar merge 与 actual consumer slices，跨 `.pdata` fragment 的 merge 只称 scalar slice，不冒称完整函数。父包既有 bool/rows 验证不重跑；新 provider 只运行一次 `/O2 /W4 /WX` 实际组件验证。

实际接口为 [religion_doctrine12002_numeric.hpp](../../ck3_autonomous_player/native_bridge/include/xar_bridge/religion_doctrine12002_numeric.hpp) 的 `BindNumericSpecialParameters12002`、`ReadPlayedNumericSpecialParameters12002`、`LookupNumericSpecialParameter12002` 和 `SerializeNumericSpecialParameters12002`。它复用已有 exact-build `religion::Bindings/CoreBindings`；只从实际 played Character 取得当前 Rite、Faith/main Rite 的完整 generation ID，分别复制五项原生缓存。DTO 的 `supported_key_count=5` 和行级 raw/scale/unit 描述当前支持范围，不声称已覆盖所有特殊参数或未来热忱预测。

typed lookup 分开 `Value`、`Unset`、`UnsupportedKey`、`UnavailableSource`。真实观测零返回 Value；最低热忱 -1 返回 Unset、保留 raw=-1 而 value=null；合法无 Rite 可 available=true/source=null；失败 available=false，没有伪造零缓存。default-zero 字段始终是有效合并值，不输出 invented authored presence。

本轮验收 GREEN：`religion_doctrine12002_numeric_native.py` 校验 **10 spans、5 个实际 key、6 个 provider offsets**；`religion_doctrine12002_numeric_tests.py` 只编译并运行一次 `/O2 /W4 /WX`，链接实际 core 与实际 production reader/serializer，**15 项检查、6 份实际 C++ DTO JSON**：current-versus-main、known-zero-current、minimum-unset、legal-absent、faith-unavailable、state-changed。JSON parser 互证 0.05、0.5、signed threshold ±5、integer protection、原生 unset 与失败。没有 Od / 旧 Boolean 19 / Rows 15 / mailbox 29 重跑，也未启动 CK3。

证据根：`Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-doctrines/numeric/`。`native/native-verification.json`、`native/native-disassembly.txt`、`provider/result.json`、`provider/O2/build.log`、`test.log` 与实际 JSON 保留。新增六份实际 DTO 的可移植冻结文件为 [numeric_wire_fixtures.json](../../research/religion_doctrine12002_numeric_wire_fixtures.json)。这是 provider DTO，尚不是中央 mailbox command_result 或 paused 游戏证据。中央 query / Python SDK / MCP 接线由协调者合并，真实 paused 读样通过后才能提升 production-live primitive。最终 Faith heresy threshold 的 native define 与 callback 已闭合，在后续独立扩展中提供原生最终比较值。
