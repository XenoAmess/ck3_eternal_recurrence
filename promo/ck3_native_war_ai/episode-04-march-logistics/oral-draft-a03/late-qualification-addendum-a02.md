# 2026-10-05追加：R0173后续数字资格

本条是原a03正文之后的独立研究增量。原14个便携文件、6907字69段正文、逐段研究账和原pending切点均保持准确字节，未回填第44日平分3337/3342，也未把后续整数增长替换为早期人数。旧pending描述属于当时切点；本追加记录后来实际观察到的资格结果。

正式来源为master `700b6917ad7ee1a9ca7bcb930b114f8bd4f11498` 的[专题][doc]、[索引][index]和[只读复核代码][verifier]。专题5650B/SHA7393ef0d024ff68dbe8ab771937ae3fa91d3a1ad2a0bf0443fa149708a07485f；索引47381B/SHA4abb9de818d1dbf1dd7ad4e572bb90cadfff1b3d9bedf998af7b9133375eded8。整合lane终态回执为OfficialCI37318647289 completed/success；本包只核已保存正式来源字节，未调用Git或CI。实际阶段分开如下。

| 独立实际窗口 | 观察到的结果 | 口播权限和边界 |
| --- | --- | --- |
| 原+49→+50日，q03→q04 | 两军分别在2174/2327停驻，regular、空路线；当前补给月值均由−4.23728变+20，库存不变 | 可讲已找到本次两处正补给驻点；不能在此帧提前讲库存已经增加。+50 Main当地用量3337/上限4960，child3342/4160；单位是士兵。 |
| 原+64→+66日，q10→q11 | 子军库存110.37716降到容量100，月值仍+20；成功更新标记到+65 | 实际超容量封顶，方向为下降；不叫低库存恢复、补兵、死亡或加权合军超容量截断。 |
| 原+70→+72日，q13→q14 | Main3337→3344，净+7；child3342→3345，净+3；六条DATA整数增长 | 完整27FullIDs/37DATA身份与max不变，库存和补给更新锚点不变；实际整数增长可讲，日历一致性不升级为producer PC/调用栈或已应用补员账本证明。 |
| 原+74→+76日，q15→q16 | Main库存106.13988→126.13988，净+20，容量300/月值+20；成功更新标记到+76；child仍100 | 这是主军实际正库存写回，完整27军团/37DATA全部整行不变。它与前一个整数增长窗口不同，不拼成同一次结算。 |

可供下一轮句稿冻结选择的短说明：

“第50日，两军终于在不同驻点读到正20补给的当前月变化，库存还没有增加。后面要继续等真实更新：新分队复制来的110多库存先回到100容量；另一独立窗口，两军各自实际补进7人和3人。再之后，主军库存从106.13988升到126.13988。补兵与补给增加有各自的日期和完整记录，不能合成同一瞬间。”

这段说明是新增draft备选句，未加入原6907字统计，未TTS、未测时长、未绑定可用连续视频。若采用，应另行冻结最终句稿和对齐原版动态画面，不能把新增文字当音视频已完成。

## 时间、身份和仍未读取的条件

原Jan20 raw53147376的90日资格时钟仍截止53149536；最后原+76日raw53149200，已用76日、还余14日，不因冷载或正例出现重置。R0173平分前未拆whole保存仍是d052a2e4…；c43f71c4…只是本次split资格备用，不能当A/B/C未拆共同起点，也不能用后来的现金/半军路线替换最初whole状态。完整保存SHA和本期source绑定见[本包追加来源pin](provenance/r0173-master-source-pins-a02.json)。本包不读取、复制或重hash大存档。

第50日独立typed统帅查询分别为Main27357和child33388；这个身份只授该帧，不能外推为第72或76日仍未改变。capacity300/100也不是统帅身份读取。London目标1527的当地usage0不证明friendly、到达后总用量或将来正补给；1506仍只写省份编号。

原+52日外部1609围城/占领变化STOP与子军超容量库存下降STOP均保留原失败/审阅事实。后续仅在Root限定的有限两处休整协议中继续，没有将旧STOP改写GREEN。2174/2327不在已读取war objective rows；Army/health/site端点相等不证明完整occupation/controller/garrison连续不变。未读取字段继续unknown，不宣称世界静止。

原health.source的game_version/executable_sha256为null保持原样；Root协议独立绑定exact1.20.0.3与源码7f1db1a773e647b9f31378d4a9ccf57a60cf9e73，不补造payload字段。数字资格具实际端点，但执行时producer、完整应用损耗/补员/死亡账本、精确结算时刻仍未由本追加读取。

正式A/B/C仍0/3，无胜出结论；加权合军超容量截断、威廉饥饿实测、实际付款事件账仍独立pending。成片、clean span、人工1×完整观看和signoff信用均0。Root最后原图小收据在已结束原片之外，没有encoded timecode binding，本包不读PNG或原片，也不给新媒体信用。

[doc]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/700b6917ad7ee1a9ca7bcb930b114f8bd4f11498/docs/ck3-native-ai/army-r0173-split-rest-qualification-12003.md
[index]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/700b6917ad7ee1a9ca7bcb930b114f8bd4f11498/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0173-split-rest/index.json
[verifier]: https://github.com/XenoAmess/ck3_eternal_recurrence/blob/700b6917ad7ee1a9ca7bcb930b114f8bd4f11498/promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0173-split-rest/review_frozen.py
