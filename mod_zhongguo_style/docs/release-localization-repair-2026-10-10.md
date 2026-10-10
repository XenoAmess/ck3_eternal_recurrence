# 361 0.3.1：七语最小补全与格式修复（2026-10-10）

本记录绑定基线 `b37013edc19dc3b8841634a4c8a9c5ac3d173f44` 和外置 `361-release031-localization-final04` 候选。法、德、日、韩、波、俄、西七语各补入 37 个缺键（共 **259**），各迁移 4 个已证实跟不上当前中英源的旧键（共 **28**）；其余 **195 项旧值/语，共 1365 项逐值不变**。七语 core 均为英文权威顺序的 236 keys。中英四份权威文件和七语 mechanisms 文件字节不变；后者既有英文 fallback 不称为已完成翻译。

按 `docs/localization-workflow.md` 先仅报告 `MINIMAX_API_KEY configured`，没有输出或保存 key。复用共享 `tools/translate_localization_minimax.py`（19055B，SHA-256 `774e41a9268c775ca8c0c7a3efa503abedbd11a70185fcc95006cdf499e63115`），模型 `MiniMax-M3`，仅送最小选定中英文本及必要语境，4 并发、每响应上限 6000 tokens、每语最多 2 次；实际两批各 7 次、全部一次响应成功，没有重试。墙钟分别 27.4733 秒和 20.1950 秒，未舍入合计 **47.6683 秒**（两批显示值 27.47 + 20.19 = 47.66 秒）；这只是 API 两批耗时。

明确迁移的四键为 `setting_zg361_off_desc`、`zg361.50.desc`、`zg361.53.service`、`zg361.53.receipts`：按当前中英源重新请求，保留真实 scope、protected tokens 和换行；没有机械拼接 engine token。初版请求列表漏了完整小数保护项，原 producer 真实拒绝了五语 `3.25` 被本地化成 `3,25` 的候选；保留该 RED 与原响应后，仅精确恢复五个值中各两处字面 `3.25`，没有新增 API 请求。最终生成器沿用原完整保护词 `3.75 / 3.5 / 3.25 / 361 / KPI / OKR / PIP / HC`。

改动通过最小生成器扩展和永久 JSON 输入投影，没有手改生成文件。英文完整 key 顺序仍权威；默认拒绝覆盖已有译文，仅显式 `--replace-token-drift-key` 且旧值确有 token 漂移才允许替换。实际生成 exit 0（0.4011 秒），幂等 `--check` exit 0（0.3385 秒）；默认禁止覆盖 guard 也已取得实际回执。

以下是已执行命令的精确 argv，不要求重复运行：

```text
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -X utf8 C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/candidate-root/mod_zhongguo_style/tools/gen_phase2_placeholder_localization.py --candidates-json C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/candidate-root/mod_zhongguo_style/tools/release_localization_0_3_1_candidates.json --replace-token-drift-key setting_zg361_off_desc --replace-token-drift-key zg361.50.desc --replace-token-drift-key zg361.53.service --replace-token-drift-key zg361.53.receipts
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -X utf8 C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/candidate-root/mod_zhongguo_style/tools/gen_phase2_placeholder_localization.py --check
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -X utf8 C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/candidate-root/mod_zhongguo_style/tools/prepare_release_localization.py audit --write-report C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/candidate-root/mod_zhongguo_style/docs/release-localization-audit.json
```

终验复用原 `prepare_release_localization.py` 的精确字节（109954B，SHA-256 `e36d60d3cabae163485621ee7d7ad6e8fd8c0fbf77a43898fbf3f627c8c2827a`），外置最小源布局中的原 audit 实际 **exit 0、3.0308 秒、stderr 0B**。报告覆盖 4 author source / 14 target 文件及 `utf8_bom, header, syntax, key_order, protected_tokens, value_encoding` 六项。非中文仅 **format-certified**，不扩充语义、native、UI 布局或实机验收门槛。

| 七语 core 文件（`localization/<language>/zg361_l_<language>.yml`） | Bytes | SHA-256 |
| --- | ---: | --- |
| french | 28197 | `273f32c1b3e78ea6d9baa93ca73b76d2428f4e8b0ee4381ee7d28e7054d4580f` |
| german | 28168 | `f18ffce0f4ea402c4ad07aeb9fad0fbe62c8a8c8cd56418c1e8828f649e34c7c` |
| japanese | 27132 | `b27fccd8618cfacff9c18172e0d2aa5d90023ea1627799823476aff2df6f242b` |
| korean | 26904 | `0ecdbba7a2fe414ac938be2683996c42ab9a786dbe74722da17900d7505d65ea` |
| polish | 27063 | `0e2587b077745cc4ff3aec9bd95e72dcbbdb863734c45ac8d91ea8d5f384cfe0` |
| russian | 34773 | `28941c0a5a9c9d43cf3c36e9b407c7883304aabbcca1fcf5ef01397770629a6e` |
| spanish | 27755 | `d594fc2d9c7d752a422aab8b21b53a0d967ee27c79a8b2e7de87c3f8e2b17c4c` |

| 证据 | 精确外置路径 | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| 原 199 译文快照 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-candidate02/original-target-values.json` | 185596 | `f26e575d3d29b859d875c934236a03f565e1f5a2978cf1843723272e600fa15b` |
| 37-key 最小中英输入 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-candidate02/minimal-source-inputs.json` | 23726 | `1faa4f22cdf29953005d46b43c1d75740d351679a5007ca01536b3ca898ebb99` |
| 第一批 7 请求回执 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-candidate02/TRANSLATION-CANDIDATES-RESULT-02.json` | 6952 | `5080db5eea24162c2ed6ea3bf55acb657ddf5be6ee6aac653e6aa0651f09ddea` |
| 第二批 7 请求回执 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-tokenfix03/TRANSLATION-EXACT4-RESULT-03.json` | 6447 | `b405112fc2bff2e932bd64c5ac1abe5506e8c31af309b2aa3c89b3961ccb2ad3` |
| 历史旧报告 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-tokenfix03/historical-original-inputs/mod_zhongguo_style/docs/release-localization-audit.json` | 3867 | `2dbc82570c88a6da06f5a4de1f4b93ad77d9d1b1dacdffb50838546dc8b40a88` |
| 原始缺键 RED 回执 | `C:/workspace/ck3-upgrade-20261010/resume-release-ready-02/361-format-audit-actual-once-01/result.json` | 2764 | `15285da16797e1cf56a26c69444a4cf78b7a13790256013dad71da3a7038da9d` |
| 补 37 键后真实 token RED 回执 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-candidate02/candidate-original-format-audit-after37-actual-02/result.json` | 1685 | `af8f03319677677226952a630e97901713d7f64206ce5aa0c4720735c10ebab6` |
| 小数格式 RED 回执 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-tokenfix03/final-original-format-audit-once-03.result.json` | 1162 | `767f13422b3d3ee61661d316677fe04be43bc66b4c60ad2cb2df12aac242b72e` |
| 5 语数字精确修正 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/EXACT-FIVE-DECIMAL-FORMAT-NORMALIZATION-04.json` | 3472 | `4eef67bee45143a375f8339cef4232e1bbf92495bb5b330c20decc9f3ee3bc35` |
| 最终生成器 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/candidate-root/mod_zhongguo_style/tools/gen_phase2_placeholder_localization.py` | 7872 | `d735c848aaa5035c1bb99bd0fc3e10e04b82eb5ef3807434c94ad02a97d286d3` |
| 永久候选数据 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/candidate-root/mod_zhongguo_style/tools/release_localization_0_3_1_candidates.json` | 35372 | `eabe540eb75c56319464f95152d2c5311ad6c89302f61c7f57c3047d1833ccbd` |
| 最终格式报告 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/candidate-root/mod_zhongguo_style/docs/release-localization-audit.json` | 3866 | `d1b0ccfc0bee8abeff218d27f54cb59f2dc9e1b3d774d03abce03d81dc6591f9` |
| 原 producer 终验 stdout | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/final-original-format-audit-once-04.stdout.raw` | 3093 | `a2968417e582e6ef1a8d78aa3b4d0b746ac5ab07f1df7c3a8f5642a969860a9d` |
| 候选 patch | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/361-seven-locale-format-generator-data-report-final04.patch` | 134983 | `904bed98f87f98e5b224ce7ce63635f0cd44129b147fdaed780ee714f2312818` |
| 最终候选完整回执 | `C:/workspace/ck3-upgrade-20261010/361-release031-localization-final04/ROOT-361-LOCALIZATION-FINAL-READY-04.json` | 21253 | `20234627cbf782b126e9280d864ea065d8f26b60b3d1590562605b7ef6fd25c4` |

机器为 `4号执行者`，现场标识 `4-8e1c2f1861`，工作区 `C:/workspace/ck3_eternal_recurrence`，仅用 `cmd.exe/login=false`。共享 manifest 绑定 CK3 `1.20.0.4` / Steam build `25734779` / EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；本任务未重新启动或使用 CK3。共享 Source13 fd1f runtime 保持原样，本格式修复不要求重建 native。

已保存原始缺键 RED、补键后 token RED、小数 RED、原 199 译文与旧 audit。所有候选和回执均外置，MAIN/Git 前后保持上述提交且 clean；`git apply --check` 实际 exit 0。闭场采纳后，361 必须以新字节做 **一次正式 production 投影与 newprepare**，不能把旧 1034 文件 staging 或旧 prepared sibling 当新输入。此格式 GREEN 不代替业务场景验收；正式 tag、SDK/Notes 匿名回读、缓存加载与永久发布 changelog 均仍待完成，未记录发布事实。
