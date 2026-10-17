# Review02 局部预览入口

现有 `war_ai_promo.episode04_review02_mixed_rough:compose` 支持在原 rough input JSON 中明确设置：

```json
"preview_cue_ids": ["C02-09", "C03-08"]
```

这些 ID 必须按原 69 段顺序排列且不重复，每段都要有真实 `visual_overrides` 输入。未知 ID、待拍槽和仅有静态卡的槽均拒绝进入这个预览。原片 SHA、帧区间、实测口播长度和 rough 标签继续核对；未选中的素材无需冒充已准备好。

省略该字段仍走完整 69 段合同：存在 pending 就拒绝 build，不用静帧补齐。局部模式沿用原引擎和 CLI，输出文件、artifact ID 与画面水印明确标为 `PARTIAL PREVIEW / NO SIGNOFF`；它不是完整影片，也不增加研究、业务或 11 项正式动态信用。

源码见[项目 composer](../../integration/src/war_ai_promo/episode04_review02_mixed_rough.py)，新选择器测试见[focused tests](../../integration/test_episode04_preview_selection.py)。正式 CI 明确执行这 7 项测试。

先在环境中设置项目集成 `src` 的 `PYTHONPATH`，并以 `XAR_E04_ROUGH_INPUT` 指向准备好的完整 rough JSON；可只读核对配置：

```text
python -m xar_promo plan <project.json> --workdir <fresh-plan-path> --composer war_ai_promo.episode04_review02_mixed_rough:compose --validate-only
```

真正 build 前，按现有流程新查正式工具链 release、完成容量准入，并把输入、三份元数据及所选段的音轨、字幕和原片精确 pin 保存在真实原生 RunManifest。随后使用原有命令：

```text
python -m xar_promo build <run-manifest.json> --workdir <fresh-render-path> --composer war_ai_promo.episode04_review02_mixed_rough:compose --offline-tts
```

准备观察时间 `2026-10-17T17:19:21.607206+00:00`，`machine_id: desktop-3fevhd2-1c74096080`：[R198 媒体索引](../../../../docs/ck3-native-ai/evidence/episode04-r198-military-toggle-12004/media-index.json)提供 C02-09 的 `[780,1675)`；依据[R199 媒体索引](../../../../docs/ck3-native-ai/evidence/episode04-r199-refill-position-12004/media-asset-manifest.json)及已审 40 秒样本，另选 C03-08 的 `[1200,2205)` 作为已有路线背景。后者是剪辑选窗，不是精确事件切点。两段合计 1900 帧／63.333333 秒。R199 未证明抵达、补员或位置条件通过；R198 玩家开关不等于封臣 AI 实测。

外置准备包的只读 plan 已实际确认 2 段，新 focused 测试 7 项通过；本次尚未实际 render、创建新 Run 或取得人工签核。原完整候选为 6 rough／19 卡／44 pending，原 canonical 3／20／46 与正式动态 0／11 不变。机器上的媒体可用性与原生资格须由目标机器重新核实，代码可复用。
