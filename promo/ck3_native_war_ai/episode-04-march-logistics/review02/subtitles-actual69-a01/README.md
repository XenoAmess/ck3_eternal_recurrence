# Review02 actual69字幕

由现有legacy.caption_cues/subtitle_document与xar-promo0.2.1公开ASS API生成，仅使用冻结双语文本、actual provider SentenceBoundary和actual30fps合并时间线。ZH时间来自实际中文provider句边界；EN按已有工具规则在该段真实语音时长内按句长比例分配，不是英文强制对齐。没有读取MP3、调用provider、ffprobe、转码或接入游戏。

subtitles.zh-en.ass保留项目2560×1440的49/31号双语样式；zh/en.srt分别保存独立轨，zh-en.srt将两轨边界取并集，保留两轨各自实际/比例计时。per-cue-ass供现有composer接线。当前是未绑定画面的默认图卡布局，实际gameplay镜头确定后必须按原工具重新定位，不能把这些字幕视作画面避让已签核。

chapter-timing.actual.json与chapters.ffmetadata保留30fps整数帧边界。chapters.txt只是便于阅读的向下取整MM:SS入口。全长58406帧/1946.866666667秒。源文及输入哈希见SOURCE-PINS.json，逐段守恒、轨内无重叠和ASS合同验证见CHECK.actual.json。

subtitle-inputs.actual.json是可复用文本/计时输入；audio_binding_reference_only只是原机器的来源引用，不能拿本机同名MP3冒充。视频尚未render、人工完整1×审阅和签核均未完成，研究卡信用不变。
