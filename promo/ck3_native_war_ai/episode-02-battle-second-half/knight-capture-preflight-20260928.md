# E2-04/05 骑士事件镜头：源档、无启动预检与录制方案

2026-09-28。R0271 占用 CK3 屏幕时只读复核历史报告，并在四个**全新外置 attempt** 执行 `capture_session.py` 的无 `--capture` 预检。四份结果均为 `READY_FOR_BOUNDED_LIVE_ATTEMPT`、`ck3_started=false`、`runtime_capabilities_verified=false`。没有新游戏录像或 clean span，也没有证明新回放会重复旧随机事件。

## 精确源档和分轨边界

下表路径均以 `D:/workspace/ck3_native_war_ai_promo_work/` 为根；哈希为本次对原件重新计算的 SHA-256。所有配对回执都是原生 `save-checkpoint` 成功响应，不是推测的文件名。四个源档均为原版、`enabled_mods=[]`、`xar_off`、玩家角色 `29829`，CK3 `1.19.0.6`。

| 拍摄入口 | 源档；bytes；SHA-256 | 真实保存回执；bytes；SHA-256 | 日期与使用限制 |
| --- | --- | --- | --- |
| E2-04 第 5 日事件 | `episode01-paired-counter-trace-attempt-010/d05-immutable.ck3`；52,172,645；`695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885` | `episode01-paired-counter-trace-attempt-010/ck3-output/interactive-requests-responses/d05-save.json`；13,437；`6650C0DB79D063E066AB72402735C22FAE9FCB5D458A56CE1C10B9545CD1F3C7` | `date_raw=53146344`；039 曾从这里拍到骑士 `34333` 致残，新回放须独立确认事件。 |
| E2-04 历史次帧对照 | `episode01-day05-wound-growth-attempt-039/d06-postevent-immutable.ck3`；52,181,389；`9ACACDE3E2D1987180EFE5FFDDC32B092146E6116779AF0D4BEBC7C97B9B7F9A` | `episode01-day05-wound-growth-attempt-039/ck3-output/interactive-requests-responses/008-after-save.json`；13,426；`0947BFCE60C184EBF5803D16BA34E84F36C52821513AB5C9B76BC0237F447301` | `date_raw=53146368`；040 **只**复载 039 后档。历史对照可拍独立来源卡，不能接在新第 5 日回放后冒充其下一帧。 |
| E2-05 第 26 日三条分轨共同入口 | `episode01-paired-counter-trace-attempt-010/d26-immutable.ck3`；52,880,496；`C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B` | `episode01-paired-counter-trace-attempt-010/ck3-output/interactive-requests-responses/d26-save.json`；13,452；`78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C` | `date_raw=53146848`；020 击杀者选择器、070 成长权重、036 随机列表是**三个独立回放**，相同源档不代表同一 RNG。 |
| E2-05 历史次帧对照 | `episode01-day26-random-list-type-attempt-036/d27-postevent-immutable.ck3`；52,797,811；`CD0648D7603290E470ED07261128C05FF449C0FFAEA89D01A1102D0D56208A55` | `episode01-day26-random-list-type-attempt-036/ck3-output/interactive-requests-responses/008-after-save.json`；13,446；`CBEDD4832CA78A8233A059E3CDC34C4C6E58948030F7F76703C8380AEFDF35C7` | `date_raw=53146872`；038 **只**复载 036 后档。不能把 038 名册变化接到 020 或 070，更不能接到新第 26 日回放。 |

本地 CK3 EXE 95,206,008 bytes、SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；`D:/workspace/cwb2/xar_ck3_bridge.dll` 3,301,888 bytes、SHA `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`；同目录 injector 39,936 bytes、SHA `CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247`。当前受检四条源档、四条回执、DLL、injector 均已到位，无需向 `OneDrive/WAR` 发缺件请求。

## 历史报告哈希和画面状态

下表均为 `ck3-output/capture-report.json` 的本次独立 SHA-256。六份报告的 `raw_video=null`、`clean_spans=[]`；报告不是可剪的游戏录像。历史 `040/map-start.png` 被系统对话框遮挡，不能当干净的骑士次帧画面。

| attempt | 报告 SHA-256 | 研究身份 |
| --- | --- | --- |
| `episode01-day05-wound-growth-attempt-039` | `CF1918B63FA61F7535848967C6A47ED2DE1B50577EFFBF84231B13C6D9ED70C2` | 第 5 日致残事件；039→040 链首。 |
| `episode01-day06-maim-next-input-attempt-040` | `94998B0C427DFB825B1381581E1A72349EE9E95AB341C1E2DE4DDA3FED0D2689` | 只复载 039 的后档。 |
| `episode01-day26-knight-selector-attempt-020` | `818EC3935B272890FDB46A400E6B0715B41E1DEBEA36C7178D7C93581A545614` | 击杀者局部选择器。 |
| `episode01-day26-runtime-weight-attempt-070` | `CA2B46E4CED76513278A4D7827F166B29377F01C9D626E546E8A46E18A4EB17B` | 成长列表 `[40,30,15]` 运行时权重。 |
| `episode01-day26-random-list-type-attempt-036` | `B973A1158F6A8AABA89EF8237967C52A9829422F9C24D8DA9FBB7EE67627AE92` | 036→038 链首。 |
| `episode01-day27-next-input-attempt-038` | `2D09C0B1432B5E2D608B95ECDA75C143169C56404C138FF85EA266B8E5504D5D` | 只复载 036 后档。 |

## 本次独立 no-launch 回执

选用显式解释器 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python 3.14.7、`mcp 2.0.0`、Pillow 12.3.0；本隔离 worktree 无相对 `.venv`。每个新目录永久保留 `ck3-output/command.json`、`preflight.json` 和 `static-capability-strings.json`。无启动预检只证明本机源档、回执、构建与静态环境可用于下一次受管尝试，**不能替代 Steam 离线画面、实机加载或运行时能力验收**。

| 源轨 | 新外置目录；`ck3-output/preflight.json` SHA-256 |
| --- | --- |
| E2-04 第 5 日 | `episode02-e2-04-day05-preflight-20260928-a01`；`A4AEE08B5B39B859D0EEFFED2FCB28EEFE12110DF0A37B652C3799CFCC6CDE0F` |
| E2-04 039→040 对照 | `episode02-e2-04-day06-next-preflight-20260928-a01`；`DADFC711CEBCB5F7494116B051B6CF9D169E533AB1F3277B27571155BA39A72C` |
| E2-05 第 26 日 | `episode02-e2-05-day26-preflight-20260928-a01`；`7B156DA2593408261A07A297825F8E862543FD916842BDD228DD53B4CCCA7BCE` |
| E2-05 036→038 对照 | `episode02-e2-05-day27-next-preflight-20260928-a01`；`54D7960A5D2A6FE81954EAB565655D9798E7722F5C452B7C9A4B3ED7981C5BA9` |

## 后续受管拍摄顺序和 600 秒窗口

R0271 释放屏幕后仍须先查任务总线 `ck3-screen:acquired` 和战争高优先级到货。获屏、确认无 CK3/录制进程后，按 `AGENTS.md` 对**当次实时窗口变化和新桌面像素**取证，亲自审阅 Steam“离线模式”并保存回执。每次 live attempt 使用全新 state/output/profile/pipe，重新哈希源档、回执、EXE、DLL、injector。受管入口仍为 `promo/ck3_native_war_ai/integration/capture_session.py`：以上相应精确 `--checkpoint-save` 和 `--checkpoint-receipt`，`--interactive-seconds 3600 --steam-offline-receipt <本次新回执> --capture`。不用 `--record-debug-desktop` 充当正式录像。加载后必须读取 actor、date、CombatID、WarID 和面板实际可见性。

每条 live 轨只有一个正式 recorder。用 Python `subprocess.Popen(argv, creationflags=CREATE_NO_WINDOW)` 启动 FFmpeg；完整 argv、UTC、`monotonic_ns`、PID、退出码、stdout/stderr 均保全到该 attempt，输出 `-n` 拒绝覆盖。命令模板如下，`<TRACK>` 各取 `e2-04-d05-d06`、`e2-05-d26-selector`、`e2-05-d26-weight`、`e2-05-d26-random-next` 或带独立来源卡的历史后档对照；这些轨不能共用同一 raw 或把后档交叉接成连续轨迹。

```text
ffmpeg -nostdin -n -hide_banner -loglevel warning -f gdigrab -framerate 30 -draw_mouse 0 -i desktop -t 600 -c:v libx264 -preset ultrafast -crf 18 -pix_fmt yuv420p -an <NEW_LIVE_ATTEMPT>\raw\<TRACK>.mkv
```

实际启动一个 recorder、追加 mark 与生成 raw/probe 回执时，使用同目录 `record_bounded_gameplay.py`；具体 `record`/`mark` 命令与新子目录要求见[追击补录方案](pursuit-capture-preflight-20260928.md#一个正式-recorder-与时间锚点)。E2-04/05 的每条独立来源轨必须各建 recorder 子目录，分别传入本表对应的源档和真实回执，不可复用 E2-02/03 的源档或 raw。

1. **E2-04 优先同一新 run 拍第 5 日到第 6 日**：暂停前的战斗、双方人物/骑士名册、目标伤势；日推进和事件 UI；次暂停帧目标伤势、仍在名册和属性。`marks.jsonl` 追加 `recorder-start`、`d05-before`、`event-fire`、`d06-after`、`recorder-end`。若随机结果不是骑士 `34333` 致残，以新原生回执重写数字与旁白；历史 039→040 的数字只用来源明确的研究卡。039 后档可另开短对照 run，镜头之间必须显式来源卡。
2. **E2-05 第 26 日独立三轨**：020 型 selector 轨拍事件前名册、被击杀者 `33437`/团 `65`、击杀者 `34120`、事件后人物/战报；070 型 weight 轨单独拍，其 `[40,30,15]` 和 draw 来自原生研究回执，原版 UI 本身不展示；036 型轨从第 26 日一直拍到其**自身**第 27 日暂停帧名册，再以新回执绑定前后。只在该新 run 确实复现目标和名单时才给“69→68、30→29”旁白。各轨 marks 追加 `d26-before`、`event-fire`、`d27-after` 等实际出现的节点。历史 036 后档/038 对照必须独立标注，不能替代新 036 型 run 的后档。
3. 每条 mark 记录 UTC、`monotonic_ns`、近似录像起点墙钟秒、原生日期/CombatID/WarID/人物与兵团 ID、原始请求/响应和截图的 bytes/SHA。墙钟 mark 不是视频 PTS。媒体封口后保存完整 `ffprobe -v error -select_streams v:0 -show_streams -show_format -show_frames -of json <raw>` 的命令、stdout/stderr、退出码；用实际 decoded PTS 对齐 HUD 与回执，为每段给 clean frame 两端可见性门和精确 clean span。调用当前正式 `xar_promo.adapters.ck3.load_capture_bundle` 只读验证，不修写旧 RED；最终 1× 人工审片另行记录精确成片 SHA。

拍摄当天重新核对最新正式 xar-promo Release 和工作树解释器，再新建 ProjectConfig 绑定 run；当前 no-launch 回执没有创建工具链 run，也没有赋予任何录像 GREEN。录制每条轨都以当次受管成功、单 recorder 完整解码及时间锚点为准；600 秒是上限计划，画面不足便保留 RED attempt 另开新 run。
