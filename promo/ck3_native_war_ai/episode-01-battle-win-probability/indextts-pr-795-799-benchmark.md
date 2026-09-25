# IndexTTS PR #795 / #799 本机速度对照

2026-09-25，在 RTX 3060 Laptop 6 GB、CUDA、PyTorch 2.8.0+cu128、bfloat16、IndexTTS 2.5 下，以同一份用户参考声音、同一段中文文本、同一个随机种子 `20260925` 分别启动独立进程进行一次实际合成。计时为模型加载结束后到音频完成；RTF 是推理秒数除以生成音频秒数，越低越快。各配置生成音频长度不同，所以比较以 RTF 为主。

| 配置 | 音频长度 | 推理耗时 | 冷启动加载＋推理 | RTF | 相对原版速度 | CUDA 分配峰值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 原始基线 | 15.293 秒 | 358.679 秒 | 422.675 秒 | 23.454 | 1.00× | 5.87 GiB |
| 仅 #799，复用说话人条件作为情感条件 | 14.654 秒 | 183.262 秒 | 210.603 秒 | 12.506 | 1.88× | 5.43 GiB |
| 仅 #795，参考音频编码放 CPU | 14.364 秒 | 37.058 秒 | 69.266 秒 | 2.580 | 9.09× | 3.47 GiB |
| #795 + #799 | 16.164 秒 | 43.573 秒 | 80.457 秒 | 2.696 | 8.70× | 3.47 GiB |

本机这次测量中，#795 单独开启的表现最好，CUDA 分配峰值较基线降低 40.9%。#799 可能改变声音或情感表现；它的独立配置虽比基线快，但叠加 #795 未见进一步提速。因此本机后续可优先试用 `reference_device=cpu`，不默认打开 `reuse_spk_cond_for_emo`。这是每个配置各一次、约 14–16 秒输出的短片测试，不能保证整片按相同比例提速，也不是音质盲听验收。

本地安装位于 `D:\workspace\index-tts`，分支 `local/pr795-pr799-installed`，集成提交 `5bb1a21d0add49e164e1438144e48da31bb34582`，基线 checkout `D:\workspace\index-tts-pr-base`。离线 CPU 集成测试为 31 passed、12 deselected。四份原始 WAV 与逐次 JSON 回执保存在 `D:\workspace\ck3_native_war_ai_promo_work\indextts-pr-benchmark-001`；本仓库的可复跑脚本为 `integration/src/war_ai_promo/benchmark_indextts_prs.py`。对应上游改动为 [#795](https://github.com/index-tts/index-tts/pull/795) 与 [#799](https://github.com/index-tts/index-tts/pull/799)。
