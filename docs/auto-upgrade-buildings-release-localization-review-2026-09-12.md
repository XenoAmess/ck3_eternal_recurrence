# 自动升级建筑维护版：1.19.0 发布本地化审阅

日期：2026-09-12（Asia/Shanghai）

## 范围与方法

- 发布语言：简体中文、英文、法文、德文、日文、韩文、波兰文、俄文和西班牙文。
- 英文与简体中文是人工审阅基准；法、德、日、韩、波、俄、西各新增 10 项，共新增 70 项翻译。
- MiniMax-M3 只接收这 10 个既定 key、双语基准、目标语言、简短 CK3 界面语境和保护 token，并只返回候选 JSON；它没有分析项目、修改文件或判断验收结果。
- 当前执行者逐项复核候选并人工修正了用词、语法和不自然表达，包括西班牙文残留的英文单词、日/韩排队检查语义、波兰文“自动升级”术语，以及各语言确认按钮和资金来源表述。

## 自动审计

- 九份文件均为 UTF-8 BOM、正确 `l_<language>:` 头、10/10 相同 key、无空值。
- 七种新增语言不存在逐值等于英文的占位；`\\n`、`CK3`、`1.19.0.6`、`Mandala` 的逐 key 数量与英文基准一致。
- `py tools/validate_auto_upgrade_buildings_static.py`：GREEN。
- `py tools/test_build_auto_upgrade_buildings_release.py`：5/5 GREEN。
- `py tools/build_auto_upgrade_buildings_release.py --check`：14 文件 deterministic build GREEN。

## 实机与诚实边界

玩法脚本没有因本地化补全而变化。简体中文基准已由
`desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0013` 在 CK3 1.19.0.6 完成核心功能矩阵并取得 GREEN；产品相关诊断为零。
本轮不为七种候选语言重复七次冷启动，也不把结构/token 检查冒充逐语言截图、游戏内截断或母语者签核。

当前结论是：九语发布结构、格式、保护 token 和可由执行者复核的明显语义问题已通过；七种新增语言没有母语者签核，仍不声明母语级润色。
