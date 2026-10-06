# 外置夹具的一次开局与实际玩家绑定

本包解决重整河山等夹具在 `on_game_start` 改政府或切换玩家后，普通罗贝尔开局后态合同不再适用的问题。普通入口及其 feudal/one-life 验证保持原样；新增入口仅在显式 `--fixture-profile --frontend-robert-bootstrap --frontend-fixture-start-policy <file>` 下注册。实机 **NOT_RUN**，不增加产品通过数。

`ck3_submit_frontend_fixture_robert_start_v1` 是无参数、不可重放的单次动作。先核精确 `.3` EXE、PID/连接代次、Bookmarks、实际罗贝尔条目及 feudal 政府；必要时选择一次，再读回选中模型，最后 Start 一次。发送任何 mutation 前，以独占新文件、flush/fsync 记录 claim；断线或 ACK 丢失后，同一 state 的新 driver 也拒绝重放。Start 的 ACK 只记 `acknowledged_verification_pending`。

显式 policy 绑定 preparation SHA、配置和全量 mounted 文件 SHA、真实期望政府/头衔层级/独立状态，以及必须各一次和禁止出现的日志标记。只能使用全新空日志 profile。该路径使用现有 `native_campaign` projection；普通 one-life episode 不被自动放宽或重绑。

随后实际 snapshot 与同 revision campaign-root 对齐，核 `.3` provenance、同 PID/generation、书签日期、活角色、政府、原生头衔 ID/层级与独立状态。两次一致业务绑定还须跨真实 application-main pump epoch，并用已绑定 profile 的固定日志查询确认当次初始化。它只证明实际业务角色及列出的条件；接口未提供 history/script 或 stable title key 映射，仍记录 `fixture_target_identity_proven=false`，不能凭 numeric ID 推断 `h_china` 或产品验收。

冻结候选在 `C:/workspace/ck3-upgrade-20261003/zhongguo-agent-01/fixture-start-package-01/`。combined-v2 patch SHA `413fd74b51e6b4729be553fef836ca8cb518345a553f62146c195c771964cd97`；core-v2 SHA `f03fcead5b1b34c29aa76446ee78300963f19e3b7cf8511067a82ebded6c3b06`。21 项独立新聚焦检查通过，实际 MCP SDK 为 2.2.0；前两次 import overlay/缺依赖环境失败保留。default-invariance AST 检查和实际 patch apply/check 已完成；旧通过项未重跑。无需重新编译 DLL，完成的 f4 source/DLL 仍原样保留，后续 runtime 源要另冻结并精确记录。

外置 RMTM/Ox policy 已绑定各自 profile03 的实际输入；361 目前只有来源明确的 intent 与 factory，未因此生成或验证新的 profile。下一步在新 run 中先验该入口与实际后态，再执行各产品功能；不得用准备、schema、合成测试或日志字面值替代玩法结果。

## 2026-10-06 行政与贤能政府的夹具后态输入

体验优化的行政、贤能任命验收准备暴露出 policy 校验只接受封建与天朝政府，真实 `administrative_government` / `meritocratic_government` 输入会在启动前被拒绝。本次仅将这两个原版政府 key 加入 `post_start` 合法集合；原 Robert1066 的封建选角、一次 Start、实际 actor/government/title 与两 epoch 绑定保持。`campaign_root_context` 的现有政府 key 读取支持这些值，无需修改 native DLL。

外置政府入口的10项有限 loader/绑定检查与6项 compile 已通过，见 `C:/workspace/ck3-upgrade-20261006/xqol-post-defense-appointment-ui-next-agent-01/government-entry-ready-01/government-entry-finite-shape-receipt-02.json`。新增入库回归经过真实 bound-policy loader，再要求实际帝国政府匹配；仅 policy 接受不能授予业务绑定。新政府37文件输入仍 NOT_RUN，实际政府、任命法、候选与任命后态须由后续独立实机证明；已冻结 Source09/Source10 与各产品当前输入不变。
