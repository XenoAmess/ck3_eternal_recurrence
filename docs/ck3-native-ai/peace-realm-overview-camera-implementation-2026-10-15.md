# 和平期全境镜头：独立展示通道候选（2026-10-15）

状态：**代码已实现、离线验证；未部署到当前长局、未授实机全境覆盖或性能 GREEN。** 本包基于 `e97673186312c78c721ce1af8147beab7f8ab758`，没有启动、停止、注入或操作当前 CK3/OBS，也没有桌面输入。用户授权来源是 2026-10-15 明确要求开子线程实现全境视角，同时保持 30 年游玩与优化继续。

## 行为

- 连续 30 个游戏日没有战争热点、强制选择、事件、待处理交互或活动军队需求，自动请求全境镜头。30 日是游戏日期差（每游戏日 24 raw units），不是墙钟等待；同日重复回合不累计。和平期静止的军队不阻止展示。
- 全境来自当前角色和封臣契约递归枚举到的实际县头衔；县 ID 去重后，各县原生地图边界取并集。飞地、跨海的领地均进入包围盒，不用主头衔法理范围代替。继承换角、连接 generation/episode 变化、日期回退都会重置安静期。
- 战斗、围城、行军等已有热点立即优先；事件和强制选择取消待展示的全境意图。新热点换县才重新定位，和平全境每 30 游戏日刷新实际县集和边界；当前没有可复用的领土变化 revision，所以不声称和平领土改变已实现逐帧即时刷新。
- 镜头目标按实际 CK3 客户区尺寸、横纵比例与 15% 留白扩展范围，再选该 exact build 的原生 title-map zoom bucket。原生 camera canonicalizer 验证目标坐标，直接更新既有 target/zoom 字段，正常 native camera update 负责插值。回执明确区分排队、已提交、已稳定、取消、过期/换角、被热点抢占、不可用和目标被改变。
- 悬浮窗消费异步镜头摘要，展示全境/战争热点、原生回执、县数，并将模式或回执变化加入滚动记录。排队 ACK 与旧请求的 settled 回执不能变成本次成功。

## 独立通道与性能边界

原 `CreateNamedPipeW` 单实例 gameplay 通道保持原用途。本包新增 native 进程创建的 `Local\XarCK3CameraPresentationV1-<CK3 PID>` 共享内存（128 KiB）。SDK 后台 worker 仅打开已有通道、发布最新意图，不创建第二 gameplay pipe，不等待原生执行或镜头稳定，也不获取 gameplay driver 锁。

原生 application-main 只在普通 query mailbox 为 idle 时消费展示意图；排队的 gameplay ticket 优先。每次只保留最新请求，奇偶发布序号排除半帧数据；意图 10 秒墙钟过期，并再次检查当前角色、日期、地图、事件/交互、战争和活动军队。展示回调不提交/回收普通 gameplay ticket，不等待、不执行磁盘读写。通道检查最多每 50 ms 一次；完整县集与边界只在新全境/只读请求时读取，后续只做轻量相机稳定读回，最多 5 秒后结束等待状态。idle callback 通过独立注册函数配置，不改变已冻结 InstallEnvironment/Mailbox 的结构布局。

Python worker 保留首个待处理请求的 eligible_at，后续意图只替换内容，避免持续快速回合让 debounce 无限推迟。自动回合只带小摘要，完整县 ID 列表在状态查询读回，避免每回合重复写入大县集。通道未部署、桌面归属不符等失败仅记录并按 30 游戏日退避，不阻止 gameplay，也不重放游戏动作。

这消除了 Python 等待镜头/原命令管道占用，并不代表游戏 owner-thread 工作免费。县遍历、县 bounds 与一次 target 写入仍由游戏线程执行；回执含 `native_elapsed_us`，需要在下一次获准 native 部署后的真实桌面 1 长局量测。当前没有严格的每回调毫秒上限或大型帝国的增量遍历验收，不能承诺它在所有领土规模下都没有推进开销。

## MCP 与实现入口

| 入口 | 合同 |
| --- | --- |
| `ck3_center_map_on_player_realm_v1(expected_revision)` | 发布异步全境意图，返回 `queued_native_presentation` 和 `request_sequence`，不是镜头成功 |
| `ck3_query_player_realm_map_bounds_v1(expected_revision)` | 经同一独立通道请求实际县集/边界，原生 `bounds_available`，不移动镜头 |
| `ck3_realm_camera_status_v1()` | 无 gameplay pipe 的本请求实际回执读取；旧请求回执不冒充当前请求 |

自动游玩在已完成业务回合后，把同一 planner observation 的轻量输入交给后台 worker。桌面约束在发布端检查该 PID 的唯一 CK3 HWND，以及 Shell 第一桌面的 GUID；原生复核 HWND 仍属本 CK3 PID、窗口非最小化及真实客户区。没有切桌面、激活窗口、截图、OCR、鼠标或键盘输入。

主要文件：`bridge/realm_overview_camera.py`、`bridge/auto_camera_follow.py`、`bridge/service.py`、`bridge/mcp_server.py`；原生 `camera_presentation_v1.cpp/.hpp`、`realm_camera_geometry_v1.hpp`、现有 `main_thread_query_mailbox_v1` 的可选 idle callback。`ck3_12002_faction_alerts.cpp` 的既有县遍历被导出为共享只读函数，exact `.4` faction binder 复用该读取语义。

## 精确版本与未闭合范围

- 唯一新增生产绑定：CK3 **1.20.0.4**，EXE SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`。使用现有 `.4` title-map resolver、bounds、camera target/zoom/angle offsets 和 canonicalizer；地址来源见 [title-map 迁移](title-map-navigation-12004-migration.md) 与对应 `.4` headers。其他 SHA/版本不会被本候选假定兼容。
- 当前缩放依据是 **native bucket + viewport padding 的估算**。尚无已验收的 native world-to-screen/projection 查询，因此 `coverage_verified` 恒为 false。`settled` 只证明新目标与当前相机状态读回一致；不能证明全部县像素都在可见地图区域，也不能声称最大缩放装不下时已可靠返回 `cannot_fit`。
- 强制普通事件/交互在原生执行前复核；通用 modal 的新鲜提示由已有 planner frame 驱动取消。尚未实机证明所有模态变体出现到展示取消的延迟。地图边界 canonicalizer 改变 X/Z 的情况返回 unavailable，不假称全境成功。
- 不改变宣战、战争胜负、建设或事件选择策略，不生成 gameplay credit。

## 离线验证与后续实机门槛

外置测试构建：`D:/codex-ck3-demos/2026-10-14-robert-30year/realm-camera-native-build`。公共 `tools/run_native_msvc.py` 使用实际 MSVC 19.51 x64，生成 focused EXE 和 compile-only objects。新生产 `camera_presentation_v1.cpp`（`/W4 /WX`）与完整 `bridge.cpp` 注册点离线编译通过。

另已实际生成可部署候选：`realm-camera-native-candidate01/native.dll`，18,101,248 bytes，SHA-256 `5f391893f4f017057399dce8654a5f7d9815eed1d6f3cfb853fadec5f7bb9cb0`。该候选以正在实机使用的 B17 原始 bridge、final03 mailbox 及 native89 job 392/479 原始源码为基线，只应用本包镜头补丁；五个 TU 重编后替换两个旧 direct OBJ、增加三个 direct OBJ，复用其余不可变 OBJ 与原 runtime archive。完整源码差异、实际 include pins、编译命令/结果、所有 retained link inputs 的 SHA 和 link response 在候选目录。当前 master bridge 中另有约 299 行其他研究/军力查询改动，未把这些无关变化夹带入 B17 候选。五项 DLL exports 与 B17 一致，新镜头/县集/idle 注册符号已链接，旧被替换的 archive member 未被重新拉入；旧 B17 DLL 仍为原 SHA。候选没有部署、加载或操作游戏。

为与 root 的性能分析合并冷载，后继 `realm-camera-native-candidate02/native.dll` 在上述候选上只替换 B17 的宣战枚举 TU，加入已合回 master `bb6b0312` 的 opt-in 按 CB 聚合计时。实际验证该 profiler 的父源码与 B17 所用 B16 c0389 源码字节相同；其余镜头候选 OBJ/库均复用原件。候选 02 为 18,104,832 bytes，SHA-256 `b15fda9a68067eec82b11b37197430f3d6240bc301f1502348a8205092ef9912`，候选 01 未覆盖。首次实际 MSVC `/WX` 捕获 `_wgetenv` C4996：原 `suppress` 与调用之间有预处理 `#endif`。仅以函数内 `warning(push/disable 4996/pop)` 包住环境读取，保留全局 `/WX`，修复后同一生产 recipe 编译并链接通过。原失败日志/回执保留于候选 02；没有新增 EXE。采样默认关闭，下一次游戏启动前设置 `XAR_CK3_DECLARATIONS_PROFILE_JSONL` 为 D 盘现存输出目录下的 JSONL 路径才会写入。

三个 focused native CTest 通过：

1. 真实封臣县枚举，直属县/封臣县、重复县、非县头衔过滤、full-generation 不符拒绝。
2. 飞地并集、不同视口比例与留白、overflow 拒绝、原生 bucket 选择和 C++/Python wire layout。
3. 实际 main-thread mailbox 的 idle presentation：gameplay 排队时让路、unpaused owner 帧可执行、TLS 不符跳过、卸载清空 callback。

Python 覆盖游戏日安静期、月度刷新、战争/事件抢占、继承重置、持续请求不饿死、最新请求合并、跨语言结构布局、半写回执不授成功，以及 service 不读额外 snapshot/不走 gameplay pipe。还实际验证了 Windows 共享内存 API 打开、发布与回读（测试自有 PID 名称、无 CK3/桌面接触），捕获并修复了 x64 kernel32 不导出 InterlockedCompareExchange 的生产绑定问题；发布采用限定 AMD64 的自然对齐 32 位序号与 FlushProcessWriteBuffers。另有旧热点、和平单点显式接口和悬浮窗回归。精确测试数量以本包最终 delivery 回执为准。

Defender 公共 hook 已运行，但当前普通 token 的精确 EXE 登记实际返回 `admin_required_for_verified_readback`，没有 Add、UAC 或设置成功事实。原失败 manifests/receipts 保留于外置构建 `defender-exe-exclusions/`；编译通过与 Defender 设置未完成分别记录。

`open_kaishek` 对本包 not-applicable：没有新增 Paradox 脚本/AI 语义；确定性 C++ 边界、原生图遍历与 Python 调度由上述离线测试直接覆盖。它们不能代替真实 CK3 验收。

后续仍需由 root 在允许更换 native binary 的自然存档边界/独立场次完成 exact DLL 部署、桌面 1 全境/飞地截图和录像、war/modal/继承抢占、窗口尺寸变化，以及带/不带展示的同策略秒/游戏日对照。当前有效长局继续使用原 DLL，本子线程不为候选中断或重启它。

存储采用通用策略 v1.0.0，D 卷由 root 串行准入 2 GiB 新增峰值；本包 worktree 与 focused build 当前合计约 265 MB 逻辑大小。工作树为待集成输入，构建为 build 类；交付后按 14 日期限复核，必要评审输入仅限期保护，不自动永久保留。
