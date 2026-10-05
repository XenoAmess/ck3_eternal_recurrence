# R0177 A2：A-only 到达与多段录像的小型离线证据包

这是一份封闭到 A2 的来源快照。A 首次到达伦敦的观测端点为 +51 日，前一未到端点为 +49 日，故真实到达只定位于 (+49,+51]；B、C 和 winner 仍为 null。三路数字进度是 1/3。完整 27 军团 / 37 DATA 的观察端点给出人数净 +10、库存 raw −423728、金币 raw 净 −1606233；费用和兵员应用账本未知。

同一 A2 有 S01 / S02 两段已关闭的独立 recorder Job。S02 a01 在录制进程建立前失败，a02 才是实际第二段；重试没有冷载或重置共同 90 日预算。额外 CUnit 16777443 的 native Army、健康及分类未评估，global partial 仍保留。required Main0 的完整向量可用。

从仓库根目录运行以下三个 stdlib 消费者（也可在 Git archive 导出树运行）。解释器不需要 CK3、SDK、媒体工具或第三方包：

```text
python -I -S -B promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0177-a2-arrival/code/verify_A2_values.py
python -I -S -B promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0177-a2-media/verify_media_catalog.py
python -I -S -B promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0177-a2-metadata/code/validate_recording_segments.py promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0177-a2-metadata/recording-segments-metadata.json
```

第一个检查供应的同暂停原生/公共帧、FullID、完整向量与派生端点；第二个检查小文件精确字节及既有媒体审计/选帧/Root 审阅关系，不重新解码或查看像素；第三个只核小 JSON 的来源、共同预算、段开始/结束、失败重试、会话退出声明。metadata checker 的 credit 固定为 0，Root 的 A 数值接纳属于另一份独立来源。

S01 3600.000 秒 / 108000 帧、S02 2884.966 秒 / 86549 帧各有既有全解码审计，Root 分别直接审阅 6 和 5 张 encoded 帧。这不能授连续 clean span、1× 完整人工观看或 signoff。段间控制器 finish 事件至下一 process start 事件的差值不能冒充最后一帧到第一帧的录像间隙。确切到达帧仍未知。第 27 日 90% 当前边进度时实际锁定；loaded cutoff 与精确 50% 执行仍未验。

所有来源原字节保留；历史绝对路径是 opaque provenance，三个消费者只读包内相对文件，不打开所引用的 RAW/PNG/存档。原录像、图像、完整媒体表和游戏本体不入库。机器/run 专用采样或捕获脚本不被包装为跨机一键操作工具。A1 原失败/closure、冷载比较和旧切点均保留，后续闭合以追加事件解释，不修改旧 pending 字段。

参见 [A2 端点知识](../../../../../docs/ck3-native-ai/army-episode04-a2-london-arrival-12003.md)、[实际端点包](../r0177-a2-arrival/ENDPOINT-BOUNDARY.md)、[媒体小文件索引](../r0177-a2-media/catalog.json)、[多段来源说明](MULTISEGMENT-KNOWLEDGE-CANDIDATE.md)。
