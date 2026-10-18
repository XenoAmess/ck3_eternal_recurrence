# 战役评分图片与讲解视频

`tools/render_campaign_score.py` 将现有 `xar.ck3.campaign-development-score/v1` 评分 JSON 转为 2560×1440 评分 PNG，以及 60 秒、30 fps 的无声 H.264/YUV420P/BT.709 讲解 MP4。它不解析存档、不重新评分、不连接游戏，也不替代成片的容量准入与实际验收。当前外置成片生产器保持原冻结来源。

Python 需安装可选依赖 Pillow；只读 JSON 校验、`--help` 和 `--check` 不要求 Pillow。视频另需包含 libx264 的 FFmpeg。字体由调用者提供，必须含报告使用的中文字形。

```text
py -B tools/render_campaign_score.py --check
py -B tools/render_campaign_score.py --report score-result.json --image score.png --font C:/Windows/Fonts/msyh.ttc --bold-font C:/Windows/Fonts/msyhbd.ttc --title "罗贝尔的30年" --receipt score-image-render.json
py -B tools/render_campaign_score.py --report score-result.json --video score.mp4 --ffmpeg C:/path/to/ffmpeg.exe --font C:/Windows/Fonts/msyh.ttc --bold-font C:/Windows/Fonts/msyhbd.ttc --title "罗贝尔的30年" --receipt score-video-render.json
```

示例中的解释器、FFmpeg、字体路径由实际机器确认；这份说明不证明任何机器已安装这些依赖。可以在一次调用中同时提供 `--image` 和 `--video`。输出必须不存在，父目录须已建立；失败的部分输出保留供诊断，不自动删除或覆盖。执行前应依通用存储策略检查容量；PNG 上限 6 MiB，MP4 上限 256 MiB，日志管道各 1 MiB。视频通过连续 RGB stdin 送帧，不落逐帧 PNG；x264 使用两线程，Windows 子进程使用 BELOW_NORMAL 优先级。这里只检查实际 FFmpeg 正常退出、全部 1800 帧发送及 progress=end，不宣称取得正式成片资格。

六维按固定权重逐项展开，展示真实数值/公式说明、累计贡献、状态总分、主要事实和缺项。区间下界向下、上界向上显示一位小数；确定值的小数近似以“≈”标明。缺历史时显著标注 `FINAL_STATE_ONLY` 或相应资格，并显示三十年总分无法完整计算；不把区间中点或当前状态分冒充完整三十年成绩。视频没有原声或配乐，最终配乐由正式合成流程添加。

纯绘图 API 位于 `xar_autoplayer.campaign_score_presentation_v1`：`validate_report(report)`、`storyboard(report)`、`draw_score_frame(report, frame, font_path, bold_font_path, summary=False, campaign_title=...)`。图像返回 Pillow `Image`，调用者负责关闭。模块没有执行机器、盘符、当前影片或原生接口依赖，Pillow 只在实际绘图时导入。
