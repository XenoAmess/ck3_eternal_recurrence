# 实机镜头导入接口草稿

此模块只准备素材，composer/produce 的接入由独立工作包完成。没有新 GREEN CK3 录像已在这里验收；成功测试使用明确标记的合成短片及 mock adapter 投影，不伪造 GREEN capture report。该模块不启动游戏、不修补 RED capture、不判断原生 AI 因果，也不产生人工签核。

## 输入与调用

`war_ai_promo.capture_media.load_capture_spec(path)` 读取如下项目 JSON，返回单条 clip 字典列表。`bundle_root` 必须是既有捕获目录的绝对路径；`offset_seconds` 相对指定 clean span 的起点。示例是输入形状，路径和 cue 需由实际素材/新版脚本绑定：

```json
{
  "schema": "ck3-war-ai.capture-clips.v1",
  "clips": [{
    "cue_id": "NEW-CUE-001",
    "bundle_root": "D:/capture-runs/REPLACE-WITH-EXISTING-GREEN-RUN",
    "span_id": "REPLACE-WITH-EXISTING-SPAN",
    "offset_seconds": 0.0,
    "duration_seconds": 8.0,
    "evidence_role": "context",
    "claim_ids": ["W2-03"]
  }]
}
```

`evidence_role` 可为 `context`、`mechanism-illustration`、`candidate-causal-case`、`controlled-experiment`。它们都是编辑标签，即使标了候选因果案例也不能自动证明机制。`claim_ids` 留给新版台账/脚本核对，本模块不偷偷把旧 C03 或新 W2-03 视为已完成 live。

```python
from pathlib import Path
from war_ai_promo.capture_media import load_capture_spec, prepare_capture_clip

clip = load_capture_spec("capture-clips.json")[0]
result = prepare_capture_clip(
    clip,
    Path("D:/film-attempts/NEW-ATTEMPT/capture/clip-001.mp4"),
    "ffmpeg", "ffprobe",
    Path("D:/film-attempts/NEW-ATTEMPT/capture/clip-001-audit"),
)
```

这是实际 library API，不是另造的 `xar-promo` CLI。内部直接使用正式 `xar_promo.adapters.ck3.load_capture_bundle`，要求指定 span 存在，并沿用其 report/timeline/index/bytes/SHA/clean-frame 验证。源 bundle 只读，destination 与 audit 必须全新。

## 输出与时序

- 返回 `media`、`receipt`、`source_recording` 的 `path/bytes/sha256`；原始 raw 可以由调用者在 run 中保全一次。
- `controls` 的每条记录有 `source` 和 `preserved` 两组绑定。后者是新审计目录内 report、timeline、index、全部已验证 span 证据的精确字节副本；原文中的绝对路径不改写。这不是可搬迁的完整 capture bundle。
- `control_index`、原始/输出 `bound_probe`、`request`、FFmpeg 与 ffprobe 命令审计均留存。调用者应保全整个 audit 树、receipt、源 raw 和剪辑产物，再让 composer 使用已保全的媒体，避免依赖随后可能变化的原 root。
- 源视频可为 CFR 或 VFR，须有真实递增 PTS 和可证明的时间覆盖。媒体时间仍须零起点；窗口向内取完整30fps**输出时间网格**，不能越出请求区间或 clean span，最多省去一帧时间。实际时长与省去的边界余量单列；不冒充完整请求时长或旁白长度。
- 保持1倍速、画面比例和2560×1440黑边布局；依据真实 PTS 在每个输出时刻显示当时最新的源帧，允许标准重复/丢帧，但不插值、不循环、不变速、不在源有效尾端后补帧。源音频不进入剪辑。
- v2 receipt 保留 source 实际帧数、PTS间隔/最大gap、尾帧支持范围、逐输出帧的源采样映射。30fps是交付帧率，不是源采样能力；旧约9fps录像只作可读context，不从长gap推断无行为。原生因果、源hash、clean span及审帧合同保持。
- 使用 FFmpeg [`fps`](https://ffmpeg.org/ffmpeg-filters.html#fps-1) 的时间采样，`round=up` 使未来帧不提前显示；未使用运动插值滤镜。已有真实前帧才允许窗口开始时继续显示，EOF只使用已证明的最后帧duration，不按旁白补长。
- 源在渲染后执行一次 adapter `verify_unchanged`。失败保留控制文件、stdio、命令和 partial，写独立 failure；不能覆写成成功。导入前后都不修改或删除 capture 素材。

目前为精确时序采用完整解码到所选窗口，远端时间很靠后的长录像可能较慢。该代价不授权改成关键帧粗切或变速。媒体通过也只证明连续剪辑与证据绑定，尚需项目判断画面内容、可读性及当次原生决策链。

## 聚焦验证

在已验证依赖的工作树解释器中运行，artifact root 必须新建且永久保留：

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/test_capture_media.py --artifact-root D:/workspace/ck3_native_war_ai_promo_work/capture-import-SYNTHETIC-NEW
```

专属测试包含真实 FFmpeg 合成短片的剪辑/尺寸/30fps/无源音频、向内窗口与越界拒绝、真实 adapter 对 RED 的拒绝、来源渲染期间改变时拒绝并保留 partial，以及目标不覆盖。成功路径显式 mock adapter，不创建可被误认成实机成功的 GREEN CK3 报告。
