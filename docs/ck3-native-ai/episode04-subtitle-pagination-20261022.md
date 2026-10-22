# 第四集字幕分页修复来源（2026-10-22）

machine_id: `desktop-3fevhd2-1c74096080`。本轮观察从 2026-10-22T11:07Z 开始，来源为本机当前 47 段黄色审核片的实际 ASS、固定项目文本和原排版器；检查回执见[交付记录](evidence/episode04-subtitle-sentence-pages-20261022/DELIVERY.actual-a01.json)。

现片开头 N01-01 在局部 12.90 秒把“补给上限”跨页拆开，N05-03 在局部 23.74 秒拆开“目的地”；N01-07 的局部 27.43 秒页只剩句号。原算法先逐字按宽度折行，再每两行合成一页，页面没有遵守句子边界。

[后继排版器](evidence/episode04-subtitle-sentence-pages-20261022/mechanics_composer.py)让中文每个完整句子占同一页，两行内优先在标点处换行，并保留数值的完整性。未来长句可按从句标点分页；无法容纳的完整从句明确拒绝。47 段当前句子均能完整放入两行，每行最多 32 字且实测不超过 1370 像素。[补丁](evidence/episode04-subtitle-sentence-pages-20261022/sentence-pages.patch)可用于前述最终来源包的 `r/mechanics_composer.py`，其他依赖来自其原始 `r/mechanics_contract.py` 与正式 `xar-promo`。

实际项目的 `Editorial`、`Voice` 校验模型经过后继生成器，再重新读取 ASS，47 段中文全文均相等；新 231 页没有标点独占页，原为 153 页。47 条英文字幕轨逐段与原 ASS 精确相等。生产源码和检查脚本的严格 mypy 检查通过，第三方 wheel 缺 `py.typed` 时使用 `--follow-untyped-imports` 分析其实际注解，没有用宽泛忽略绕过错误。完整结果见[47 段检查](evidence/episode04-subtitle-sentence-pages-20261022/CHECK.actual-a01.json)、[类型检查](evidence/episode04-subtitle-sentence-pages-20261022/STRICT.actual-a02.json)和[检查源码](evidence/episode04-subtitle-sentence-pages-20261022/check_subtitles.py)。

这是已检查的后继源码和实际 ASS，尚未接入新的正式编片配方，也没有更改当前 MP4。字幕时间仍按实测语音时长近似分配，不能当作逐字对齐或整片人工听看。下一次整合 R08/R05 章节时应采用新冻结的排版器和来源 pin 后统一重编，再验证实际成片。正式动态主题仍为 **9/11**，整片人工 1× 和最终签收仍待完成。

本机外置原始检查根为 `C:/ck3-e04-resume-20261022-b01/root/subtitles`；用途复核 2026-10-24T10:00Z，必要来源保护截至 2026-10-29T10:00Z，不自动续期。仓库来源可重建字幕文本；旧外置运行依赖须依实际所在机器重新映射。
