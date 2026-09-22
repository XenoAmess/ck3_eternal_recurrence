# 战争 AI 影片的项目实现

本目录提供战争影片自己的文案选择、机制图解和 composer；运行清单、素材保全、字幕布局、媒体探测、渲染与审阅包调用独立 `xar-promo`。实际成果与限制见[制作记录](../production-stage.md)。

## 解释器和依赖

本次媒体解释器为当前隔离工作树的 `tools/.venv/Scripts/python.exe`，Python 3.14.7；运行时核对的最新正式 xar-promo 为 0.2.1。以后每次新 run 仍须核对最新正式版本。先按主仓的 `tools/requirements-promo-toolchain.txt` 安装最新正式 wheel，再安装本项目：

```text
tools\.venv\Scripts\python.exe -m pip install -e promo/ck3_native_war_ai/integration[edge]
tools\.venv\Scripts\python.exe -m war_ai_promo.prepare_narration --help
tools\.venv\Scripts\python.exe -m war_ai_promo.produce --help
```

Edge 配音需要该解释器中的 `edge-tts`，本次实际为 7.2.8；FFmpeg / ffprobe 必须可用。IndexTTS 使用它自己的 Python 3.11 环境，不向影片的 Python 3.14 环境混装模型依赖。

## 真实入口

以下命令在仓库根目录运行，输出路径必须是不存在的新目录。示例 `next-*` 只表示操作者选定的新 attempt，不能反复覆盖。

```text
tools\.venv\Scripts\python.exe -m war_ai_promo.prepare_narration --script promo/ck3_native_war_ai/longform/narration-help-sample.json --timeline promo/ck3_native_war_ai/longform/timeline.json --provider edge --output D:/workspace/ck3_native_war_ai_promo_work/next-help-speech
tools\.venv\Scripts\python.exe -m war_ai_promo.produce --project promo/ck3_native_war_ai --inputs D:/workspace/ck3_native_war_ai_promo_work/next-help-speech/production-inputs.json --run-root D:/workspace/ck3_native_war_ai_promo_work/next-help-build --run-id next-help-build
```

`produce` 在线核对最新正式 xar-promo，拒绝版本不符；随后使用真实 CLI 完成 `start-run / preserve / plan / build / review`，每次 run 修改后验证配置和清单。`plan` 不生成工作目录。输入是实测音频，不按导演案参考秒数拉长静音。

全片使用完整稿，并以 `--full-film` 检查八章齐备和 20–40 分钟实测时长。最终播放器书签无重编码封装到新的 `war-ai-full-film-review.mp4`，原始构建视频仍保留：

```text
tools\.venv\Scripts\python.exe -m war_ai_promo.prepare_narration --script promo/ck3_native_war_ai/longform/narration.json --timeline promo/ck3_native_war_ai/longform/timeline.json --provider edge --output D:/workspace/ck3_native_war_ai_promo_work/next-full-speech
tools\.venv\Scripts\python.exe -m war_ai_promo.produce --project promo/ck3_native_war_ai --full-film --inputs D:/workspace/ck3_native_war_ai_promo_work/next-full-speech/production-inputs.json --run-root D:/workspace/ck3_native_war_ai_promo_work/next-full-build --run-id next-full-build
```

Edge 批量最多并发三段，每段最多三次尝试；失败音频和错误记录永久保留，成功 take 的绑定另存，不覆盖失败 attempt。

`--provider index` 必须同时提供 `--index-python`、`--index-runner` 和 `--reference`；批量任务在一个模型实例中顺序生成。不会自动回退到另一供应者。

## 已验证的边界

- 八章、90 段完整稿与全部图解已进入实际全片，最终文件的全量解码与书签检查通过；等待用户审片。
- 图解中的赤河、蓝岭、甲乙、阈值示例属于教学假设。图解不是自然 AI 战争采样。
- 中文字幕使用实际 SentenceBoundary；英文在实测段长内分句分配，尚无逐词强制对齐。两种字幕最多两行并做字体宽度检查；音乐未加入。
- 审阅包采样实际章节边缘及每个镜头组最后一条 cue 的两种画面状态。采样不代表完整播放检查，不能产生人工签核。
- `capture_session.py` 独立使用主仓 MCP/native-session。仅 no-launch 预检路径实际运行；本机旧 DLL 缺正式前端能力，live 分支尚未验收。具体依赖、排除的旧素材及原始 RED 收据见[素材盘点](../longform/capture-inventory.md)。

所有原始录音、修订录音、请求、图卡、分段、字幕、日志、失败 attempt、清单及审阅包永久保留；新版本另建目录。

## 2026-09-23 重制状态更正

以上“等待用户审片”和旧 DLL 缺能力是旧产物当时的状态。用户已退回纯图解全片；新版按 [导演案 v3](../longform/director-plan-v3.md) 与 [主张台账](../research-first-claim-ledger-20260923.md) 执行。新 DLL 已构建，前两次实机分别为 pipe 占用 RED、360 秒未到主菜单 RED，第三次独立 run 正在有界运行。现有 composer 的纯图解输入不能满足重制要求，实机导入接线正在施工；没有新成片或因果案例完成。
