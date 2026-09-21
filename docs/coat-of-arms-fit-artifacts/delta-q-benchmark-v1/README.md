# Delta-Q benchmark-v1

本目录是拟合质量 2.0 的 append-only 基线入口。

- `baseline-manifest.json` 冻结七张真实图片在 v14、1,024 实例预算下的质量优先候选，逐项绑定输入 receipt、候选源码、230px 预览、报告、legacy 指标和 SHA-256。
- 合成语料位于 `coat_of_arms_editer_of_ck3/src/data/fit-quality-synthetic-corpus-v1.json`：256 个确定性真值，固定分为 192 dev 与 64 holdout，并绑定 exact `ck3-1.19.0.6` 素材名和逐文件 SHA-256。
- 合成 manifest 只保存家徽语义和扰动合同，不复制 DDS 或重复生成大体积像素资产。
- v14 质量优先候选已有 CK3 原生证据；v15 剪枝候选仍明确保持 `pending-mcp`，不能从浏览器 GREEN 外推。

生成与逐字节复验：

```text
cd coat_of_arms_editer_of_ck3
python tools/gen_fit_quality_benchmark.py
python tools/gen_fit_quality_benchmark.py --check
```

生成器没有时间戳和系统随机源；相同仓库输入必须逐字节一致。
