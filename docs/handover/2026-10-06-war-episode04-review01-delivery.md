# 第4期 Review01 制作与可复用知识交接（2026-10-06）

第4期《大军为什么越走越少？——CK3 行军、补给与损耗》实际 Review01 已制作完成。影片为 28:55.80、1920×1080、30fps、六章、69段中文旁白与326组双语字幕。制作完成、全片机器核验、AI抽帧审阅、客户端同步、人工完整观看和签核分别记录；指定单MP4的本地SHA与两次客户端InSync元数据已核验，实际终态见文末；独立远端SHA未回读。

精确文件为 `CK3-War-AI-Episode04-March-Logistics-Review01.mp4`，1,199,061,934字节，SHA-256 `a1abb0f2abaa06f3fd38839123e9f4ddd4c4218f8dd15e0965732d3596c69346`。固定客户端目录为 `C:/Users/1/OneDrive/CK3-War-AI-20260923/`，仅交付此一个视频。

## 实际内容与研究边界

实际六章依次为：C01行军后勤读数与结果，C02补给容量与兵员，C03兵员净变化的原因边界，C04路线锁定与实际到达，C05三个方案与记录，C06玩家后勤步骤和证据边界。B在第38日因冻结编制与统帅条件变化停止；C的15次两日采样偏差原样保留，所以本片没有A/B/C因果赢家。

| 回放 | 实际结果 | 可授范围 |
| --- | --- | --- |
| A 整军直走伦敦 | 首次抵达观测区间(49,51]日，原始27团/37DATA，6689/max6747 | 独立实际回放；精确抵达tick仍未知 |
| B 分军休整后合军 | 第38日停止，剩余52日；出现额外1/1团与统帅变化，伦敦结果NULL | 合军补给加权上限算术有实际证据；冻结比较门槛未通过 |
| C 整军经2176改道 | 首次抵达观测区间(75,77]日，6689/max6747，库存101.90260 | 描述性实测；controlled comparison NOT_GRANTED |

人数净变化不等于死亡/补员流水；A现金净减16.06233与C净减15.81510不等于行军或登船费用。当前1%损耗getter也不等于本次实际死亡。C终态仅授原始Main队列，玩家全军总数仍NULL。详见[A记录](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0177-a2-metadata/README.md)、[B停止记录](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-b-gate-stop/README.md)和[C描述性实测](../ck3-native-ai/army-episode04-C-descriptive-march-12003.md)。

研究仍缺低库存小于10的饥饿及实际扣兵闭环、补员/付款执行流水、精确50%行军锁定边界，以及原生AI最终选点评分、调度和许可链。已有结论只用于实际1.20.0.3人物/场景；旧1.19证据不自动外推。研究没有正式加权分母，不把影片制作完成写成机制研究100%。

## 本轮已完成的核验

实际全片机器审计为新attempt-a02，52,074视频帧、AAC每声道83,318,400个48k样本，原始整数PTS没有缺口或偏移。编码priming1024和实际末帧640样本分别保留；NaN/Inf为零，解码混音未超过0dBFS。源旁白41,658,624个24k单声道样本，1735.776秒；影片网格尾差0.024秒。旧A-only的PTS RED与本轮被中断的attempt-a01均保留。

Root直接审阅了18张来自最终MP4的原始1080p编码单帧，未发现这些样本中的阻断问题。该范围不授连续clean镜头、全片主观听感或人工1×完整观看。正式preserve/validate已有实际rc0，public API生成的审阅包仍为pending-human-review，没有approval或signoff。

## 其他机器如何使用

先从最新`origin/master`获取代码，保留来源commit及各包相对manifest。研究事实在上述A/B/C包；最终69段中文、旁白方法和字幕分别在[旁白生产知识](../../promo/ck3_native_war_ai/episode-04-march-logistics/production/final-BC-a06/README.md)；双语字幕的[相对校验入口](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/final-bc-subtitles/verify.py)与[全片ASS](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/final-bc-subtitles/subtitles/full-global/subtitles.ass)在独立evidence包。最终画面源方法在[冻结画面包](../../promo/ck3_native_war_ai/episode-04-march-logistics/production/final-picture-a06/README.md)。

本次新增[实际producer收口包](../../promo/ck3_native_war_ai/episode-04-march-logistics/production/final-review01-completion-a01/README.md)、[全片机器审计文本包](../../promo/ck3_native_war_ai/episode-04-march-logistics/production/review01-machine-a02/README.md)与[Root/客户端实际收口包](../../promo/ck3_native_war_ai/episode-04-march-logistics/production/review01-delivery-a01/README.md)。包中保全项目源码、实际argv、结果、bytes/SHA及81,366行AAC整数时钟CSV；不携带raw录像、图片、音频、最终MP4或外置CAS。

用已验证Python执行producer包的`verify_package.py`与`plan_metadata.py`，或执行审计包的`portable_consumer_a02.py <该包目录>`。这些相对文本检查不打开历史C盘媒体路径，也不代表另一台机器已有原素材、重新验证了媒体或得到了人工签核。跨机器可复用的是知识和项目代码；重拍/重编码必须绑定新的实际版本、输入和媒体，重新查询工具链最新正式Release。

## 当前制作收口与历史

旁白/字幕生产知识commit为`448fcf0485799c2412ee8f2c1f26a1c440f6b8f7`，官方CI37397079758真实SUCCESS。冻结画面方法commit为`16de9d530b608522aefcce3261271aac77386d79`，官方CI37398374126真实SUCCESS、82条step records；新鲜终态另存，不改此前RUNNING/NULL与首轮失败回执。最终实际收口文本的commit及官方CI将在外置最终Git回执中记录，本文不预填尚未发生的结果。

人工1×全片观看/听审与精确字节签核仍待完成。OneDrive独立云端内容回读未执行；客户端InSync只授它的元数据状态，不能声称远端SHA已核验。

## 2026-10-06 客户端实际交付追加

实际只复制指定Review01 MP4。源文件、复制流与本地OneDrive目标同为1,199,061,934字节，SHA-256为上文A1ABB…69346。2026-10-06 04:17:57.804328 UTC与04:19:12.513579 UTC的CloudFiles实际成功样本相隔74.709251秒，fileID1407374883646263、mtime1791259477605413000一致；HRESULTs均0，syncroot5910974510929700、InSync1、size/on_disk/validated一致、modified0。Root实际收口原件位于[客户端回执](../../promo/ck3_native_war_ai/episode-04-march-logistics/production/review01-delivery-a01/client/Root-actual-OneDrive-delivery.original.json)，SHA-256为`966073f0784b51e2042b35b5c4c370747de4d5e5cef231626619e329ee7c981d`。

本地精确字节与客户端同步元数据已验；独立远端SHA未回读。前三次pending metadata与5次只读UIA样本保留原输出/分类，不回改成PASS。没有同步设置修改、其他云文件内容下载或新的UAC操作。人工1×完整观看/听审与精确字节签核仍尚未完成。
