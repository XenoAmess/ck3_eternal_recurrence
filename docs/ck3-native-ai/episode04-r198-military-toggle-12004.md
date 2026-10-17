# Episode 04 — R198 军务补员开关一次实机读回

`machine_id: desktop-3fevhd2-1c74096080`；原生拍摄观察时间 `2026-10-17T10:14:41.301716+00:00`；源码、运行时 native source `dc031358981450ae3f8e40c6234b7f27fd4662ef`；场景 `R0198`，游戏版本 1.20.0.4。此页把开关动作的原生结果与媒体资格分开，供视频核词及跨机器智能体复验。

[小原件索引](evidence/episode04-r198-military-toggle-12004/source-index.json)、[ZIP](evidence/episode04-r198-military-toggle-12004/small-originals.zip)和[stdlib verifier](evidence/episode04-r198-military-toggle-12004/verify_portable.py)保留 16 份 exact JSON；四个关键原生 response 分别是打开军务、开关前新鲜帧、一次关闭开关、后验帧。索引精确 pin 未复制的另外两响应、桌面原图、录像和存档；本包不读取或审核原片。源机器资格不外推其他机器。

本场身份绑定 PID24728、creation filetime134367039851411170、generation1、episode `native-31254-a9475f27e7e8`、actor31254、日期 raw53148192。一次原生 `activate-ingame-military-v1` 后，唯一 `disable-military-reinforcement-v1` 返回 `verified_desired`，同路径 `0/0/0/2/3/0/0/0`、同owner31254，military raw byte `4A9` 在后续读回由1变0。动作包里的即时 `native_after_switch` 仍为1，不把这项当作即刻成功；同一包的 `later_observation` 与 take 聚合才读出0。前后 frame native revision3、ticket7→9、pump90051→90065、thread29140、日期不变；动作 `accepted=true`，后续稳定观察验证目标状态。15秒及20秒 hold 已请求；期间始终暂停，不是自然日推进。

原生结果仍标 `current_variable_table_observed=false`、`native_receiver_selected=false`、`provider_invoked=false`。因此本场证明实际关闭补员开关，但没有证明自然补员 ADD、围城扣兵、费用付款或R04县边损失。R06的完整补员正例仍缺。录制 `Finish=NORMAL_TREE_EMPTY`、guard error null、partial false；正常Save 5,264 B／SHA-256 `3fc07750458cac695677eab6d28db3bb9a47e36a808a82ead4b8253ea801aed5` 绑定 checkpoint 73,689,233 B／SHA-256 `09c5bf2f2aa3dad559a602c292ede45868d90c185bf491fb2e958f849f5bf9a0`；游戏exit0、screen资源清空。录像尚无完整解码、PTS、clean/1×及人工签核，不能计合格动态。研究 9/14、业务6/11、动态0/11、ABC0/3；R07-v1严格口径仍8/14、5/11。

来源镜头仅能陈述“本场原生读回开关从开到关”，口播不能由开关变化推成补员机制已自然生效。R197 的timeout/shutdown exit1是独立失败场次，不能被R198正常闭场追认。

## 2026-10-17 11:44 UTC 媒体基础审计（待采纳增量）

`machine_id: desktop-3fevhd2-1c74096080`。[媒体索引](evidence/episode04-r198-military-toggle-12004/media-index.json)绑定原[报告](evidence/episode04-r198-military-toggle-12004/review-report.md)、[asset manifest](evidence/episode04-r198-military-toggle-12004/asset-manifest.json)和小seek探针；报告内场景相对链接属来源位置，跨机按manifest的原始路径与SHA辨识。八张原尺寸JPG及原片仍在外置来源，未复制。原片57.266秒／1718帧，全解码exit0、PTS严格递增；8张抽帧及24×24 ROI将勾选→中间→未勾选界定为全片n1088／n1089／n1090。`C02-09`仅为`source_frames:[780,1675)`、895帧／29.833333秒的连续可解码候选。连续无遮挡clean仍`PENDING`，人工1×/signoff=false；玩家owner31254画面不等于封臣AI实测。R06自然ADD仍未证，研究9/14、业务6/11、动态0/11、ABC0/3不变。
