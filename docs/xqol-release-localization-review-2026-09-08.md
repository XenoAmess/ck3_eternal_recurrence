# XQOL 1.0.2 发布本地化审阅

执行日期：2026-09-08（Asia/Shanghai）
产品：`mod_xenoamess_quality_of_life` 1.0.2
基准语言：English、简体中文
发布语言：English、Français、Deutsch、日本語、한국어、Polski、Русский、简体中文、Español

## 处理边界

- 在确认 `MINIMAX_API_KEY` 已配置后，用 `MiniMax-M3` 为法、德、日、韩、波、俄、西七种语言各生成 22 个候选值；只发送最小必要的英文 key-value、简体中文参考、短语境和受保护 token。
- 模型输出只作为候选；文件选择、逐项改写、原版 CK3 术语比对和验收结论均由当前执行者完成。
- 未把密钥、请求头、完整项目或与翻译无关的源码写入日志或仓库。

## 人工审阅

- 七语文件均为 UTF-8 BOM、正确 `l_<language>:` header、22/22 同构 key。
- 统一采用 CK3 1.19.0.6 的候选分、任命继承、官僚制/行政制和封臣移交术语；清除了英文占位、混入的中文表达及多余语义。
- `#P`、`#N`、`#!` 的集合与英文基准逐 key 一致；`XenoAmess` 品牌名保持不变。
- 本轮没有七语母语者签核，因此对外只声明“已翻译并通过结构、格式与术语审计”，不声明母语级润色。

## 自动检查

```powershell
& tools/.venv/Scripts/python.exe tools/test_translate_localization_minimax.py
& tools/.venv/Scripts/python.exe tools/test_build_xenoamess_quality_of_life_release.py
& tools/.venv/Scripts/python.exe tools/validate_xenoamess_quality_of_life.py --release-localization
& tools/.venv/Scripts/python.exe tools/build_xenoamess_quality_of_life_release.py --check
```

发布构建器的 `--release` 模式会拒绝七种目标语言中与英文逐字相同的占位值、空值、key 集合漂移、BOM/header 错误和 CK3 格式 token 漂移。实机语言界面证据在发布验收完成后回链到本文件。

## 实机证据

状态：`PENDING`。将在正式 tag 的 staging 或 Workshop fresh cache 上完成，并记录 artifact 路径与哈希；静态检查不冒充游戏内渲染验收。
