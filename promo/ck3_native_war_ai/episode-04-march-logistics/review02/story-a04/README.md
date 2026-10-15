# Review02 story-a04：16段可录音机制与实测增量

本目录补原69段中的16个新ID；不覆盖story-a02的24段或story-a03的13段。三批合计53/69仅是**正文草稿覆盖数**，不换算研究、镜头、声音或成片完成率。原六章与全片30–35分钟编辑目标保持；目标尚未由音轨验证。

[口播与逐段镜头](narration.zh-CN.md)是实际正文；[机器映射](claim-shot-agent-map.json)沿用现有paragraphs结构；[来源精确字节](source-index.json)把源码机制、R0175/R0176实际后果和媒体候选分开。只读查找可使用[source_delta.py](source_delta.py)；不用SDK、桌面、provider或外置import。

新内容优先补员许可/准备/实际ADD的区别、来源角色开关、首段与终点的时间范围、R12停止和R13改道的实际后果，以及selected93实体250守恒与角色1/1变化。R03/R04/R05/R06/R07及ABC没有因为本次写作获得新的实机资格；R09全卡仍未闭合。

D10–D12为[repo-native SVG](cards-svg)。生成器[render_cards.py](render_cards.py)只写SVG并拒绝覆盖；不生成PNG，不调用图片服务。与a03的D01–D09互补。SVG使用同一系列棕金配色、2560×1440、标题69/body45；底部1120–1440留给字幕。该lane只核XML/字号/文本墨迹边界，没有连续视频审阅或人工签核。

```text
python -B promo/ck3_native_war_ai/episode-04-march-logistics/review02/story-a04/source_delta.py --paragraph C04-07
python -B promo/ck3_native_war_ai/episode-04-march-logistics/review02/story-a04/render_cards.py --output-dir <new-explicit-directory>
```

媒体候选：R0175的0–4、4–24、24–43.5秒；R0176的0–4、4–10、10–20秒。全部仍是candidate。R0175视频面板显示登船，次日静止不是片内结果；R0176替代终点在45秒片外，不能给终点镜头信用。响应墙钟未校准encoded PTS。

纯lookup不会启动任何实机或媒体动作。换机器可以复用源码解释、原件重算与reader；新机器实际状态仍需自己取证。旧Review01交付保持，本目录不是新成片或人工approval。
