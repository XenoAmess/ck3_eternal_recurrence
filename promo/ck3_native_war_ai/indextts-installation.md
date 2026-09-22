# 本机 IndexTTS 安装与使用

本次战争视频样片按用户要求使用 **EdgeTTS / zh-CN-XiaoxiaoNeural**。IndexTTS 独立安装已完成，真实 CUDA 中文生成与 WebUI 本地 HTTP 启动均通过；下面的测试 WAV 没有进入影片。[机器收据索引](build-records/indextts-installation-20260923.json)绑定具体文件和 SHA。

## 已安装环境

- 安装目录：`D:/workspace/index-tts/`；独立解释器：`D:/workspace/index-tts/.venv/Scripts/python.exe`，Python 3.11.16。
- [官方 IndexTTS 源码](https://github.com/index-tts/index-tts/tree/ee40fa7d6c6b8a2c7f06105f9f1e65775b74868c)固定于 `ee40fa7d6c6b8a2c7f06105f9f1e65775b74868c`，采用 IndexTTS 2.5 推理入口；上游代码未修改。
- [官方模型 IndexTeam/IndexTTS-2.5](https://huggingface.co/IndexTeam/IndexTTS-2.5/tree/c39ce5ba981572cb187443877ff559dfb246ce63)固定于 `c39ce5ba981572cb187443877ff559dfb246ce63`；连同 w2v-bert、BigVGAN、CAM++ 所需文件，共 21 个、7,082,514,638 bytes，逐文件哈希核验；各来源 revision 在机器索引中。
- PyTorch `2.8.0+cu128`；RTX 3060 Laptop 6 GB，现有驱动 546.33。矩阵、卷积及真实中文 GPU 推理通过，未升级系统驱动。
- 安装过程中发现 OpenCV 4.9 与 NumPy 2.2 的真实 ABI 冲突，仅在此独立环境将 OpenCV 调整为 `4.10.0.84`；上游源码和 lock 保留。未将模型依赖混入影片 Python 3.14 环境。

下载中断、官方 wheel 分段下载与完整 SHA 检查、模型清单、环境版本、所有请求/返回及失败日志永久保存在 `D:/workspace/ck3_native_war_ai_promo_work/indextts-install-20260922-r1/`。

上游包元数据仍显示 `indextts==2.0.0`，实际执行的是 `indextts.infer_v2_5.IndexTTS2` 与 2.5 模型。日常运行使用下述独立 Python，普通 `uv sync/run` 会把 OpenCV 同步回上游不兼容版本，需要保留该本机覆盖。安装目录和证据目录都要保留：venv 绑定的 uv-managed Python 也在证据目录内。完整安装操作记录为 `D:/workspace/index-tts/LOCAL_INSTALL.md`。

## 启动本机网页

在 cmd.exe 中运行：

```text
cd /d D:\workspace\index-tts
.venv\Scripts\python.exe webui.py --version 2.5 --model_dir checkpoints --host 127.0.0.1 --port 7860 --fp16 --gui_seg_tokens 80
```

随后打开 `http://127.0.0.1:7860`。本次同参数实测 141.56 秒就绪，首页与 `/config` 可读，Gradio 5.45.0 / 119 组件；检查后已关闭服务并确认端口关闭。`--fp16` 是上游参数名，本机 2.5 实际选择 BF16。未启用 DeepSpeed、自定义 CUDA kernel 或 torch.compile；6 GB 配置跳过 QwenEmotion，文本描述驱动的情绪模型未下载。此处验证了网页加载和 HTTP 响应，实际语音验收使用下面的命令行入口。

## 实际中文输出

| 独立安装测试 | 实际 WAV 时长 | 模型加载 | 单条推理 | 波形结果 |
| --- | ---: | ---: | ---: | --- |
| 官方短参考 | 6.780 秒 | 108.00 秒 | 69.34 秒 | 22050 Hz、单声道 PCM16，非静音，零削波 |
| 清晰女声参考，第 1 句 | 3.750 秒 | 两句共用一次加载 67.61 秒 | 141.31 秒 | 同上 |
| 清晰女声参考，第 2 句 | 4.423 秒 | 沿用同一模型实例 | 106.59 秒 | 同上 |

这说明本机可以生成语音，吞吐较慢；长参考下尤其明显。清晰女声参考来自本次生成的合成 Xiaoxiao 音频，官方 API 将约 16.7 秒参考按自身规则截至 15 秒。批量两句进程共约 336.91 秒，不包含整片配音。CUDA allocator 的 allocated/reserved 峰值与显卡物理占用不是同一个口径，收据分别保留原始数值。

波形检查不等于人工听感通过；独立 ASR 转写存在同音字偏差，也不能替代逐句听审。本轮尚未给 IndexTTS 音色作人工批准。

## 命令行入口

使用安装目录内的 `local_infer.py`，项目中保留[精确脚本快照](integration/indextts/README.md)。输入文本为 UTF-8，参考音频显式指定；输出目录须存在，文件及 sidecar 必须是新路径。

```text
D:\workspace\index-tts\.venv\Scripts\python.exe D:\workspace\index-tts\local_infer.py --text-file D:\workspace\my-new-script.txt --reference D:\workspace\ck3_native_war_ai_promo_work\voice-reference-20260922-r1\xiaoxiao-reference.wav --output D:\workspace\my-new-narration.wav --device cuda
```

上例 `my-new-script.txt` 由操作者准备，未将占位路径描述为已执行任务。每条输出保留 `.request.json` 与 `.receipt.json`；错误保留 `.failure.json` 和 partial。使用 `--batch-file` 时，输入为 `{id,text,output}` 数组，同一模型实例顺序执行；不自动切换供应者或设备。

完整机器收据为 `D:/workspace/ck3_native_war_ai_promo_work/indextts-install-20260922-r1/installation-receipt.json`，SHA-256 `5afa7c8b2394fe88e7306c2a599acbf50112e6fdb216a15bf836f18d92045eb1`。当前影片的生产输入明确绑定 EdgeTTS 录音，安装 IndexTTS 不会改变该绑定。
