# G2-M4 玩家建设视图受控候选 c31886f0

状态：**READY_NO_LAUNCH；尚无本候选 CK3 paused 私有查询结果；建设动作与 M4 治理闭环未通过。** 候选清单在 `Z:\ck3_mod_rewrite_process_assets\g2m4-player-view-live-candidate-c31886f0\candidate-manifest.json`。CK3 本体没有进入制品。此目录独立于当前/历史预览 state、profile 与运行工作区；候选源是 master-only、无远端依赖的 Git 副本，checkout 为 `c31886f0571932546a4445faef61c08606830288`。

已核验版本：CK3 exact EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；私有选项默认 `OFF`，封存 Release DLL 中为 `ON`；DLL SHA-256 `2730604da481caa9052c7e5c4788ec24d32c77de391840a2cfe7483a5d342850`，injector SHA-256 `e8364379fbef1b70842560c91a2331327435a15ba5bd03834d64aa3e41ed20f4`。production-only profile 环境 SHA-256 `4628ae1d155ab1578e24c550253fb054d8be795ef32bfd6be2c2c3ae4cfbe22a`；加载清单是唯一 `mod/xar_autoplayer.mod`、`disabled_dlcs=[]`，游戏规则、显示、已装 DLC descriptor 指纹均在 candidate manifest 与 profile manifest 中。当前宿主 2560×1440 全屏、简体中文。

immutable seed 来源为 R697 的普通 production 一代 checkpoint，存档 SHA-256 `d8bdc3c44d21a6f94dc7e4c050db464f6c5036d5ba7e66233354b171f3401474`，paired driver-state SHA-256 `163850711947eacb8dfb3dec82e39bad332bd00bc119dbb36642ed701de4fb1a`。R697 的只读资格证据在 `Z:\ck3_mod_rewrite_process_assets\g2-preview-pay-ransom-eefc88e4\live-eligibility-attempt-1\report.json`：paused/native revision 3、date_raw 53178312、活玩家 29829、`feudal_government`、玩家所持 county TitleID 2102/2142/2173、capital province 2619；war/army/event/pending 全空。R697 **没有**读取本候选建设 cache；不复用后续 R698 覆盖的 preview state。

本候选的 `fresh-profile-state` 在 R700 回收 CK3 后由正式 `prepare_profile` 生成，随后复制 immutable source pair；`verify_profile`、`validate_cold_start_checkpoint_for_pipe`、配对 driver state 角色/date，以及正常/`-O` 封存制品 no-launch preflight 均通过，CK3 inventory 为零。`prepare_profile` 的项目实现明确拒绝任何 CK3 存活时运行，因此跨机器迁移必须从候选冻结 source 在目标宿主获授权、无 CK3 时重新准备独立 profile；只读查询接口可用不等于该宿主可运行 CK3。

当前单实例负责人取得新单调轮次后使用清单中的 Python、候选根 `run_g2m4_player_view_live_candidate.py`，传入真实 `--round`、独立 `--evidence` 和固定 `--candidate-root`。入口在同一 owner Python 进程启动一个 CK3，从配对存档冷加载，然后按现有 bounded contract 用正式 campaign-root query 资格校验，再执行不广告的私有 `g2_player_construction_view_probe_v1` 一帧只读查询，保存 paused frame/请求 ID/原始结果与无点击桌面截图，最终回收 CK3。上限为 readiness 300 秒、两查询各 12 秒、总 480 秒。完整断言和参数见 manifest；普通与优化模式预检已实际验证，**CK3 live 入口仍待负责人运行**。

cache present 时下一施工是 typed row、成本、原生最终 `CanConstruct`；cache empty 时立即从已定位的 player definition/holding 模型枚举补最小只读能力，不能推断“没有合法建设”。县窗口是否关闭只可由同轮同帧截图/GUI receipt 真实核验；没有 receipt 时 runner 保留 `closed_view_evidence_insufficient`，不称 closed-view GREEN。查询没有 construction typed action、独立游戏建设结果、后续 turn 消费或 cold restore 治理目标证据。入口和资格断言的设计边界见 [`g2m4-paused-player-view-read.md`](g2m4-paused-player-view-read.md)。
