# 《礼与道》产品验收矩阵

当前版本：CK3 1.20.0.4/build25734779。历史1.20.0.3证据按原轮次保留。此矩阵是验收合同；没有实机回执的项目保持 `NOT_RUN`。源码解析、命令 ACK、按钮可见或离线模拟均不能替代实际游戏状态与重载证据。

2026-10-08增量：[R0024](../../docs/li-yu-dao/acceptance/2026-10-08-r0024-e0e017da1-signed-protection-red/REPORT.md)的410/412/411/413实际批准链与独立B3保存证书通过，一次factory创建新宗教Title；B4五个政治Title的heir及actor succession保护失败，整体仍NOT_GREEN。完整AST保护不放宽；新Title冷载、NPC在任授予与C3未执行。修后源码检查通过不替代这些实机门槛。以下早期轮次的NOT_RUN/RED属于当时事实，不覆盖本增量。

随后[R0025](../../docs/li-yu-dao/acceptance/2026-10-08-r0025-720ef066c-native-injection-crash-red/REPORT.md)在首次native注入时栈溢出，未成功attach、无B0或新87项保护、无正式业务回调。实际DLL/COFF与崩溃帧证明army和route构造互相递归；最小直接leaf绑定修复及完整构造器focused已exit0，DLL/实机尚未复验。CAS3727及辅助进程原HANDLE exit0证明占用已闭环；game OS退出码、typed正常退出、autosave保持NULL。此轮不能替代R24六项保护复验，C3/I4仍待其前置通过。

## L0：无需游戏或桌面的检查

使用已核验的解释器 `C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe`（3.13.15），无需项目 venv 或第三方 Python 包。以下命令从仓库根执行。

```text
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/test_build_release.py
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/test_run_acceptance.py
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/test_school_consent.py
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/test_content_leadership.py
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/gen_content.py --check
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/gen_runtime.py --check
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/validate_static.py --report <fresh-attempt>/static.json
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/build_release.py --check
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe mod_li_yu_dao/tools/build_release.py --output <fresh-attempt>/mod_li_yu_dao
```

正式树只包含构建 allowlist：固定运行文件及两个限定的 `lyd_*.txt` helper 文件族。每份 manifest 冻结实际路径、大小与 SHA-256；ZIP 固定顺序、时间与权限。`tools/docs/tests/debug/fixtures` 排除，运行目录里的未知文件或测试命名文件拒绝构建。已有输出拒绝覆盖，重跑使用新的目录。

| 编号 | 检查 | 必须证明 | 不能证明 |
| --- | --- | --- | --- |
| L0-01 | Clausewitz 结构解析 | 全量运行脚本及 descriptor 能形成 AST；重复定义、非法顶层和未闭合结构报错 | CK3 原生 scope 类型、effect 的运行含义 |
| L0-02 | 本地化 | 中英文 UTF-8 BOM、语言头、键集合、重复键、插值一致；使用的 LYD 文案存在 | 实际 UI、翻译质量和字体显示 |
| L0-03 | 引用及入口 | LYD helper／faith／rite／事件引用闭合；decision effect 有玩家 guard；互动限制 actor；事件仅显式触发且有玩家入口调用路径 | NPC 响应链的实际 scope、原生 AI 行为、授权真实有效 |
| L0-04 | 可复现构建 | 同一输入的两次 manifest 与 ZIP 字节一致；测试夹具不泄漏；多余 staging 文件验签失败 | 生产游戏加载成功或 Workshop 发布 |

测试程序以临时 fixture 验证构建与校验器，不会修改正式 runtime。其 GREEN 只证明工具合同；正式产品源仍须单独通过 L0-01—04。

只读编排入口 `tools/run_acceptance.py --output <fresh-attempt>` 会保存每条命令的 argv、stdout／stderr 原始字节、退出码及哈希，并记录前后源码输入。它检查生成结果、产品静态与构建，也分别报告工具合同；不会启动 CK3、Steam 或 MCP 服务。`--preflight-only` 只记录环境。游戏路径可用 `--game-dir`／`--game-exe` 或 `XAR_CK3_GAME_DIR`／`XAR_CK3_EXE` 显式指定；每次冻结启动器版本、设置原文及 EXE SHA。

退出码 `0` 表示本次请求的 L0 检查通过或 preflight 准备就绪，`1` 表示 L0 失败，`2` 表示没有 L0 失败但 live 环境缺失，`3` 表示 runner 配置／基础设施错误。任何退出码下 live 都是 `NOT_RUN`。缺少 CK3 会话或当前版本 MCP 证据不把代码标为 RED；配置注册及旧 1.19 doctor 不证明端点可用。`--mcp-evidence` 只核对外置 tools/list 证据的当前版本、EXE 哈希及回执字节，不声称重新探测端点或验证产品能力；具体格式见 runner 的 `inspect_mcp` 文档。没有本产品 1.20 profile／fixture 时 Open Kaishek 明确记 `NOT_APPLICABLE`，不会使用历史默认 profile。

## Live 前的环境门禁

每次新 attempt 记录解释器、源码／staging／夹具／EXE SHA-256、游戏版本、DLC、mod加载顺序和存档。按仓库受管实机规则取得当次新鲜 Steam 离线画面、任务总线与屏幕独占及备份；不得拿旧截图或 1.19 实机证据代替本次条件。

2026-10-04只读环境调查：本机 Python 3.13.15 可用；`tools/.venv`、根 `.venv`、`ck3_autonomous_player/.venv` 未发现；当前工具会话及 Codex 配置没有可调用 CK3/operator MCP endpoint。`C:/workspace/open_kaishek`、`D:/workspace/open_kaishek`、`Z:/workspace/open_kaishek` 均未发现，因此当前 Open Kaishek 子集评估为 `NOT_APPLICABLE: checkout/JAR missing`，不能填 GREEN。`java` 在 PATH；缺口是工具 checkout／JAR 与相应已支持 profile。

仓库已有只读安装助手 [ck3_installation.py](../../tools/ck3_installation.py)、离线预验适配器 [kaishek_preflight.py](../../tools/kaishek_preflight.py)、桌面恢复 [desktop_steam_offline_recovery.py](../../tools/desktop_steam_offline_recovery.py) 及 [ck3_native_profile_mcp.py](../../tools/ck3_native_profile_mcp.py) 服务源码。既有产品 runner 可参考隔离 userdir、日志与回执流程，不能直接作为本产品完成证据；部分 runner 仍绑定其他产品或历史版本。当前没有《礼与道》专用实机 runner。

每项先判断 Open Kaishek 当前实际 CLI/profile 是否覆盖：未声明支持 faith/rite 重绑定、领袖生命周期和授权迁移时记 `UNSUPPORTED/NOT_APPLICABLE`，然后由 CK3 实机验证。不得虚构 profile 或把通用 parser GREEN当成分合语义 GREEN。环境缺依赖或 endpoint 是 environment RED，不是代码 RED；不得通过启动游戏或改 Steam 来伪造可用状态。

## 分轮产品验收

第一迭代声明玩家进入、选派与样板祭修。R0003 由普通非领袖玩家开始，独立存档已确认正式入门、取消修习与择师不改变人物块、择朱子礼仪以及一次朱子修习的实际费用、收益与冷却；这些只计代表路径通过。入门决议两条领袖条件缺本地化，整体 UI 仍为 RED；显示修正只有 L0 信用，待新冷载。自然冷却届满、存档重载、完整 8×3 修习和多人尚未执行。I2 正式分合已集成，运行状态仍 `NOT_RUN`；只绑定 R0002 原语准入，不能升级为流程通过。宗师、议定宗主与争统仍待 I3。详见 [R0003 报告](../../docs/li-yu-dao/2026-10-04-R0003-formal-representative-ui-red.md)。失败重跑使用新 attempt，旧证据不改写。

后续集成状态：I3 师承、宗主合议与政治争统、I4 的36派及修习已进入正式源码，实机均 `NOT_RUN`。原生 challenger 登记仍关闭，普通无宗主学统尚无转为世俗宗主制度的正式路径；不能把工厂存在写成全部玩家已可建立宗主。军会与圣物为 `NOT_IMPLEMENTED`，历史时代门禁留二期。

R0004 冷启动为 `RED`，未开战役：[永久报告](../../docs/li-yu-dao/acceptance/2026-10-04-R0004-cold-loading-red/REPORT.md)。发现不支持的教义接口与 quoted divergence 参数展开，以及外置 NPC 创建参数冲突。修复后的保守 Doctrine 集合比较和固定目标 scope 必须在新冷载、真实分合及存档重载中证明；结构 L0 无权豁免这些场景。

R0005 使用实际59生产文件及两套各7文件夹具，最终原生日志有4条I3 trigger错误；本轮没有此前R4对应错误。观察到大厅后游戏产生访问冲突崩溃，`normal_exit=false`，原因未证实。未进入战役、附加bridge或保存，正式流程继续 `NOT_RUN`；见[永久崩溃报告](../../docs/li-yu-dao/acceptance/2026-10-04-R0005-loading-crash-red/REPORT.md)。修复保留玩家与授权门禁，当前完整L0八项、102授权及11内容／领导检查通过；[正式静态报告](../../docs/li-yu-dao/2026-10-04-R0005-trigger-hotfix-l0.md)不替代新冷载。

| 轮次／编号 | 场景 | 必须观察的实际结果 | 必须保留的证据 |
| --- | --- | --- | --- |
| M0-01 | 新建／加载；简体中文与DLC组合 | 产品确实从本次 staging加载；简中UI无LYD解析、scope、重复定义或缺本地化错误；入口符合玩家/DLC条件；英文只进行L0结构检查 | 加载配置、staging manifest、启动日志、简中真实UI |
| M0-02 | A/B 两faith、两rite合流 | 来源rite父faith实际改为接收方；旧主流与特色按条款保留；人物及伯爵领一致；没有擅自政治独立 | 前后faith/rite及人物、领地状态；日志及存档 |
| M0-03 | 合流→自立→再合流 | 同一学统每步归属、改宗可用性、领袖及临时scope正确；没有一次性永久锁 | 每步原生状态与存档；冷却到期实际可再议 |
| M1-01 | 双向授权；无领袖 | 有宗主与临时大会均可发起/回应；派内认可、大会多数及逐rite授权分层生效；出资者不冒充全部代表 | 议案、参与范围、代表、各批准与最终对象 |
| M1-02 | 拒绝／过期／撤回／对象变化 | 未通过不迁移、不重复扣费；改条款或代表死亡重新授权；届期可重新提议 | 前后资源、归属及议案状态；时间推进证据 |
| M1-03 | 和平请立与旧宗主拒绝后自立 | 拒绝不永久锁死；合法支持范围能另立faith；新faith可有无领袖制度；政治领主关系不被意外改变 | 旧宗主回应、新faith定义与人物／领地状态 |
| M1-04 | 多rite；三项中两项同意 | 只迁授权范围；留存方有可持续主流与领袖；不同意者不被悄悄带走 | 完整rite名单、逐派授权、迁入及留存状态 |
| M1-05 | 同一全球rite的不同阵营／多国 | 先真实分支再局部迁移；否则保留原结构并明确失败；皇帝国礼决定不伪称全球授权 | 境内外正反双方、分支、人物与伯爵领前后对照 |
| M2-01 | 宗师争传／宗主争统 | 普通争传可留同faith/rite；只有同一最高职位竞争才形成争统；胜败不意外夺地或换政体 | 正式领袖、候选与支持关系、头衔、政体、土地 |
| M2-02 | 宗主／代表／候选／保护者死亡 | 已失效授权作废；继任、挑战者、代理人、空头衔与冷却正确；旧宗主不得未经认可顶替本派宗师 | 死亡前后及继任状态、议案状态、日志 |
| M2-03 | 保存重载与三轮循环 | 三轮合流／分立，跨两次继承和存档重载；换接收faith、动态faith及空旧faith均可处理；稳定学统仍存在 | 每个重载存档hash、人物/rite/faith绑定及历史 |
| M2-04 | 主流／最后rite；高偏离度 | 不留下非法旧faith；部分追随者先分支；原生自动分立如实保留；不循环后台吸回 | 主流、剩余rite、实际偏离度、自然推进与日志 |
| M2-05 | AI／NPC／多人玩家 | 新主动内容只能从玩家发起；NPC只能在限定议案链回应；受影响玩家能拒绝；共享被动影响如实记录 | AI对照、事件链起点与scope、多人选择、自然推进 |
| M3-01 | 军会／圣物／领袖绑定 | 各faith绑定对象依已审议策略保留、迁移或阻止操作；无悬空引用、重复组织或免费资产 | 绑定对象前后、征用资格、存档与日志 |

尚未实现的内容写 `NOT_IMPLEMENTED`，缺 live 环境写 `ENVIRONMENT_BLOCKED`，已执行失败写 `RED`。只有对应矩阵实际断言、日志与状态证据通过，才写该轮 `GREEN`；L0 不升级为 live。
