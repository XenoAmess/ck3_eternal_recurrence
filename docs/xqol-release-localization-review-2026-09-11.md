# XQOL 1.1.0 发布本地化审阅

执行日期：2026-09-11（Asia/Shanghai）  
产品：`mod_xenoamess_quality_of_life` 1.1.0  
基准语言：English、简体中文  
发布语言：English、Français、Deutsch、日本語、한국어、Polski、Русский、简体中文、Español

## 处理边界

- 确认 `MINIMAX_API_KEY` 已配置后，用 `MiniMax-M3` 为法、德、日、韩、波、俄、西七种语言各生成二期新增的 50 个候选值，共 350 个候选值。
- 每次请求只发送指定 key-value、简中参考、短语境和自动提取的 CK3 格式 token；没有发送项目源码、文件系统信息或凭据。
- 第一轮把 `Gold` 误设为不可翻译 token，导致法、波、俄、西四语候选被调用器拒绝且未写入文件；移除该错误限制后，只重试这四种失败语言。
- MiniMax 输出只作为候选。文件选择、写入、逐项修正、原版术语比对和验收结论均由当前执行者完成。

## 人工审阅

- 九语文件均保持 UTF-8 BOM、正确的 `l_<language>:` header 和 72/72 同构 key。
- 对照 CK3 1.19.0.6 原版本地化统一了核心术语，包括法语 `hameçon`、德语 `Druckmittel`、日语 `フック`、韩语 `구실`、波兰语 `hak`、俄语 `рычаг влияния`、西班牙语 `anzuelo`，以及各语言原版的参战、改宗、赎金、招募用语。
- 修正了候选中的日语简体汉字、韩语混入汉字、非原版牵制术语、错误的囚犯/赎金表达和不自然的按钮文案；七种目标语言不再保留二期英文占位。
- `#P`、`#N`、`#!` 和所有 `[GetPlayer.MakeScope.Var(...).GetValue|0]` 动态 token 均与英文基准逐 key 一致。
- 本轮没有七语母语者签核，因此只声明“已翻译并通过结构、格式和原版术语审计”，不声明母语级润色。

## 自动检查

以下命令于 2026-09-11 在同一工作树一次通过：

```powershell
& tools/.venv/Scripts/python.exe tools/test_translate_localization_minimax.py
& tools/.venv/Scripts/python.exe tools/validate_xenoamess_quality_of_life.py --release-localization
& tools/.venv/Scripts/python.exe tools/test_build_xenoamess_quality_of_life_release.py
& tools/.venv/Scripts/python.exe tools/build_xenoamess_quality_of_life_release.py --check
```

结果：26/26 翻译调用器测试 GREEN，XQOL 发布本地化门禁 GREEN，8/8 构建器测试 GREEN，24 文件确定性双构建 GREEN。开发候选 manifest SHA-256 为 `617c4eb6d4dc3e9b2b717465c21351de9d45640b896d56d9e5bb8af53309a058`，ZIP SHA-256 为 `58f79aa467615d11d1473898b5b9e08f63b08d609a0ef0c68c575bffc5bbe9b8`。

## 实机边界

九语发布级静态门禁已经完成；1.1.0 的最终简体中文发布候选仍需完成一次完整 CK3 实机矩阵。不会为七种候选语言重复七次冷启动，也不把静态结构检查表述为逐语言截图或母语者签核。
