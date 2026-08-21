# CK3 Autonomous Player

`ck3_autonomous_player/` 是【琉焰卿的永恒轮回】专用的 CK3 视觉智能体工程。Python 包名为
`xar_autoplayer`。它与 `tools/run_acceptance.py` 完全隔离：验收 runner 证明 mod 机制；这里的智能体只在
production、非 debug、仅加载本 mod 的正常游戏里扮演玩家。

## 当前完成度

**Phase A 已完成。** 提交 `11ab443050132341bb27f6f924d792772f397396` 的冻结候选在同一环境指纹下连续三次
通过 production、非 debug、单 mod、可见主菜单 isolation smoke：
`20260821T180045Z-a3c49b20`、`20260821T180248Z-7ad2dd83`、`20260821T180531Z-9c6bb34b`。
三份事件链均已重新计算 hash chain 并通过一致性校验，另行逐项检查的报告硬条件无失败。完整证据边界见
[Phase A 实机证据](../docs/autonomous-player-phase-a-evidence.md)。加固前的三次运行只保留为历史探索记录，不能作为
当前退出证据。

已实现：

- 仓库外持久 state/profile，且与仓库、真实 CK3 profile、Steam userdata、CK3 Workshop 根目录双向隔离。
- 通过 `tools/build_release.py` 构建 production-only 投影，不加载开发树或 acceptance/selftest 内容。
- `dlc_load.json` 精确只有 `mod/xar_autoplayer.mod`；outer descriptor 仅指向隔离 profile 内的投影。
- 原版 81 个声明默认规则，加 `xar_on`、`xar_inherit_100`、`xar_score_growth`，总计 84 个 setting。
- 简中、2560×1440、云存档关闭；`tutorial.txt` 只在首次创建，之后不读取、不清空、不回滚。
- 同一 state 的锁覆盖 prepare/verify/smoke；同一 CK3 安装的全局启动锁覆盖完整 smoke 启停周期。每次启动前和退出后
  都用 `tasklist` 与 WMI 双源清点 CK3，任一查询失败、格式异常或结果不一致都按 unknown 拒绝继续，绝不把查询失败解释成零进程。
- unsafe marker 在启动 watchdog 前建立；watchdog 先持有并复核 supervisor 的 PID、可执行路径和创建时间，之后才写 ready。
  CK3 以 `CREATE_SUSPENDED` 创建，先进入 kill-on-close Job、完成 WMI 身份验证并原子写入 launch record，resume 前还要让
  双源全局清点精确只看见这个新 PID，因此第一条 CK3 指令开始就在 Job 内。record 绑定 nonce、父 PID、可执行路径和创建时间；
  watchdog 只终止持有句柄后再次认证的进程对象，崩溃 fallback 要达到五秒稳定空窗。清理证明不完整时保留 unsafe marker，
  并禁止 postflight。
- OCR 连续两帧确认可见【新游戏】；每次启动前删除隔离 profile 的旧日志，再以新日志的唯一 session marker、精确单项
  enabled inventory、已安装 DLC mount 白名单、唯一隔离 mod mount 和零未知 mount 做 supervisor 取证，退出后再解析一次。
- 真实 profile 顶层文件、player/rulers/正常存档与 Steam 云存档条目在退出后回到语义 baseline，并连续稳定 5 秒；Workshop
  `ugc_*.mod` descriptor 内容哈希与已注册目标树的路径/大小/mtime 元数据只做退出后一次 baseline 比较。两者都不声称运行期间
  从未发生瞬时写入；Steam 自行刷新 `remotecache.vdf` 的允许字段单列报告。
- 游戏 exe、launcher、原版规则、DLC descriptor、outer descriptor、production manifest/tree、实际构建脚本、解释器与依赖均纳入
  selected-contract 指纹；smoke 还要求选中的 agent runtime 与 production release source 文件全部已被 Git 跟踪且无修改。
  没有真实指向当前提交的 tag 时
  `git_tag=null`，不会伪造 release provenance。
- shutdown attestation 显式记录 CK3/watchdog PID 与创建时间、Job 最终成员数、双源全局清点、watchdog 退出状态和控制文件消失；
  `cleanup_proven` 是这些条件的显式合取，只有它严格为 true 才允许受保护存储复核。`report.json` 先落
  `finalized=false, ok=false`；最终事件链逐项重算、链接和 tail 绑定验证成功后才原子转为 GREEN。
- 六类版本化 JSON schema 草案、首个 `growth100.v1` 策略假设和追加写入、带 SHA-256 链的 smoke 事件流。文件系统尚无防截断
  保证；schema 的运行期验证
  与不可变 episode store 属于 Phase E，当前不能把“JSON 可解析”称为已完成约束。

尚未实现的关键能力：游戏规则页的视觉复核、正常 UI 新开局、事件/当铺/交易决策、HUD 状态抽取、战争与内政、
保存续玩、自然死亡结算、episode 学习与多局优化。主菜单 smoke 只是基础设施证据，**不是有效得分局**。

当前加固候选还增加了两项基础能力，其中 crash 路径已通过本机 GREEN 门禁，纯视觉输入路径仍未接入真实 CK3：

- `crash-smoke` 使用外层验证器、可牺牲 supervisor、detached watchdog 三个逻辑角色；Windows venv 可在 outer 与
  supervisor 之间增加一个经完整命令行和进程身份认证的 interpreter redirector。outer 必须先固定真实 supervisor
  的进程句柄并回写 acknowledgement，subject 收到它之前不得启动 CK3；ready、ack 与 armed 同时记录 UTC 和
  跨进程可比的 monotonic 时间，实时路径强制严格顺序，离线回放只验证归档记录值与内部关系一致。在 CK3 已 resume、可见主菜单且
  单 mod load attestation 成立后，通过固定进程句柄终止 supervisor。CK3 与两个合成 Job 子孙必须全部退出、命名 Job
  必须销毁、watchdog 必须正常退出、全局 CK3 清点必须连续 5 秒为空，之后才允许 protected postflight。两帧主菜单、
  handoff、supervisor ready/ack、armed、三份控制文件、watchdog final、production manifest 和日志前缀均复制进证据包；
  在同一 validator、仓库代码与 OCR runtime 下，整个 run 目录可更换父目录后回放，但它不是跨机自包含归档。报告固定声明
  `integrity=unkeyed_sha256`、`historical_execution_authenticity_proven=false`：它能复算已实现的 schema/manifest 关系、PNG→OCR 与哈希链，
  但不逐项把每个 event payload 的全部语义重新绑定到 report；
  不能在没有密钥或外部信任根时证明一份历史归档必然来自真实执行；实机资格仍以本轮外层 verifier 的当场 OS 观察为准。
- `recover-stale-control --run-id <finalized-RED-run-id>` 只处理一次明确指定、已完成且仍保留 unsafe marker 的 crash RED。
  它重新认证源证据、当前全部进程均不存在、命名 Job 已销毁和双源 CK3 清点为空，再把 control 文件逐项按原哈希归档；
  unsafe marker 的 compare-and-swap 归档是最后一次 recovery 证据/控制提交，之后不再写 recovery report 或 artifact
  （锁实现仍可清理自己的 owner 文件）。恢复会生成独立 report，固定声明
  `historical_cleanup_proven=false`、`current_absence_proven=true`，绝不修改旧 report、把旧 RED 升成 GREEN，或在启动前自动清标记。
  write-ahead report 在 marker 提交前已含条件式 `ok=true`；该字段不能单独视为成功，必须由
  `validate_recovery_report()` 同时验证 active marker 已消失且归档 marker 的 SHA-256 匹配。
  旧 RED `20260821T211059Z-crash-833b9587` 已由恢复 `20260821T215805Z-recovery-46a3518c` 按此协议归档；
  旧 report SHA-256 未变，恢复只解除启动阻塞，不资格化那次 RED。
- Phase B 的纯视觉底座已经建立 PID/创建时间/可执行路径绑定的 CK3 窗口捕获、OCR 屏幕分类、短期 HMAC 控件 token、
  点击前后状态反证和 fail-closed 导航骨架。当前动作白名单只有主菜单【新游戏】，并显式禁止大厅【开始】；未接 CLI、
  未在真实桌面发出输入，也不能据此声称已经能开局。

上述改动改变了受指纹保护的 runtime，因此旧提交的 Phase A 三连只证明历史冻结候选，不自动为后来实现背书。
runtime 实现提交 `98d55caf3ed4a398b0a3bd7bc8e6ee16591d8f26` 已重新准备 profile，并在同一环境 SHA-256
`5e7fb63ef98a7fd802caa864b64c593053c68bfb5f1798321cde6b02d6cd0d5f` 下通过普通 `smoke`
`20260821T215910Z-780cd6cb` 与 post-resume `crash-smoke` `20260821T220127Z-crash-adc0ac63`。
普通 `validate_smoke_report()` 已重算无密钥事件链、final tail 与 finalized/ok，load、cleanup、protected 和 production 硬字段
另行逐项核对；`validate_crash_report()` 则完成 crash 归档的 schema 与内部一致性回放。两份报告仍只证明单 mod 可见主菜单、
受控退出与崩溃回收，`valid_score_episode=false`，不证明 Growth+100 已在大厅实际采用，也没有发送任何游戏输入。
截至 2026-08-22，本候选离线单元回归为 119 项：118 通过、1 项显式真实桌面集成跳过；这不能替代上述本机门禁。

## 运行

使用项目现有桌面依赖环境：

```powershell
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" doctor
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" prepare-profile
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" verify-profile
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" smoke
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" crash-smoke
& "tools\.venv\Scripts\python.exe" "ck3_autonomous_player\agent.py" recover-stale-control --run-id <finalized-RED-run-id>
```

默认运行状态在 `%LOCALAPPDATA%\XarAutoplayer`，可用 `XAR_AUTOPLAYER_STATE_DIR` 或
`--state-dir` 改写，但安全检查拒绝仓库、真实玩家目录、Steam userdata 与 Workshop 的父目录或子目录。

`smoke` 会在仓库外创建：

```text
XarAutoplayer/
  profile/
    mod/xar_autoplayer.mod
    mod-content/xar-production/
    player/game_rules/presets.txt
    dlc_load.json
    tutorial.txt
    xar-autoplayer-environment.json
  runs/<run-id>/
    events.jsonl
    report.json
    artifacts/
  recoveries/<recovery-id>/
    report.json
    artifacts/
  control/
```

## 安全与合法性边界

- 策略只能消费截图、OCR、模板结果和玩家可见 tooltip/账簿/事件/结算。
- `debug.log` 只由 supervisor 压缩成 enabled-mod 与 mount 证明，原文永不进入观察或策略层。Phase B 接入 policy 前必须实现
  单独进程与字段白名单序列化边界，不能只依赖 Python 模块约定。
- 禁止 debug mode、控制台、内存/存档解析、隐藏变量、acceptance marker/wire、教程位读取和回档重掷。
- Phase B 接入正式局后的目标契约是：未知屏幕只允许在已视觉认证暂停控件时暂停，否则留证并由 supervisor 终止；不采用
  验收 runner 的盲点恢复策略。当前 Phase A/候选只会等待【新游戏】两帧稳定 OCR，超时留证并在清理证明完成后终止，
  尚没有已接线的通用未知窗口暂停能力。
- 工程 smoke、识别调试和环境失败永不计入得分榜或训练策略结论。

## 分层架构

```text
supervisor: profile / production projection / PID / attestation / integrity
       ↓
perception: window capture / OCR / templates / screen classifier
       ↓
state: visible facts + uncertainty + temporal reducer
       ↓
control: safe action catalogue + precondition + postcondition evidence
       ↓
policy: survival / contract / dynasty / economy / war / XAR bargains
       ↓
episodes: append-only evidence / settlement / validity / metrics
       ↓
memory: cross-run retrieval / constrained reflection / strategy experiments
```

历史 Phase A 基线已落在 `src/xar_autoplayer/{environment,integrity,locking,rules,runtime,process_watchdog}.py`；加固 runtime 已重新通过
普通 smoke 与 crash-smoke。后续模块只有在上一层的结构/一致性测试和对应本机门禁都通过后才接入正式局，避免把固定坐标脚本误称为
会玩 CK3 的智能体。

## 路线图

1. **Phase A（已完成）**：committed candidate 已连续三次通过 production、非 debug、单 mod 主菜单 isolation smoke；每次都保留
   非零引擎 diagnostics 的原始证据，且受保护存储在退出后回到同一语义 baseline。原生 Windows Job/句柄测试和两次启动期
   fail-closed RED 覆盖失败契约；加固 runtime 的 resume 后 supervisor 崩溃注入也已通过本机门禁。
2. **Phase B（进行中）**：纯视觉菜单/大厅/规则页/地图 HUD 驱动；点击必须有后置反证，未知窗口 fail closed。当前只完成
   主菜单、稳定书签大厅分类与【新游戏】动作契约的确定性合成单测，尚未执行真实点击。
3. Phase C：先完成“罗贝尔 1066 → 契约 → 当铺 → 首轮垂青 → 十年低风险经营 → 自然死亡结算”的首个合法竖切，
   再扩到多种角色类型的有效整局基线后退出本阶段。
4. Phase D：婚育、议会、生活方式、建设、宣战理由、军队和领地的分层规划器。
5. Phase E：不可变 episode、截图回放集、策略版本、局后复盘与少量受控实验。
6. Phase F：同一时间线保存续玩、崩溃隔离、资源预算与连续多局。
7. Phase G：按版本、DLC 指纹、政府、开局等级与余烬位阶分榜，持续优化真实最终分数。

Phase A 的 GREEN 只表示 `acceptance_claim=isolated_single_mod_visible_main_menu_only`。本机前端会枚举既有 Steam Cloud
存档 meta，因此即使 `cloud_save=no`，旧 PoD 存档中的规则和贴图引用仍会形成非零 `error.log`；enabled inventory 与 mount
反证证明 PoD 没有被加载。本 smoke 以 `clean_engine_boot_required=false` 和 `engine_diagnostics.zero_diagnostics=false`
记录这条边界，不把它升级为“零错误启动”。Growth+100 规则是否在
大厅实际采用、教程通知能否在正式局持续落盘，以及正常 UI 开局仍是 Phase B/C 的视觉硬门禁。

首次真实点击前仍有四个成组门禁：真实 Win32 helper-window 验证 DPI、client/screen 坐标、Z-order 与单批次 `SendInput`；
用真实 CK3 hover 帧校准最终像素 patch 的容差；把 UI 截图、receipt、`ui-events.jsonl` 接入正式 run/report hash chain；
由冻结环境按固定路径与 SHA-256 加载 UI contract，禁止策略或 CLI 注入同名控件定义。

玩法基线见 [knowledge/ck3/gameplay-v1.md](knowledge/ck3/gameplay-v1.md)，本 mod 的高分映射见
[knowledge/mod/growth100-scoring-v1.md](knowledge/mod/growth100-scoring-v1.md)。
