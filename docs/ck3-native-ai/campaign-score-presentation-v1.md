# 战役评分图片与讲解视频

`tools/render_campaign_score.py` 将现有 `xar.ck3.campaign-development-score/v1` 评分 JSON 转为 2560×1440 评分 PNG，以及 **15 秒、30 fps、450 帧**的无声 H.264/YUV420P/BT.709 讲解 MP4。2026-10-19 用户要求后续评分结算压缩为15秒；公共绘图与视频入口采用以下完整短时间表，旧60秒评分片及已交付成片不重渲染、不截取、不改写。它不解析存档、不重新评分、不连接游戏，也不替代成片的容量准入与实际验收。后续成片应调用当前公共入口，不沿用历史冻结生产器的60秒假定。

Python 需安装可选依赖 Pillow；只读 JSON 校验、`--help` 和 `--check` 不要求 Pillow。视频另需包含 libx264 的 FFmpeg。字体由调用者提供，必须含报告使用的中文字形。

```text
py -B tools/render_campaign_score.py --check
py -B tools/render_campaign_score.py --report score-result.json --image score.png --font C:/Windows/Fonts/msyh.ttc --bold-font C:/Windows/Fonts/msyhbd.ttc --title "罗贝尔的30年" --receipt score-image-render.json
py -B tools/render_campaign_score.py --report score-result.json --video score.mp4 --ffmpeg C:/path/to/ffmpeg.exe --font C:/Windows/Fonts/msyh.ttc --bold-font C:/Windows/Fonts/msyhbd.ttc --title "罗贝尔的30年" --receipt score-video-render.json
```

示例中的解释器、FFmpeg、字体路径由实际机器确认；这份说明不证明任何机器已安装这些依赖。可以在一次调用中同时提供 `--image` 和 `--video`。输出必须不存在，父目录须已建立；失败的部分输出保留供诊断，不自动删除或覆盖。执行前应依通用存储策略检查容量；PNG 上限 6 MiB，MP4 上限 256 MiB，日志管道各 1 MiB。视频通过连续 RGB stdin 送帧，不落逐帧 PNG；x264 使用两线程，Windows 子进程使用 BELOW_NORMAL 优先级。这里只检查实际 FFmpeg 正常退出、全部450帧发送及 progress=end，不宣称取得正式成片资格。

| 时间（左闭右开，秒） | 帧（左闭右开） | 内容 |
| --- | --- | --- |
| 0–1 | 0–30 | 评分口径、资格、当前状态与三十年成绩边界 |
| 1–2.5 | 30–75 | L 领地 |
| 2.5–4 | 75–120 | E 财政 |
| 4–5.5 | 120–165 | M 军事 |
| 5.5–7 | 165–210 | U 治理 |
| 7–8.5 | 210–255 | D 宗族 |
| 8.5–10 | 255–300 | H 继承 |
| 10–12 | 300–360 | 六维完整汇总、固定权重合成 |
| 12–15 | 360–450 | 主要得失与未确认信息 |

每个维度的条形动画压缩为0.4秒；末尾5秒完整保留六维数值。资格、状态总分、三十年分数可用性及缺项提示持续显示，不以删掉后45秒实现缩时。`--check` 无媒体调用地验证15秒/450帧、九章顺序、连续覆盖、FFmpeg帧率与帧数、向外舍入和未知项不能变成中点分数；评分数学合同保持原样。

六维按固定权重逐项展开，展示真实数值/公式说明、累计贡献、状态总分、主要事实和缺项。区间下界向下、上界向上显示一位小数；确定值的小数近似以“≈”标明。缺历史时显著标注 `FINAL_STATE_ONLY` 或相应资格，并显示三十年总分无法完整计算；不把区间中点或当前状态分冒充完整三十年成绩。视频没有原声或配乐，最终配乐由正式合成流程添加。

纯绘图 API 位于 `xar_autoplayer.campaign_score_presentation_v1`：`validate_report(report)`、`storyboard(report)`、`draw_score_frame(report, frame, font_path, bold_font_path, summary=False, campaign_title=...)`。图像返回 Pillow `Image`，调用者负责关闭。模块没有执行机器、盘符、当前影片或原生接口依赖，Pillow 只在实际绘图时导入。
