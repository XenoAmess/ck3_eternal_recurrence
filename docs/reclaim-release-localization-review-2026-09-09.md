# 重整河山 0.1.0 发布本地化审阅

执行日期：2026-09-09（Asia/Shanghai）  
产品：`mod_reclaim_the_motherland` 0.1.0  
基准语言：English、简体中文  
发布语言：English、Français、Deutsch、日本語、한국어、Polski、Русский、简体中文、Español

## 处理边界

- 在确认 `MINIMAX_API_KEY` 已配置后，用 `MiniMax-M3` 为法、德、日、韩、波、俄、西七种语言生成 13 个候选值；仅发送产品本地化 key、英文值、简体中文参考与最小机制语境。
- 模型输出只作为候选；文件选择、逐项改写、CK3 术语比对、格式检查和验收结论均由当前执行者完成。
- 未把密钥、请求头、完整项目或与翻译无关的源码写入日志或仓库。

## 审阅结论

- 九语文件均为 UTF-8 BOM、正确的 `l_<language>:` header，并保持 102/102 同构 key：13 个产品文案 key，加上由同一生成器投影的 89 个标准朝号组合 key。
- “Chinese Hegemony”“Age of Warlords”“Mandate”“Later Dynasty”“Proclaim the Restoration”等核心概念按语言逐项复核；“Later”作为朝号前缀与兜底“Later Dynasty”分开处理。
- 89 个 `rmtm_later_dynn_title_*` 不另行机器翻译，而是按 `$rmtm_restoration_title_prefix$$dynn_title_song$` 这一形式，由已经审阅的本 mod 前缀与 CK3 当前语言的原版朝号组合；这避免复制并漂移 801 条原版译名。
- 清除了英文占位和重复的原版本地化 key；所有 CK3 格式 token、引号和换行结构与英文基准一致。
- 七种新增语言没有母语者签核，因此只声明模型候选经结构、格式、语义与术语审阅，不声明母语级润色。

## 自动检查

```powershell
py tools/test_reclaim_the_motherland_contract.py
py tools/test_build_reclaim_the_motherland_release.py
py tools/validate_reclaim_the_motherland_static.py
py tools/build_reclaim_the_motherland_release.py --check
```

正式构建器会拒绝七种发布语言中的英文逐字占位、空值、key 集合漂移、BOM/header 错误与格式 token 漂移。

## 实机边界

简体中文用于真实 CK3 1.19.0.6 的完整群雄割据—后朝—复辟流程验收。其余七种候选语言不重复进行七次冷启动，也不冒充逐语言截图或母语者签核；Workshop fresh-cache L3 结果与永久 artifact 在产品验收报告中统一记录。
