# 《project因果律》架构图视频化导演方案

> 成片：2560×1440，30 fps；允许 20:00–30:00，导演目标 25:30
> 图册：[《project因果律》系统架构图册](README.md)
> 可执行时间线：[architecture-shot-plan.json](../../promo/project_causality/30m/architecture-shot-plan.json)

## 1. 核心决定

影片只使用 Mermaid 原生排出的节点坐标、分区和边。视频层允许做三件事：

1. 在原生 SVG 坐标系内等比缩放和移动镜头；
2. 高亮当前节点与路径，降低其他节点的亮度；
3. 在图层下方铺设章节氛围场景。

禁止在 Mermaid 渲染后抽取节点、另排网格、重画连线或为 11 号图制作第二套飞轮。这能保证文档图、视频图和源文件表达的是同一张架构。

## 2. Mermaid 原生画幅策略

目标不是强迫每张图恰好等于 16:9，而是让源图在 2560×1440 的主阅读区内天然可用。渲染器对所有 SVG 强制检查原生纵横比：

```text
1.40 <= viewBox.width / viewBox.height <= 2.45
```

当前 11 张图全部满足合同，范围为 1.466–2.393。画幅由 Mermaid 源码决定，不通过导出后的拉伸、裁切或节点重排补救。

### 2.1 源图写法

- 顶层 `flowchart LR` 或 `flowchart TB` 决定全局宽屏骨架。
- 每个功能域使用独立 `subgraph`，域内用自己的 `direction TB/LR/RL` 建立阅读顺序。
- 跨域边优先连接整个 subgraph。Mermaid 官方文档说明，只要子图内部节点直接连接外部，子图声明的方向会被忽略并继承父图方向。
- 少量使用不可见边 `~~~` 稳定同层顺序；不可见边只负责排版，不表达系统语义。
- `mmdc -w/-H` 只改变 Puppeteer 页面视口，不改变图的拓扑比例，因此不把它当画幅工具。
- 使用 `@mermaid-js/mermaid-cli@11.17.0` 与 ELK 布局；该版本在运行依赖中携带 ELK 布局包。

参考：[Mermaid Flowchart](https://mermaid.js.org/syntax/flowchart.html)、[Mermaid Layouts](https://mermaid.js.org/config/layouts)、[Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)。

## 3. 2560×1440 画布

| 区域 | 坐标 | 用途 |
|---|---:|---|
| 全画布 | `0,0–2560,1440` | 最终编码尺寸 |
| Action safe | `96,72–2464,1368` | 装饰、线条和非关键轮廓 |
| 主阅读区 | `120,90–2440,1276` | 标题、节点、边与图例 |
| 架构视窗 | `120,236–2440,1276` | 原生 SVG 全拓扑窗口 |
| 字幕叠加区 | `220,1080–2340,1360` | 字幕使用独立半透明底板，不再挤压架构图 |

全图建立镜头负责让观众认识拓扑。进入论证后，画面保持同一完整构图，只切换节点与路径亮度；不拉伸、不裁切，也不隐藏循环入口或返回边。

## 4. 氛围背景

原始头像 `images/project_causality/character/humanized_avatar_source.png` 只作为角色生成参考，永远不直接贴进成片。四章使用根据角色设定生成的完整 CK3 / 中世纪奇幻场景：

| 章节 | 场景素材 |
|---|---|
| 咒 | `generated_atmospheres/spell-court-v1.png` |
| 术 | `generated_atmospheres/method-scriptorium-v1.png` |
| 道 | `generated_atmospheres/principle-archive-v1.png` |
| 辉煌愿景 | `generated_atmospheres/vision-four-loops-v1.png` |

素材位于 `images/project_causality/character/` 下。画面处理合同：

- 场景覆盖画面下方约 82%，人物自然处于环境中，不做头像卡片或中央贴图；
- 图层不透明度为 34%–40%，轻微 3 px 失焦，保留场景颜色和可辨识细节；
- 顶部遮罩约 86%，中部 56%，底部只压暗约 22%；
- 架构视窗为 28% 黑色玻璃，不再用厚重黑幕遮掉背景；
- 节点可读性仍优先，亮背景区域由视窗玻璃和节点自身底色承担对比。

## 5. 镜头语法

### 全图建立

持续 2–4 秒，完整显示 Mermaid 原生拓扑，只要求观众看清分区、颜色和循环方向。

### 原生拓扑高亮

整张 Mermaid 拓扑始终完整、等比、居中占据 2320×1040 视窗。分镜中的 `focus` 只改变节点与路径亮度，不改变构图和取景；观众始终能看到返回边与当前局部在全图中的位置。

### 实机插镜

四个 Loop 各自保留真实玩法、OODA、trace 或 release 的插镜。实机片段不是装饰，而是架构图中的“真实结果”节点；插镜结束后必须匹配切回对应节点或返回边。

### 章门

咒、术、道、辉煌愿景各有独立 20 秒主题声明。架构图不得跨过章门持续挂在背景里。章节场景可以在章门后延续为低强度氛围，但四章颜色和语义必须明显切换。

## 6. 重点图的处理

### 01｜整套系统

先显示四个并列功能域，再按“咒 → 术 → 道 → 辉煌愿景”依次推进。镜头移动只发生在句间。结尾回到全图，强调产物、方法、原则和四环并非四份互不相干的目录。

### 02–05｜四个 Loop

每个 Loop 使用同一节奏：全图拓扑 → 输入与制造路径 → 真实插镜 → 结果与返回边 → RED 或下一轮入口。四张图都由 Mermaid 原生分区组织成宽屏工程图，不再把节点提取成后期卡片。

### 06｜自动游玩智能体 + MCP

分别巡航游戏、能力面、智能体和证据四个域。讲 ACK 时只高亮动作返回与后置验证之间的关系；讲 OCR 时让玩家可见画面承担主视觉，架构图只显示感知、typed query 和 verifier 路径。

### 07｜自动化验收

按源码输入、离线语义、production staging、隔离用户目录、CK3/MCP/OODA、后置验证与发布裁决推进。GREEN 与 RED 必须同时留在拓扑里，不能只展示成功路径。

### 08｜权威与证据

先讲规范序“意图 → 文档 → 测试 → 代码”，再讲经验序“exact build → paused state → 玩家可见结果 → artifact”。两条序列在同一裁决节点汇合。

### 11｜四环飞轮

直接使用 Mermaid 原生宽屏图，不制作独立 16:9 重排。依次高亮 A/B/C/D 的互相喂养、共同进入证据环、外部现实返回人的判断。愿景场景在底部逐渐可见，但“人的判断”仍是架构节点，不由人物贴图替代。

## 7. 实现与验收

```powershell
py tools/render_project_causality_architecture.py
py tools/render_project_causality_architecture.py --check
py tools/render_project_causality_architecture_video.py --output artifacts/project-causality/2026-09-19-r7/architecture-plates
py tools/render_project_causality_architecture_video.py --check --output artifacts/project-causality/2026-09-19-r7/architecture-plates
```

验收条件：

- 11 张源图原生纵横比全部在合同内；
- 视频 plate manifest 明确记录原生 Mermaid 全拓扑投影和 `node_reflow=false`；
- 文档图与视频画面中的节点坐标、边和分区来自同一 SVG；
- 2560×1440 与缩放到 1920×1080 后，当前节点均可读；
- 四章场景可见但不与文字争抢，且没有直接贴入原始头像；
- 双语字幕不覆盖关键节点；
- CURRENT、VISION、UNSUPPORTED、RED 与 readiness 语义不因动画而改变。
