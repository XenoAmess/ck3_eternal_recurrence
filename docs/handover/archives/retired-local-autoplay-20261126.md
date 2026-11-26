# CK3 旧自动游玩分支归档

此 [Git bundle](retired-local-autoplay-20261126.bundle) 保存 35 条已退役的本地引用。
包括 Robert C6–C13、Source25–32，以及后续已由主线覆盖的 Native、M6 和录制工作。
Bundle 为 1,018,250 字节，SHA-256 为
`e6f58363f29e75b13f90b9c8aa061bd0570168aa1e7f2808ab97fa232c7b75a3`。

Robert Source25–32 的主线整合可从 `d4ce48c660`、`ff78f42506`、`0f36c88263`、
`ac008a6e39`、`63af2d71ac`、`e2578b5927`、`b62e8527fe`、`c00481e1d0` 追溯。
旧 Robert30 引用的源码树与主线 `633e884a06` 一致。Native 合同的覆盖见
`48025dbc86`、`2bfee5eb64` 及 `3b368fcda1`，M6 的旧派系改动见 `16c8c0eeac`。
原字幕与发布记录在 `f7d37c7cb9`。归档保留各分支原始差异和历史验证层级。

在含主线 `95df3809be` 历史的仓库中读取或恢复原对象。

```text
git bundle list-heads docs/handover/archives/retired-local-autoplay-20261126.bundle
git bundle verify docs/handover/archives/retired-local-autoplay-20261126.bundle
git fetch docs/handover/archives/retired-local-autoplay-20261126.bundle 'refs/heads/*:refs/archive/retired-20261126/*'
```

2026-11-26 在 `machine_id: xenoamess-full-tower-eb9d2c1186` 的独立 bare 仓库
恢复了 35 个引用，逐项读回与退役前提交一致。原工作树和产物保留。
具体退役记录见[分支台账](../../branch-management.md#2026-11-26-主线收口)。
