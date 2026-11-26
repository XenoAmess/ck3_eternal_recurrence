# CK3 视频制作与交付手册

用于新成片、录像管线、审核与交付。运行或录制 CK3 前先读[实机与机器授权](ck3-operating-authority.md)，其它构建环境见[开发手册](repository-development-workflow.md)。月报视频与历史演示入口见[进度中心](../autonomous-agent-progress/README.md)。代码路径以仓库根为基准。

## 视频内决策内容

- 状态、决策、理由与实际结果取自当前决策 feed。影片标题留在最终编辑作品，场次标签作为身份元数据。
- 按下文 2026-11-01 更新后的规则在成片中合成文字。旧蓝色面板已退役，来源与适用范围见[原退役说明](../../promo/ck3_faith_and_power/integration/legacy-decision-panel-retirement.md)。

## 2026-11-01 实时决策只合成到视频

- 用户明确要求实时决策展示“没有边框”“半透明黑色”，直接渲染在最终视频里，不在屏幕上展示，也不强行悬浮前台。此要求覆盖此前桌面 Java 决策窗方案；后继不恢复 JFrame、置顶窗或桌面捕获来展示决策。
- 使用当前实际决策 feed 发布文本，再由已有录像管线合成；文字发布成功与视频实际绘制分别验证，不把源码配置或文件更新当作最终画面已经通过。当前制作参数为纯黑背景、60%不透明度、白字，无装饰边框。
- 自动游玩与 M0–M7 制作、原生研究和本地模型使用持续执行。显示修复不授权重放原 SAVE/ARM/RESUME，不重启当前 Game/DLL，不触碰用户的其它窗口。

## 可复用宣传视频工具链

- **汉晋春秋称号必须对齐模组实际显示（2026-11-01 用户更正）。** 该模组对称号有特殊处理，人物称呼不能套用原版 CK3 的国王、皇帝、公爵等称号，也不能由内部头衔等级、代码或地图名推定。导演稿、口播、字幕、封面与简介均按对应时点的模组实际展示核对；未核实时先用人物姓名。董卓可以称“郿侯”，严禁称“郿国王”；用户明确的称号为“相国、假黄钺、都督中外诸军事、录尚书事、郿侯、董公”。详见[拍摄复盘](../hanjin-spring-autumn-filming-lessons-2026-11-01.md)及[董卓专题](../../promo/hanjin_spring_autumn/research/dong-zhuo.md)。

- **机制卡片必须带相关游戏素材（2026-10-22用户指令）。** 卡片可继续用于比较、公式和机制讲解，但出现特质、信条、文化、技能、建筑或活动选项等正式游戏对象时，须在卡内嵌入相应原版图标、插画或界面局部，不能只列名称与数字。真实状态变化仍须由实际界面和原生后态支撑；卡片嵌原图不等于新增实拍。素材绑定实际版本、来源和动态条件，保持原色与比例，图集按原GUI选格，不能凭旧文件名猜当前分级图标。

- 可复用实现已拆到独立仓库
  [`XenoAmess/xar_promo_toolchain`](https://github.com/XenoAmess/xar_promo_toolchain)；用户入口、真实命令与能力边界以该仓库的
  `README.md`、`docs/architecture-and-migration.md` 和当前 `<verified-python> -m xar_promo --help` 为准。主仓不再
  vendoring 其源码，也不在这里运行其独立单测。**`xar-promo` 永远使用独立仓库最新正式 GitHub Release 的 wheel**：每次开始
  工具链任务或新 run 前先查询最新正式发布，不能把本机已安装版本、旧文档或旧 requirements 当作“最新”。发现新版时，先同步
  `tools/requirements-promo-toolchain.txt` 的精确 wheel URL 与发布 SHA-256，再用本次选定的解释器安装/升级并验证 `--version`、
  顶层及相关子命令 `--help`。requirements 的精确版本用于重现当次输入，不能成为长期停留旧版的理由。每个 run 记录实际版本与
  wheel SHA；已有 run 的版本记录、配置快照和素材保持历史原样，后续新 run 使用届时最新版本。本地开发或验收可设置
  `XAR_PROMO_SOURCE`（兼容别名 `XAR_PROMO_TOOLCHAIN_SOURCE`）指向独立 checkout 或其 `src` 目录。禁止为尚未接入的
  library API 虚构 CLI 命令，也不得把 plan、命令 ACK、schema 通过或单项自动检查写成“成片已验”。
- 严格保持四层边界：
  1. **通用包**（独立仓库的 `src/xar_promo/`）负责 `ProjectConfig`、每次 attempt 的 append-only `RunManifest`、配置快照、
     content-addressed 素材、TTS、字幕/布局、媒体探测、进程与审计原语；不得内置某个 mod 的文案、角色、声线或发布凭据。
  2. **Skill**（独立仓库的 `codex-skill/promo-video-pipeline/`）只提供操作方法、检查清单和能力路由；Skill 不是运行时实现，
     不能授权额外副作用，也不能声称不存在的命令或验收能力。
  3. **CK3 adapter**（独立仓库的 `src/xar_promo/adapters/ck3/`）只读验证既有 capture report、timeline、evidence index、原始录像、
     marks 与 clean spans；不得启动 CK3、用 OCR 猜缺失状态、修复/覆盖 RED attempt，或承载某个项目的故事与发布政策。
  4. **项目 preset**（独立仓库的 `src/xar_promo/presets/`）加各项目 checked-in config 负责章节、文案、语言、声线、时长、
     真实角色/测试 UI 等项目政策；各项目 legacy wrapper 在迁移期继续保持原 CLI、sidecar 与输出兼容。
- 下表记录已核验的十个 CLI 命令及职责；实际可用接口随最新正式版更新，以该版 `--help` 为准，不把此表当作永久版本或命令上限：

  | 命令 | 角色与副作用边界 |
  | --- | --- |
  | `init` | 新建 checked-in `ProjectConfig` 与首个绑定 run；已有目标拒绝覆盖。 |
  | `start-run` | 从当前 config 的精确字节创建另一个 `RunManifest` 与 config snapshot。 |
  | `validate` | 只读验证 config/run/legacy manifest；`--structure-only` 明确跳过引用文件 bytes/SHA 检查。 |
  | `preserve` | 把一个既有文件复制进不可变 content-addressed storage，并 append artifact 记录。 |
  | `signoff` | 在人工 1× 完整审阅后 append 对精确 artifact bytes 的 `approved`/`rejected` 决定。 |
  | `plan` | 必须显式给 `--composer MODULE:ATTRIBUTE`；永远只读，不建 workdir、不调用 provider，`--validate-only` 只用于显式声明同一合同。 |
  | `build` | 对原生 run 执行项目 composer；成功和 RED 的完成产物、partial、stdio 与 phase history 都必须保全。 |
  | `audit` | 写入并保全自动 audit 及其 evidence；不得读取、推断或写入人工 approval。 |
  | `review` | `--plan-only` 只读；否则只生成 `pending-human-review` 包，绝不记录 signoff。 |
  | `export` | 按显式 policy 验证或生成离线 bundle；`--dry-run`/`--validate-only` 不写目标，任何模式都不上传或发布。 |

  adapter/preset 只经本地注入或 Python entry-point 组 `xar_promo.adapters`、`xar_promo.presets` 解析；`plan`/`build`
  的 composer 是项目提供的可 import callable，不属于 registry，也不得被工具链猜测或自动发现。
- `ProjectConfig` 是可审阅的 checked-in 意图；每次 capture/render/audit attempt 必须创建独立 run/workdir，保存当时配置的
  精确字节快照。不得让后续配置修改重新解释旧证据，也不得把失败 attempt 改写成 GREEN。
- **过程素材按统一存储策略限期保留**：raw 录像/截图/音频、脚本、TTS 请求与返回、字幕、生成卡、章节段、concat 输入、
  中间编码、partial、失败 attempt、命令 argv、`stdout`/`stderr`、probe、timeline、evidence/audit/review 报告、sidecar、
  manifest 历史和最终成片按用途分级，不因“过程资产”无限期占盘。重跑使用新 run/workdir；回收不得改写历史结果，原件删除后追加可用性及精确回执。未完成交付的必要素材须限期保护；完成后的原片和中间物按到期规则回收。
- 自动 validation/audit/review package 只证明它声明并 hash 绑定的机器条件，**不等于人工按 1× 完整观看，也不等于 signoff**。
  人工签核必须发生在实际 1× 完整审阅之后，记录审阅人、结果、时间/说明，并绑定被审成片的精确 bytes + SHA-256；
  工具不得自行制造 approval。重新编码或替换任何字节后，旧人工签核自动不适用于新文件，必须重新审阅。
- 工具链的 build、audit、review、export 都不等于外部发布。每个 mod 仍必须走自己的 release staging、实机验收、
  Steam Workshop 上传、订阅缓存复核与 changelog 流程；宣传视频上传到外部平台同样需要独立明确授权。
- **后续视频交付使用 OneDrive 桌面客户端上传**（项目所有者于 2026-09-23 明确指定），单次只传输用户指定的视频文件。
  固定交付目录为 `C:/Users/1/OneDrive/CK3-War-AI-20260923/`；用户已明确采用“固定目录开启同步，后续直接放视频”的流程。
  复用该目录及已保存的选择同步设置，由客户端自动上传，不必每次重新配置或请求授权；不要把项目源码、素材目录或其他文件一起放入。
  用户此前“不许客户端下载其他任何文件到本机”的限制继续有效，除非用户明确变更；不得把渠道选择视为解除限制，
  或把按需下载、下载限速写成禁止下载。已有明确传输授权无需重复询问；如实记录实际上传结果，未上传不得写作交付完成。
- **视频本地交付例外（2026-10-21 用户指令）**：仅 `machine_id: 4-8e1c2f1861` 的当前及后续视频按
  [机器交付偏好](machine-preferences/4-8e1c2f1861.video-delivery.json)在本地交付，直到用户明确撤销或替换；
  该机不要求配置、重试或上传 OneDrive，以选定视频文件本地可读并提供实际路径为交付依据。本例外优先于上文该机的上传前置条件，
  其他机器原规则保持。连接不可用是用户报告，非本次联网测试结论；过程资产到期不撤销此偏好，也不授予视频文件永久保留。
- secondary/detached worktree 运行宣传工具链或其他依赖型 Python 验收时，先使用该 worktree 内约定的相对 `.venv`，并确认
  已安装本次查询确认的最新正式 `xar-promo-toolchain` wheel；不能为迎合历史指南降级。若相对 venv 不存在，只能**显式指定并先验证**主 worktree 的
  venv 解释器，同时设置 `XAR_PROMO_SOURCE`（若需源码调试）并在报告中记录解释器路径、版本和依赖 probe。禁止静默回落到
  缺依赖的裸 `py`/系统 Python，再把 `ModuleNotFoundError`、缺 Pillow/edge-tts 或找不到媒体工具误判为代码 RED；这类问题在
  完成解释器与依赖复核前只能标为 environment RED。
