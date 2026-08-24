# CK3 Native Bridge 版本适配与解耦契约

本文定义 CK3 升级、`ck3.exe` 改变时 native-headless 后端的失效方式、迁移边界和验收标准。目标不是让一组旧 RVA “自动兼容”未知版本，而是让每次逆向只替换一个逐版本适配器；MCP、策略、一代制生命周期和 OCR/键鼠 baseline 不随 CK3 ABI 一起重写。

证据状态：本文中的运行行为已按 2026-08-24 的 CK3 1.19.0.6 源码与实机记录核实；版本无关 contract、adapter registry 和逐 capability 发布已在本轮落地。精确 RVA、对象布局和逐能力实测结果仍以 [`native_bridge/research/README.md`](../ck3_autonomous_player/native_bridge/research/README.md) 为准。

## 1. EXE 升级后实际会发生什么

当前唯一受支持的游戏镜像是：

- 产品版本：`1.19.0.6`
- 文件大小：`95,206,008` bytes
- SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

当前 DLL 启动时会散列宿主进程在磁盘上的 EXE。只有完整 SHA-256 相同，`BindCurrentProcess()` 才把模块基址加到固定 RVA 上并令 `Bindings.enabled=true`。普通 CK3 更新即使仍显示相近的产品版本，只要 EXE 字节改变，也不会继续使用 1.19.0.6 的地址。

因此，升级后的预期行为是：

1. 通用 x64 DLL 注入、worker、named pipe、`hello`、heartbeat 和 ping/pong 通常仍能工作；这些代码不依赖 CK3 游戏对象布局。
2. `hello.ck3_build_match=false`，只公布 `bridge.identity`、`bridge.heartbeat` 和 `bridge.ping`。
3. DLL 不发布游戏 `state_snapshot`，也不进入原生 gameplay command 分派。
4. Python native driver 以 `hello.capabilities` 为权威：snapshot 和未公布的步骤返回 unsupported，而不是用旧地址尝试操作游戏。

这意味着“注入成功”不等于“native hook 仍可玩”。当前失配行为能保持进程通信，但 native gameplay 要等新版本适配器迁移完成。

### 两种运行模式在版本失配时的区别

| 配置 | 没有匹配适配器或能力尚未迁移 | CK3 最小化时 | 视觉后端 |
|---|---|---|---|
| `native-headless` | 对缺失 snapshot/step 明确返回 unsupported | 只使用仍公布的 native 能力；完全失配时没有 gameplay 能力 | 永不调用，也不恢复或激活窗口 |
| `hybrid-fallback` | 仅在调用前发现 capability 缺失时按 native → data Mod → vision 选择后端 | native 与 data Mod 可继续；vision 被拒绝 | 只在窗口当前可见时允许；已开始但失败的 native 动作不向下重放 |

当前 `restore-checkpoint`、战争、宣战和婚姻步骤在 `ConfiguredHybridFallbackDriver` 中仍属于 pure-native strategic steps；没有 native capability 时不会伪装成视觉或 data-Mod 支持。以后若为其中某项实现真正的语义后端，应显式修改该路由契约。

## 2. 稳定层与逐版本 ABI 层

版本解耦不是把所有代码改成动态配置，而是规定依赖方向：

```text
planner / one-life episode / MCP tools
                  ↓
Python GameplayBridgeDriver 与标准 snapshot/step result
                  ↓
named-pipe protocol + JSON 序列化 + command/query 调度
                  ↓
版本无关 Game API（Snapshot、Choice、Result、Capability）
                  ↓
exact-build adapter registry
                  ↓
CK3 1.19.0.6 adapter / CK3 未来版本 adapter
                  ↓
该版本的 RVA、vtable、对象偏移、构造器、validator、queue ABI
```

### 应保持稳定的层

- MCP 工具和资源：`ck3_take_snapshot`、`ck3_execute_step`、`ck3_wait_for_change` 及 typed query。
- Python 的 `GameplayBridgeDriver`、planner、战争/婚姻策略、存档恢复策略和只玩一代的 terminal 判定。
- 公开 step 名、normalized snapshot 字段、choice ID 的作用域语义及 command result 状态。
- 长度前缀 UTF-8 JSON、pipe reconnect、heartbeat、ping/pong 和 MCP daemon 热重启。
- `native-headless` 与 `hybrid-fallback` 的配置含义。
- OCR/键鼠和 data Mod 后端。

这些层只能依赖“角色 ID、战争、军队、事件、动作已提交/暂缓/失败”等游戏语义，不得看某版本的指针、RVA、command object 字节布局或 MSVC 容器。

### 必须封装在逐版本 adapter 内的内容

- EXE version、SHA-256、file size、PE timestamp 和 image metadata。
- 所有全局 slot、函数 RVA、vtable RVA、字段偏移、对象大小和对齐。
- CK3/MSVC string、array、component storage 等容器读取。
- 命令构造、validator、clone/queue flags、析构顺序和 payload 字段。
- 战争、婚姻等原生 interaction database slot 和 context 构造路径。
- 由原生对象投影为稳定 Snapshot/Choice/Result 的读取逻辑。
- 该版本的 anchor manifest、布局 fixture 和逐能力实测矩阵。

重构前，这条边界并不完整：`bridge.cpp` 直接 include `ck3_11906.hpp`，序列化器、worker state 和所有 dispatch 分支直接引用 `xar::ck3_11906::*`；预期版本、SHA 和整套 capability 字符串也硬编码在 transport 文件中；CMake 只编译 `ck3_11906.cpp`。当前实现已经移除这些跨层依赖；本段保留为迁移前基线，便于以后审查边界是否退化。

## 3. 已落地的目录和 API

本轮先收紧依赖方向，不为整理目录而搬动已经经过逆向和实机验证的大型实现。当前落地结构如下；未来增加第二个版本时，可以再把同一组版本文件机械移动进 `adapters/<version>/` 子目录：

```text
native_bridge/
  include/xar_bridge/
    protocol.hpp              # frame transport
    game_contract.hpp         # 版本无关 DTO、enum、result
    game_adapter.hpp          # adapter 接口与 build descriptor
    ck3_11906_adapter.hpp     # 1.19.0.6 adapter factory
    ck3_11906.hpp             # 1.19.0.6 私有 Bindings/ABI
  src/
    bridge.cpp                # JSON、pipe、query cache、dispatch
    game_adapter.cpp          # exact-build adapter registry
    ck3_11906_adapter.cpp     # 稳定接口 → 1.19.0.6 Bindings
    ck3_11906.cpp             # 1.19.0.6 RVA、布局和命令实现
    ck3_11906_test.cpp        # 版本专属 fixture
  research/
    ck3_1_19_0_6_anchors.json
    ck3_<next_version>_anchors.json
```

当前版本无关接口采用抽象类和 typed methods。接口表达稳定的游戏语义，不接收字符串化 RVA 或裸 command bytes：

```cpp
struct AdapterDescriptor {
  std::string_view adapter_id;
  std::string_view game_version;
  std::string_view executable_sha256;
  std::string_view checkpoint_save_name;
  std::span<const std::string_view> capabilities;
};

class GameAdapter {
 public:
  virtual const AdapterDescriptor& descriptor() const noexcept = 0;
  virtual bool enabled() const noexcept = 0;
  bool supports(std::string_view capability) const noexcept;
  virtual bool read_snapshot(Snapshot&) const noexcept = 0;
  virtual PauseSubmitResult submit_pause_map() const noexcept = 0;
  virtual MoveArmyResult submit_move_army(
      std::int32_t army_id, std::int32_t province_id) const noexcept = 0;
  // 其余 typed query/command 同理。
};
```

关键约束：

- `Snapshot`、choice 和 result enum 属于 `game_contract.hpp`，不属于 `ck3_1_19_0_6` namespace。
- `Bindings` 及其函数指针、地址、布局类型全部为 adapter 私有实现；`bridge.cpp` 不得看到它们。
- registry 在 worker 启动时只识别一次当前 EXE，按完整 SHA 精确选择 adapter；pipe 断开重连继续使用同一 adapter 和 worker state。
- 无匹配项时选择 bridge-only/null adapter，不调用任何游戏地址。
- 一个 DLL 可以编入多个已知 adapter。新版本迁移的正常 diff 是“新增 adapter + registry entry + 对应测试/研究资料”，不是修改 MCP 或复制一份 bridge。
- `hello.capabilities` 必须由所选 adapter 的 capability 集合生成，不能再在 `bridge.cpp` 手写一张与实现可能漂移的总表。
- `hello` 追加 `game_adapter_id` 与 `game_adapter_status=ready|unsupported_build`，同时保留原有 expected version/SHA 和 `ck3_build_match` 字段。只改变 RVA 或增加这些可选诊断字段不升级 pipe protocol version；只有 JSON 字段的既有语义或 frame 行为不兼容时才升级协议。

## 4. 逐 capability 恢复，而不是整包开关

当前 `Bindings.enabled` 是单一总闸：匹配 1.19.0.6 时公布全部 gameplay capability，失配时全部关闭。完成 adapter 边界后，每个 adapter 要公布实际已绑定并验收的能力集合。

建议至少按以下族独立恢复：

| 能力族 | 主要依赖 | 最小完成条件 |
|---|---|---|
| 基础 snapshot | game/Jomini state、local player、played character | 地图加载前后均可读；字段投影稳定 |
| pause/speed/life advance | 基础 snapshot、command queue、两个 command ABI | 最小化窗口中日期真实推进并可重新暂停 |
| active event/select option | event manager、event command ABI | option 提交后 active event 或实例状态改变 |
| checkpoint/restore | save command ABI、外部进程恢复器 | 文件真实产生；恢复后新进程重新连通并回到旧日期 |
| pending interaction/reply | component storage、接收方谓词、reply validator | 当前玩家请求被识别且回复后消失/推进 |
| war state 基础 | war/army storage、participant/score helpers | snapshot 与当前局面一致 |
| war objective hierarchy | title storage、de jure tree、Province table | exact 目标省完整、稳定、无部分 stale 分支 |
| war objective occupation/fort | Province 标量 getter、Character generation | occupied/empty/零级要塞与 unknown 可区分 |
| war objective garrison/siege | Holding/CSiege storage、progress/work/days getter | 仅 paused 发布；无围城、停滞与 unavailable 可区分 |
| declare/enforce | CB/interaction database、context/command ABI | 战争真实新增；100% 战争真实结算 |
| raise/move/disband | army IDs、province、各 command ABI | 军队真实出现、换省或消失；不能只看 queue submitted |
| arrange marriage | interaction database、四角色 context、validator | query 给出真实有效候选，提交后关系或互动真实变化 |

依赖缺失时只移除受影响 capability。例如新版本已迁移 snapshot、暂停和事件，但战争对象布局尚未确认，native-headless 应继续提供前三者并让战争步骤 unsupported；不能因为一个战争 RVA 未迁移而放弃所有后台运行能力，也不能反过来把未迁移战争命令列进 hello。

Python 已经根据 `hello.capabilities` 生成 action steps，并能从 capability 缺失得到 unsupported/fallback 决策。只要公开 step 和 snapshot 语义不变，新增 CK3 adapter 不应要求修改 MCP tools 或 planner。

## 5. 新 CK3 版本迁移清单

### A. 冻结新 build 身份

1. 保存产品版本、完整 SHA-256、file size、PE timestamp、preferred image base 和 size of image。
2. 新建该版本的 adapter 目录与 anchor manifest；禁止直接覆盖上一版本资料。
3. registry 只有在该 adapter 至少通过离线绑定检查后才加入新 SHA。

### B. 重定位与复核 ABI

1. 重新定位 game/Jomini state、manager、component storage 和 database getter/slot。
2. 重新定位所有调用函数、command vtable、clone/submit/validator/destructor。
3. 逐字段复核对象偏移、数组/string 表示、ID 宽度、command size、payload 和 queue flags。
4. 检查语义是否改变，而不只是寻找“看起来相近”的指令字节；若游戏语义确实改变，由 adapter 翻译为现有公共语义，无法无损翻译时才考虑升级 `game_contract`/protocol。
5. 按能力族实现并公布 capability；未完成族保持缺席。

### C. 离线验证

1. 对新 manifest 运行：

   ```powershell
   py ck3_autonomous_player/native_bridge/research/scan_anchors.py `
     --exe "<new-ck3.exe>" `
     --manifest "<new-build-anchors.json>"
   ```

2. 为新 adapter 建独立 layout/command fixture。fixture 必须故意让易混淆字段取不同值，例如 public component ArmyID 与 command-target ID、CK3GameData 与 interaction database 使用不同 trap object；否则错误基址或错误 ID 可能被测试数据掩盖。
3. 构建 native bridge 并运行 CTest；再运行 Python protocol/driver/MCP contract 测试，确认同一语义 frame 对上层产生同一 snapshot/result。
4. 验证 unsupported build 仍只公布 bridge capability；验证 partial adapter 不会 dispatch 未公布步骤。

### D. 最小化实机验收

每个 capability 族分别验收，不能用“DLL 成功注入”“heartbeat 连续”“command_result=submitted”替代 gameplay 后置条件：

1. 记录 exact build、PID，并确认 CK3 窗口在整个动作期间 `IsIconic=true`。
2. 经正式 MCP client 调用 snapshot/query/step，不调用 OCR、截图、窗口激活、键盘或鼠标。
3. 观察该能力对应的真实语义变化：日期、事件、存档文件、战争、军队位置/消失、婚姻关系等。
4. 确认 CK3 进程仍存活、pipe 仍响应；需要恢复的流程同时确认新 PID/generation 和恢复后的日期/状态。
5. 把结果写入该版本 research 文档和 capability matrix；通过的能力才能加入 adapter 公布列表。

### E. 合入与回归

1. 新增 registry entry 和 adapter 构建目标。
2. 复跑旧版本 adapter fixture，确保新版本没有改变旧版实现。
3. 用 recorded/golden protocol frames 验证两个 adapter 输出相同的公共 JSON 语义。
4. 分别检查 `native-headless` 的严格 unsupported 和 `hybrid-fallback` 的公开回落顺序。

## 6. Anchors、fixture 与实机证据各自解决什么

- `research/ck3_<version>_anchors.json` 冻结 build 身份、唯一 signature 和 vtable prefix，回答“我们分析的是否还是同一份 EXE、候选函数是否仍在预期地址”。
- `scan_anchors.py` 是离线开发工具。它可以帮助发现版本变化和验证人工迁移结果，但不证明对象字段语义或 command 生命周期正确。
- `ck3_<version>_test.cpp` 的内存 fixture 回放对象布局、选择逻辑和 command 字节，回答“adapter 是否按已知 ABI 读写”。它不能证明新 EXE 的逆向结论正确。
- native bridge host/target 测试验证通用注入、frame、hello、heartbeat、ping 和 reconnect，不证明 CK3 gameplay。
- 最小化实机验收最终回答“这个 capability 是否真的在游戏里产生预期结果”。

五者要串联，但不建设额外的巨型证明协议。对实际功能最有价值的链路是：anchor 辅助迁移 → 小型 fixture 防布局回归 → 尽快完成逐能力最小化实机闭环。

## 7. 明确不做的事情

- 不在未知 EXE 中运行时扫描若干 pattern 后直接调用猜出的地址。
- 不按产品版本前缀、文件名或“多数 anchor 相同”选择旧 adapter；registry 只认完整 SHA。
- 不把旧 RVA 与新模块基址相加后试运行，也不在崩溃后轮换候选 offset。
- 不用一个通配 ABI schema 假装能够描述所有 CK3 C++ 对象布局。
- 不因为未来可能升级而暂停当前战争、婚姻、存档恢复等可玩功能。

这是功能可靠性边界，不是泛化安全工程。项目已经实测过错误 Army storage RVA 导致 `C0000005`、错误 interaction database 基址导致崩溃，以及错误 disband payload 被 queue 接收但军队没有消失。运行时盲猜会直接破坏自动游玩闭环；exact-build adapter 的价值是把同类迁移成本和实际故障限制在一个可替换目录。

## 8. 本轮解耦施工的完成定义

1. `bridge.cpp` 不再 include 或引用 `ck3_11906` namespace，也不硬编码某个 CK3 version/SHA/capability 总表。
2. 公共 DTO/result 已从版本头文件移到 game API；版本专属 `Bindings` 不越过 adapter 边界。
3. registry 对 1.19.0.6 选择现有 adapter，对未知 SHA 选择 bridge-only/null adapter。
4. 当前 1.19.0.6 frame、MCP 行为和已完成玩法不发生语义回归。
5. capability 来自 adapter，测试至少覆盖 exact match、unknown build 和 partial capability dispatch。
6. anchor scanner、C++ fixture、protocol tests 和既有 Python native-driver tests 通过。
7. 下一 CK3 版本可以通过新增 adapter 完成迁移，不需要复制或修改 `bridge.cpp`、MCP tools 与 planner。

第 7 项要到实际出现第二个 EXE 后才能最终验证；在此之前标为架构验收目标，不宣称已经证明跨版本兼容。
