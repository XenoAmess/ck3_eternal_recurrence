# 下一期项目配置与新 run 入口

本目录的 [`promo-project.json`](promo-project.json) 是 checked-in 拍摄意图：六章均为 `planned`，没有承诺成片、实机素材或精确片长。当前 28–32 分钟是导演案的剪辑预算，不设置 `duration_limit_seconds` 硬上限。`chapters[].artifact_ids=[]` 不是缺失素材已验收，而是尚未绑定实际新 run。内容取舍与来源身份以 [导演案](../director-plan.md)、[镜头表](../shot-list.md)及[素材准入复核](../capture-readiness-audit-20260928.md)为准。

## 已核解释器和工具边界

2026-09-28 再查独立仓库 [正式 Releases](https://github.com/XenoAmess/xar_promo_toolchain/releases)，v0.2.1 仍标为 Latest。requirements 精确 wheel SHA-256 是 `f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621`；主工作树 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 实际返回 `xar-promo 0.2.1`，安装元数据 `direct_url.json` 的 URL/hash 与 requirements 一致。该解释器的 `mcp=2.0.0`、`Pillow=12.3.0`，`init`、`start-run`、`validate`、`preserve`、`audit`、`review` 的实际帮助可调用。

本次隔离工作树 `D:/w/video_capture_prep` 没有相对 `.venv`，所以只对上面的**显式主工作树解释器**运行 config 校验。该解释器安装的 `ck3-war-ai-promo-integration` 是 editable，源码指向主工作树 `promo/ck3_native_war_ai/integration`；若未来在另一个 worktree 执行 composer/build，应建立并验证该 worktree 自己的相对 venv，或明确记录所借解释器与实际 adapter/preset 源码路径，避免配置来自 A 树而项目 composer 来自 B 树。这里未设置本地 `XAR_PROMO_SOURCE`，也未调试通用工具链源码。

以下校验已执行且 exit 0：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe -m xar_promo validate --profile authoring D:\w\video_capture_prep\promo\ck3_native_war_ai\episode-02-battle-second-half\project\promo-project.json
```

返回 `GREEN: format=project-config-v1; profile=authoring; chapters=6; artifacts=0; files_checked=true`。同一 ProjectConfig 用 `--profile release` 返回 `RED: release profile requires a native run manifest`，这是该 profile 的类型要求，不能把 authoring GREEN 改写成 release GREEN。

## 实际录制前才执行的 run 顺序

1. 先把本配置与导演案/镜头表合并到所用工作树并复核精确字节；再次查询当时最新正式 xar-promo Release，若有新版先更新 requirements 的 URL/hash、安装并重新 probe。核对 `--version`、顶层及将用到的子命令 `--help`，记录解释器、wheel SHA、editable adapter 来源、ffmpeg/ffprobe 路径与版本。
2. 与战争请求队列协调：R0271 优先。领取任务总线 `ck3-screen:acquired` 后才检查桌面、现有 CK3/录制占用，取得并审阅本次实时 Steam“离线模式”画面。新鲜度或离线门失败就保存 environment RED；不启动游戏。
3. 为一个明确取材目标冻结 source `.ck3` 及真实 checkpoint 回执、EXE/DLL/injector bytes/SHA、纯原版 profile 与实际 CombatID/WarID/日期。每个取材 attempt 有独立外置 state、output、pipe、recorder 和 run directory；不能复用历史 RED 目录。先 `capture_session.py` 无启动预检，显式 `--capture` 才受管启动；其默认不录正式 gameplay，必须另起唯一 recorder。
4. 取得本次 ProjectConfig 的原生 run snapshot 后，使用 `xar-promo preserve` 把精确 source save/receipt、工具版本回执、raw 视频、控制报告、逐日原始请求/响应、截图、时间 marks、clean span 检查和失败日志纳入该 run 的 content-addressed artifacts；同时在外置 attempt 保留全部原件。`preserve` 的成功只说明复制及 SHA 绑定，不说明该素材通过 CK3 adapter 或人工审片。
5. 新录像依自身新随机轨迹重算数字。拼接之前逐条审查 capture report、evidence index、timeline、原始视频及两端 clean frame gates，并用 v0.2.1 CK3 adapter 对**既有合格 bundle**只读验证。机器 audit/review 包完成后，实际 1× 全片人工观看并对精确成片 SHA 单独 signoff。

等根任务明确分配具体录制窗口和取材目标，再创建第一个生产 run。CLI 的真实 `start-run` 形状如下；`<...>` 只能以本次冻结的真实值替换，不要把示例执行成空 run：

```text
<verified-python> -m xar_promo start-run --run-id <new-unique-run-id> --run-directory <new-external-run-directory> <checked-in-promo-project.json>
<verified-python> -m xar_promo validate --profile authoring <new-external-run-directory>/run-manifest.json
<verified-python> -m xar_promo preserve --run-manifest <new-external-run-directory>/run-manifest.json --artifact-id <unique-source-artifact-id> --collection raw --role capture <exact-source-file>
```

`start-run` 会把当时配置的**精确字节**复制为该 run 的不可变 snapshot；后续配置修改不追改旧 run。是否生成 film build 则由项目显式 composer 决定，不能从 `start-run`、`plan` 或 `validate` 推出。此文档没有创建实际新 run、录像或 signoff。

## E2-01 无启动环境预检（2026-09-28）

候选短镜头为墨西拿战斗地图和双方身份。精确来源是外置 `episode01-full-edge-attempt-002/contact-combat-16777218-raw53146248.ck3`，本次独立哈希为 `45CCE7E9A7E505C878F661333DE30D6B459DA638259A9E99990A226CE564245F`；其真正的 `065-save-contact.json` 回执哈希为 `A29293E3DD817439EEF82353DFB2B6AAB6D0383BD0D551AE905A3665A751DB9F`。二进制候选为原版 CK3 1.19.0.6 EXE `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、`D:/workspace/cwb2/xar_ck3_bridge.dll` `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`、同目录 injector `CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247`。`ffmpeg`/`ffprobe` 均为 WinGet Gyan 9.0.1，实际路径由 `where` 核对。

独立无启动 attempt `D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-01-preflight-20260928-a01/ck3-output/` 保留 `command.json`（SHA `50D89FAF6D3C465A27846F9FBE3A612B7803015BB2D8ABA90B2A2562EFC3B852`）、`preflight.json`（SHA `E419AF2C9E5308C89AC90F31A98CC37B2D52BD94BE69EB6B854707D4E06C2987`）和静态能力字符串（SHA `EAE2678D3C73F4A0E77A86C74587F9DE4C3201B9741A0297C3606B2224639054`）。结果 `READY_FOR_BOUNDED_LIVE_ATTEMPT`、`ck3_started=false`、`runtime_capabilities_verified=false`，不能称为已拍或 live GREEN。

同轮只读 `desktop_steam_offline_recovery.py inspect` 于 2026-09-28 04:52:23 UTC 返回 `screen_owners=[]`、CK3/recorder PID 均空、唯一 Steam HWND `591018` 在前台，但 `steam_offline_status_observed=null`；未领取屏幕，未移动窗口，也没有当次新鲜离线画面或可传给受管启动器的完整回执。随后得知 R0271 所需 H3388 精确资产正在传输，视频实机暂让屏幕。待重新获准录制时，必须重新查 task bus 与战争请求、取得新鲜离线画面，再为 live 建**新的** attempt；不能把本次无启动目录加 `--capture` 重用。
