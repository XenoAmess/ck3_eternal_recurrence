# 战争 AI 影片：制作记录

## v3 研究后重制审阅版 · 2026-09-23

本次完整影片为 **2033.821354 秒（33:53.8）**、2560×1440 / 30 fps，八章、45 段 EdgeTTS `zh-CN-XiaoxiaoNeural / -12%` 配音、画面内烧录的简中主字幕和英文副字幕。以 CK3 原版地图与界面、旧金纸面规则卡和五段原速连续实机画面交替讲述；无音乐。交付文件为 `D:/workspace/ck3_native_war_ai_promo_work/v3-film-attempt-003/war-ai-full-film-review.mp4`，211,373,375 bytes，SHA-256 `f2068c66a47af7fd5fcdd2abab484607870e65f588068514fa8d4182239b8192`。完整收据见 [v3 构建记录](build-records/v3-fullfilm-20260923-r1.json)。

| 播放器书签 | 章节 |
| --- | --- |
| 00:00 | 三个疑问 |
| 01:33 | 为什么选这场战争 |
| 07:36 | 开战后，先盯哪里 |
| 12:45 | 遭遇之前，它在比较什么 |
| 17:17 | 求援开关 |
| 21:41 | 一仗结束，战争还在继续 |
| 25:30 | 和平桌上的两张账 |
| 31:37 | 回到地图 |

实机画面来自 CASE-W 与 CASE-C 的同一场玩家宣战后战争，五段均按连续原速裁取，并在画面中标出 CASE ID 和“上下文而非因果证明”。CASE-R 的九项合法宣战查询与兵力比例是原生查询证据，不是自然 AI 宣战录像。当前实机没有拍到自然 AI 宣战、战斗结算或主动求和的闭合因果链，因此影片在这些位置用已经落入 `docs` 的原生逻辑和独立标示的规则算例解释，不把未观测到的结果说成实拍结果。旧片被退回后补研的静态决策树与实机边界记录见 [研究清单](../../docs/ck3-native-ai/war-video-research-rebuild-2026-09-23.md)。

正式 `xar-promo` 0.2.1 的 `plan/build/review` 已完成；失败 attempt 001/002 和当前 attempt 003 的配置快照、原始录像保全、命令与阶段历史均留存。最终文件已过实际媒体探测、八章书签核对和一次严格完整音视频解码。原生 `review` 包含 106 张边界帧，状态 `pending-human-review`、`approval_granted=false`；自动检查不能替代 1× 人工观看，也没有人工签核。只将这一个 MP4 的精确字节复制到 OneDrive 桌面客户端的固定同步目录 `CK3-War-AI-20260923/CK3-War-AI-V3-Review-20260923.mp4`；本机源/目标哈希一致。随后从 OneDrive 客户端活动中心读到新版文件“已上传到 CK3-War-AI-20260923”及全局“已备份和同步”；回读保存在 attempt 003 的 `onedrive-client-readback-r1.json`。本次操作未打开或下载其他云端文件内容；选择性同步配置沿用先前只选固定文件夹的核验状态。

## 历史：被退回的完整审片版 · 2026-09-23

用户收到求援样片后要求完成整部 20–40 分钟影片再审。本次 `fullfilm-edge-20260923-r1` 已生成完整八章、90 段旁白、45 个镜头组，实际 **1735.788021 秒（约 28:56）**，2560×1440 / 30 fps。已通过 OneDrive 桌面客户端上传至固定目录 `CK3-War-AI-20260923/CK3-War-AI-Full-Film-20260923.mp4`，并读回“已上传到 CK3-War-AI-20260923”。用户要求先上传、再完成余下检查；不以审阅包或人工签核阻塞已授权的交付。

最终本机文件为 `D:/workspace/ck3_native_war_ai_promo_work/fullfilm-edge-20260923-r1/war-ai-full-film-review.mp4`，78,679,158 bytes，SHA-256 `328b3a469acad2210c17e531a004612af7b15f2cb09e674113bd79cbdd448a0e`；永久索引见[全片构建记录](build-records/fullfilm-edge-20260923-r1.json)。

全片沿用 EdgeTTS `zh-CN-XiaoxiaoNeural / -12%`。中文按服务返回的 SentenceBoundary 编排，英文按各段实际语音长度分句分配；两层字幕均按字体实测宽度断行。270 张逐步揭示图卡已生成并进入 90 段画面。所有教学数字、角色和未知边界有明确标识；本版无音乐、无自然实机录像。

最终文件完成实际媒体探测、八章书签检查和一次严格全片音视频解码。原生 `review` 的 106 张逐次从头解码抽帧 attempt 因实测耗时中止，原命令 exit 1、部分审阅图和错误收据全部保留；这不改变此前成功的 native build 和最终媒体。独立恢复 attempt 以输入寻址抽取八章中点真实画面，保留实际命令，明确标为项目外置审阅包；真实 `xar-promo audit` 检查其精确 bytes 和证据覆盖，复用已完成的唯一一次全片解码。没有把中止的旧 review 改写为 GREEN。

原有字幕检查报告保留 `ISSUES_FOUND`：43 条英文结尾在 ASS 厘秒取整后比语音末尾晚 2–4 ms，均位于本段既有停顿内，无同语种重叠或越出段落；这是记录在案的格式取整，不据此重新编码。自动检查和抽帧不等于按 1× 完整观看，**人工签核仍为 not-provided，待用户审片**。

| 书签 | 章节 |
| --- | --- |
| 00:00 | 三个疑问 |
| 01:33 | 为什么选这场战争 |
| 05:54 | 开战后，先盯哪里 |
| 09:47 | 遭遇之前，它在比较什么 |
| 14:24 | 求援开关 |
| 18:22 | 一仗结束，战争还在继续 |
| 20:55 | 和平桌上的两张账 |
| 25:39 | 回到地图 |

本次补齐项目提取音频、整片模式、分句字幕、章节封装和全片图解；原生研究文档及既有结论不变。以下样片记录保持为历史事实，不能用其中“全片未完成”的旧时点描述覆盖本次完成收据。


用户已于 2026-09-22 授权开始拍摄，并要求本机安装 IndexTTS；随后确认沿用导演案的清晰女声，先做样片。完整影片仍采用 20–40 分钟弹性编排。

## 历史：求援样片交付：EdgeTTS 修正版

用户于 2026-09-23 再次明确样片使用 **EdgeTTS**。当前交付保持 `zh-CN-XiaoxiaoNeural / -12%`；IndexTTS 只单独安装和验证，不替换样片配音。

第二次实际构建 `help-sample-edge-20260923-r2` 为 **237.988021 秒（约 3:58）**、2560×1440 / 30 fps，12,280,618 bytes；SHA-256 `4fbb165bc70bd712d7537c9bdc9245addd7c6df0cd1cfdd2bc2103c2b3f61712`。视频保存在 `D:/workspace/ck3_native_war_ai_promo_work/help-sample-edge-20260923-r2/build/war-ai-radio-cut.mp4`，完整索引见[修正版构建记录](build-records/help-sample-edge-20260923-r2.json)。

新版保留首版 11 条录音的精确字节，只重录 N30-051 的歧义句。求援者甲与候选助手乙同属赤河，蓝岭明确为敌方；箭头只在匹配示例中由乙指向甲所在省。0.65、0.70、0.76 使用可见求援状态灯；相同 0.70 的历史条件作上下对照，标题改为面向观众的中文问句。旧 attempt 完整保留。

已抽查实际成片中开始求援、相同数值对照及匹配目标三帧，中文与英文字幕进入画面且处于预留区。审阅包按实际章节边缘和六个镜头组的代表状态抽帧；这是机器条件与局部画面检查，没有人工 1× 完整观看签核。当前交付是无音乐、无实机镜头的求援章节图解样片，完整 20–40 分钟影片仍未完成。

## 第一段实际样片

选择求援章节 S30-24…29，先验证数字讲解、固定地图、中文主字幕与英文副字幕能否连贯工作。[样片稿](longform/narration-help-sample.json)含 12 条 cue；全片[阅读稿](longform/narration.md)与[机器稿](longform/narration.json)共 90 条、45 个镜头组、8 章。

首个声音 attempt 明确使用 `edge-tts 7.2.8 / zh-CN-XiaoxiaoNeural / -12%`，IndexTTS 的安装和推理验证另立记录。12 段实际语音加短停顿形成约 236.93 秒的参考拼接；最终媒体时长以 build-record 中的真实 ffprobe 为准。没有靠静音填满四分钟。

[首个实际构建记录](build-records/help-sample-edge-20260922-r1.json)：视频为 236.954687 秒、2560×1440 / 30 fps、11,044,920 bytes，SHA-256 `47d70323b7cc3af2a0585673f30b84d3f69c147d5ddcd0daf5e5f10ad62d81e6`；真实 `plan/build`、完整 config/run 验证、bound probe 和 pending review package 均已完成。执行者仅抽看三帧布局；发现的原口播歧义、朝对手方向的地图箭头及内部标题列入下一版，不称人工审片通过。

本版是**无音乐的教学图解粗剪**，不是已经拍到普通 AI 求援全过程的自然实机记录，也不是完整影片。字幕按真实单段语音分配；段内暂按实际文字宽度和长度分组，尚未做逐词强制对齐。地图、阈值面板、中文与英文字幕均已进入实际渲染，而非仅有 plan。

首个声音快照保留 N30-051 的原口播“答案是否／答案是”；文字检查发现容易听成疑问句，当前稿已改为“条件不满足／条件满足”，供下一次声音 attempt 使用。旧声音快照和旧媒体不覆盖。全片另已明确和平案例中蓝岭为主动提出方、赤河为接收方；玩家对照只改变赤河的控制者。

## 本片项目集成

项目实现位于 [integration](integration/pyproject.toml)：注册既有 adapter/preset ID，由 `war_ai_promo.composer:compose` 提供真实 `PipelineInvocation`。通用运行、渲染、字幕文档、文字测量、媒体探测、命令保全和 pending review 都调用独立 xar-promo；本项目只负责战争文案、图解和输入选择。

安装使用当前 worktree 的显式依赖解释器；每个新 run 都在线查询最新正式 xar-promo，并核对已安装版本。示例中的 `<verified-python>` 必须替换为已验证的解释器：

```text
<verified-python> -m pip install -r tools/requirements-promo-toolchain.txt
<verified-python> -m pip install -e promo/ck3_native_war_ai/integration
<verified-python> -m war_ai_promo.prepare_narration --help
<verified-python> -m war_ai_promo.produce --help
```

`prepare_narration` 显式选择 `--provider edge` 或 `--provider index`，不自动切换供应者。Index 路线要求独立安装解释器、批量推理入口和明确参考音频；单模型顺序处理多 cue。TTS 请求、返回、字节哈希和实际媒体探测保留在新目录。

`produce` 接收已生成的 `production-inputs.json`，建立仅包含本次选择章节的配置快照及新原生 run。真实执行 `start-run → preserve → plan → build → review`，每次 run 修改后完整校验 config/run；plan 不创建 build 目录。生成的可看样片、分段、图卡、字幕、命令日志和 pending review 均保留。完整影片 config 的八章仍是 planned，不以单章样片提升整片状态。

## 实机与安装记录

[素材盘点](longform/capture-inventory.md)记录本机可访问的旧素材及排除原因。本机存在与研究基线相符的 CK3 1.19.0.6；旧的其他 mod 受控验收录像未选入本片。新拍摄须独立原版 profile、真实状态和镜头锚点，不能用游戏安装成功或 launcher ACK 声称已拍摄。

本次实际无启动预检因现有 DLL 缺正式前端启动链的三项能力字符串而 RED，原始记录在 `D:/workspace/ck3_native_war_ai_promo_work/capture-preflight-a02/`。本包零 CK3 启动、零新 raw，live 取景分支尚未验收。独立 `vanilla` 编号空间的既有 7 项测试通过；最终取景相关五文件的 AST/JSON/Python-only 检查通过，收据为 `capture-preflight-final-static-check.json`。这些结果没有提升原生 AI 研究成熟度。

所有过程资产位于 `D:/workspace/ck3_native_war_ai_promo_work/` 的不同 attempt；模型与独立 IndexTTS 环境位于 `D:/workspace/index-tts/`，不进入 Git。自动检查和帧抽样只证明其具体检查范围，尚无人工 1× 全片签核。

[IndexTTS 安装已完成](indextts-installation.md)：实际 CUDA 中文单句、同一模型实例双句批量与官方 WebUI 本地 HTTP 启动通过；检查后服务关闭、端口释放。安装机器收据 SHA 为 `5afa7c8b2394fe88e7306c2a599acbf50112e6fdb216a15bf836f18d92045eb1`。这三条测试 WAV 仅用于独立安装验证，影片依然绑定 EdgeTTS；声音听感未作人工签核。

样片代码、90 条双语稿、两次构建索引及无启动取材阻点已经 rebase 到最新远端并以 `12440d575bf697cc457f975a071b477b2e94ecdc` 推送 `master`。原生研究文档、既有评分、其他任务进度和全部旧运行素材保留。

该样片提交的 [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/35753571023) 已完成且为 success；这是提交级静态/离线检查，不能替代尚未完成的实机取材与人工全片观看。
