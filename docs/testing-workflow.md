# 实测工作流程（CK3 mod 调试）

## 启动与日志

```powershell
Start-Process "...\binaries\ck3.exe" -ArgumentList "-debug_mode"
```

日志目录 `Documents\Paradox Interactive\Crusader Kings III\logs\`：

- `error.log` — 解析错误（加载期）+ 运行时脚本错误（带调用栈和文件行号，**最有价值**）。累积式，按时间戳过滤
- `debug.log` — `debug_log` effect 的输出（jomini_effect_impl.cpp:450 前缀，带文件行号）
- `gui_warnings.log` — GUI 警告
- 解析错误在到主菜单前就会全部写入，启动游戏到主菜单即可完成静态验证

## 当前并行优先级与 `open_kaishek` 预验（2026-09-02 起）

当前验收调度按以下顺序执行：

1. **天朝二期（P0）**：在正式发布闭环前保持最高优先级，优先解除其真实 CK3/MCP blocker。
2. **G2 演进（P1）**：与天朝二期并行推进，不因等待另一条线而停工。
3. **`open_kaishek` 演进（支撑线）**：持续完善 `Z:\workspace\open_kaishek` 的伪 Runtime、profile、validator、IR 和 replay，作为上述两条线的验收加速器；支撑线不得抢占正在运行的有效 CK3 长局。

### CK3 验收前置顺序

每个 CK3 验收步骤（包括静态/fixture 检查、paused snapshot、启动、MCP 动作和后置断言）在启动游戏或桌面交互前，都必须先做一次“是否可由 `open_kaishek` 预验”的判断：

1. 把本步骤拆成确定性输入、解析/schema、IR/runtime/replay 子集与只能由真实 CK3 证明的部分。
2. 对 `open_kaishek` 已声明支持的子集，使用其仓库 README/对应 profile 的实际离线命令先行预验；不得凭空发明尚未暴露的 CLI 能力。预验通过后再执行现有的 CK3 no-launch/native preflight 和 live 流程。
3. 将预验结果与同一验收 run 绑定，至少记录：`open_kaishek` Git commit、profile/version、CK3 exact build 与 EXE SHA-256、fixture/corpus ID 与 SHA-256、实际命令/解释器、结果、覆盖范围以及 `UNSUPPORTED` 项。推荐写入该 run 的 `open_kaishek-preflight.json` 或等价 machine-readable artifact，并在报告中回链。
4. 若该步骤没有可覆盖的离线语义，记录 `not-applicable` 和原因后直接进入 CK3；不为形式重复执行已由相同 immutable inputs 证明的预验。若预验出现 RED，先保留原始输出并区分 `open_kaishek` 工具/fixture RED 与 CK3 capability RED，不得把任一结果改写成另一类。

`open_kaishek` 预验只缩短确定性失败的反馈周期，不替代真实 CK3/MCP paused artifact、真实输入/动作、自然推进、结算或 GREEN。没有 paused artifact 时，状态仍只能写为 `static-ready`/`runtime-fixture` 等实际级别；ACK、schema 通过和 synthetic replay 都不能升级为 `fixture-live` 或 `production-live`。

## 可复用宣传视频工具链验收

权威入口是独立仓库
[`XenoAmess/xar_promo_toolchain`](https://github.com/XenoAmess/xar_promo_toolchain) 的 `README.md` 与
`docs/architecture-and-migration.md`。本仓库不再包含工具链源码；公开命令必须以当前
`<verified-python> -m xar_promo --help` 及各子命令 `--help` 的实际输出为准；library 中存在函数或 handler 不代表 CLI 已暴露该能力。

### 当前冻结 CLI（`xar-promo 0.1.0`）

下表按 2026-09-01 实际 `--help` 记录；尖括号表示由项目提供的路径、ID 或 import target，不是可照抄的字面值。

| 命令 | 实际调用形态 | 验收含义 / 副作用 |
| --- | --- | --- |
| `init` | `init <project-directory> [--project-id <id>] [--title <title>] [--adapter <id>] [--preset <id>] [--run-id <id>] [--narration-locale <locale>] [--subtitle-locale <locale>]...` | 新建 config 和首个 run；不覆盖已有文件。 |
| `start-run` | `start-run [project-config] --run-id <id> [--run-directory <dir>]` | 为当前 config 精确字节新建独立 run 与 snapshot。 |
| `validate` | `validate [document] [--profile authoring|release] [--structure-only] [--json]` | 只读；普通模式核对引用文件 bytes/SHA，`--structure-only` 不核对，故不能代替 release 验证。 |
| `preserve` | `preserve <source> [--run-manifest <run>] --artifact-id <id> --collection raw|derived --role <role> [--label <label>] [--media-type <type>]` | content-addressed 复制后 append artifact 记录；不应移动或覆盖源。 |
| `signoff` | `signoff [--run-manifest <run>] --artifact-id <id> --reviewer <name> --decision approved|rejected [--note <text>] [--reviewed-at <timestamp>]` | append 人工决定；操作者必须先完成同一 bytes 的 1× 全片审阅。 |
| `plan` | `plan <project-config-or-run> --workdir <fresh-attempt-path> --composer <module>:<attribute> [--validate-only]` | 始终只读：不创建 workdir、不调用 provider、不 append run；flag 只显式重申该合同。 |
| `build` | `build <run-manifest> --workdir <fresh-attempt-dir> --composer <module>:<attribute> [--offline-tts] [--max-tts-attempts <n>] [--retry-backoff-seconds <seconds>]` | 执行 composer；GREEN/RED 均把已生成 artifact、partial、stdio 与 phase 记录保全到 run。 |
| `audit` | `audit <run-manifest> --subject-artifact-id <id> --evidence-bundle <path> --report <path> --report-artifact-id <id> [--created-at-utc <timestamp>]` | 写并保全自动报告及输入证据；结果明确不包含人工 approval。 |
| `review` | `review <deliverable> --storyboard <timeline.json> --probe <bound-probe.json> --output-directory <dir> --audit-directory <dir> --ffmpeg <exe> [--working-directory <dir>] [--plan-only]` | `--probe` 必须是与成片 bytes/SHA-256 绑定的 `xar-promo-bound-media-probe` v1 envelope；`--plan-only` 不写，执行模式只生成 pending review package 和抽帧素材，不 signoff。 |
| `export` | `export <run-manifest> <destination> --policy <policy.json> [--dry-run | --validate-only]` | 默认仅生成离线 bundle；两个检查模式不创建 destination；都不联网、不发布。 |

`plan`/`build` 的 `--composer` 必须解析为项目提供的 callable `MODULE:ATTRIBUTE`；它与 manifest 中 adapter/preset ID
是不同接口。adapter/preset 只从本地 registry 注入或 `xar_promo.adapters`、`xar_promo.presets` entry points 解析，
不得把 composer 塞进 registry，也不得虚构一个通用默认 composer。

先安装独立仓库的冻结 wheel，再用选定且已验证的解释器做无副作用 CLI smoke。仓库提供
`tools/requirements-promo-toolchain.txt`，默认指向 GitHub Release `v0.1.0`；离线或本地源码验收时，
可设置 `XAR_PROMO_SOURCE`（兼容别名 `XAR_PROMO_TOOLCHAIN_SOURCE`）指向独立 checkout 或其 `src` 目录，
以覆盖已安装 wheel：

```powershell
$PromoPython = (Resolve-Path "tools\.venv\Scripts\python.exe").Path
& $PromoPython -m pip install -r tools\requirements-promo-toolchain.txt
# Optional source-checkout override (do not set this for a wheel-only run):
# $env:XAR_PROMO_SOURCE = "Z:\workspace\xar_promo_toolchain"
& $PromoPython -m xar_promo --version
& $PromoPython -m xar_promo --help
$PromoCommands = @("init", "start-run", "validate", "preserve", "signoff", "plan", "build", "audit", "review", "export")
foreach ($PromoCommand in $PromoCommands) {
    & $PromoPython -m xar_promo $PromoCommand --help
    if ($LASTEXITCODE -ne 0) { throw "xar-promo help RED: $PromoCommand" }
}
```

这里的 `$PromoPython` 必须先按本节末尾的 venv 规则解析；secondary worktree 不得临时把它替换成裸 `py`。

### 分层与证据流

宣传生产固定为四层：

1. 独立仓库 `src/xar_promo/` 通用包管理 `ProjectConfig`、每个 attempt 的 `RunManifest`、配置快照、不可变素材、TTS、字幕/布局、
   媒体探测、进程执行与审计原语。
2. 独立仓库 `codex-skill/promo-video-pipeline/` 只指导编排和检查，不是执行器，也不提供隐含权限。
3. 独立仓库 `src/xar_promo/adapters/ck3/` 只读验证 CK3 runner 已产出的 hash-bound capture bundle；它不启动游戏、不解释 OCR、
   不删除失败素材，也不决定某个 mod 的宣传主张是否充分。
4. 独立仓库 `src/xar_promo/presets/` 与项目 config 承载项目独有的章节、声线、语言、时长、角色来源、画面洁净和发布门禁；
   legacy wrapper 在完成 parity 迁移前仍是各项目生产入口。

标准证据流为：审阅 checked-in config → 为本次尝试创建新 run 并冻结 config snapshot → 取得/验证 raw source →
只读规划 → 在新 workdir 构建 → 自动媒体/字幕/内容 audit → 生成 pending human-review package → 人工按 1× 完整观看 →
对精确成片 bytes/SHA-256 记录 signoff → 生成离线发布 bundle。任一步 RED 都保留原 attempt；下一次从新 run/workdir 开始，
不得修改旧报告来“转绿”。

### 过程素材保留

每次 attempt 都必须保留并纳入可核验索引：

- raw 录像、截图、配音输入/输出、字幕源、项目 config 及 run-local snapshot；
- clean spans、timeline、probe、evidence index、OCR/抽帧等外部 producer 的原始输出及其 bytes/SHA-256；
- 生成卡、章节段、concat manifest、ASS、intermediate、partial、失败输出和最终 deliverable；
- 每条外部命令的 argv/cwd、`stdout.txt`、`stderr.txt`、result、返回码与 partial 清单；
- manifest preimage、phase/audit history、sidecar、自动 audit、pending review package、人工 signoff 与离线 export manifest。

工具只允许新增或 content-addressed 复用相同字节，不得移动、截断、覆盖源素材。失败命令的 stdio、partial 和已完成阶段同样是
诊断证据，不能因为最终命令返回非零而清理。大体积文件可以不进 Git，但必须保留稳定路径、bytes、SHA-256 和对应 run ID。

### 自动审计、人工审阅与发布边界

- 自动 audit 只能证明其采样计划、媒体属性、字幕布局、项目规则和证据绑定；抽帧全绿不等于整片逐秒看过。
- review package/template 的状态只能是 pending human review；生成 review material 不得自动写 approval。
- 人工 signoff 的前置是审阅人对**同一精确文件**按 1× 从头到尾完整观看。记录至少包含 reviewer、decision、reviewed_at、
  说明以及 deliverable 的 bytes/SHA-256。重新编码、补字幕或任何字节变化都要求重新完整审阅和新 signoff。
- 通用 `release` profile 或离线 export 只证明工具链内部候选条件，不发布 Steam/视频平台，也不替代项目验收。
  各 mod 继续执行自己的 release projection、实机 CK3 矩阵、Workshop 上传/缓存复核和永久 changelog 流程。

### secondary worktree 的 Python/venv 规则

依赖型命令开始前先解析解释器，不能等 import 失败后静默换解释器：

主仓 `tools/requirements.txt` 与 `tools/requirements-static.txt` 不再间接安装宣传工具链。准备全自动或静态验收环境后，
必须用同一解释器显式执行 `-m pip install -r tools/requirements-promo-toolchain.txt`；该文件固定独立仓库的 GitHub
Release wheel。需要源码调试时，再设置 `XAR_PROMO_SOURCE`（或兼容别名）覆盖 wheel。

1. 优先检查当前 worktree 约定的相对 venv（本仓库 runner 通常是 `tools\.venv\Scripts\python.exe`）。
2. secondary/detached worktree 没有该 venv 时，显式填写已经在主 worktree 验证过的 venv **绝对路径**；禁止直接落回 `py`。
3. 使用主 venv 时，默认使用已安装的独立 wheel；若需源码调试，把 `XAR_PROMO_SOURCE` 显式设为当前独立
   secondary checkout（或其 `src` 目录），防止测试到旧 editable install 或旧 wheel。
4. preflight 记录解释器绝对路径、Python 版本，并按任务验证依赖：core 至少能 import `xar_promo`；TTS 路径验证
   `edge-tts 7.2.8`；visual/render 路径验证 `Pillow 12.3.0`；实际媒体命令另验证所指定的 ffmpeg/ffprobe。
5. preflight 未闭合时结论是 environment RED。只有已证明使用目标源码和正确依赖后出现的可复现失败，才可归类 code/capability RED。

禁止用“系统 `py` 能启动”替代上述检查，也禁止在 secondary worktree 自动创建、覆盖或升级主 venv。需要改依赖时回到拥有该 venv
的主 worktree 按项目依赖合同处理；secondary 只显式借用已验证解释器。

## 全自动验收 runner（tools/run_acceptance.py）

runner 共用同一套现场备份恢复、静态校验、工坊同步和 OCR 大厅导航。`selftest`、`persistence-restart`、`death-edges`、`death-with-heir`、`bargain-reopen`、`progression-ui`、`scoring-matrix`、`courtier-creator`、`balance-long` 加载开发树；四个生产 smoke 会先生成 production-only release 投影，再将该投影 `/MIR` 到工坊缓存后启动 CK3。

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-first-life
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-recorded
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-high-budget
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario off
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario persistence-restart
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario death-edges
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario death-with-heir
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario bargain-reopen
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario progression-ui
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario scoring-matrix
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario courtier-creator
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario balance-long --balance-fixture count
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_balance_matrix.py"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_terminal_acceptance.py" --mode observer
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_terminal_acceptance.py" --mode ironman
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_vivhite_acceptance.py"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_vivhite_acceptance.py" --scenario vivhite-alone
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_vivhite_acceptance.py" --scenario original-then-vivhite
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_vivhite_acceptance.py" --scenario vivhite-then-original
```

原 mod 场景基线与边界：

- `selftest`：默认场景，保持原有完整死亡/计分/UI 全链；只有此场景读取 `--import-record 0|100`。
- `on-first-life`：固定 `xar_on` + 纪录 0，真实接受契约，OCR 验证 `xar.0010` 的「未燃之世」及「前世余烬」「余烬位阶」，再进入祝福窗口即结束，不触发死亡。
- `on-recorded`：固定 `xar_on` + 纪录 100，真实接受契约，验证生产商店（优先补充 100 点 OCR 证据；标题与 `shop event fired` 同时证明非首世分流），不购买商品，直接开始此生并进入祝福。
- `on-high-budget`：固定 `xar_on` + 纪录 2000，在默认成长 + 100% 下 OCR 确认 2000 预算，翻到第四页真实购买 250 分恐怖值和 500 分正统性服务，返回第三页购买 1133 分宗教改革，断言余额 117、一次性选项消失，再进入祝福。
- `off`：固定 `xar_off` + 纪录 0，进局后观察 30 秒；契约标题或本次新增的任意 `XAR:` 启用日志均判 RED。
- `persistence-restart`：一次外层备份内启动两个 CK3 进程。A 从纪录 0 跑完整 selftest 并真实写入非零 lesson，进程树完全退出后固定 handoff SHA-256；B 不调用纪录预置函数，以新日志 offset 断言 importer 精确命中 A 的位阶及 request/ready/consumed 全链。该场景禁止非零 `--import-record`。
- `death-edges`：固定 selftest + 导入位 1，真实杀死带 `xa_enabled` 的 AI Roger，断言生产计分被 `is_ai=no` 阻断；再逐日使当前继承人失去继承资格，直到 `player_heir` 不存在后真实杀死玩家，验证前向提交链、原生继承窗内的八值结算、无“继续扮演”、退出确认和返回主菜单。随机原生事件会由 recovery 点击底部选项后继续日 tick。
- `death-with-heir`：固定 selftest + 导入位 5，在确认玩家存活、启用且确有 AI 继承人后，以 acceptance-only 心脏事件触发普通玩家死亡。runner 必须精确点击原生「继续扮演」，确认控制权已转移给人类继承人，再等待生产计分/分流/可见结算各恰好一次。2026-08-20 共同 AI 闸门 post-review 复验 GREEN：`xar_death_with_heir_postreview_20260820`。
- `bargain-reopen`：固定 selftest + 导入位 2，但不进入主 selftest。独立 bootstrap 调用生产契约/运行初始化，并用 release 会整文件剥离的 acceptance-only `immortal` 固定九年观察体存活；随后真实点击三轮 `xar.0004` 祝福与 `xar.0005` 咒痕。安全 wire id 只由 acceptance instrumentation 固定，祝福/诅咒仍走生产 dispatcher。每轮成交后保留生产 option 的 `xar.0006 days = 1095`，另设仅观察状态的 day-1094 probe；脚本保存成交时的 `current_date` 并在两条路径相减，断言累计对数 1/2/3、session 在祝福后为 1 且 `xar.0006` 重置为 0、XP `0→1→2→3`、拒绝数 0、1094 日不重开、1095 日精确重开及第三对后的完整新窗口。runner 用鼠标选择速度 5，并以底栏渲染日期 OCR 判断游戏是否仍在推进；debug marker 只负责机制断言，合成键盘不参与。
- `progression-ui`：固定 selftest + 导入位 3，通过玩家限定 acceptance 编排依次调用生产贤王契约进度 effect，真实点击 3/6/10 三个生产里程碑事件；随后调用两次生产成交 effect 达到【琉焰之视】10 XP 并点击其生产里程碑事件。runner 要求 `tutorial.txt` 精确稳定为该契约的 PB 3/6/10 与完成四个 lesson，再从原生决议打开账簿，同帧 OCR 确认当前 `0/10`、历史 `PB 10`、贤王图鉴、`R 1` 与 `S 0`。该场景不伪造 PB、图鉴或里程碑状态，acceptance 只负责安全地产生生产入口所需的玩家行为。
- `scoring-matrix`：固定 selftest + 导入位 4，先保存历史角色的生产计分与只读 preview 基线，再创建受控谱系：同一后代经兄妹两条路径可达、另一支穿过已故第一代延伸到第五代，并额外创建第六代排除项。跨事件边界后要求新增宗族/家族计数恰为 7、头衔桶不变、临时去重 flag 全清、preview 增量为 1.4 且与生产总分误差不超过 0.01。随后 200 个 wire ID 逐一调用生产 apply dispatcher；每个实际命中的分支自行写 marker，下一事件再断言 100 次祝福计数、代表修正、最终稀有度和 100 XP 已提交。
- `courtier-creator`：固定 selftest + 导入位 6，从带琉焰图标的【琉焰卿的永恒轮回】原生决议分组真实打开七页契页，并依次打开账簿、契约、廷臣三张原生详情图取证。随后验证取消零副作用、119 金确认禁用、默认 120 金成交、年龄/六维步进、五类生成 trait 目录、动态文化/信仰、同家族、348 金配置关窗重开保留、第二次实际角色交付与 AI 拒绝。runner 对文化只点击缩进子项，对信仰等待选择 effect marker；选择阿卢克古道后必须返回【心性】，分别从【勤勉】与【懒惰】原生 tooltip 读到该信仰的美德与罪恶，且两者均不得出现天主教。创建角色必须同时不同于玩家文化与信仰。2026-08-21 权威定向报告：`xar_decision_group_trait_both_20260821`，三图、美德/罪恶上下文、两次购买与 AI 闸门 GREEN，0 `xar` errors。
- `balance-long`：必须指定 `--balance-fixture count|king|emperor|synthetic`。runner 把原版 81 个规则全部重建为当前 1.19.0.6 声明的默认值，追加 `xar_on`、成长 + 100% 和仅开发夹具；大厅仍走已验证的罗贝尔路径，生产初始化前再切换到史实奥塔/腓力一世/亨利四世或脚本标准化奥塔替身。固定选择第一项祝福与咒痕，不做 CK3 战略操作；逐对采样生产分数，30 年后允许自然死亡，否则在 40 年右删失。生产链在 dying root 有效时先保存 `scope:xar_dead` 并向 `player_heir` 排入 `delayed = yes` event，再内联计算；carrier 随后交付 record、settlement 和 kind 4 terminal wire。继承窗只走专用 OCR 路径；不把新统治者继续当作同一寿命采样。GREEN 只证明夹具、逐笔 1095 日节奏、被动策略、结构化采样和零 `xar` 错误，完整边界见 `docs/balance-test-protocol.md`。
- `run_terminal_acceptance.py --mode observer|ironman`：以非 debug CK3、禁用云存档和仓库外一次性 `-userdir` 运行开发验收夹具。observer 要求结算后出现原生【正在观察】；Ironman 要求 modal 强制暂停、原生暂停菜单可打开、点击继续后重新阻断、原生保存确认、返回主菜单、同一进程内重载同一存档后再次阻断。包装器在运行前后逐文件比较真实 Documents 的教程/规则/启用项/设置及全部 `*.ck3` 存档，以及本地 Steam `userdata/*/1158310` 后备目录；两组都必须在退出后的五秒观察窗保持基线聚合哈希。远端 Steam 服务不在此证明范围内。仅当场景与后置检查均 GREEN 时才删除隔离 userdir，再把实际删除结果写入报告。
- 自主玩家 Phase A 的 non-debug 实机 smoke 在 2026-08-22 发现当前 Steam 客户端会在部分直启退出后改写 `userdata/<account>/1158310/remotecache.vdf` 的顶层 `ChangeNumber`，稳定运行也会刷新该文件 mtime；真实 Documents 和云存档条目未变。自主玩家不回写或恢复真实文件，而是把 `ChangeNumber`/mtime 作为 Steam 自有易变元数据单列 before/after，比较时只规范化该整数并对其余字节做 SHA-256。任何云存档条目字段或其他 userdata 文件差异仍判 RED。该白名单是 1.19.0.6 + 当前 Steam 客户端的实测边界，不应悄悄放宽既有 terminal acceptance 的历史验收口径。
- 同轮 fresh-log 实测还表明：`cloud_save=no` 只禁止本局写云档，并不阻止 CK3 前端枚举已有 Steam Cloud 存档 meta。隔离 profile 的正常存档为零，production tree/原版文件均无 PoD 引用；但 cloud meta 中的 17 个旧 PoD 规则 key 与两张 PoD 贴图引用和 `error.log` 逐项匹配。与此同时 enabled inventory 精确只有【琉焰卿的永恒轮回】，全部 mount 只来自已安装 DLC 或隔离 production tree。因此这些报错是旧云档前端元数据，不是第二个 mod 被加载。自主玩家 isolation smoke 必须归档非空 error log，并写入 `clean_engine_boot_required=false` 与 `engine_diagnostics.zero_diagnostics=false`；其 GREEN 只证明单 mod 隔离和可见主菜单，不得表述为零引擎错误。该来源判断有内容全匹配、零隔离存档与 mount 反证，置信度高；尚未用 ProcMon/ETW 做因果 I/O 跟踪。
- 自主玩家 Phase A 的正式退出证据为提交 `11ab443050132341bb27f6f924d792772f397396` 在同一环境指纹下的三次连续 GREEN：`20260821T180045Z-a3c49b20`、`20260821T180248Z-7ad2dd83`、`20260821T180531Z-9c6bb34b`。三份历史 format v1 `events.jsonl` 与最终 `report.json` 均已用当时的 `validate_smoke_report()` 重新计算 hash chain 并做一致性校验，语义硬条件另行逐字段断言；每次都满足两帧可见【新游戏】、精确单项 enabled inventory、唯一隔离 production mount、零未知 mount、退出后二次日志解析、Job 成员 1→0、双源 CK3 inventory 为空、watchdog/控制文件消失和 production tree 不变。真实 profile 与 Steam userdata 回到 baseline 后连续稳定 5 秒；Workshop descriptor 内容哈希与目标树路径/大小/mtime 只做退出后一次 baseline 比较。该三连由 supervisor 终止 CK3，不证明 graceful exit，也不是有效得分局；完整边界见 `docs/autonomous-player-phase-a-evidence.md`。
- 自主玩家的 post-resume 崩溃门禁使用 `agent.py crash-smoke`，不能复用普通 `smoke` 的 `finally` 来模拟。外层 verifier 持有 state/launch mutex 和 protected baseline；subject 先发布完整身份与命令契约的 ready，outer 验证后固定真实 supervisor 进程句柄并写 ack，subject 必须验证 ack 后才可创建 CK3。ready、ack、armed 都写 UTC 与 Windows 同机跨进程可比的 monotonic 时间；UTC 必须可解析且为零偏移，实时路径强制 monotonic 严格满足 `ready < ack < armed`，无密钥回放只验证归档记录值与字段关系自洽。随后 subject 创建 suspended CK3、先加入 nonce 命名的 kill-on-close Job 再 resume，并把两个 Python 父子 sentinel 加入同一 Job；detached watchdog 只等待 subject。外层固定 supervisor、CK3、两个 sentinel 和 watchdog 的精确进程句柄，只对 supervisor 句柄注入退出码 77，且不得持有 Job handle。只有四个 Job 相关句柄均退出、命名 Job 已销毁、watchdog 句柄退出码为 0、四类控制文件消失、全局 CK3 双源清点连续 5 秒为空，才能设置 `cleanup_proven=true` 并开始 protected postflight。普通可捕获失败必须 finalize 为 RED；`KeyboardInterrupt`/`SystemExit` 等外部异步中断仍先执行句柄清理，但可留下 `finalized=false` 的 provisional，不能作为任何验收证据，若清理未获证明则 unsafe marker 与全局进程清点继续阻断下一次启动。
- crash run 的 artifact 层必须在同一 validator、仓库代码与 OCR runtime 下可自包含回放：两张连续的 2560×1440 PNG、完整 OCR bbox、运行时日志前缀、DLC mount 冻结白名单、owner/handoff、supervisor ready/ack、armed、三份 crash 前控制文件、watchdog final、environment 与 production manifest、protected before 都以 run-relative path + SHA-256 入 manifest；protected after 只在 cleanup 已证明且获准执行 postflight 时存在。运行期绝对路径仅与报告记录的原执行目录绑定。复制整个 `runs/<run-id>` 后，validator 从副本读 artifact，不再实时扫描原游戏 DLC 目录，并从 PNG 重跑同一 OCR 以绑定像素与【新游戏】文本；这不是跨机或脱离当前仓库/OCR adapter 的自包含格式。GREEN 与任何声称 cleanup 成功的 RED 共用同一清理语义验证函数和完整五事件序列，但 validator 尚未逐项把每个 event payload 的全部语义与 report/artifact 交叉绑定。若 storage postflight 已成功但随后 profile/tree 复核失败，RED 可保存这段局部成功证据，但不得声称 production tree 已验证。该报告固定记录 `integrity=unkeyed_sha256`、`claim=archive_schema_and_internal_consistency_only`、`historical_execution_authenticity_proven=false`；无密钥链不是数字签名，复制后的归档不能独立证明历史执行真实性。
- 2026-08-22 首次本机 `crash-smoke`（`20260821T201701Z-crash-9708619d`）在创建 CK3 前按预期 RED：`tools\.venv\Scripts\python.exe` 在本机不是透明替换，而是保留一个 venv redirector，再由它启动基础解释器中的真实 subject，进程链为 `outer → redirector → subject`；把 `Popen.pid` 当 subject PID 会误判“不是直接子进程”。独立休眠探针进一步实测：redirector 的 `ExecutablePath` 与命令行 `argv[0]` 都是 venv launcher，而真实 subject 的 `ExecutablePath` 是基础解释器、`argv[0]` 仍保留 venv launcher。崩溃门禁因此只接受 `outer → subject` 或恰好一层 `outer → authenticated redirector → subject`，分别绑定两段 PID/父 PID/创建时间/映像，并对两进程解析同一套完整隐藏入口 argv；两跳仅允许真实 subject 的映像与 launcher argv0 按该实测关系分离。subject 先发布 nonce 绑定的 ready，outer 认证并固定真实 supervisor 句柄后回写 acknowledgement；ack 到达前禁止启动 CK3。armed/report 另存 redirector 身份与退出码，watchdog、sentinel、注入句柄和 `subject_pid` 始终绑定真实 subject，禁止任意祖先搜索。该 RED 只定位启动器语义，不能算崩溃回收通过；后续 GREEN 见下。
- 同日第二次本机 `crash-smoke`（`20260821T211059Z-crash-833b9587`，环境 SHA-256 `64fa69124f341dfcae6ffc7422ca7b07ec1d9b0e82373c7453c7fe49368994a2`）已通过两帧可见主菜单、单 mod load、四个 Job 相关 pinned handle 退出和命名 Job 销毁，但 detached watchdog 与 Job teardown 竞态中对同一已认证 CK3 handle 调用 `TerminateProcess` 得到 `ERROR_ACCESS_DENIED`。旧实现异常后只等待 1 秒，因此 watchdog 正确返回非零，outer 将运行 finalize 为 `cleanup_proven=false` / `unsafe_cleanup=true` 的 RED，禁止 protected postflight，并保留 record、ready、watchdog error 与 unsafe marker；稍后的当前态清点为空不能回写该历史结论。修订把正常终止、WMI 行先消失和 `TerminateProcess` 异常三条路径统一为最多 20 秒的同一 pinned-handle 排空，只接受 handle signaled；fallback 和五秒稳定空窗使用独立预算，outer 最多等待 watchdog 90 秒。非零 watchdog 结果还必须归档并绑定结构化 failure、final/error 原文和 control-before，unsafe RED 的搬移回放不能删改这些诊断后仍通过。
- 陈旧 crash control 绝不由 `prepare-profile`、`smoke` 或下一次启动自动删除。只能显式执行 `agent.py recover-stale-control --run-id <finalized-RED-run-id>`：在 state/launch 双锁内验证 source report 与归档哈希、环境和 game exe、record/ready/marker nonce、所有记录 identity 当前不存在、命名 Job 不存在、双源 CK3 清点稳定为空；成功 report 先以“active marker 已消失且 marker 归档哈希匹配”为完成条件写前日志，再做末次即时 inventory、末次 Job absence，最后用 nonce+哈希 CAS 归档 unsafe marker。该 CAS 是最后一次 recovery 证据/控制提交，之后不再写 recovery report/artifact；锁实现仍可清理自己的 owner 文件。write-ahead report 可在 CAS 前已含条件式 `ok=true`，单看该字段不算成功，必须由 `validate_recovery_report()` 同时观察 active marker absent 与归档 marker SHA-256 匹配。旧事故的外置 watchdog-final 不受源 report manifest 绑定，恢复证据必须明确 `source_report_bound=false`，不能把它当成历史 cleanup 证明。恢复另建 report，声明 `historical_cleanup_proven=false`、`current_absence_proven=true`，源 crash RED 永不修改或升级；任一未知、漂移或中途失败都保留/恢复 marker 并 RED。旧 RED `20260821T211059Z-crash-833b9587` 已由 `20260821T215805Z-recovery-46a3518c` 显式恢复并经 `validate_recovery_report()` 重放通过；源 report SHA-256 仍为 `eb429f5513f6610b433ee0349e571cd4f4fd8278cb666fbfc58c01896aa6a68f`，四份 control 原哈希归档且 active 路径消失。该恢复只解除阻塞，不改变旧 RED。
- runtime 实现提交 `98d55caf3ed4a398b0a3bd7bc8e6ee16591d8f26` 在环境 SHA-256 `5e7fb63ef98a7fd802caa864b64c593053c68bfb5f1798321cde6b02d6cd0d5f` 下完成本轮资格：普通 `smoke` `20260821T215910Z-780cd6cb` 与 post-resume `crash-smoke` `20260821T220127Z-crash-adc0ac63` 均 finalized GREEN。该历史 normal 是 format v1：`validate_smoke_report()` 只复算其无密钥事件链、final tail 与 finalized/ok，下面的 load/cleanup/protected/production 硬字段另行逐项断言；`validate_crash_report()` 重放 crash 归档的完整 schema 与内部一致性。两次都是 non-debug、两帧可见【新游戏】、enabled inventory 精确单项本 mod、唯一隔离 production mount、零未知 mount；crash run 中真实 supervisor 精确句柄退出码 77，CK3 与两个 sentinel 所在命名 Job 销毁，四个 pinned handle 退出，watchdog 返回 0，四类 control 消失，双源 CK3 连续 5 秒为空，之后 protected postflight 与 production tree 复核通过。两份都没有作出游戏内玩法选择、`valid_score_episode=false`，不证明规则页已视觉确认 Growth+100，也不是有效得分局；ordinary/crash 的旧主菜单观察器可能发送合成 Alt 获取前台，不能将其称作全程零输入证明。
- Phase B 的 `agent.py menu-smoke --timeout 180` 是独立 sealed lifecycle，不复用 acceptance 的导航或普通 smoke 的 OCR 聚焦副作用。命令在启动 CK3 前必须从当前 state 中找到同一 environment、时间有序的 self-contained format v2 ordinary GREEN 与 post-resume crash GREEN，完整重放后复制进本次 run；当前 runtime 一旦改变，旧资格自动失效。场景能力精确只有 `main_menu.new_game`，大厅 `bookmark_lobby.start_game` 必须保持 forbidden；fresh frame 后、任何鼠标移动前向主 `events.jsonl` fsync `ui_input_armed`，最终只允许一次 `SendInput(LEFTDOWN+LEFTUP)` 批次。GREEN 必须看到两帧稳定书签页，RED 必须保留实际 receipt/WAL 前缀并仍走受控清理。无害 Win32 helper 已实测 96 DPI、client/screen 换算、前台/Z-order/180×120 topmost 遮挡、WMI 空 `ExecutablePath` 的 pinned-handle 信任和两记录输入；桌面枚举中可见的 `(0,0,1,1)` ghost HWND 仅在宽高都不超过 1 时忽略，最终点击点仍须由 `WindowFromPoint` 精确命中。Windows foreground-lock 偶发拒绝 helper overlay 抢焦点时，夹具只记录实际前台结果，但独立 Z-order 遮挡反证仍必须拒绝目标像素。该 helper 不等于 CK3 实机输入；在提交、重新 prepare 并取得同环境两项资格前禁止运行 menu smoke。
- 2026-08-22 的第一次真实菜单竖切以提交 `226d80e`、环境 `219c77d9d5e8b7e50e32314f2f8fcb57130fedc3c853880677e4149c425556ba`、ordinary `20260822T005515Z-03f296c7` 与 crash `20260822T005727Z-crash-38023ffc` 资格运行。`20260822T010001Z-menu-193c8062` 在任何 `ui_*` WAL、action receipt、鼠标移动或 `SendInput` 前因 CK3 失去前台而安全 RED；tracked cleanup、全局 CK3 空清点和 protected/production postflight 均完成。该不可变报告同时实测到 COM WMI 的 DMTF 创建时间 `20260822090033.870978+480` 与 PowerShell CIM UTC ISO `2026-08-22T01:00:33.8709780Z` 表示同一进程时刻，且 29 个 DLC mount 按引擎日志顺序而非字典序出现。回放器现严格解析两种时间后比较 UTC，并保留 DLC engine order、要求绝对白名单成员和不重复；旧 RED 已可原样回放但仍是 RED。后续前台协议在唯一窗口绑定后先 fsync `foreground_activation_planned/armed`，只允许一次 direct `SetForegroundWindow` 与至多一次 caller→当前 foreground thread 的严格 attach/detach fallback，detach 或身份未知时不重试；成功才写 finished attestation。`GetLastInputInfo` 相等只记录采样值未变，不证明无人输入。该修订改变 runtime，旧两项资格不能用于下一次菜单尝试。
- 提交 `af3df58` 在环境 `31e68f6d8e439643a7ff8fcb6029d72f93a85ead2d74bb58d24042c382753f72` 下重新取得 ordinary `20260822T020912Z-7dc8269d` 与 crash `20260822T021144Z-crash-b010d18c` 两项 GREEN。唯一一次后续菜单 run `20260822T021436Z-menu-c9b3d667` 在稳定主菜单观察前因客户区被外部置顶窗口 `(2130,1095)-(2560,1392)` 遮挡而安全 RED。公开回放确认无 `visible_main_menu_attested`、`ui_*`、receipt、鼠标或 `SendInput`，tracked cleanup、双源空清点与 protected/production postflight 完整。事后只读活体查询把 HWND 定位为 Kaspersky `avpui.exe` 的 WPF `AlertWindow`，但原 run 只绑定 HWND/矩形，产品身份不是历史归档证明。自主玩家不自动关闭安全软件通知；外部窗口须由用户自行处理，原 run/候选不得重试。
- 后续 ordinary producer/report 已升级到 format v2：两帧 PNG/OCR、initial/final debug 前缀、load、diagnostics、精确 process/pre-resume/shutdown、protected、production 与完整 artifact inventory 全部使用 run-relative 引用，公开 `validate_smoke_report()` 从归档字节重跑 OCR、日志解析和硬条件，并支持搬移后删除源目录。最终 event 先以 report-body hash 写入并 fsync；最终 report 用同目录临时文件先 flush/fsync，再 atomic replace provisional。live 菜单资格和新 archive 只接受 v2 normal；v1 仅允许外层为历史 RED、且没有任何 `ui_*` 输入 WAL、bookmark、navigation、action/receipt 的菜单档只读回放；纯观察 PNG/JSON 可以保留，但永不授权输入。无密钥 SHA-256 仍只证明 archive schema 与内部一致性，不证明历史执行真实性。该升级改变 runtime 指纹，因此 `af3df58` 的 ordinary/crash 资格只保留为历史证据，下一次尝试必须在新提交与新 environment 下重新取得两项资格。
- 提交 `38fd5fa` 在环境 `75f8c6b0271d82183ba2d345a48e4a191e36ea2fd85d98b9a8d30327ce6c7367` 下取得 ordinary v2 `20260822T033531Z-9a595275` 与 crash `20260822T033759Z-crash-f289e776` 两项公开回放 GREEN。唯一菜单 run `20260822T034104Z-menu-49f9b8bd` 的 foreground transaction 以 `already_foreground` 完成，且未调用 SetForeground/attach/合成输入；两次已落盘 capture 都通过前后 foreground/unobscured guard，但 PNG 是 2560×1440 全黑、OCR 为空，第三次 capture 的前或后 guard 才报告 foreground lost。主链无 visible 主菜单、`ui_*`、bookmark、navigation、action/receipt 或 SendInput，cleanup、双源空清点、protected 与 production postflight 全部通过。旧异常未保存失败瞬间的 actual foreground HWND/PID/TID，因此当前档不能区分外部抢焦、同进程另一 HWND 或空前台；下一提交必须先把单次只读 loss sample 绑定进主链与公开 RED replay，禁止用延时或第二次 foreground activation 猜测性重试。
- 提交 `c8531be` 把 typed foreground-loss 证据接入 sealed lifecycle；环境 `925b8deafa0053fffb2522b86770bb377fbbb5e28a28e53a559ce1ecc40584cc` 下的 ordinary v2 `20260822T045930Z-6ce9874f` 与 crash `20260822T050200Z-crash-95b63c14` 均公开回放 GREEN。唯一菜单 run `20260822T050447Z-menu-0eae4606` 在 `capture.pre_grab`、sequence 2 记录 actual raw/root 为同全屏矩形、不同 PID、class=`Ghost`；该 owner 的 `OpenProcess` 被拒，所以历史 process identity 只能是 unknown，不能用停机后 CIM 追认 `dwm.exe`，更不能把 Ghost 当 CK3 代理。主链无 visible 主菜单、任何 `ui_*`、navigation、action/receipt、鼠标或 `SendInput`；cleanup、Job/watchdog/control、双源空清点与 protected/production postflight 全部通过。该档是可回放 RED，原 run/候选不得重试。
- 提交 `39860a0` 在所有 `SetForegroundWindow`、`AttachThreadInput` 和输入前增加 exact-target 响应稳定门。门前做完整 WMI/唯一窗口认证；门内与门后仅使用 pinned process handle、exact HWND/PID/TID/client rect、`GetLastInputInfo`、`SendMessageTimeoutW(WM_NULL, SMTO_BLOCK|SMTO_ABORTIFHUNG|SMTO_ERRORONEXIT)` 与 `IsHungAppWindow` veto，不做 WMI、全桌面枚举或输入。总等待不超过 30 秒且受场景 deadline 约束；成功必须由至少 21 个响应样本组成、相邻间隔 250–500 ms、连续覆盖至少 5 秒，last sample→gate finish 与 gate finish→direct/attach/第二次 Set/完成各不超过 500 ms。hung、无响应、调度空洞、identity/geometry/tick 变化均在 mutation 前 fail closed。证据嵌入 `foreground_activation_finished`，新 `foreground_protocol_version=2` 的 GREEN/RED completed foreground 都必须带 gate；缺版本只允许四份既有零输入 RED 的 run ID + final-event digest 固定回放。环境 `d343278a3e2d046c7aadc2ad90d75640aadca483b3192801234f4e8a096befa2` 下 ordinary v2 `20260822T060233Z-be4794fb` 与 crash `20260822T060508Z-crash-123c80f3` 均 GREEN；随后唯一菜单 run 的真实响应稳定证据通过，因此该门已在 CK3 上运行，但不等于菜单导航 GREEN。
- 唯一 run `20260822T060758Z-menu-fc73b5c5` 在稳定主菜单、fresh frame 与已 fsync 的 `ui_input_armed` 后把鼠标移动到 `(600,558)`，hover OCR/patch 也匹配；最终提交前 caller token 年龄约 5.85 秒，超过当时覆盖整段流水线的单一 5 秒 TTL，以 `visible control token expired at input submission` 安全 RED。receipt 固定 `pointer_input_may_have_occurred=true`、`button_click_may_have_occurred=false`、`send_input.accepted=null`，所以 `SendInput` 未调用，没有 LEFTDOWN/LEFTUP 或点击。shutdown attestation 为 Job 1→0、tree gone、watchdog/control absent、双源 inventory 空；protected baseline 与 production tree 后置相同。原 run/候选不得重试，不能将这次 RED 记作书签大厅或有效局。
- 根因是 caller 的 5 秒 TTL 同时承担 admission、fresh capture、WAL、鼠标移动和较慢 hover OCR，而非状态漂移。修订不扩大全局 TTL：caller token 仍为 5 秒且只负责 admission；fresh observation 签发 5 秒 `fresh_move` lease，绑定 frame/target/caller 父授权/绝对 action deadline；hover observation 再签发 5 秒 `hover_click` lease，绑定 frame/同一 target/fresh 父授权/同一 deadline。两份 lease 均一次性消费，分别紧邻 pointer move 与 `SendInput`；capture 返回时若已越过绝对 deadline 必须拒绝，postcondition 只能使用 deadline 剩余时间。新报告以 `visible_action_protocol_version=2` 让公开 validator 复算 claims、父链、时序和 WAL；旧 `20260822T060758Z-menu-fc73b5c5` 仅按 run ID + final-event digest `aef3dc4d0dc6bbcaf117dfaabc1d27b263309ec2f58cab5b9a14aa4ffb46396d` 固定只读兼容。后续真实候选均完成 `SendInput` 2/2，证明该 liveness 修复已生效。
- 2026-08-22 实机 run `20260822T074235Z-menu-60587e33` 已成功提交【新游戏】的单次点击，但 CK3 1.19.0.6 随后显示中国教程欢迎窗，阻断书签大厅识别。退出后的隔离 `pdx_settings.txt` 实证：旧键 `promt_for_tutorial=no` 不会关闭该提示，遗漏的新键 `prompt_for_china_tutorial` 会被引擎补成 `yes`；隔离 profile 必须同时写入两者为 `no`。该 run 不得重试，修订后须重新 prepare、ordinary/crash 资格化并仅运行一个新菜单候选。
- 提交 `fc1d9bc` 的唯一菜单 run `20260822T075944Z-menu-f66f06b7` 已无欢迎窗：receipt 记录 `SendInput` 2/2，主链写入 `ui_action_finished(status=confirmed)` 与 `bookmark_lobby_attested`，两帧稳定画面均为真实书签大厅。其最终ization 却被 `menu smoke full capture sequence differs` 拒绝，因为成功证据序列 `16,17,18,19,21,22` 中的 sequence 20 是已归档的 post-click `unknown` 转场帧。validator 现仅在 hover 与首个稳定大厅帧之间允许这种严格向前的间隙，主菜单/fresh/hover 与两张大厅稳定帧仍各自要求连续；该 provisional run 不改写、不升级为 GREEN。
- 提交 `7cb1545`、环境 `531e529f7b301330e902ecf7b44821a462a83ffd9dd4359b23a8482a73590057` 依次取得 ordinary `20260822T080818Z-c0fa1742`、crash `20260822T081016Z-crash-fa350c80` 和 menu `20260822T081240Z-menu-f3d8a8a5` 三项真实 GREEN。menu receipt 的【新游戏】批次为 `requested=2/accepted=2/last_error=0`，无教程欢迎窗，最终两帧均分类为 `bookmark_lobby`，报告 finalized/ok=true，清理与 postflight 完成。这是自主玩家首个真实可见菜单动作 GREEN；它不包含角色选择或【开始】点击，下一功能竖切从书签大厅继续。
- 每次运行都写 `report.json` 与 JUnit `report.xml`；JSON 包含 run ID、UTC、版本、Git SHA、实际 runtime tree SHA-256、source mode、CK3/平台/Python 环境、场景、结果、artifact 清单、各阶段秒数和错误原因。terminal 包装器另记三份 harness 文件的聚合 SHA-256。即使中途失败，也会先恢复现场再写 RED 报告；后置存储或清理检查失败时，包装器会同步把已有 JSON/JUnit 降级为 RED。`tutorial.txt`、`presets.txt`、`dlc_load.json` 与 `save games/autosave*.ck3` 备份位于独立临时目录；运行期只启用本工坊项，结束后原样恢复并删除备份，手动命名存档不移动。

白绮独立版矩阵边界：

- `run_vivhite_acceptance.py` 默认串行运行 `vivhite-alone`、`original-then-vivhite`、`vivhite-then-original`。每格都用全新的仓库外 disposable `-userdir`，从源码构建 Vivhite 精确 27 文件 production projection；双 mod 格还构建原 mod production projection，12 文件外部 `erva` 夹具始终最后加载。
- standalone 夹具投影会剥离 `# ERVA_DUAL_ONLY_BEGIN/END` 区域，禁止残留任何 `xar_`/`xa_` 运行时引用。双 mod 两格分别证明 ERVC 348 金配置和 XAR 120 金配置互不污染、两个原生决议组/窗口同时存在、各交付一名廷臣且各扣款一次。
- runner 不读写真实工坊缓存，不调用原 runner 的同步或全局杀进程路径。所有 Steam library 的 `workshop/content/1158310` 根、真实 profile、仓库和 Steam userdata 都是 artifact/userdir 禁区；全部 `ugc_*.mod` 必须含绝对路径并落在已发现的 CK3 Workshop 根。前后比较真实 profile、Steam cloud 后备目录、descriptor 精确哈希及每个已注册 target 的递归 path/size/mtime 元数据。最终安静窗从一次完整相等扫描结束后才开始计时，等待五秒后再做完整复扫。
- 正式矩阵不加 `--keep-userdirs`：只有场景、阻塞性项目日志、保护存储和删除检查全部 GREEN 才删除该格 userdir。`error.log`、`gui_warnings.log`、`database_conflicts.log` 同时扫描 `xa_`/`xar`/`ervc`/`erva`；仅原 mod 冻结代码的两个 loc-only rarity 警告走逐字窄白名单并写入报告。矩阵以 JUnit 先落盘、JSON 最后原子发布；任一 postflight 失败都整体降级 RED。
- 每格由 debug mount 记录反证实际 product 顺序、无额外启用 mod 且 fixture 最后；启动前后还要求 launcher `rawVersion/exePath` 与 CK3 可执行文件 SHA-256 不变。独立 detached watchdog 在 runner 被强杀时只按记录 PID 终止该 CK3 进程树，绝不按镜像名全杀。
- CK3 冷启动可在大厅按钮消失后继续加载数分钟；必须等底栏日期 HUD 实际出现才开始点决议。原生决议分组标题可能附带条目计数；具体决议行必须精确 OCR，并以相邻 bounding-box 顺序证明各行直属对应组，不能把组标题中的同名文本当成行。marker tailer 只消费换行完整记录，CK3 退出后再 flush 尾行并逐 marker 要求恰好一次。

普通场景冷启动通常约 2 分钟；`bargain-reopen` 还要在速度 5 下实走 9 个游戏年，预计整场约 16-22 分钟，随机原生事件多时更长。所有场景都输出 `RESULT: GREEN/RED` + 退出码。判定依据：

1. `tools/validate_static.py` 通过：八套脚本生成器与三张决议 DDS 逐文件 parity、全部运行文件 UTF-8 BOM、9 语言 loc 引用与首世/账簿/廷臣窗口格式 token parity、原生决议分组/前缀图标/三张独立插画、自动发现的全部 XAR event/decision AI 闸门、挑战继承/成长基线、契约 hook/PB/图鉴/里程碑、生产/selftest 共用入口、21 个当铺购买 effect、付费廷臣五类目录计数/数值边界/原生元数据与冲突/玩家隔离/确认前零副作用/单次扣金、无继承人 fallback/原生继承窗投影、奖池过滤/权重/稳定 ID、descriptor 与发布资源；其中 `tools/validate_loc.py` 负责动态 wrapper、custom-loc 和 modifier 名。
2. debug.log 的 57 个具名 `XAR: TEST PASS`、`XAR: TEST sweep complete`、零 `FAIL` 及 `DONE` 标记全部出现（自测 effect：`common/scripted_effects/xar_selftest_effects.txt`，
   由游戏规则第三档 `xar_selftest` 触发，检查器 xar.0007 嵌套在结算事件 xar.1001 里跑）
3. OCR 真实接受契约、购买外交、结束商店，再依次真实点击重抽、拒绝、祝福、封印、第二次祝福和最终咒痕；验证动态文本无 raw/fallback，并断言 token 消耗、拒绝基线、封印免除效果及封印后的正常咒痕。
4. 从原生右栏进入决议面板，真实执行【琉焰账簿】并关闭，断言快照生成和五个临时 global 清理；随后真实执行【选择本世契约】并选择【征服者】，断言生产 effect 写入契约。
5. 通过 acceptance-only GUI 直接调用 `DefaultOnCharacterClick(GetPlayer.GetID)` 打开玩家原生人物页，以 DDS 模板定位【琉焰之视】，hover 后 OCR 确认“当前分量”实时渲染。
6. 结算确认后必须从原生 HUD OCR 到「正在观察」，证明观察者切换真实完成。
7. **error.log 中任何包含 `xar` 的日志，以及任何 `failed to read trait level star texture` 都视为项目失败**，不再白名单过滤。后者必须单列，因为 `_stars_N.dds` 是按 track entry 数生成的通用路径，错误行本身不含 mod 前缀。
8. 铁人终局必须三次读取同一底栏日期证明时间冻结，并完成原生菜单 resume 重阻断、自动保存退出、主菜单重载和重载后重阻断；真实 Documents 受保护文件与本地 Steam userdata 后备目录快照任一变化均判 RED。

截图证据和 JSON 摘要在控制台报告里的 artifacts 目录。

### GitHub 官方 CI 与本机 L1-L3

`.github/workflows/static-ci.yml` 只使用 GitHub 官方 `windows-latest`。每次 push/PR 都安装最小静态依赖并执行 Python 编译、no-heir 投影测试、两套 release manifest 测试、`validate_static.py`、`validate_vivhite_static.py`、计分 reference vectors 和两套 `build_*_release.py --check`；手动触发或对应 `v*`/`vivhite-v*` tag 时额外构建并上传匹配的 ZIP/manifest，tag 构建仍要求 clean worktree、HEAD 上存在正确命名的版本 tag。

官方 runner 没有 CK3、Steam 授权、工坊缓存、用户目录或可靠交互桌面，因此禁止调用 `run_acceptance.py` 或 `run_vivhite_acceptance.py`，也不能把云端 L0 表述成引擎或 UI 已验。官方 CI 能证明生成器 parity、BOM/loc、玩家/AI 闸门、release allowlist、acceptance 剥离和构建可复现；不能证明 Paradox 运行时语义、跨存档落盘、鼠标/OCR 或游戏日期推进。

2026-08-30 的 push run `33301313411` 进一步实证：即使 L0 测试已用 import stubs 隔离 `pyautogui`/OCR，
单测调用到 `sha256_file(CK3_EXE)` 或 `declared_vanilla_rule_defaults()` 仍会在官方 runner 因游戏树不存在而 RED；本机
integration worktree 的游戏目录 junction 会遮住这类偶然依赖。L0 合同测试必须在测试上下文提供最小 fake executable
与明确的 vanilla-rule fixture，不能读取真实 CK3 安装，也不能因此把游戏文件打包进 CI。该 RED 是 test-fixture isolation
RED，不是 title-map、Workshop 产品或 CK3 实机能力 RED；原 run 保留，不重标。

同日 follow-up run `33301609323` 已通过上述无游戏树用例，随后在 promo step 暴露两条 Windows L0 事实：
GitHub `windows-latest` 不保证 `ffmpeg` 在 PATH，而 draft/manifest-only 工程只有 title-card/still 时本来就不需要媒体
probe；项目校验与 `--validate-only` 现在只在存在 `video_clip`（或真正渲染）时发现 ffmpeg/ffprobe，真实视频源和正式
编码仍保持硬依赖。其次，runner 的 `%TEMP%` 可能返回 `RUNNER~1` 8.3 路径，而写入证据的 `resolve()` 路径是
`runneradmin` 长路径；测试做子路径比较前必须同时规范化两端，不能直接把两种等价拼写交给 lexical `relative_to()`。
这两项都是 CI 环境/测试路径 RED，原失败 run 同样保留。

真实游戏层在本机串行执行并保存 artifacts：

- L1：`off`，production release 投影冷启动、引擎解析及禁用规则负例。
- L2：`selftest`、`persistence-restart`、`death-edges`、`death-with-heir`、`bargain-reopen`、`progression-ui`、`scoring-matrix`、`courtier-creator`，覆盖 57 项机制断言、200 effect body 与 200 dispatcher runtime sweep、两进程持久化、AI/无继承人/普通继承死亡边界、三轮生产交易的 1094/1095 日边界、PB/图鉴/里程碑生产链、受控后代去重/深度/死亡中间节点计分，以及付费廷臣两次真实交易与动态目录。
- L3：`on-first-life`、`on-recorded`、`on-high-budget`，覆盖 production-only 首世、已有纪录和第四页高预算真实 OCR/点击。L2 的交易 UI、决议、trait hover 和无继承人窗口也计入整体 L3 证据，不重复启动。
- 白绮独立版并行门禁：专用三格矩阵覆盖 standalone 完整购买链、双 mod 两种实际 mount 顺序、状态隔离、各自单次交付/扣款、AI 闸门、零阻塞性项目诊断及真实用户存储零改动；该矩阵不使用原 mod 的 Workshop item 或真实缓存，已知原 mod loc-only 警告必须透明记录。

本机报告必须记录 JSON/JUnit、截图、runtime hash 和本次增量 `debug/error/gui_warnings`；发布 QA 引用具体 run ID，不把未运行的远端 CK3 状态写成 GREEN。GitHub tag artifact 只提供经过 L0 验证的候选 ZIP/manifest，不自动创建 GitHub Release 或上传 Steam。

### 覆盖边界（什么算验过、什么不算）

**验过的**：
- 奖池全部 200 条目的**运行期执行**：自测在死前跑 `xar_test_sweep_effect`（生成器产出，
  每条 code 内联按序施加），带 `xar` 上下文的报错会被 error.log 扫描抓红（drain 修正漏定义就是这样抓到的）
- 引擎解析 + PostValidate 静态校验全部生成文件
- **当前校验范围内的静态 loc 全覆盖**：event/custom-loc/GUI/trait/rule/modifier 引用、奖池目标键与五个 wrapper 精确表达式，均检查 9 语言。
- 生产契约接受、商店外交购买与结束、祝福三选一、诅咒二选一的简中实际像素渲染和点击。
- 商店样例的扣款 `200→175`、整数价格 `25→30`、纯脚本小数涨价 `11→14`、外交增长，以及余分换金币。
- 契约事件与纯脚本 selftest 都调用 `xar_enable_player_pact_effect`、`xar_initialize_run_state_effect`；外交生产 option 与 `25→30`/扣款脚本样例都调用 `xar_buy_diplomacy_shop_item_effect`。静态校验禁止两处重新内联对应实现。
- 14 个可重复购买商品和宗教改革/三种高价批量商品/三种冠冕服务各自调用具名生产 effect；166600 点自测先购买原四种固定商品并断言余 5467，再购买重抽、封印和三种冠冕服务并断言余 3217、代币涨价和所有权。商店结束调用 `xar_finish_shop_effect` 完成余分兑换、清零及垂青会初始化。
- 原生 trait track 的 100 XP/10 级、每对 +1 XP、满级状态及 hover 当前分数的实际像素渲染；hover 公式还与死亡结算值作脚本断言。
- 生产里程碑 effect 在 10/20 XP 发放早期单枚代币，30-100 XP 逐步升级为重抽/封印组合，并同步增加原生属性；selftest 精确断言 30 XP 奖励和 40-100 XP 累计奖励。UI 真实消耗重抽与封印，并验证拒绝未发祝福、封印未施加首个咒痕、下一次正常接受施加了咒痕。
- 传说祝福只抽到稀有/传说诅咒、拒绝每次 -1% 最终分、request/ready/consumed 零值导入、同阈值不破纪录、跨阈值破纪录、cap 量化、死亡结算、纪录写入和教程落盘。
- 0/25/50/100% 继承的生产 effect；1200、5000、50000、166600 四档均实机脚本断言无额外预算封顶，2000 production-only UI 场景覆盖第四页冠冕服务和 1133 分宗教改革。AI 兄弟 scope 还会实际调用契约进度和导入消费 effect，确认 `is_ai = no` 在运行期阻断。
- 奖池 200 个 effect body 的运行期语法/引用 smoke test
- 静态验证首世 0 纪录分流和 selftest 200 点优先分支，并逐阈值校验账簿 candidate/next/gap 生成关系、cap 状态、七个展示字段及禁止写纪录/资源的边界；纯脚本自测直接调用生产 `xar_prepare_ledger_effect`，断言非负分数、投影关系和历史纪录不变后清理临时 global，不打开账簿 UI。
- 原生决议面板实际点击【琉焰账簿】和【选择本世契约】：账簿 UI 验证只读快照及关闭清理，契约 UI 验证确认页、`xar.2000` 和【征服者】生产选项。
- 账簿生产 UI 用三个连续事件分别捕获即时分数、投影阈值、复制显示快照；2026-08-18 实机证明只用一个或两个事件会让同一 `immediate` 的读后写依赖产生 `none`，三阶段链为 0 `xar` errors。
- `persistence-restart` 两进程实测：A 写入非零余烬 lesson 后完全退出，B 在 `process_b_preseeded=false` 且 `tutorial.txt` handoff SHA-256 不变的前提下导入同一位阶；JSON 记录两 PID 生命周期对应的耗时、位阶和 hash。
- 真实 AI 死亡负例：目标明确带 `xa_enabled`，引擎 `on_death` observer 确认死亡，但 `XAR: computing score on death` 在 AI 区间内未出现且分数 sentinel 未变。无继承人链验证 `player_heir` 确实为空、计分/写位与快照按前向事件边界提交；OCR/像素覆盖八项数值、无「继续扮演」、原生退出确认及主菜单。最新 GREEN：`xar_accept_fmq_wxxc`，0 `xar` errors。
- 独立 `bargain-reopen` 开发树场景覆盖生产一场一对语义：三轮真实 options/dispatchers、累计对数 1/2/3、session `1→0`、XP `0→1→2→3`、拒绝数 0。每轮 acceptance-only day-1094 probe 与生产 `xar.0006 days = 1095` 都用 `current_date - 成交日` 分别精确断言 1094/1095，三个生产 reset marker 必须有序且第三次确实打开下一场。2026-08-19 首次完整 GREEN：`xar_accept_ue4ye_un`，九游戏年、三次生产 reset、0 `xar` errors。
- 独立 `progression-ui` 开发树场景覆盖生产贤王 3/6/10 和【琉焰之视】10 XP 事件的正文、选项与真实点击；四个 tutorial lesson 必须精确落盘，原生账簿必须同帧显示当前 `0/10`、`PB 10`、贤王已完成、`R 1`、`S 0`。2026-08-19 首次完整 GREEN：`xar_accept_gqppgi_f`，图鉴 mask 16，0 `xar` errors。
- 独立 `scoring-matrix` 开发树场景实测 1–5 代计入、第六代排除、同一后代双路径只计一次、穿过已故中间节点后继续计分、清理不对 dead scope 执行 flag effect，并比较 preview/生产误差。全部 200 个稳定 wire ID 还会逐一穿过生产 dispatcher，结合冻结语义契约证明 ID→effect/filter/weight 映射。2026-08-19 GREEN：`xar_accept_h0lgmvyf`，200/200 marker，0 `xar` errors。
- 非 debug 终局双路径实测：`xar_terminal_observer_nondebug3_20260821` 从开发夹具中的生产 `observe` 分支进入原生观察者 HUD；`xar_terminal_ironman_nondebug9_20260821` 完成强制暂停、resume 重阻断、原生自动保存退出、主菜单同进程重载与重载后阻断。两轮都实际 hover 十级【琉焰之视】，其完整 1–10 轨道可见且不再产生旧 run 中的 248 条 `_stars_10.dds` 错误。铁人轮的三个日期检查均强制读出并固定在同一日，隔离存档重载前后路径/大小/SHA-256 相同；真实 Documents 的 9 个受保护文件与本地 Steam app 1158310 userdata 的 2 个文件在五秒观察窗内聚合哈希不变，隔离 userdir 删除后实际不存在。两轮 runtime tree 均为 `235d92fb36fd1052b0261c05f059e525d76a06231a7b92a8a27cc8e6764d242a`，harness 为 `f56a0e364198e6fe1be465d447d1f5170965de275e6a28e4d443ca68934e7b9f`，且均为 0 project errors。该证据不等于 release projection 运行或远端 Steam Cloud 审计。
- 2026-08-21 最终 exact-candidate 套件绑定提交 `45cf7ea`：`xar_final85_selftest_20260821`、`xar_final85_persistence_20260821`、两条 `xar_final85_death_*`、`xar_final85_bargain_20260821`、`xar_final85_progression_20260821`、`xar_final85_scoring_matrix_20260821`、`xar_final85_courtier_creator_20260821` 与四条 `xar_final85_on_*/off_20260821` 全部 GREEN，0 project errors。开发树 runtime 为 `235d92fb36fd1052b0261c05f059e525d76a06231a7b92a8a27cc8e6764d242a`；四条 production smoke 实际加载从它构建并剥离验收夹具的 85 文件 projection `29dde4460b7f86b1779e902712e856776dd99de703802a92a64c1fa39c28d221`。每条报告均保存 JSON/JUnit、截图与增量日志；该结论只关闭自动化候选回归，不替代九语言人工审校、干净截图、Workshop 强制重下载或发布签核。
- 2026-08-21 白绮独立版 hardened schema-v2 三格矩阵 `ervc_acceptance_hardened_final_20260821`：非 debug CK3 `1.19.0.6` 串行完成 standalone 与双 mod 两种加载顺序，3/3 GREEN、0 blocking project diagnostics。Vivhite production projection 为 `93fb559a61ace1a3c2bd8a9680a0ed5039db765753da8c787d28b0dd67c09fef`，原 mod projection 为 `97b9f386ab17364eec0859be1f7c6407816a27a396b2edcf6427d697789ba2ab`；debug mount 顺序逐格精确匹配请求顺序且 fixture 均最后加载，两种顺序都证明两个决议组及其直属决议行、ERVC 348/XAR 120 独立状态、最终 532 金与两次独立交付。双 mod 格各自透明记录原 mod 冻结代码的 `xa_curse_a_rarity` / `xa_curse_b_rarity` 两类 loc-only unused-variable 已知警告，没有以漏扫 `xa_` 隐藏；除此之外 `error.log`、`gui_warnings.log`、`database_conflicts.log` 无项目诊断。CK3 可执行文件逐格前后 SHA-256 均为 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。真实 profile、Steam cloud 后备目录、82 个已注册 Workshop target 的 162,960 项递归元数据在完整扫描后再等待五秒并复扫，聚合哈希保持 `ed9a9cce6db99148f08aac997d38caae00f64c79827fdb1dcf642c3af9c38336`；三个 disposable userdir 与 detached watchdog 均实际退出/删除。该证据不替代 clean committed-candidate 重跑、品牌差异审阅或新 Workshop cache 验证。

- 2026-08-21 发布本地化候选矩阵 `ervc_release_final_20260821`：3/3 GREEN、876.590 秒、0 blocking project diagnostics，Vivhite projection 更新为 `6242ca7eec1b33f6da939c3a161b7338011122780c4740c6e831e2de0e20577c`；原 mod、两类 fixture、CK3 EXE 与受保护存储哈希均保持上述值。七页功能、两种双 mod 加载顺序和全部购买/隔离 marker 再次通过，三个 userdir 与 watchdog 均已消失。
- 2026-08-21 clean committed-candidate 矩阵 `ervc_release_clean_6575997_20260821` 绑定完整提交 `6575997b14a90b0afda75fdde304170206478c21`：3/3 GREEN、910.962 秒、0 blocking diagnostics，runtime/fixture/EXE/受保护存储哈希与上一轮完全一致。standalone 同时留存决议入口和七个子页的八张 2560×1440 原始截图；tag `vivhite-v1.0.0` 指向同一提交。
- 2026-08-21 白绮 `1.0.1` clean committed-candidate 矩阵 `ervc_v101_clean_092e61b_retry_20260821` 绑定完整提交 `092e61bf2fa9d90167eea91369ac8bb4bfa1b543`：3/3 GREEN、887.637 秒、0 blocking diagnostics。Vivhite production projection 为 `f00898467746145316ff850c898d6402709e19c612044f9945d3af280d0e576c`，原 mod 与两类 fixture 哈希保持不变；9 个真实 profile 文件、2 个 Steam cloud 文件、82 个已注册 Workshop target 的 162,960 项元数据在五秒复扫前后保持 `541376448f2073679434cc2aac109c619a4efca89e911bb12e0c6dcd800a4e22`，三个 userdir 均删除。前一目录 `ervc_v101_clean_092e61b_20260821` 因 JetBrains stale-index 通知遮住大厅【开始】而在任何 fixture marker 前 OCR RED；原报告保留 RED，关闭通知后使用全新目录完整重跑，不把基础设施失败重标为 GREEN。

**没验的**：
- 数值是否符合最初产品意图仍需人工平衡审阅；冻结契约能阻止未审阅的 `50→500` 或 ID 重排，但不能证明首次冻结前的设计值天然正确。
- 付费廷臣尚未独立验证无地玩家交付、跨进程配置保留和九语言窗口截断；`xar_final85_courtier_creator_20260821` 已在最终树覆盖登陆玩家的完整功能链及真实非默认文化/信仰。
- 长期平衡只有 `synthetic --balance-smoke-pairs 2` 的短烟测证据；kind 4 自然死亡、40 年/14 对/pair 10 和四夹具串行矩阵均未完成，但这些只属于非门禁 soak/stability/telemetry，不证明数值平衡。
- 九语言已有源文本，不等于母语级术语/人格审核或游戏内窗口截断验收。

### 关键事实（2026-08-17 实证，血泪）

- **游戏加载的是 Steam 工坊缓存，不是仓库 dev 目录**：dev .mod 带 `remote_file_id` 后启动器
  把它和工坊订阅合并，播放集里生效的是 `mod/ugc_3784706360.mod`
  （内容在 `Z:\SteamLibrary\steamapps\workshop\content\1158310\3784706360`）。
  **改完代码在游戏里看不到，先怀疑这个**。runner 每次跑前 robocopy /MIR 仓库 → 工坊缓存
  （用户已批准，不恢复；工坊更新时 Steam 会重下复原）。
- **CK3 PhysFS 会拒绝过长的 disposable mod 路径**：2026-08-26 的 paused event-window Attempt1 使用长度 99 的
  默认 root，`error.log` 对四个 fixture localization 路径报告 `path is over 250 characters long`，CK3 在事件出现前
  以 code 1 退出。live runner 的默认 root/stage 必须为最长 localization 文件预留到完整路径严格小于 250 字符，并在
  启动前按实际 root 枚举校验；默认前缀应保持短小。调用者指定的目录超限时，改用显式短 `--state-dir`，不要继续启动。
- **事件脚本 flag 必须按 exact parser token 映射，不能用邻近 GUI 字段猜名**：同日 Attempt2 的 path gate 以最长
  243 字符通过，generic event 真实加载且日志没有 unknown/`is_cancel_option` parser error，但旧 bridge 把
  `CEventOption+0x478` / `CEventWindowData+0x2C` 的 `timeout_option` index 错标为 cancel，导致 authored
  `is_cancel_option=yes` 的 row 发布 `cancel=false` 并使验收 RED。exact parser 证明
  `timeout_option/show_unlock_reason/is_cancel_option` 分别位于 `+0x478/+0x479/+0x47A`；修法是按 materialized
  authored native index 找回 `EventData` 的 `CEventOption*` 并读 `+0x47A`，不能把夹具预期降为 false。
- **事件 calculated ID/runtime ordinal 不能跨不同 playset 比较相等**：Attempt3 在相同 save、完整 event instance ID、
  canonical definition key 与逐字节相同 fixture 下，seed（额外加载 mod bridge）观测到 `4360001/6773`，cold
  production+fixture 观测到 `3940001/5881`；两次 cold 同帧查询各自稳定。两字段是当前 loaded definition table 的
  process/playset-local 数值。跨进程 fixture identity 应绑定 canonical key、definition bytes、完整 active instance 与
  save/date；数值字段只要求各进程内是 signed int32 且同帧不漂移。
- **事件 Attempt4 已证明修正合同**：2026-08-27 的 seed/cold PID `22976/43140` 在同一 instance `17` 与 key
  `xar_event_window_live_fixture.1` 下分别观测到 `3930001/5847` 与 `3940001/5881`，三条 materialized native indices
  `[0,1,3]`、index `3 cancel=true`、空 indicator surface 与 cold 双查询全部一致；artifact SHA-256
  `690EB5EA188B0903281E5F5DFDA343DA795117EE0FB1C83C3FCDC7F572170B7B`。该 GREEN 只升级 fixture-scoped
  current-window query，不升级非空 effect kinds、selection lifecycle 或 semantic decision。
- **大厅规则选择持久化在 `player\game_rules\presets.txt` 的 `LastAppliedRules` 块**，新开局重放它；
  改规则文件的 `default` 不影响已有档案。runner 会先移除该块内全部 `xar_on/xar_off/xar_selftest`，再写入场景目标值并验证同时只剩一个（事后恢复）。
- **pyautogui 合成键盘事件进不了 CK3**（esc/space/+ 实测全部无效），鼠标点击有效。
  解暂停只能点底栏日期旁的 ▶（坐标 (2315,1410)@2560x1440）。
- 速度 5 也必须走鼠标：原生 `timeline_widget` 最右侧 `speed_5` hitbox 中心约 `(2536,1418)@2560x1440`。2026-08-19 对照截图与原生 `hud.gui` 实测：该按钮只执行 `SetGameSpeed`，不会解除手动暂停；但关闭运行中弹出的原生事件会自动恢复时间，此时再点 ▶ 反而会暂停。`bargain-reopen` 现 deliberate-click 速度 5 后先观察底栏日期 2 秒，仅在尚未前进时 deliberate-click OCR 识别出的日期按钮，最终要求日期在 10 秒内前进才视为成功。
- 旧 acceptance runner 每次 OCR/点击前会用 `AttachThreadInput` + Alt 抢回并反证 CK3 前台；2026-08-19 曾实测裸 `SetForegroundWindow` 被 Windows 前台锁静默拒绝后，runner 把 OpenCode 整窗识别成事件选项。该做法只属于旧验收工具，不能移植到合法自主玩家。Phase B sealed menu smoke 改为主证据链 write-ahead 后的一次 direct exact-HWND 激活，以及至多一次 caller→同一个稳定前台线程的严格 attach/detach fallback；不使用 Alt、PyAutoGUI、鼠标或 `SendInput`，任何身份、detach 或前台后置条件未知都立即 RED 且不重试。
- `parentanchor = center` 的小型验收 widget 不要点击精确屏幕中心：锚点可能落在 64×64 控件边界并穿透到地图。`xar_trait_test_window` 改为点击中心内偏移 20 px；最终咒痕后还要先按渲染出的“暂停”状态锁住一日死亡计时，完成特质 hover 后才恢复时间。2026-08-20 CK3 1.19.0.6 实测。
- 主菜单【新游戏】也必须 deliberate-click 并以罗贝尔书签实际出现作反证；2026-08-19 实测 OCR 找到按钮后的一次瞬时点击可被 CK3 丢弃，runner 若直接进入 30 秒书签等待只会在原主菜单超时。
- 安全软件、Chrome 与 JetBrains 通知都可能置顶遮住大厅“开始”按钮。2026-08-22 两次 opening 实测同一 YouTube/Chrome 通知持续覆盖该按钮；Windows Toast 总开关和应用级 banner 开关不足以阻止它再次出现，最终必须把 Chrome Default profile 的默认通知和 8 个显式允许站点全部改为阻止。用户已持续授权自动游玩期间立即关闭任何右下角 Toast；只能点击通知自身的【关闭】，不得点击通知正文。原 RED 保持原结论，清理后使用全新 run。
- 截图读坐标要用 PIL 裁真实 PNG（2560x1440）实测——聊天里显示的图有缩放，目测坐标必歪。
- 2026-08-22 `20260822T130230Z-opening-cb15ab30` 再次实证这一点：聊天预览把 2560×1440 缩到
  2048×1152，直接读出的 HUD 生活方式中心 `(278,1118)` 必须两轴同时乘 1.25；只修 Y 得到
  `(278,1398)` 会以 `SendInput 2/2` 点中角色压力状态条，画面继续保持 `map_hud`。原版 `hud.gui`
  的 `bottom_left_button_row` 排列与真实 PNG 共同给出生活方式按钮中心约 `(348,1398)`。
- 修正坐标后的 `20260822T131930Z-opening-a4f7cfab` 已真实打开【选择生活方式】：标题框
  `[1192,30,1370,64]`，军事框 `[842,367,913,407]`，管理框 `[1208,367,1279,408]`。
  旧 classifier 把居中标题限制在左侧 `x≤0.24`，因此画面虽正确却连续判 unknown；选择页标题区域应覆盖
  屏幕中部 `x=0.40..0.60`，军事/管理仍由各自可见 OCR 框动态定位。
- `20260822T133343Z-opening-1c6306f5` 随后已真实进入军事生活方式页；标题 `[60,57,325,100]`，
  【生活方式重心】`[501,284,617,308]`，【当前：无重心】`[500,328,617,352]`，可点击的【权威重心】
  `[430,706,526,734]`。旧 fixture 把前两项虚构在 y≈520/565，导致真实页面再次判 unknown；分类区域现按这张
  2560×1440 实机 PNG 校准，权威按钮继续从 OCR 框动态取点。
- `20260822T135113Z-opening-272e7264` 已真实点击【权威重心】并收到 `SendInput 2/2`；CK3 随后显示的不是
  已选择状态，而是原生【选择权威重心】确认层。确认标题框为 `[1191,435,1369,471]`，底部【取消】为
  `[1121,972,1166,998]`，【选择】为 `[1397,972,1442,998]`。opening 合约因此把该层冻结为独立画面，
  先以【选择权威重心】反证未确认页面，再动态点击唯一【选择】，最终才要求【当前：权威重心】。
  此次错误 postcondition 还让动作一直消耗场景剩余预算、空跑约 228 秒和一百余张 OCR 帧；地图内即时面板跳转现使用
  20 秒局部后置超时。全屏 RapidOCR 单帧约 1.3–2.5 秒，一次完整点击通常需 8–15 秒，因此 20 秒既能容纳正常
  fresh/hover/双帧反证，又能在合约写错时尽快留下 RED，而不是等待数分钟全局超时。
- 自主玩家 OCR 默认使用本机 NVIDIA 独显：`onnxruntime-gpu 1.28.0` 的 `CUDAExecutionProvider` 固定
  `device_id=0`，检测、方向分类、文字识别三段模型都必须以 CUDA 为首选 provider；初始化失败会由 doctor
  直接拒绝运行，不静默退回纯 CPU。2026-08-22 在 RTX 3080 上用同一张 2560×1440 实机 CK3 帧复测，热态
  OCR 为 0.52–0.55 秒/帧，原 CPU 路径约 1.3–2.5 秒/帧，单帧实际加速约 3–5 倍。CUDA 13.3、cuDNN 9
  与相关运行库均精确 pin 并纳入 environment 指纹；GPU runtime 变化后旧 ordinary/crash 资格自动失效。
- GPU 候选 `20260822T142513Z-opening-19fe85e9` 中，OCR 已稳定读出【继续游戏】【新游戏】【载入游戏】，
  但旧 `main.center_void` 探针把主菜单轮换背景当成固定纯黑；实机 `20×20` 区域均值为
  `(61.90,47.43,43.75)`，而旧范围只允许 `0..2`。该探针已从两份主菜单合约及 canonical 定义删除，
  仍保留左侧菜单/按钮的四枚像素探针和全部模态文案反证。`opening-smoke` 第一次主菜单等待同时收紧为
  120 秒局部上限，同类合约错误不再消耗整个全局场景预算。该 RED 主链无任何 action receipt，未发生游戏点击，且 CK3 完整清理。
- 删除失效探针后的提交 `2f87ae3` 在环境 `c34400dcd9b20d04b2ededa042850430c8b2cc407eb556dfdb8b239b64eff31e`
  下依次取得 ordinary `20260822T144016Z-5c323968`、crash `20260822T144218Z-crash-c86ef48e` 与 opening
  `20260822T144449Z-opening-b30af184` 三份 GREEN。opening 在约 216 秒内完成 13 个动作，从【新游戏】到
  地图、玩家角色页、军事生活方式、【选择权威重心】确认层，最终双帧读出【当前：权威重心】；
  所有按钮批次均 `accepted=2/2`，退出后 CK3 进程树与双源 inventory 均为空。
- 提交 `a734a91` 首次把地图时间控制接入 opening：关闭生活方式页、选速度 5、点底栏日期启动、从可见日期证明前进、
  再点日期暂停。首份候选 `20260822T150350Z-opening-1ecbdd30` 的开局七步已全部到达，咒痕收据也记录
  `SendInput accepted=2/2`，但暂停地图被误拒为 `map_hud.resume matches=0`。实机 OCR 是完整【公元1066年9月15日】，
  而新控件文本只写【公元1066年】却漏了 `contains=true`。补上后，同一归档最后帧用修订合约直接重放为
  `map_hud`/`confidence=0.7537`/零失败原因；祝福、咒痕即时转场同时改用 20 秒局部后置上限，不再因此类文本配置错误消耗剩余全局预算。
- 发布截图还要检查画面中心：2026-08-21 的 non-debug terminal artifact 实测把 CK3 原生
  `clausewitz/gfx/cursors/software_cursor_normal.dds`（100x100）留在 `(1280,720)`；它在地图上是深色方框，
  还会透过半透明事件窗，看起来像坏掉的事件控件。该方框不是 mod GUI。发布衍生图应优先换用无光标帧或收紧裁切；
  若只能用同帧事件图，只能从同一次 run、同一固定事件背景的无光标帧恢复该区域，并在截图来源文档记录坐标，禁止
  用生成式补图伪造游戏内容。软件光标滞留在画面中心的具体引擎触发条件**未查明**；规避必须依靠发布前逐帧检查，
  不能假定移动 Windows 硬件光标就会让它从 `ImageGrab` artifact 中消失。
- OCR 定位按钮必须避免正文中的同词。2026-08-21 铁人 modal 的正文含“打开游戏菜单”，全屏 `contains=True` 会点到正文而不是底部按钮；按钮改在 modal 区域做精确匹配。RapidOCR 还会把 CK3 字体的“余烬”稳定识别为“余焰”，流程断言因此使用唯一后缀“已封存”，不修改正确的产品文案。
- `pdx_enum_setting.cpp` 在真实 profile 和隔离 profile 均可能先记录 `Could not find enum 'l_simp_chinese' ... default 'l_english'`，但随后实际画面仍是简中；该启动期 debug 行不能单独证明最终渲染语言，验收以画面 OCR 和本地化结构为准。2026-08-21 非 debug 铁人实测。
- 隔离 runner 只终止自己记录的 CK3 PID。若 preflight 后、真正 launch 前又出现任意 `ck3.exe`，必须 RED 并拒绝启动测试，不得调用按镜像名全局强杀；否则会误杀用户刚开启的真实会话。后置安全检查同样属于权威结果，失败时 JSON、JUnit 与退出码必须一起 RED。2026-08-21 runner 审阅加固。
- full selftest 的最终咒痕 option 不能只在 1 游戏日后排入强制死亡：character event 关闭会自动恢复时间，runner 尚在打开账簿/契约/trait hover 时，死亡窗便可能抢先覆盖决议面板。acceptance-only 首次 `xar.0008` 现留 30 日 UI 宽限，若 importer 尚未交付才继续逐日轮询；release 投影完整剥离该夹具。2026-08-21 两次非 debug 铁人 RED 截图复现。
- 长测日期 12 秒不推进时禁止盲点固定坐标。runner 每次用单调递增序号保存 `stall_<场景>_<序号>.png`、候选框标注图和完整 OCR JSON：在画面下部找真实选项，并在候选栏中优先同一 x 轴纵向堆叠的最下行。点击后必须观察到日期继续推进；连续三次仍卡住立即 RED，并由执行者读取这些截图/OCR 分析，不能继续空点到总超时。2026-08-18 实测定位：全宽事件【摆脱尘世】的选项约在 `(0.68,0.79)`，旧恢复点 `(0.38,0.72)` 落在正文空白处。2026-08-19 【诺曼人的西西里】实测三个真实选项纵向对齐在 `x≈930`，人物名位于 `x≈1377/1841`，按右侧优先会误开人物面板；【埃玛成年】仅有一个左侧选项 `x≈930`，人物名/关系则纵向对齐在 `x≈1505`，不能只按列密度判断。【对未来的思考】实测人物页会在真实选项下方露出被纵向裁切的地图标签，OCR 将其识别为高框并误当成同列最末选项；经典选项现限制为 `x=0.34..0.41`、`y≤0.75` 且 OCR 框高不超过画面 `3.5%`。互动信函【要求改信】【剥夺头衔】会把真实 `拒绝/同意` 按钮放到 `y≈0.79`，其效果正文却占满旧候选区，因此两个精确动作标签优先于正文。全宽【波希米亚的宫廷】正文会侵入 `x≈0.42`，真实选项位于 `x≈0.68`；没有经典栏时，runner 先选右侧纵列，再退回中栏。同期实测 `debug.log` 在无事件时可长期没有日期行，不能用它单独判断冻结；长测改读底栏 `公元 Y年M月D日` 的实际像素。
- 2026-08-20 【精神崩溃：心脏疼痛】的花体选项没有被 OCR 读出。旧特判把 y 写死为画面高度 `0.91`，实际点到 `(928,1310)` 的地图并循环 122 次；真实按钮框为 `[621,1020,1247,1064]`、中心 `(934,1042)`。现从标题下方 Canny/Hough 横边配对出全部符合 CK3 option 比例的矩形，按框尺寸、横向对齐和置信度选择；检测不到可信框就不点击，同一 resume modal 三次无进展立即 RED。离线缩放到 0.75/1.0/1.25 倍均命中同一归一位置。
- 暂停链因场景而异。`selftest`/`death-with-heir` 的普通继承路径是：开局默认暂停 → 原生继承窗强制暂停 → OCR 精确点击「继续扮演」约 `(1453,1129)` → 等待生产结算事件；不得把继承窗右栏约 `(1721,1048)` 的「处于战争」状态交给通用纵列算法。
- `balance-long` 的自然死亡同样使用精确「继续扮演」路径，但生产 terminal 不再依赖死者 event 排队：`on_death` 先保存 dead/carrier scope 并排入存活继承人的 `delayed = yes` dispatch，再内联计算；延迟边界后只用预先建立的 pact/fixture character globals 认证，不重查会在死亡时清除的角色 flag。runner 最多等待 30 秒 kind 4 terminal wire，且不采集继承人的后续普通样本。
- 大厅路径坐标（2560x1440）：新游戏 (600,560) → 1066 罗贝尔卡 (1600,1230)（有儿子必有继承人）
  → 开始 (2257,1245)。结算确认选项 (1130,1041)（点了进观察者模式，桥有效）。
- 2026-08-22 opening 实测罗贝尔标签 hover 后会从中心 y≈1211 上移到 y≈1203，且标签/卡片像素持续动画；点击标签本身不会选中。自主玩家因此从唯一 OCR 标签派生 `(0,-130)` 的头像点击点并按住 120 ms，只对该控件允许最终 hover patch 动画，仍保留唯一标签、窗口前台、点击点归属与后置 `bookmark_lobby_selected` 反证。
- 同次 opening 后续实测，“开始”按钮的 hover 说明框会盖住地图上的罗贝尔标签；已选中状态必须改用右侧详情面板的【公爵罗贝尔，51岁】与可见【开始】共同分类，不能继续依赖被 tooltip 遮挡的地图标签。
- 【开始】按钮的 hover 高亮也会在 OCR 帧与最终点击前 patch 之间持续改变像素；`20260822T095109Z-opening-10f49d7e` 已实证两个 SHA-256 不同且 `SendInput` 尚未调用。opening 合约因此只对该按钮放宽静态 patch 相等，仍要求唯一【开始】、右侧罗贝尔详情、前台/点击点归属与点击后【终末之契】反证。
- 关闭 Chrome 后，提交 `3a292c8`、环境 `13496c86f545eee215a5adac679c027c05ad03d5f789b99fdee6b3c02e720221` 的
  `20260822T095721Z-opening-019ba6a7` 首次 GREEN：新游戏、罗贝尔、开始三次收据均 `SendInput 2/2`，最终两帧 OCR
  【终末之契】与【又见面了，旅人。】，随后 Job active 归零、tree gone、双源 CK3 inventory 为空。该 run 没有点击契约选项。
- 随后的提交 `c8a27d5`、环境 `f54ca88ac450ae8d2c4d7401e115695069ac10781e2a37e8af14cc5d3521304d` 中，
  `20260822T102802Z-opening-4cc459ce` 完成七次 `SendInput 2/2`：接受契约、开始此生，并按可见文本选择
  【兵棋的余局（+500军事经验）】与较低损失的【千面的哑剧（-1000谋略经验）】。最终连续两帧识别 `map_hud`，
  Job active 归零、tree gone、双源 CK3 inventory 为空；这是首个完成祝福/咒痕对并进入地图的可计分开局基线。
- 提交 `106278f`、环境 `f11b248ccc09bb80b5a9d92f0b9e3bc19646af333d21ccd0961183d583c09cbe` 的
  `20260822T111130Z-opening-a27391b9` 又执行第八次 `SendInput 2/2`，从地图 HUD 打开玩家角色页。最终双帧分类为
  `player_character`，OCR 读出罗贝尔本人、配偶、玩家继承人与 7 名臣属；截图人工复核正确，进程树与双源 CK3 inventory
  清理为 GREEN。该切片用于证明地图内状态读取，不代表已完成任何治理决策。
- `20260822T151145Z-opening-6ec69979` 实测角色页已经打开，但【这是你自己】在相邻全屏 OCR 帧中间歇漏识别，导致相同画面
  在 `map_hud` 与 `player_character` 间抖动并耗尽 20 秒后置窗口；同期【配偶】【玩家继承人】与罗贝尔姓名连续稳定。
  角色页分类因此改用后三项实测稳定锚点，并以【玩家继承人】作为底层地图反证；该失败不是 CUDA OCR 未启用或点击未生效。
- `20260822T152245Z-opening-01eb15f1` 随后实机确认上述角色页修复有效，并完成军事【权威重心】选择；关闭生活方式页时
  原合约误把 2048 宽预览图上的 X 中心 `(1972,63)` 当成 2560×1440 客户区坐标。原始 PNG 的金色 X 像素连通域为
  `(2451,65)..(2478,92)`、中心 `(2464.6,79.1)`，故固定点击点校正为 `(2465,79)`；该失败是坐标标定错误，不是 OCR 延迟。
- `20260822T152918Z-opening-22741b9b` 实机确认关闭点和速度 5 均生效，时间已从 1066-09-15 推进到至少 09-24。
  鼠标停在底栏日期上时 tooltip 会额外显示【当前日期】与【开始】两条完整日期；全屏日期正则因此得到三项而 RED。
  日期抽取现只接受底栏 `x=1792..2381, y=1368..1439` 的渲染日期，明确排除上方 tooltip 文本。
- 修订日期区域后的 `20260822T153549Z-opening-69644bad` 是首个完整地图经营 GREEN：17 个动作完成首轮
  祝福/咒痕、读取玩家页、选择并确认军事【权威重心】，再以速度 5 从 1066-09-15 推进至 10-10 并暂停；
  `elapsed_days=25`、最终画面 `map_hud`、tracked cleanup 成立。下一版输入优先复用原版
  `Crusader Kings III/game/gui/shortcuts.shortcuts`：角色页 F1、关闭窗口 Esc、速度 5 键、暂停/继续 Space，
  事件选项按原版 `event_option_N = shift+N`；可见 OCR 仍负责判断当前画面和选择哪个选项，只有执行方式从鼠标
  改为快捷键。主菜单、书签角色/开始和没有直达键的生活方式图标/焦点仍使用动态视觉点击。
- 快捷键候选提交 `d99331a`、环境 `1466eac2cd09f903e2bff59225d59d039ba9ea21c7857568f142cf1e98ab576c`
  的实机 `20260822T155740Z-opening-b33c1328` 再次 GREEN：17 个动作中 11 个为键盘、6 个为鼠标；
  `Shift+1` 连续完成契约/此生/祝福与本轮咒痕，F1 开关玩家页，Enter 确认权威重心，Esc 关闭生活方式，
  `5` 设最高速度，Space 恢复和暂停。每个单键批次 `2/2`、组合键批次 `4/4`，总耗时约 216 秒；
  日期从 1066-09-15 推进至 10-02（17 日），最终 `map_hud`、tracked cleanup 成立。下一功能切片是持续推进并
  识别、选择首个真实普通事件，而不是继续扩展开局固定动作。
- 首个普通事件竖切提交 `bdd9956`、环境
  `e0187715652fe969bfa36b306d3a432752cbc89133ef8c64b83ae07ae2c3b031` 的实机
  `20260822T162844Z-opening-33bdd96f` 为 GREEN。OCR 双帧识别【诺曼人的西西里】和三个可见选项，执行器用
  `Shift+1` 选择【所有这些，甚至还有更多，都会是我的！】；第一张后置帧仍含事件淡出残影，第二张已是运行地图，
  因而后置判断以稳定末帧为准。全程 18 个动作中 12 个键盘、6 个鼠标，日期从 1066-09-15 推进至 11-06
  （52 日）后 Space 暂停，最终 `map_hud`、`ok=true`、tracked cleanup 成立。前一候选
  `20260822T162157Z-opening-e64b42bd` 的 Shift+1 实际已经生效，只是旧判断把淡出首帧误作事件仍在；该 RED
  保持原结论，修订后使用新提交和新环境运行，未重标或重用原候选。
- 连续事件提交 `c9d2c31` 首次候选 `20260822T164851Z-opening-ccfefe4e` 已成功处理前两个普通事件；第 3 个
  【挑战】的 `Shift+1` 又立即串出【优势】，旧后置判断把新的事件页误作原事件未关闭，故该 run 保留 RED。提交
  `f6bba36` 将稳定的新标题/选项页作为链式事件继续处理；新环境
  `eb7479741e26a9688720951129b8c376cf19b1471cab2ffd7ea2490939ec6ec0` 的
  `20260822T170117Z-opening-eaeef47a` 随后 GREEN：目标 3 个普通事件，实际处理【诺曼人的西西里】、
  【患病：肉体凡胎】、【患病：宫廷医生】、【患病：治疗时间】和【患病：些许起色】共 5 页；全部使用
  `Shift+1`，22 个总动作中 16 个键盘、6 个鼠标，日期从 1066-09-15 推进 451 日至 1067-12-10 后暂停，
  tracked cleanup 成立。普通地图等待改为只对 `x=.23..48,y=.22..80` 事件栏做不落盘 CUDA OCR 预检，命中后
  才保存两张全屏确认帧；同一实机事件图裁剪约 0.172 秒、全屏约 0.456 秒，五事件归档 663.9 MB，与此前单事件
  run 基本相同。
- 地图面板快捷键提交 `75642ca`、环境
  `e3f8504582f19b19cd0ed10b3d3b04303c519064e20be6eddd8546631df66135` 的实机
  `20260822T172415Z-opening-d20b8adb` 为 GREEN：处理【诺曼人的西西里】后暂停，用 F2/F3/F4/F8 依次
  打开、双帧 OCR 读取并关闭【我的领地】【军事】【内阁】【决议】。26 个动作中 20 个为键盘、6 个为开局阶段
  无可靠直达键的鼠标动作；最终 `map_hud`、tracked cleanup 成立。决议面板上的红叉同时证明【扩大公国领地】等
  当前不可执行，策略层不得仅因 OCR 看见决议标题就点击。
- 首个经济建设提交 `c16e22f`、环境
  `86d5e8847bd0591dfa4f9811544f7eb979b4da1d79c63254fca50b79e8f2f3a4` 的实机
  `20260822T190656Z-opening-bfa943a7` 为 GREEN。F2 进入【我的领地】后，原版 `Alt+1..N` 只遍历已存在的
  `GUIBuildingItem`，不会选中空 `+` 槽；2560×1440/100% UI 下左侧普通空槽中心为 `(461,1398)`，右侧
  `(763,1398)` 是公国建筑槽。执行器只在这里使用布局点击，随后 OCR 看到三个【修建】候选，并按可见经济文本
  选择第 3 项【等级1：简易牧场】（成本 150、赋税 `+0.50/月`）。CK3 启动工程后的地产行实际显示
  【22个月内完工简易牧场】而不是【正在修建】；后置条件因此匹配稳定片段【个月内完工】。该 run 共 31 个动作，
  22 个键盘、9 个无可靠快捷键的鼠标动作，最终返回暂停的 `map_hud`，报告 `ok=true` 且清理完整。
- 用户真实纪录靠 tutorial.txt 备份/恢复保护；默认 selftest 与 `on-first-life/off` 会剥掉 `xar_hs_ge_*` 行（纪录 0），`on-recorded` 固定预置 100；`--import-record 100` 仅改变 selftest。
- restore watchdog 等 runner 退出后，只终止 runner 启动的 CK3 PID，再用临时文件 + `os.replace` 原子恢复并做 SHA-256 校验。2026-08-20 实测发现宿主超时会终止 runner 的整个子进程树，普通 `Popen(CREATE_NO_WINDOW)` watchdog 也被一起杀死，遗留隔离后的 `dlc_load.json` 与测试 autosave；已从该次精确 backup 全量恢复并核对六项 hash。watchdog 现由 WMI `Win32_Process.Create` 启动在 runner 进程树之外。2026-08-19 另实测 dev selftest autosave 会让下一次 release 投影扫描已剥离的 `xar_selftest` 规则键并误报；现启动前先完整复制并校验全部 `autosave*.ck3`，写 ready 标记后才移走，结束时删除测试 autosave 并恢复原件。
- 2026-08-19 长期平衡摇测发现当前播放集还启用了四个自动控制/改宗 mod，会污染领地、信仰与资源结果。runner 现同时备份 `dlc_load.json`，启动前把 `enabled_mods` 精确收敛为 `mod/ugc_3784706360.mod`，杀死测试 CK3 后再恢复；watchdog 同样覆盖此文件。
- `--artifacts-dir` 只创建调用方给定的新目录；CI 上传只包含从本次日志 offset 起的新内容，严禁用 `%TEMP%\xar_accept*` 通配上传，因为 `xar_accept_backup_*` 可能含玩家现场。
- gameplay Python 策略、OCR 条件或单步控制修改不要求重启 CK3。2026-08-23 的实机开发使用
  `opening-dev-session` 在同一 PID 38416 内连续执行 71 个命令，覆盖存档、王朝/继承、婚姻和巴勒莫战争；每条命令前热加载模块。
  只有 mod/runtime/启动参数改变、需要确定性状态复位或正式里程碑验收时才 cold start。纯 `strategy-review` 必须在窗口绑定前返回；
  同一会话实测从原 UI 路径约 6 秒降到 11 ms。
- 原生 CK3 检查点使用 Esc → `1`（保存游戏）→ Enter 接受默认名；2026-08-23 实测保存
  `阿普利亚公爵，罗贝尔_1067_08_01.ck3`，约 10.2 MB，并记录 SHA-256。恢复测试必须通过主菜单【载入游戏】读取 CK3 自己的
  存档列表与日期，不得用复制文件冒充游戏内载入成功。
- 一代制 roguelike 的死亡测试分两类：有继承人时原生【继续扮演】仅允许作为延迟投递生产结算事件的技术载体，之后不得执行
  任何继承人 gameplay；无继承人时直接使用注入原生继承窗的【退出到菜单】。两类最终都要记录结算分数并回到主菜单。
  非 debug 常驻会话不能为测试强制 `die`，不应因此重启；先用历史 `10_death_settlement.jpg` 和确定性模拟链回归，等自然死亡再做实机终验。
- 2026-08-23 首个 `auto-turn` 在速度 5 下等待普通事件 180 秒，超时后没有暂停；游戏随后继续从 1067-08-02 推进，丹麦
  【召集加入战争】信函被旧普通事件栏裁剪漏检并过期，地图可见记录【无视了国王斯温的召唤参战 -20】。因此常驻循环不得把“等到
  下一个事件”为无界动作：`life-advance` 只开放约 10 秒现实时间窗口，无事件也必须返回 GREEN 且 `map_hud` 暂停；外交信函另用
  中央 letter lane 预览，稳定后用原生 `Shift+2` 选择【同意】。普通事件、外交信函和死亡终端现共用一次裁剪 OCR，避免同一轮询
  重复推理。同一 PID 修订后已连续推进、暂停，识别并处理真实事件【锈迹斑斑的工具】，把单回合实测从 41.3 秒降至 26.75 秒，
  并在三个回合后自动保存 `阿普利亚公爵，罗贝尔_1069_01_21.ck3`。
- 常驻开发会话的 `auto-run N` 必须按子回合顺序更新同一份策略历史，而不是把 N 次动作当成一条不可见宏。2026-08-23 实机先发现
  `auto-run 2` 的带参数命令名未被历史展开器识别，导致周期存档少算两回合；修订后下一批真实执行先保存
  `阿普利亚公爵，罗贝尔_1069_05_08.ck3`，再推进到 1069-06-25。回归应使用带数字的真实命令字符串，不能只测裸 `auto-run`。
- 纯原生 `native-auto-run` 必须先建立 named pipe driver，再在后台启动持有 launch/state lock 的 `native-session`；停止顺序相反：
  先设置 session stop event 并等待 `stop_tracked` 返回 `tree_gone=true/cleanup_proven=true`，最后才关闭 driver。外层不得重复获取
  session 已持有的锁，也不得先关 pipe 后等待 CK3。initial readiness 要在同一 PID/generation 上同时闭合 exact-build hello、
  default-OFF containment/recorder、paused map、存活 episode character 与同日期 main-thread mailbox；cold checkpoint 还要闭合
  `driver_state_restore_kind=cold_checkpoint`、`episode_binding_state=active_resumed` 且无 candidate rejection。
- 正式一代续跑前先执行 `native-one-generation-preflight`。这是严格的 no-launch/no-desktop 检查，不需要 DLL 或 injector，也不会调用
  OCR、输入、窗口或 CK3 launch 路径；但全局 `--bridge-pipe` 仍必须是合法 Windows named pipe。命令行必须显式 pin
  `--expected-character-id`、`--expected-episode-run-id`、`--expected-checkpoint-sha256` 与
  `--expected-driver-state-sha256`。检查顺序是：双源 CK3 进程清单为空、prepared profile 全量 verify、v2 checkpoint 绑定、
  同 pipe 的真实 native driver consumer 全量解析、四项 pin 精确相等。driver preflight 与 live `_read_driver_state()` 共用
  `load_native_driver_state_for_resume()`，因此不能用只检查 anchor 的轻量 parser 绕过缺失 `bridge_pid` 或历史中段损坏。
  无论结果如何都原子落盘 `state/preflights/<run-id>/report.json`；GREEN/RED/argparse 退出码分别为 `0/1/2`。这个 artifact
  只资格化“可从指定恢复点开始下一次正式运行”，不启动 CK3，不能替代 live readiness、自然死亡或 committed settlement。
- 完整一代验收使用独立 `native-one-generation`，不得把 `native-auto-run` 的 bounded `turn_limit` GREEN 当成替代。该入口始终要求
  pipe 名与 v2 cold checkpoint driver state 完全一致，在首个 gameplay action 前把 checkpoint 和 driver state 复制到本次
  `state/runs/<run-id>/seed/`。默认每 3 个 verified eligible advance checkpoint；这是动作次数，不是游戏日，和平
  `life-advance` 通常约 30 天一步，因此默认大致形成季度级恢复点。turn/wall bound 耗尽必须返回
  `bounded_incomplete` 并写 `first-blocker.json`。唯一 GREEN 终点是本次执行的 `death-terminal` 同时闭合：初始
  episode CharacterID/run 未变化、terminal reason 为 dead/changed/missing、settlement ready 且 source/score 匹配、record persistence
  已证明或明确无需、cross-run episode 已记录、继承人 gameplay 为零、cleanup proven。终局已存在于启动帧、裸
  `status=terminal`、`strategy-review`、ACK 或 `settlement_unavailable` 都不能计为一代完成。
- 战时自适应 speed-3 首次实机 A/B 必须等当前 production owner 与 CK3 进程树完整退出；不得抢占仍在运行的同名 pipe。
  先把最新 checkpoint state 在静止状态复制到新的 `%TEMP%` 子目录，并逐字节核对源/副本的
  `profile/save games/xar_checkpoint.ck3` 与 `native-session/driver-state.json`；副本继续使用 driver state 已绑定的 pipe 名，
  然后从包含候选 Python policy 的干净 runtime 执行：

  ```powershell
  & "<python>" "<candidate-runtime>\ck3_autonomous_player\agent.py" `
    --state-dir "<fresh-cloned-state>" `
    --game-dir "<CK3-dir>" `
    --bridge-mode native-headless `
    --bridge-pipe "<checkpoint-driver-state-pipe>" `
    --bridge-dll "<exact-build-xar_ck3_bridge.dll>" `
    --bridge-injector "<exact-build-xar_ck3_bridge_injector.exe>" `
    native-auto-run --turns 40 --timeout 7200 --readiness-timeout 300 `
    --cold-start-checkpoint
  ```

  旧 production artifact 直接作为 speed-1 baseline，不重复消耗一次 CK3 长跑。候选若在 40 turns 内没有至少 6 个
  `timeline_policy=remote_enemy_route`，结论是“未命中/inconclusive”，不是 GREEN 或 capability RED；可从其最新 checkpoint
  继续同一隔离 A/B。命中后逐项重算：`requested_horizon_days` 必须仍为 `1`，action 必须恰好一次
  `set-speed-3 -> resume-map -> pause-map`，最终 `paused=true`，且实际 `elapsed_days` 逐条记录，不能由 fixture 或 speed 数值
  假定。首次生产切换门槛是：speed-3 的最大实际跨度不得超过同一 production 段 speed-1 已观察到的 3 日上界；每个起始帧
  均通过完整 player/war projection 与 full-route-disjoint 重放；after frame 能看见任何新 route/contact/battle 并令下一片回到
  speed 1；没有 player route、combat、retreat、Assault 或 exact route-contact transaction 使用 speed 3；游戏日/现实小时相对
  baseline `207` 至少提高 `2x`；周期 checkpoint、source clone hash 与 managed cleanup 全绿。任一项失败就保持正式长跑旧策略，
  保留 report/driver history 后再校准，不用 bounded fixture 冒充 speed-3 调度实证。
- 2026-08-28 使用同一个 immutable `date_raw=53209560` checkpoint（SHA-256
  `A8DD4034C32856B8D1E05D6B834BBBF3C51AA74DA038BB22A0CA23A998AD76CF`）完成三轮 clean-runtime live A/B，专门区分
  Python transcript/history 复制成本与 native `life-advance` 本身。只比较每轮 runner 已进入 turn loop 后的运行段，不把 cold launch
  或一次 12-turn 样本外推成长跑稳定吞吐：

  | runtime | 运行段 | query 首 / 尾 | life-advance 首 / 尾 |
  |---|---:|---:|---:|
  | `79b8d2a` | `48.134s` | `3.398s / 2.579s` | `5.065s / 4.600s` |
  | `e0688c7` | `44.875s` | `3.317s / 2.516s` | `4.583s / 4.111s` |
  | `9ff04ae` | `24.684s` | 约 `0.050s / 0.068s` | `4.569s / 3.643s` |

  最终 `9ff04ae` 轮为 `12/12` turns、`6` gameplay、`6` queries、`2` checkpoints；每个 gameplay turn 都是
  `timeline_policy=player_tactical / speed=1 / elapsed_days=1`，每次动作后 `paused=true`，managed cleanup 全绿。最终 checkpoint
  为 `date_raw=53209704`、SHA-256 `39379D0224788198FECCCA82DA4B7B7257DB7E1AEE6B3750F62AA845E312678A`，driver-state
  SHA-256 记录为 `D47DAA...BDA`。因此这三轮证明 query/history 热路径可在真实 CK3 loop 中降本，却没有命中
  `remote_enemy_route`，不能用来把 speed 3 升为 production-live；相同玩家 12-hop route 与敌军追尾仍应选择 speed 1。

  对应的确定性 instrumentation 必须和 live wall-time 一起保留：life history 完整复制 `9 → 1 → 0`；planning transcript
  复制 `1 → 0`，局部计时约 `600.637ms → 5.813ms`；termination query 内部复制 `3 → 0`，局部计时约
  `1815.527ms → 1.852ms`。最新全 unit 为 `1341 passed, 2 skipped, 900 subtests passed`，独立审查 `PASS`。
  query 已降到几十毫秒不等于 native life 已免费：最新首/尾 life 仍为 `4.569s / 3.643s`，后续优化必须由新的实测拆分证明必要性。
- `first-blocker.json` 以 first-write-wins 保存当前失败尝试，而不是事后取上一条成功 turn；它包含 plan、selected step、action
  result、before/after paused binding、事件/互动/WarID/ArmyID 摘要与最后 durable
  checkpoint。它表示 runner 看到的第一个停止点；bound exhaustion 是 harness incomplete，不能自动升级为 capability RED。真正改
  对应策略前仍须先更新该域的 exact-build 原生 AI 专题；梳理完成后允许先做最小 blocker-removal 并把质量差距记账。
- `driver-state.json` 是恢复状态，也保留完整 command history；不得为每条纯只读命令同步重写已经增长到数十 MB 的整个文件。
  2026-08-27 production 战局的冻结状态已有 `2744` 条 history、`79,517,587` bytes；同一 paused 日期连续执行
  `132` 次 move preview 与 `35` 次 route-contact query 时，旧实现每条都 deepcopy 全 history 并 pretty-print atomic replace，
  实际把只读扫描放大到分钟级，证据见 [army-controller.md](ck3-native-ai/army-controller.md)。成功的 `query-*`、合法
  `preview-move-army-*` 与 `preview-active-combat-retreat-v1-*` 因不改变 CK3 frame，可以只先进入内存 history；下一条非只读
  command、任意失败、其它 driver-state 状态迁移或正常 driver close 必须同步冲刷完整 suffix。这样动作 ACK 返回前仍把其前置
  query/preview 与动作一起持久化，`save-checkpoint` 的 v2 history anchor、managed restore 的 pre-relaunch marker 与失败 artifact
  合同均不变；硬崩最多遗失末尾成功只读 suffix，恢复后必须重新查询，不能把遗失 cache 当成 gameplay 进度。
- 2026-08-28 对 immutable seed
  `20260828T003711Z-one-generation-0e6e6129/seed/driver-state.json`（SHA-256
  `26AB2BF062E5605560087B428E6D131985D076EEE3172E9D42BD898F51D0CE27`，`79,884,717` bytes，checkpoint history
  anchor `4087`、含其后 deferred query suffix 共 `4096` rows）的
  逐字段剖析确认另一项动作 barrier 固定成本：旧 `_war_progress_summary` 在每次 timeline advance 的 before/after 中复制一场战争的
  全部 objective province state；该局典型是 `187` 行，其中 `172` 行未占领、无 active siege 且 besieging strength 为零。历史策略
  实际只从这些 state 读取 active siege 的 work/progress、besieging strength 与 assault 状态；完整目标身份已经独立保存在
  `war_objective_province_ids`，军队、路线、war score 与日期也各有字段。新投影因此只持久化带 `active_siege` 对象的 state，同时保留
  完整目标 ID 和全部其它 tactical 字段；读取 v2 旧状态时原位执行同一幂等压缩，使既有长跑在第一次 barrier 就获得收益，不必重开
  episode。冻结 artifact 的确定性重放删除 `312,650` 个 inactive historical rows，编码结果为 `16,818,672` bytes
  （减少 `78.946%`）；同一进程重复 compact JSON 编码的中位数由 `0.4133s` 降至 `0.1034s`，同卷 atomic replace write
  由 `0.0626s` 降至 `0.0064s`，所以每个动作 barrier 的可重复 Python 固定成本至少减少约 `0.366s`。确定性单测还要求
  active-siege work 原值、完整 objective ID、history index/command 顺序与 same-PID restore 全部不变；这项优化不裁剪当前 paused rich
  snapshot，也不改变 checkpoint cadence、存档 SHA-256 或恢复语义。
- 冻结 history 上把两次完整 `choose_one_life_turn`、一条 deferred route query record 和随后一条 route advance action barrier 合在同一
  端到端 Python A/B，七次中位数由 `0.4936s` 降至 `0.1343s`（减少 `0.3593s`）。每次样本都严格是 `1` 次 encode + `1` 次
  atomic write：成功 query 本身 `0` 次，advance 将 query suffix 一并冲刷；当前 production route path 也使用 internal semantic snapshot，
  没有 public full-history deepcopy。单测锁定这个调用数，因此没有证据支持再拆 WAL、降低 checkpoint 频率或改变恢复合同。
- 同一 seed/date 的 speed 1–5 production-path matrix 也排除了另一条错误优化方向：除 speed-3 第一次 route query 的一次性
  `2.9461s` 冷异常外，该 run 后续同类 query 为 `0.0731s` / `0.0662s`，所有其它有效 runs 都在 `0.0487–0.1015s`；完整
  `choose_one_life_turn` 在 `4096` rows 上中位约 `0.010s`，capability projection 约 `0.00018s`，fresh proof scan 约
  `0.00030s`。因此不得为这个单次异常重构 query/proof/planner；matrix 中 exact +1-day turn 的 speed 1/2/3/4/5 实测分别为
  `3.1841s` / `2.2505s` / `2.1723s` / `1.8114s` / `1.3805s`，需要优先消除的是每个 advance 都会支付的持久化固定成本。
- `xar_checkpoint.ck3` 是原位覆盖。保存命令开始提交后、完整 post-snapshot/hash/history 验证前失败时，core 必须撤销同路径旧
  metadata 的 `recoverable` 声明；readiness preflight 在提交前失败则保留旧恢复点。`native-one-generation` 对前一种失败只能回落到
  run 开始前归档在 `seed/` 的 immutable checkpoint + driver state。
- `service.auto_turn()` 的 plan+execute 在普通异常返回前仍是不透明的：若 selected step 未知，或已知为 `save-checkpoint` 但提交状态
  未闭合，继续撤销 live path。若 typed exception 已携带明确 non-save step，则 canonical checkpoint 不可能被该 step 覆盖，保留上一
  durable anchor；`StepPostconditionError` 的 gameplay 尾部在 cold restore 时由 history anchor 截断。
- `GameplayBridgeService` 必须把已选 plan/step 附在所有 `BridgeUnavailableError` 子类上；这不改变异常类型，也不声称命令是否发送，
  只让 runner 可靠区分“明确 non-save step”与“step 未知”。例如 route timeline query 返回 unavailable 时，报告仍须保留原
  parameterized query literal，并以最新 checkpoint 为恢复点；不能因 plan 丢失回落 immutable seed。
- 2026-08-28 formal run `20260828T061802Z-one-generation-9d1b52c5` 实测了一种更窄的零提交形状：planner 基于 public revision
  `517` 选择 `query-war-entry-assessments-v1-1-29097`，执行入口 fresh snapshot 为 `518`，revision gate 位于 request sequence
  分配和 `endpoint.send()` 之前。该路径必须抛 `PreSubmissionRevisionMismatchError` 并保留 plan/selected step。runner 只允许一次：
  重新等 readiness、更新本轮 before、重验同一 episode，再运行完整 fresh planner；不得把旧 step 直接换绑新 revision。第二次仍
  mismatch 就停止，但仍保留上一 durable checkpoint，即使旧计划恰好是 save，因为 typed gate 已证明没有提交。成功 turn 在 artifact
  记录 `pre_submission_revision_replans=1`；普通 `BridgeUnavailableError` 不重试。
- committed-route multi-day production composite 只在 `committed_route_sentinel_live_ready=true` 时广告。计划 step 必须是
  `committed-route-sentinel-advance-army-<subject>-to-<target>-until-<date>`；driver 逐项对拍 scope/subject/target/bound、
  完整无重复 controllable watch、零 active combat/retreat，并要求 arm `combat_count=0`。结果 scope 必须仍为
  `committed_route`，从 resume 到 native stop 之间必须零 external pause/RQ/overshoot。原 active-battle parameterized step 仍强制
  `combat_count>0`，不能与 route scope 互换。当前 production 默认已由 cold continuation
  `20260828T080926Z-one-generation-9e0ac8cb` 验收：5 臂共 44 日，接触同日停表，全部零 external/intermediate pause、零
  running rich query 与零 overshoot；任何改变该 native stop envelope 或显式绑定合同的后续实现都须重新做 cold live 验收。
- 2026-08-27 正式全寿命续跑 `20260827T104548Z-one-generation-5eb950f7` 在第 97 回合命中真实 harness B1：此前
  `96/97` turns 成功，包含 `44` 个 gameplay turns 与 `14` 个 checkpoints；CharacterID `29829` 仍存活，cleanup 全绿。
  `first-blocker.json` 报告 `native gameplay revision mismatch: expected 159, current 160`，SHA-256
  `9243C785F434C8354D5D39E921A093FC748C30D9D3C2E2033145724F89DD81D1`；`report.json` SHA-256
  `7F5ECDCF1133BF4D071425B29D542F069F2812086866489DE196A28A3CE17994`。错误发生在 opaque composite 返回前，故正式
  wrapper 仍按合同撤销 live path 并指向 immutable seed；不得从该报告本身声称未知内部动作未提交。
- 同次故障的独立事后取证确认：最后一次已完成 checkpoint 位于 turn 93、`date_raw=53196960`、history `1996`，且
  `xar_checkpoint.ck3`、`last_save.ck3`、`autosave.ck3` 字节完全一致，SHA-256 均为
  `1D6A994388232C130AE1BD168132D9ECBE6825725D7FF8E53A4A8C3F9E4F443D`；失败尾部没有再次提交 save。它可在新 state
  中作为人工重新冻结并逐字节验证的 cold seed，driver history 必须回退到其 `1996` anchor，不能把失败分支的尾部 history
  当成已持久进度。
- 此类 revision turnover 的回归合同是有界重新观测：一般 planner 必须 re-plan；只有 composite owner 能证明某阶段可安全重入时
  才允许内部重试，并必须验证目标后置状态。首个最小例外只给 `life-advance` 暂停收尾一次 fresh-revision `pause-map`；它已在
  `20260827T112207Z-one-generation-3c7aa5e2` 越过旧边界并形成 17 个新 checkpoint，但随后由 production artifact 证明连续
  running revision 仍可在同一暂停窗口耗尽一次重试（`expected 183, current 185`）。第一次更新后的 timeout 收敛在
  `20260827T115837Z-one-generation-9bed68f0` 连续成功 47 回合并保存 7 个新 checkpoint，随后又由真实 speed-five 帧流证明
  public revision 可在完整 10 秒内持续变化，最终明确超时。exact production DLL `51fe8cf` 的 `pause-map` handler 不解析或比较
  wire `expected_revision`；它自己 fresh-read CK3，已 paused 就返回 `already_paused`，否则提交幂等 `paused=1` 原生命令。
  因此最新最小合同只让 `life-advance` 内部 pause owner 跳过 Python 的冗余 public-revision 预检：提交前仍 fresh-read，一次请求只
  记一个真实 ACK，并在同一剩余 deadline 内等待真实 paused 后置帧。不得外推到 direct primitive、query、其它 action 或旧 plan。
  单元测试只授予 static-ready；必须从最新显式 checkpoint SHA `578B0289...5C38` cold restore 实机越过超时边界并再产出合格
  checkpoint，才能关闭该 blocker。
- 2026-08-28 的后继正式 run `20260827T163217Z-one-generation-ace7cbcf` 暴露了不同的 post-ACK 形状：`85/86` turns、
  42 gameplay 与 14 checkpoints 后，composite 已提交不受 public revision gate 约束的 `pause-map`，但原 10 秒窗口没有观察到
  `paused=true`。report/blocker SHA-256 分别为 `49D2A8BB...B50808` / `A0BD8C79...A484`，cleanup 全绿。它不能改写成 GEN-012
  复发，也不能在缺失 ACK status/窗口帧时断言 queue drop。
- opaque `service.auto_turn()` 的通用 invalidation 会把 first-blocker 回绑本轮 immutable seed，但本例另有确定物理证据：history
  `2960` 是成功 `save-checkpoint`，其后只有成功只读 query 与失败 life，无新 save；磁盘 `xar_checkpoint.ck3` 为
  `date_raw=53210712 / F15D383B...35559` 并匹配 driver metadata。把该 checkpoint 与 driver state `D272510F...FA323` 复制到新
  state 后，cold restore 会验证 history anchor 并截断失败 tail。未修改 `9ff04ae` 的独立 4-turn 重放随后两次 life 均 GREEN，生成
  更新 checkpoint `date_raw=53210760 / 79B71103...85F2`；这证明原错误是瞬时故障，但不撤销 RED。
- GEN-014 的最小回归合同是在原绝对 deadline 内最多两个 pause 请求：第一次 ACK 后只观察 1 秒；latest observed frame 仍是同 bridge
  generation、episode、map-ready、speed/event 的 running owner 时，才补交一次 exact handler 已证明幂等的 `pause-map`；随后只以
  真实 paused snapshot 成功。没有第三次、不重置 deadline，owner 漂移直接失败；失败 evidence 保留每次 ACK status 与第二次
  request 错误，direct primitive/query 完全不变。确定性测试必须
  覆盖一发成功、第二发成功、两发仍 running、owner 漂移、non-revision error 与原 GEN-012 路径；live gate 必须从
  `79B71103...85F2` cold restore 越过同类 slice 并保存更新 checkpoint。
  当前 blocker-removal 的 focused 测试为 `12 passed, 10 subtests passed`，完整 native driver 为
  `153 passed, 128 subtests passed`，全 unit 为 `1344 passed, 2 skipped, 908 subtests passed`，独立复审 PASS；这些只授予
  `static-ready`，不能替代上述 live gate。
- 2026-08-26 default-OFF 实机连续执行 12 次成功的战时 `life-advance`，但自动 planner 没有选择 checkpoint；最后的
  66,426,917-byte 存档是控制器显式提交，不能倒推为周期存档成功。原因是 active-war 分支在通用
  `periodic_checkpoint` 统计之前早返回。因此生产 owner 另行只累计 `life-advance`/`economic-event-cycle` 中
  `progress_status=postcondition` 且 snapshot 有语义变化的回合，每三个后在第四个 gameplay action 前强制物化 checkpoint；
  query、ACK、失败、同帧 cache 更新都不计数。验收必须重算文件 size/SHA 并核对 native history anchor，不能只看 command ACK。
- 2026-08-26 `native-auto-run --turns 6 --cold-start-checkpoint` 在 default-OFF production12 上完成首次生产 owner
  实机闭环：PID `81684` 从 checkpoint 日期 `53176104` 冷恢复，依次执行三次同帧战争终止查询与三次
  `progress_status=postcondition` 的一日 `life-advance`，推进至 `53176176`；第 3 个 eligible advance 后立即写出
  66,420,106-byte checkpoint，SHA-256
  `E8041581C789C21792280A893325082452F8A9717C8CDD421358FF9739189F07`，其 `history_index=166` 与当时 history tail
  相同。退出后 CK3、injector、host 均不存在，`tree_gone=true`、`cleanup_proven=true`，且没有新增 crash bundle 或
  unsafe marker。随后 PID `34084` 从这份新 checkpoint 再次冷恢复到同一日期与角色，证明产物可加载；该重放在四个
  fresh route preview 后因所有 objective 路线都与敌军 `357` 的 `target/route` 相交而按既有策略停止，并完整回收。
  因此“周期存档和恢复”已实证闭合，但“从任意检查点继续整局”仍受 exact combat/contact forecast 缺口阻断；不得把
  第二次的安全停止写成完整自治通过。
- 2026-08-26 同一 `53176176` checkpoint 的首轮 route-contact 诊断在 native reader 执行前 RED：ticket 仍为
  `queued`，被通用 2 s wait 取消；exact EXE SHA、adapter 与 timing bindings 已通过，不能把这次超时归咎于
  RVA/ABI。修复让同一 queued ticket 最多保留 8,000 ms，若已进入 `executing` 则以 2,000 ms slice 等到
  terminal；2,200 ms delayed-pump fixture 验证原 ticket 只执行一次并正常 reclaim。最终生产 DLL SHA-256
  `7AF3472A67218BDC407693D93A51826E2D99E29DB101EF724DC0B10FA60DC524` 的重放在 2.466 s 返回
  `available`，mailbox `executed_requests 0 -> 1`；完整敌军 scope 的 route timeline 证明一日无接触，controller
  才执行 speed 1 paused-to-paused 的 `53176176 -> 53176200`。war snapshot 发生语义变化，随后物化 checkpoint
  SHA-256 `51A3C202D6785988F3E3E7F028B64C4F0949DD83A4E32F3222E286B110224BE8`，normal cleanup proven。
  该 GREEN 只验收 production arrival/一日 contact horizon；同日 stored order 与 actual contact sides 仍未闭合。
- 2026-08-26 post-fix continuation 从 `53176200` 依次完成 `12 + 30 + 90 + 60 + 15` turns 的五轮托管冷恢复，
  五轮全部 qualified；连同修复后的首轮 3 turns，累计 `210/210` successful turns、78 个 visible gameplay turns，
  从 `53176176` 累计推进 75 game days 至 `53177976`（续跑本身增加 74 days）。过程中多次执行 route horizon 与
  普通 clear-route advance，抵达 `2568` 后逐候选 preview，对 `2600` 完成 candidate contact horizon、提交 move，
  并完成周期及最终 checkpoint；全程没有 recovery，每轮 cleanup 均 proven。当前 checkpoint SHA-256 为
  `12FD30A079982E3B01FAD6442574D7938E795A84A59B4EBDD53023135B04F37D`。这是持续自治进展实证，不代表整局已经
  完成，也不改变 `actual_contact_scope_ready=false`。
- 2026-08-26 `query-battle-control-snapshot-v1` 用 fresh production bridge 从 checkpoint
  `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63` 托管冷恢复，PID `80196` 连续推进
  maneuver day 1/2/3、main day 0/1/2。main day 1 与 2 均读到真实 current/soft/hard ledger delta；双方
  `CCombatSide+0x98/+0xA0` tick-start cache 在 damage 后稳定落后于 retained-entry derived sum，两个 match flag
  如实为 false，而每帧 immediate query pair 仍 canonical-equal、sequence 严格增加。artifact size `1253493`，
  SHA-256 `A0FC6BB7268E38026CC8EED6D6388BFD675AD5DCFB60A1A65FE1C1B64E816AC6`；DLL SHA-256
  `2F50F14699B8E6D9DF468DCFBEDD145814E50CAC0204D70A32E8CBFD36C34E8F`，injector SHA-256
  `B22548AEC9EE2B60EBA14CCDE2290AA1CED47EE5D2D277D5031742D683E0F1A3`。session/shutdown、`tree_gone`、
  `cleanup_proven` 与 driver close 全部通过；该 GREEN 关闭 battle identity/hold observation，不关闭 retreat command。
- 同一 checkpoint 与 fresh DLL SHA `490E90B41AF43747E43CAE104D11DEFA20D3E27353577114DB7874E1ED09A190`
  又完成 active-retreat expanded projection 的 17 帧 progression：elapsed day 0–14 均为 native/legal false + `too_early`，
  day 15/16 在 main phase 变为 true；artifact SHA
  `FB521B39AD5529434596212DB9ADC1EA27D4C270D28D13575B9A2D80913BCF40`。随后 full-side action harness 在 day15
  对 target `2579` 完成 exact preview/token/order，并在更新 paused snapshot 实见 CUnit `83886341` 为 retreating、target/route
  均为 `2579`；artifact size `627856`、SHA
  `A57FF20DCAD39DF79DAB6A9418054C36B0F5489C5D8B5E9E880CE899AE89DF9C`，cleanup proven。旧 battle query 因
  retreating subject 拒绝，故该 GREEN 只关闭 semantic action，不关闭 prior-CombatID winner/phase 完整 postcondition。
- 随后的 full-CombatID lifecycle query 不再依赖 retreating subject eligibility。同一 immutable save 的 managed v6 run 在
  full-side 命令后直接读取 prior `CombatID=335544325`，实见 `main/12 → pursuit/0`、winner=`defender`，attacker
  `[83886341]`、defender `[357,33554657]`，并保持 source save SHA
  `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63` 不变。artifact size `629571`、SHA
  `21D58737126CA4ED8B0B49DB7749EA4701F3BA6F94A8B8493698F8737E5784FA`；DLL SHA
  `BD7C309E27EE2A8C1432A501CB45ADC0C2E0A33FC2D83D23B78E311CB63009AB`，injector SHA
  `7AB872D0F364527EFB1581D7B2E3025B14441CE0426900A7894F38794121FDD3`，managed cleanup 成立。该证据关闭
  homogeneous-owner full-side postcondition。
- 2026-08-26 owner-subset v13 随后从同一 immutable source save 完成完整 managed GREEN。production-only
  session 先推进到 date `53178624`；non-debug 临时 `production + mod_bridge` seed session 用
  `province:2543.province_owner` 解析动态 Character `36108`，换人/清 guard 后各取得两个不同 request ID 的完整
  paused poll frame。只迁移 seed save bytes 后，fresh production-only PID 重新绑定 Character `36108`，exact preview/token/order
  只撤 CUnit `357`；同日 native state 为 retreating、target/route `2581`，旧 CombatID defender 从
  `[357,33554657]` 变为 `[33554657]`，attacker 仍为 `[83886341]`、phase `main/12`、winner `none`。artifact size
  `790823`、SHA `7780B619B2E7B90B8D5D5030D779F58F266585A6246A79B6C2FE20EF0F2701F9`；source hash 未变，所有
  session、tree 与 driver cleanup 均通过。`character:<number>` 只能解析历史数据库 key，不能拿动态 save CharacterID
  当链接；动态对象必须先从已冻结的 province/title/army 等 live scope 锚点解析。
- 同一实机还确认 `-continuelastsave` 在 fresh copied profile 中解析 `save games/autosave.ck3`；只复制根目录
  `last_save.ck3` 或另存为 `save games/last_save.ck3` 会在 `error.log` 写
  `Could not load save game [autosave]` 并回到主菜单。所有 fresh acceptance stage 必须把目标 bytes 物化到精确
  `autosave.ck3` 槽，同时保留 source SHA 校验；ACK 或根指针不能替代 map-ready snapshot。
- 2026-08-26 `BattleReinforcementAssignmentV1` 在 disposable production profile 上完成 paused、只读 managed GREEN：
  subject CUnit `357` 连续两次返回相同 frame（frame SHA
  `F410E1A5F19BF16F5C8AE34B62E69A10DAA0B7C55E178E16749EE27003DE5023`），exact build、capability、main-thread
  generation、CombatID `335544325` membership、完整 route 与 cleanup 全通过。artifact size `36470`、SHA
  `F0A6F3C73D49AE93CC20680E23E787F28B54CA086DAD80392E27651DAB1DB9C6`；source/clone save SHA 仍为
  `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`。本帧 `asking=true`、`assigned=false`，
  因而只关闭 query production-live，不关闭 assigned+aligned ETA/join gate。实机同时证明 active combat 中 direct
  `CUnit+0x30=2579` 可与 ArmySnapshot 的 remaining-route endpoint `2581` 不同，验收器必须分别校验这两个契约。
- `run_planner_battle_control_live_acceptance.py` 随后在自动创建并删除的隔离 profile clone 中，直接调用 production
  `choose_one_life_turn` 完成两轮 battle query→one-day advance→requery：`CombatID=335544325` 不变，日期
  `53178264→53178288→53178312`，maneuver day `1→2→3`，两轮均返回 `same_combat_advanced`；retreat action 数为 0，
  source autosave SHA `9104CCB8...CC63` 前后不变，cleanup 与 clone removal 均成立。artifact size `432082`、SHA
  `96CE25384517F0060A58623958DE071F43C3C2F7B68AEB6E668473E986C1DD57`；这关闭
  `planner_battle_hold_live_ready`，不关闭 forecast/retreat strategy。
- 2026-08-26 `run_battle_terminal_journal_live_acceptance.py` 用 fresh MSVC DLL SHA
  `BF2FB694358604D53DBE5AC553EC88C720F0540539333126EC68680F5002A5E0` 从同一 immutable active-battle save 托管冷恢复；
  仅执行 33 个“一条命令正好一天”的 `life-advance`，在 date `53179056` 观察到 `CombatID=335544325` 的 passive journal
  sequence `14`。terminal kind 为 `normal_result`，old CombatID 已从全局 storage 与 Province `2586` 双重删除；retained
  ResultID `553648135` 的 relevant-player count 为 `1`，WarID `16777290` 新 row index `2` 记录 `2135850` Q100000，
  war-attacker relative delta `-2135850`。玩家 CUnit `83886341` backlink/active combat 均清空，movement raw `3`，即使其
  AI membership 子域为 typed `unavailable`，仍由独立强证据得到 `subject_retreating`。两次 immediate paused frame 相等，frame SHA
  `D4815EFB4F71C99524DEDBDAB6CBEEDB0A5ADD19647CB668B77A7693D1D480BF`；完整 artifact size `772939`、SHA
  `61D0D912206A90D9B34DDE3555AEC941EC3538C253DBC4DCEB9D177D7456FDB1`。source save SHA 前后仍为
  `9104CCB8...CC63`，same bridge PID/generation、shutdown、tree gone、driver close 与 disposable clone removal 全部成立。
  该 GREEN 关闭 production normal-terminal query，不替代 no-normal、residual 与 assignment-reopened fixtures。
- 2026-08-26 reinforcement join 预夹具 v4/v6 保留为可重放 RED。v4 证明 contact 前 AI parent 的真实布局为单行
  `[357,33554657]`，不能硬编码两个 subunit row；artifact SHA
  `0D222C1A4C0676E63B0A775FCF3CE899D5483BBB96BD07125B421AD42736575E`。v6 在 date `53177040`
  得到 `CombatID=436207632`、Province `2596`、attacker `[83886341]`、defender
  `[33554657,357]`：helper 已在创建帧中，不存在 assignment/ETA/join 中间态；artifact SHA
  `A87D2272095FE5BE931DF2FF9B3E1EC117A7A4860D51CB7FEF75C21335EAF757`。两轮 source hash、managed
  cleanup 与 disposable clone removal 都通过，但不得升级业务 readiness。后续固定改用 owner-subset retreat 后的
  assignment-reopened 路径。
- 2026-08-26 owner-subset rejoin v1-v3 进一步证明“撤退后仍由玩家控制”不是合法的 AI assignment-reopened
  夹具。v1 artifact SHA `33D2A136ADB2909F2F19043234C073E831184061344BEE7F5A3EEA5994595107` 首次实见
  `battle-reinforcement snapshot changed; retry after heartbeat`；runner 只为这条明确只读 transient 加入最多 6 次/8 秒、
  且禁止跨日/跨 episode/unpaused 的整束重采样。v2 SHA
  `F15EA207F3024FC60786A02BECB4B5CD321888E8F73A2C4AE9C46086F875629D` 越过 transient 后发现 lifecycle drift；
  v3 SHA `33C65F95085718A120FFC2EB1BD766F3C37CC4C728B9BC77BBFCAC4D327F0F57` 完整保留诊断：从
  `53178624` 到 `53179272` 的 27 个一日 advance 中，CUnit `357` 每帧都是
  `unavailable/subunit_backlink_mismatch`，结束撤退后仍 `controllable=true`；旧 `CombatID=335544325` 最终进入
  `pursuit/0`、winner attacker，stored roster 仍为 `[83886341]` 对 `[33554657]`。三轮 source 不变、托管回收与
  disposable cleanup 均 GREEN，但业务 readiness 均为 RED。下一夹具必须在 production 撤离存档后同日 seed-switch
  回原玩家，再 production-only reload 观察已恢复 AI 控制的 `357`；不得继续等待玩家军生成 AI assignment。
- 2026-08-26 四阶段 AI reassignment v4 又证明“恢复 AI 控制”与“重新挂回 AI coordinator”不是同一帧。artifact SHA
  `E64CB22B4C4129C0DEF43CB463F1F9DA90BC38095E0706236CA35AC3796831A2`：同日切回原玩家后，fresh
  production-only reload 上 CUnit `357` 已 `controllable=false`，但仍为 native retreating state `6`、Province `2586`、
  route `[2581]`、`in_combat=false`，所以其 reinforcement query 合法返回
  `unavailable/subunit_backlink_mismatch`；anchor `33554657` 同帧仍 available。旧 `CombatID=335544325` 保持
  `main/12`、winner none、`[83886341]` 对 `[33554657]`，terminal=`active_not_terminal`。source 不变、三个 managed
  session 与 disposable cleanup 均通过，业务 RED 只来自 stage 3 错把 immediate pair availability 当作 AI-control proof。
  后续 runner 必须先独立证明 `controllable=false`，再在最终单一 production PID 内逐日等待 backlink/member 重建；只有随后
  捕获 assignment、aligned ETA 与同 Combat rejoin 才能关闭 readiness。
- 四阶段 v5（artifact SHA
  `88BF6AB94C1658B915F06C625CBAD6CAC46ADFD325F57BF978D4D902B217CA57`）进一步关闭了“重挂接时两军必须同
  parent”的夹具错误。最终 production PID 精确推进一天到 `53178648` 后，`357` 已由 mismatch 变为 available，但属于
  `CArmy=344`、coordinator `33554513`、unit-stack index `1`、parent `[[357]]`；anchor `33554657` 同帧属于
  `CArmy=50331769`、同一 coordinator、unit-stack index `0`、parent `[[33554657]]`。这是原生 other-stack matching 的
  真实前置形态，不是 drift。该帧 `357` 尚在 retreating state `6` 且 asking/assigned=false，旧 Combat/terminal 仍 active，
  因此 v5 仍不关闭 assignment/ETA/rejoin；runner 应只把 subject 自身完整 membership 作为 reopen gate，再等待跨 stack
  assignment，不能要求先与 anchor 合并 parent。
- 四阶段 v6（artifact SHA `4AFE99B8F239871D3869D24E940AF4725E093352B715224DBECEFBB2D90EE248`）已把
  `native_pair_reopened_after_retreat_live_ready` 关闭为 GREEN，但也证明当前两军夹具不可能产生所需 assignment。31 个 paused
  frame/30 个严格一日 advance 中，`357` 第一天以独立 CArmy `344` 重挂，第 9 天到达 `2581` 并结束 retreat；全程仍
  asking=false、assigned=false、target null、no_assignment。旧 Combat 从 `main/12` 走到 `main/39` 再进入
  `pursuit/0..2`，terminal 一直 active。原因与 `0x1848310` 静态树一致：分离后 anchor parent 只剩
  `[[33554657]]`，singleton parent 会清 asking，other-stack helper 无 requester 可匹配。延长 bound 没有价值；下一 fixture
  必须有至少三支同侧 CUnit，使撤一支后 requester parent 仍有两个 subunit。source、四 managed stages 与 disposable cleanup
  均 GREEN，但 assignment/ETA/rejoin readiness 仍保持 false。
- 2026-08-26 `campaign-root-context-v1` 用 fresh DLL SHA
  `F070E5E0C9AE248F25E12F9FEAF948E5C96E1E3BD3B6B59B08538A5BEF6F2F5E` 完成两个 immutable checkpoint 的
  production `query/query/save -> 新 PID cold query/query`。独立 Character `29829` 场景 artifact SHA
  `DA5EB7F01A48A2869B8C9B6B2F6607825FA5319715F66D2C0D04AFFCF802CDDC`，实值为 duchy `2141`、capital
  `2619`、top=self；附庸 Character `36108` 场景 SHA
  `677C4FF9727A479B40D068EC7E62A7AC54EF2E21A3EF57649D624C7648B279F9`，实值为 duchy `2296`、capital
  `2543`、immediate/top `37011`。两场均发布 `feudal_government` 的完整 5 flags 与当前 playset 的 84 个 selected
  setting tokens；各自两 PID、相邻双查询、cold business equality、source SHA、managed cleanup 与 nonce cleanup 全 GREEN。
  首轮 RED 证明 save 会合法推动 snapshot/public/native revision；查询稳定 gate 必须保持 save 前严格同帧，save 后改验同
  date/episode/paused 与 revision 单调前进。当前尚未覆盖另一 rank/government 或 landless 合法 absent，不得把“两角色”写成
  “两 rank 已完成”。
- 2026-08-26 `loaded-feature-manifest-v1` 用 fresh Release DLL SHA
  `F05C7DACB657114B1F85CB1C93925409906E1606F5847E16A6F9D98C5452D60D` 在单一受管 PID `13232` 完成 paused/map-ready
  同帧 query sequence `1 -> 2`。`date_raw=53178264`、public/native revision `4/3`；两次完整 normalized frame 严格相等，
  发布 44/44 index/CStringId/key rows、当次 playset 44 个 true flag 与 29 个 unsigned-UTF-8-bytewise 排序 runtime
  `has_dlc` key，entitlement 明确保持 `unavailable/store_verdict_provenance_unclosed`。源存档 67,287,758 bytes、SHA
  `9104CCB8...12CC63` 前后不变；155.073 秒受管 session、进程树与 nonce disposable root 均 GREEN。artifact 位于
  `C:\Users\xenoa\AppData\Local\Temp\xar-loaded-feature-manifest-live-v1.json`，SHA
  `2B1C8CA495A3A03F39C8C27351411B5AED2285D732946AACF5AFE89D8B3C2F2D`。runner 只允许两条只读 query；不得把
  全 true 或 29 keys 写成 hard-coded fixture，更不得将 runtime key 推断成 ownership、entitlement 或宗教语义。
- `pending-character-interaction-context-v1` 的非宗教实机验收由
  `native_bridge/research/run_pending_character_interaction_context_live_acceptance.py` 执行。它只读复制 immutable source
  `xar_checkpoint_pre_white_peace_53175816.ck3`（SHA
  `5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F`）：seed PID 在暂停态证明 WarID
  `16777290` 为普通 `claim_cb`，以 raw production bridge 发出 white-peace offer，再由 repository `mod_bridge` 同日切换至
  recipient CharacterID `36108` 并保存 pending checkpoint。只有 checkpoint bytes 进入第二个 fresh production-only
  userdir；新的 PID cold reload 后必须在同一 revision 连续执行两次 typed query，证明完整 pending ID、canonical key
  `end_war_attacker_white_peace_interaction`、角色/路由/选项/期限/合法性与只读 query sequence。runner 不会默认 accept、
  reject、block 或 acknowledge，并检查原 source 字节与元数据不变及受管清理。当前 snapshot discovery 会先过滤
  `+0x5C6` auto-accept notification，故本验收只覆盖 ordinary pending interaction；ACK 分支仍是明确未闭合的 discovery
  依赖。宗教专用语义继续 owner-deferred，不得借此夹具探索。
- 2026-08-26 上述 runner 用 fresh Release DLL SHA
  `152FB65A9F302B67423F5AE604AEE0DD9A791498E74C9CA924E47DCAF14F568C` 完成 GREEN。seed PID `93972` 创建并保存
  pending checkpoint（66,579,686 bytes，SHA `3ABF8B9750911910D95B6AE2108B71BAA040613B3E4410578F1C4F76F16019DF`），
  production-only PID `39180` 冷恢复后，两次同 revision query 都返回 full pending ID `738197506`、date `53175816`、
  stable key `end_war_attacker_white_peace_interaction`（hash `3450334569`）、roles `29829 -> 36108`、route kind `0`、
  target absent、exclusive/zero send options、deadline `0/60/60`、accept/reject/block true 与 acknowledge false。
  structured costs/exchanges/effect preview 保持 typed unavailable，semantic readiness 为 false，runner 未执行 reply。
  139.363 秒后两个进程树与 nonce root 均清理；source SHA 前后仍为 `5BA21369...CFFFC5F`。artifact 位于
  `C:\Users\xenoa\AppData\Local\Temp\xar-pending-interaction-context-v1-live-20260826-04.json`，SHA
  `D20E339D56AFEFF8EB53F90FFD120AA8C42216AD214D38B7AC1B0EA9A2B8BC89`。
- 同一轮首个诊断暴露两项 runner/normalizer 约束：typed query action 必须由当前 snapshot 的真实 pending ID 动态展开，
  seed 前只能检查 hello capability；Python 对 JSON 解码后的 status 字符串必须做值比较，不能用对象 identity 比较。
  两项均有单元回归。失败报告的所有嵌套 stage 字段也必须按 nullable object 处理，否则会遮住真正的 seed/live 错误。
- 同轮旧增量 MSVC build directory 曾产出注入后 `C0000005` 的 RED。原因不是 CK3 ABI 漂移，而是中文编译器
  `/showIncludes` 输出未被依赖跟踪解析，`game_contract.hpp` 已变更却仍链接旧对象。`native_bridge/CMakeLists.txt`
  现只针对已实测的乱码探测值，把 Ninja 的依赖前缀修正为编译器实际输出的 `注意: 包含文件:`；fresh `v1h`
  构建中 `bridge.cpp.obj` 已记录 18 个 header dependency（含 `game_contract.hpp`），`ck3_11906.cpp.obj` 也包含该公共
  header，full CTest `23/23` GREEN。exact bridge 改公共 header 后若出现只在旧目录复现的入口崩溃，仍须先用全新
  构建目录复核，并记录候选 DLL/injector SHA；不能把“build 命令返回成功”当作所有 translation units 已按新 header
  重编译的证据，也不能为消除 RED 去调用任何会写真实 combat 的 refresh helper。
- 2026-08-28 的 Visual Studio 18 / CMake 4.3 fresh configure 又实测到另一条合法输出：`rules.ninja` 已直接以 UTF-8
  保存 `注意: 包含文件:`，不再是需要 code-page 逆转换的 mojibake。`build_fresh.ps1` 现在只接受两种 exact 结果：
  已正确的 direct UTF-8 原样保留，或旧 CMake 的已知 mojibake 做一次确定性修复；其它前缀继续 fail closed，随后仍必须由
  `ninja -t deps` 证明 `ck3_11906.hpp` 同时进入 producer/consumer 对象。fresh Release 目录
  `xar-native-gen015-20260828T0145Z` 以 `direct-2052-utf8` 模式完成 `37/37` CTest；DLL/injector SHA-256 分别为
  `50227D28...831F2` / `2F6CEB43...35B5C`。这是构建兼容修复，不放宽公共 header 依赖门禁。
- 2026-08-31 实测当前 `PATH` 中裸 `ctest` 可能解析为 `C:\cygwin64\bin\ctest.exe`。它会把 Windows CMake 生成的
  `C:/.../test.exe` 再错误拼到当前目录，表现为全部测试 `BAD_COMMAND / no such file or directory`，实际 0 个 test binary
  被执行。这是 runner 调用错误，不是 native capability RED。Windows build 必须使用 Visual Studio/CMake 随附的原生
  `ctest.exe`（当前为 `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe`）
  并把 build directory 设为工作目录；同一 G2 build 随后真实完成 `44/44` GREEN。
- 2026-08-30 在普通 PowerShell 外壳内串联 `vcvars64.bat` 与 `build_fresh.ps1` 时，`cmd.exe` 会在执行整行前展开
  `%PATH%`；若在 `call vcvars64.bat` 后再写 `set "PATH=<cmake>;<ninja>;%PATH%"`，该旧值会把刚注入的 MSVC
  `cl.exe` 路径覆盖掉，helper 会报 `cl is required`。同机 `vcvars64.bat` 还要求先让 Visual Studio Installer 目录中的
  `vswhere.exe` 可见。可复现做法是先把 Installer 目录加入 PATH，再用 `cmd /v:on` 和延迟展开
  `set "PATH=<cmake>;<ninja>;!PATH!"`；随后 fresh 222-step Release build 与 `44/44` CTest GREEN。失败构建目录应换
  新名字重试并保留，不能复用成“fresh”证据。
- 2026-09-01 G2 GEN-034 的三项 Raiktor offline contract test 已补入
  `native_bridge/CMakeLists.txt`：`xar_ck3_native_bridge_raiktor_surrender_six_domain_v1`、
  `xar_ck3_native_bridge_raiktor_surrender_truce_v1` 与
  `xar_ck3_native_bridge_raiktor_war_bound_regiment_v1`。clean `d7a2871` 的 CTest
  注册数由 68 增至 71；本次只扩大静态/fixture 覆盖，不增加 public wire、ABI、MCP 或 surrender action。
  用 Visual Studio 随附的原生 `ctest.exe`（不要使用 PATH 中的 Cygwin 版本）执行 `ctest --test-dir <build> -C Release
  -R raiktor --output-on-failure`，三项 focused tests 应全部通过；GEN-034 仍保持 unresolved。
- 2026-08-21 同一发布候选的第一次矩阵在第二格到达主菜单前发生 CK3 原生 `C0000005`，crash bundle 停在数据库图标初始化，无 fixture marker、无 blocking project diagnostic，运行树、EXE 与受保护存储未变。该 RED 必须原样保留；只有全新 userdir 的同格重试完整 GREEN，且随后另一全新目录的正式三格矩阵 3/3 GREEN，才能把它判为一次性引擎冷启动崩溃，禁止直接重标原报告。
- Windows Python Launcher 的 `py <script.py>` 会解释脚本首行的 `/usr/bin/env python3`，可能选中 `PATH` 里的另一套 Python，而不是刚由 `py -m pip` 安装依赖的默认解释器。2026-08-21 实测该分裂让非固定 Pillow 重建的三张 DXT1 DDS 与仓库字节不同，产生假 stale；项目 `.venv` 的 `Pillow==12.3.0` 与官方 CI 均 GREEN。遇到素材 parity 全红时先打印实际解释器和 Pillow 版本，本机 L0 优先直接调用 `tools\.venv\Scripts\python.exe`，禁止为消除环境假红而重写已发布素材。
- `ToggleGameViewData('character', GetPlayer.GetID)` 可能保留地图当前选中角色；要确定打开玩家本人，直接用原版 `button_me` 同款动作 `DefaultOnCharacterClick(GetPlayer.GetID)`（2026-08-18 实测）。
- trait 含原生 `track` 时，UI 会自动读取 `gfx/interface/icons/trait_level_tracks/<trait_key>.dds`；缺文件会在真正 hover 时写 VFS error，主 trait 的 `icon =` 不会替代它（2026-08-18 实测）。
- 原生决议右栏按钮是 `F8` 对应的羽笔图标；合成键盘无效时可按屏幕比例 `(0.987, 0.367)` hover，先 OCR 验证“决议”tooltip 再点击。低处条目必须在滚动框内下滚到中段后用 `deliberate_click`，否则底缘 hit-test 会关闭面板但不选中。决议触发的事件或 scripted GUI 关闭后，决议面板会随动画恢复；先等待并复查面板标题，再决定是否点 HUD，否则会把刚恢复的面板反向关掉（2026-08-18/20 实测）。

## 断点标记法（链路定位）

在每个环节插 `debug_log = "XAR: <步骤名>"`（项目约定 XAR: 前缀），然后：

```powershell
(Select-String -Path "...\logs\debug.log" -Pattern "XAR:").Line
```

链条断在哪一目了然。生成器生成的文件也可以带标记（本项目导入 scripted_gui 每条都带 k 值标记）。

## 运行时行为验证

- 全局存储落盘：直接读 `tutorial.txt` 数 `xar_hs_ge_*` 条目
- 控制台：`die`（死亡链）、`event xar.0001`（手动触发事件）、`effect xxx`（跑 effect）
- 修改后必须重启游戏（无热重载）；`-load` 启动参数实测无效（1.19.0.6）

## GUI 调试

- debug 模式工具栏：`Gui.Debug`、GUI Editor、Script Profiler
- 可视化调试面板：临时注册一个可见窗口，用 `text = "[Tutorial.GetStepText]"` 之类实时显示数据表达式的值（本项目用它发现 Tutorial 上下文在外部窗口为空）
- GUI 表达式解析错误：`error.log` 的 `pdx_data_factory.cpp` / `pdx_gui_factory.cpp` 条目（含文件行号）

## 自动化测试 harness（GUI 桥方案，已被 runner 取代）

GUI state + `ExecuteConsoleCommand` 可以在进游戏后自动执行控制台命令（打标记、设变量、触发事件）。注意：窗口必须注册；`ExecuteConsoleCommand` 在 state 的 on_start 里可用性未完全验证（本项目后来改用真实链路测试，最终定型为上文的全自动验收 runner）。

## Ox Here 多语言原生 UI smoke

`tools/run_ox_here_loc_smoke.py` 的 Workshop 模式先用 sidecar 严格验证 numeric cache leaf，再只在一次性 userdir
副本中移除 launcher 注入的 descriptor ID。每个语言必须使用新的 CK3 进程，并依次保留决议列表、详情、拒绝
tooltip、招募 tooltip、二阶段确认和到庭事件截图；每张画面自动拒绝 raw `ox_here_*` key。

2026-08-27 实机发现两个不能写死成单次坐标/单行 footer 的 harness 事实：CK3 偶尔会吞掉第一次 Decisions HUD
点击，所以必须以语言专属 ASCII anchor 的真实出现确认窗口已打开并有限重试；波兰语额外显示社区翻译版本行，会把
CK3 build label 上移，版本 OCR ROI 必须覆盖多行 footer。反过来，到庭事件已经可见而外部 scripted-GUI observer
未打 marker 时，保留 RED 与截图即可；不要把展示事件、代码合同或人工画面审核重写成 marker GREEN。

## 排障心法

1. **先分清"没加载/没注册"与"加载了但没触发"**——CK3 大量失败是静默的
2. 报错要看完整调用栈（"while building tooltip/description" 这类后缀说明评估时机）
3. 怀疑优先级：目录名 > BOM > 注册 > scope 类型 > 求值时机（并发/延迟）> 逻辑
4. 对照原版/成熟 mod（POD）的同类写法是最快的验证手段

## 分支与冻结 runtime clone 的验收边界（2026-08-30）

- `git branch --all` 只覆盖当前 Git common-dir。runtime/live 实验常是独立 clone，不会出现在主仓的 branch/worktree 清单里；
  全量收口必须枚举 workspace/process roots 与 `%TEMP%` 直属 `xar*` repository config，取得各自 `--git-common-dir` 后去重，
  再分别检查 refs、worktrees 和 dirty state。只扫一个 common-dir 不得声称“所有分支已审计/清理”。
- 冻结 clone 若在 fetch 时报告 `unresolved deltas` / `invalid index-pack output`，记录为该证据环境的 object-store RED，
  不把它升级为产品/capability RED，也不修复或删除现场来消除错误。在健康 audit repo 中无持久 ref 地读入该 local tip，
  再用 ancestry、patch-id 与逐文件内容证明它已被 master 等价或更强实现覆盖。branch ref 退休后仍保留 clone 与 marker；详见
  [branch-management.md](branch-management.md)。

## G1 一代人 production 终局（2026-08-30）

正式 run：
`C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\runs\20260830T070223Z-one-generation-1f934571`。

- 从 frozen checkpoint `0DF9CB66...69C` 冷恢复 CharacterID `29829` / episode
  `native-29829-ee172aa720db`，按 `50000 / 604800 / cadence 3 / speed 3` 运行；没有人工 gameplay。
- `155/155` turns 全成功：`101` query、`53` gameplay、`15` checkpoints、`1` terminal；墙钟 `424.216s`，
  `first_blocker=null`。
- 角色自然终止后 runner 继续等待到琉焰卿 committed settlement：`ready=true / commit_serial=1 /
  source_character_id=29829`；顶层、settlement、recorded episode 三处人生分数均为 `14.8`。
- cross-run record 已持久化到 `tutorial.txt`（lesson `xar_hs_ge_14`，两次稳定观测）；
  `continue_as_heir_after_death=false / heir_gameplay_actions=0 / no_heir_gameplay=true`。
- 全部 qualification gates 为 true；cleanup 的 session report、shutdown、tree-gone、driver close 均 GREEN。
- `report.json`：`2,515,261` bytes，SHA-256
  `FF689E88ED2C728D21BDF3AB66853E95435002D27979D37702C8A5D13E7BEFB3`。
- `terminal-settlement.json`：`274,412` bytes，SHA-256
  `D26744BFC619374A91499DAC6DDA178BD65B3666D5EF25A40DAD1433A41E850E`。

该 artifact 只证明 fixed production seed 的 G1 完整一生 OODA；不证明普通 campaign 跨继承或全游戏自治。

## GEN-032：死亡先于 tactical sentinel stop（2026-08-30）

同一 checkpoint `date_raw=53286864 / history=6320 / C2A5E6F4...C122A` 的三次 bounded production-native 尝试：

1. `20260830T071626Z-g2-seed-smoke`：`8/9` turns。第三个 stationary sentinel 期间，日期
   `53287200→53287296`、玩家 `29829→38822`，但 native sentinel 尚未发布 stop；旧 Python 只认 event/pending
   interaction，最终超时等待 pause。capability RED，cleanup GREEN。
2. `20260830T072905Z-g2-terminal-boundary-retry`：`8/9` turns。driver 已发布
   `one_life_terminal=true / played_character_changed`，但 explicit-pause stabilization 仍把同一 terminal 的日期漂移判成
   不同 boundary。capability RED，cleanup GREEN；checkpoint 未变。
3. `20260830T073735Z-g2-terminal-boundary-date-drift-retry`：最小修复后 `10/10` turns，`6 query / 3 gameplay /
   1 terminal`；`episode_complete / qualified / ok=true`，final `date_raw=53287296 / played=38822 / episode=29829 /
   settlement ready`，`first_blocker=null`，cleanup 全 GREEN。

这一步当时只允许同 bridge PID、connection generation、episode CharacterID/run ID、当前玩家与 terminal reason 下的日期单调前进。
后续 formal G2 又实证 terminal surface 可在显式 pause 服务期间从死亡角色帧演化为继承人已接管帧；最终合同见下一节：owner pins
保持不变，但不再要求 played-character/alive/reason 表面完全相等。active event 与 pending interaction 继续要求原 exact identity，
战争/终战偏好没有变化。

受管 state 的 episode seed 也已逐字节验证：`76,980,533` bytes、SHA-256
`E3B4A97D6B4E00BD4C3FF3E350FA9D883033712C939455446B0A5BC5719C5D91`、`date_raw=53211552 /
CharacterID=29829`。GEN-032 第三次 runner 在 `episode_complete` 返回，因此该时点只能关闭 GEN-032；随后 GEN-009/G2 由下述
严格 runner 单独验收，不能倒写早期 artifact 的能力边界。

## G2：`start-next-episode` 到新 episode checkpoint（2026-08-30）

正式命令（运行时另设置本 worktree 的 Git safe-directory 临时环境，不修改全局配置）：

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" ck3_autonomous_player\agent.py `
  --state-dir "C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state" `
  --game-dir "Z:\ck3_mod_rewrite\Crusader Kings III" `
  --bridge-mode native-headless --bridge-pipe "\\.\pipe\xar_ck3_restore_exact2_7aff1d0" `
  --bridge-dll "C:\Users\xenoa\AppData\Local\Temp\xar-gen031-war-query-build-20260828T2025\xar_ck3_bridge.dll" `
  --bridge-injector "C:\Users\xenoa\AppData\Local\Temp\xar-gen031-war-query-build-20260828T2025\xar_ck3_bridge_injector.exe" `
  native-next-episode --max-turns 30 --timeout 1800 --readiness-timeout 300 `
  --checkpoint-every-advances 1 --route-contact-speed 3
```

三次 artifact 均独立保留：

1. `20260830T101417Z-next-episode-1f7afbf7`：turn 9 capability RED。sentinel 真实推进 4 天并观察
   `played_character 29829→38822 / one_life_terminal=played_character_changed`，但普通 decision-boundary stabilization 拒绝
   terminal surface 演化；cleanup GREEN，最后 durable checkpoint 可恢复。
2. `20260830T102101Z-next-episode-77c4006e`：0-turn harness RED。另一个正式 ZhongGuo runner 持有 CK3 install owner lock；
   没有启动第二个 CK3，也没有抢占/结束已存在进程。
3. `20260830T102401Z-next-episode-23c58fa1`：`next_episode_checkpointed / qualified / ok=true`，`7/7` turns，
   `3 query / 2 gameplay / 1 checkpoint / 1 recovery / 1 terminal`，墙钟 `118.968s`，`first_blocker=null`。

GREEN 的权威链：

- source terminal 为 episode `native-29829-ee172aa720db`，score `14.8`；`start-next-episode` durable ACK request
  `next-episode-4de95f5265044abeb766a4af97a21919` 返回 `status=relaunched`。
- CK3 PID `57484→33200`，connection generation `1→2`；`continue_last_save=false`，明确加载
  `xar_episode_seed`。seed 为 `76,980,533` bytes、SHA-256 `E3B4A97D...C5D91`、`date_raw=53211552 /
  CharacterID=29829`。
- 新 binding 为 `active_new / driver_state_restore_kind=new_episode_seed`，run ID
  `native-29829-fffa4ba935f6`，不是 source run ID；在新 episode 完成一次可见 committed-route gameplay，日期推进
  `53211552→53211576`。
- gameplay 后 checkpoint 为 `76,979,955` bytes、SHA-256 `BB4CD2B5...DC235`、`history_index=4`，显式绑定新 run ID；
  15 项 qualification gate 全 true。
- cleanup 的 session report、shutdown、tree-gone、cleanup-proven、driver-close 全 true，结束后 CK3=0。两个 PID 的目标 UI
  thread 均逐次证明并保持 US English HKL `0x04090409`；证据是 artifact 内 `keyboard-initial.json` 与
  `keyboard-next-episode.json`，没有使用 OCR。
- `report.json` 为 `1,080,001` bytes、SHA-256 `22F54519F4FB52E9D0D633240D618DD8423847F1FF61A231FE71EA8A0F93E565`；
  `next-episode.json` SHA-256 `AC085365800EB5DE7963647FC49B3FEFB6C65C95145EA4B6414073880702B626`。

实机教训：one-life terminal 是 episode-scoped 的单调边界，不是普通 event identity。CK3 可在 runner 观察终局和显式 pause
稳定帧之间完成死亡角色到继承人的切换，因此只固定 bridge PID、connection generation、episode CharacterID/run ID；允许
played-character、alive 与 `played_character_dead→played_character_changed` 表面演化。paused/map-ready/fresh revision、同 episode
owner、合法 terminal identity 与后续 settlement 仍必须逐项验证。该放宽不得复用于 active event 或 pending interaction。

该 GREEN 只证明同一冻结 seed 的首个跨 episode OODA 与 checkpoint；第二个完整寿命由下述续跑单独证明。

### G2 第二寿命至再次跨局（2026-08-31）

正式 continuation 为
`C:\Users\xenoa\AppData\Local\Temp\xar-marriage-reject-c21c096-state\g2-runs\20260830T182851Z-next-episode-19d679de`。
它从 no-launch preflight 已逐项绑定的 `history=2181 / date_raw=53295288 / checkpoint SHA-256 816B8B02...6D26`
cold resume；fresh Release bridge 先完成 222-step build 与 native CTest `44/44`，DLL / injector SHA-256 为
`3B1BE173...4EB6 / 0E85B1F5...ACC6`。

- 结果为 `next_episode_checkpointed / qualified / ok=true`，`472/472` turns、墙钟 `1198.576s`；310 query、160 gameplay、
  151 checkpoint、1 terminal、1 recovery，`first_blocker=null`。
- turn 468 的原生 sentinel 从 `53319720` 自然推进到 `53319768` 时观察 `played_character_changed` 并立即暂停；没有执行
  `die`、控制台或任何人工死亡动作。turn 469 的 `death-terminal` 验证 matching episode settlement、score `0`、7 次 blessing
  与 `heir_gameplay_actions=0`。
- turn 470 的 `start-next-episode` 把 PID `72636→39036`、connection generation `1→2`、run ID
  `native-29829-fffa4ba935f6→native-29829-6e06850de2a3`，逐字节重载 immutable seed；turn 472 在新 episode
  `53211552→53211576` 完成可见 gameplay，并保存绑定新 run 的 checkpoint `56C00CDC...408E`（history 4）。
- 15 项 qualification gate 全 true；session report、shutdown、tree-gone、cleanup-proven、driver-close 全 true，结束后 CK3=0。
  report / terminal / next-episode SHA-256 为 `2D798DAB...C4DD / C72C3A11...667A / BB570624...33A3`。

本次 user turn 曾中断上一条长跑 `20260830T180744Z-next-episode-1cd83c9e`；其报告只到
`preflight_ready / finalized=false`，故归类为 harness/user-turn interruption，不得伪造为 gameplay RED。接手时应以
driver `last_checkpoint` 与 checkpoint 实物的 size/SHA/history/date 四项一致性选择最新 durable anchor，而不能只复用 provisional
report 的旧 preflight 输入。另一个实测坑是 CK3 线程在无人输入时仍可能被系统从 US English 带回中文 HKL；长跑需独立轮询
目标 UI thread，只在异常时发 `WM_INPUTLANGCHANGEREQUEST`，保留 before/after 证据，并始终留在 `0x04090409`。

该 GREEN 完成同一冻结 seed 的第二完整寿命与再次跨 episode；不证明不同 seed/ruler/government/DLC、普通 campaign 跨继承或
全游戏自治。

## ZhongGuo v0.4.x phase2：MCP-first 纵切验收（2026-08-30）

首纵切 #001/#018/#069/#357 的权威 GREEN artifact 为
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-worktrees\v0.4-main_process_assets\zg361\runs\zga_20260830_191131_7e82d061`。
顶层 `report.json` SHA-256 为
`409CF4366A7A96801CFE56C91792D11C7B779A6DEECB1D2DDDF4876C87D8DD6B`，`evidence-index.json` 为
`140E5FF79F37717B25D1233E02427ADE7F2031FAC6B7944B2ACCDA6AF979B450`。运行 `477.458s`，保护存储未变，
PID `31904` 的 job active `1→0`，process tree、watchdog、driver 和 runtime locks 均完成清理，结束后 CK3=0。

MCP-first 合同：

1. 通用 New Game/bookmark、acceptance-only initializer，以及一期 GUI 的截图抽样目前仍可使用**已登记的 startup/bootstrap
   视觉辅助**，因为尚无 decision-list/action MCP。它们不读取二期角色、头衔、事件、案卷或资源，也不参与 GREEN；因此完整
   runner 不得写成 zero-OCR。
2. 二期角色/头衔、可见事件 canonical definition、选项解析、typed submission 与独立 ACK 只能使用 frozen exact-build native
   MCP。`.50` 实例 `8` 在 public revision `53` 被识别，拒签为 rendered option `3` / native index `2`；提交 ACK 从
   `54→55` 并逐项证明 instance advanced 与 postcondition。随后 `.4` 实例 `9` 在 revision `60` 被识别，option `1` /
   native index `0` 的 ACK 从 `61→62`。不得用 OCR 或按钮坐标替代这些绑定。
3. 隐藏 `.51` 没有 event window，D+7 见证送达只能由产品 marker 与只读 fixture oracle 对账；两个 marker 各恰好一次，重复调用
   delivery/settlement 后资源不再变化。`.52` 的通用 timer marker 未绑定本案角色，不能冒充 `han_6875` 的案卷证明；`.53`
   本轮没有 live 命中，因此个人陈述重开仍是 `static-ready`。
4. OCR 只允许在 native identity 闭合后保存画面证据。任何 canonical key、revision、instance、option、ACK 或 receipt 不一致都
   保持 RED；不得拿视觉文字反向放行。
5. 当前 MCP 不发布通用 mod character variables、`treasury`、`merit` 等资源快照，所以这次 evidence 上限是 bounded
   `fixture-live`，不是 `production-live`。夹具只建立可重复前置条件并提供只读 oracle，不得直接写 grade、处分、receipt 或 PASS
   后置状态。

本轮还冻结了两个必须复用的测试经验。其一，visible multi-option interruption 在 `set-speed-1` 后必须等待**后续 public
revision** 再查询 event context；不能因为没有配置 preferred option text 就跳过 settled-revision 门。其二，CK3 多条件
`NOT` 不能承担 unset/value compare 的短路逻辑：新案把 settlement/refund posted serial 初始化为 `0`，事务只允许零值进入，
成功后写正数 case serial；验收准备态必须断言 `0`，不能继续要求变量不存在。对应语法索引见
[grammar/pitfalls.md](grammar/pitfalls.md)。

## ZhongGuo phase2 seed loader 早停门（2026-09-01）

`phase2_seed_20260901_042407_head_48fbe07_attempt07` 实证了一个不能再用“延长 readiness timeout”掩盖的阶段：bridge
transport 可以先连接并持续 heartbeat，但 CK3 仍可能卡在 database/script 初始化，尚未发布 semantic snapshot。该现场
`debug.log/error.log` 在 `04:26:53` 后逐字节不再增长，进程却继续运行到 `900s`；健康旧基线会继续出现
`Setting idler 'Frontend' → 'Load Save' → 'In Game'`。因此 transport GREEN 不是 map-ready，也不是 event waiter 的启动许可。

仓库工具 `tools/zg361_phase2_loader_stage.py` 把这条经验做成了可执行门：

```powershell
py tools/zg361_phase2_loader_stage.py `
  --log-dir "<isolated-userdir>\logs" `
  --progress-jsonl "<artifacts>\loader-stage-progress.jsonl" `
  --timeout-seconds 300 `
  --fatal-stall-seconds 45
```

- 输入只允许 CK3 自己 append 的 `debug.log/error.log`；输出也只 append JSONL。监控者不得轮询读取另一个 producer 正在
  temp-file + atomic-replace 的 partial report。attempt 05 已实证：Windows 上外部 reader 持有该目标时会令 writer 的 replace
  抛 `WinError 5`，制造与产品无关的 harness RED。
- early fatal allowlist 只覆盖 attempt 07 已实证且能归属 `events/zg361_*`、
  `common/script_values/zg361_*`、`common/scripted_effects/zg361_*` 的四类：非法生成 event 注册、算术 value 被当 trigger、
  `TICKET_SUBJECT` 未声明、`revoke_court_position` 缺 block。日志停在 database init 且含这些错误，quiet 45 秒后输出
  `loader_parse_red` 和去重 fingerprint，不再等待完整业务 timeout。
- `Theme missing` 单独计数但不触发 early fatal。fixture visible event 仍必须通过静态合同显式提供 theme；“不早停”和“可以留着
  不修”不是同一件事。
- 只有 `Load Save`、`In Game` 或 native semantic readiness 才授权进入 event wait。只到 Frontend 的 bounded 终点是
  `save_resume_red`，用于把 `-continuelastsave`/存档选择故障与 parser stall 分开；还没到 Frontend 时不得猜是旧 save 损坏。
- 双挂载必须由 `Mounted Data` inventory 判定。attempt 07 的 product/fixture 各恰好一次，且报错 event 在物理文件中各只定义
  一次；同路径 duplicate 是超限 ID 的恢复噪声，不能臆测为 descriptor/load-order 重挂。

离线门禁：

```powershell
py tools/test_zg361_phase2_loader_stage.py
py -O tools/test_zg361_phase2_loader_stage.py
py tools/test_zg361_phase2_seed_fixture.py
```

测试必须覆盖：已实证 parser errors 早停并去重、theme-only 不误判 fatal、普通日志从 database init 继续到 Load Save。下一次
真实 CK3 运行必须先清零当前 parser/compiler/theme 项，再用这一门做单局验证；不得直接再开 900 秒 blind wait。
