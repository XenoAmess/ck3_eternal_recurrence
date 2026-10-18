# P67–P68：战斗只读query的大回执与有限归档

`machine_id: xenoamess-full-tower-eb9d2c1186`。本页只整理已封小metadata；P67结构扫描观察于2026-10-17T23:48:16.258802Z，归档stat为23:49:56.511053Z。全部原件、大小、SHA与来源时间见[小证据](evidence/p67-p68-combat-query-archive-performance-2026-10-18.json)。本次文档工作没有重复读取AUTO77、archive、Driver、SAVE或媒体，没有重跑测试、发MCP或修改现场。

## AUTO77实际大在哪里

R7 AUTO77实际执行`query-combat-simulation-inputs-v2-2619-2623-a-1-167772577-d-1-285213101`，status executed、query_sequence7。原回执100,646,305 B，SHA `7718048c9023d65eb7fbb35ae8378be4df61383e0f9d22446e56ecebcd61150d`；Root授权仅一次≤128MiB流扫描，派生59,514 B，不whole-JSONdecode或复制大正文。

| 原JSON字段 | 编码字节／项数 |
| --- | ---: |
| MCP `content[0].text` | 75,645,309 B |
| `structured_content` | 25,000,533 B |
| 其中plan | 11,471 B |
| 实际combat inputs | 24,986,853 B |
| 其中knight_stat_consumption_v1 | 24,818,879 B；16 events／144 contexts |
| contexts内preparation_entry_inputs合计 | 12,091,779 B |
| contexts内preparation_capture_at_consumption合计 | 12,001,914 B |

父子字段重叠，不能把表内大小相加当I/O。这次主因是只读战斗输入及MCP文本呈现，不能归成市场584候选或history全文进入plan。entry内preparation_at_entry与consumption capture恰有相同总字节数，只证明结构／大小重复，不证明内容逐项相等或可互换。

实际小config仍为64MiB／query、256MiB总、4份。唯一archive root已有q3–q6四份json、无partial、合106,670,827 B；**份数先到4/4，字节预算尚未耗尽**。原producer成功归档才缩public结果，无source ref则保完整结果。query7没有projection，与此fallback吻合；没有冒充读取私有运行期event来证明逐次命中。此前同step的AUTO26有完整26,667,668 B归档ref，公有回执40,570 B、elapsed10.350287秒；它与77不同帧，不能当同状态A/B。

## 87.814秒的实际边界

AUTO77记录开始23:44:22.672118Z、结束23:45:50.486451Z、elapsed87.814358秒。实际queue源码在MCP调用／client解码与model_dump后就记录ended/elapsed；后续整包JSON计字节、atomic回执写入、classifier/display/credit都不包括在内。这个值不是whole-turn墙钟，也不能全部算Native CPU。

SDK48 query执行路径只含primitive send/wait、typed normalize、同帧检查及canonical cache deepcopy，不在这个selected query内跑whole-battle simulation；原plan在before_submit前已完成。该query未进入现有send/result profile启用列表，小日志也没有它的阶段耗时，故Native采集、管道等待、Python归一化／复制、归档与MCP编码占比仍未知。不能用其他scalar操作的ns或snapshot毫秒值替代。后继本来必要的埋点应分别记录这些阶段的小数值、requestID/queryseq和payload字节，不再记大正文。

## P68透明压缩：转引一次实际样本

以下是**转引 `/root/archive_compression` 的实际回执**，本页作者没有自行运行该bench。2026-10-17T23:57:34.897132Z至23:57:41.946663Z，该owner读取闭q6一次，创建一个新文件并在首字节前设置NTFS压缩，再单次读回：logical均26,667,819 B、SHA均`3c90c2a0df841cb4cf8a605d34b249f2d8ab64a07b5a6b78eb8a409375863f5e`，新文件storage为**6,361,088 B（logical的23.85%）**；标准json.loads完整payload通过。旧q6的文件身份、logical bytes与压缩属性保持，0Game／Native／MCP。bench回执6,558 B、SHA `d41fea7646867a3d0372f189c16bd7c0e95dcfeabf07b9412e56183be4e8925e`。

这只证明该机器NTFS单个闭样本同bytes压缩；storage读数不含文件系统metadata。限速复制／读回与JSON解析墙钟不授压缩CPU开销或吞吐提升，比例也不外推其他卷、机器或未来输入。候选只作用新archive空临时文件：`x+b`后、写前设置并读回压缩，保原encoder、logical计数、SHA、fsync、create-only发布；失败沿原完整结果fallback，不伪称归档成功。

后继候选逻辑门保持64MiB／query、256份／8GiB，两个上限独立生效；**透明压缩不抵扣任何逻辑预算或预留**。应在新epoch唯一root与获准component下采用，旧4份不改，不因压缩绕容量门。该样本derived副本保护至2026-10-19T23:57:41.946663Z复核，不扩为永久保留。

## 保留业务输入，采用另验

knight capture虽大，当前typed contract仍要求完整结构；实际simulation用每个Ci自己拥有的consumption capture构造postimage和property override，不能凭character/capture序号借另一份历史，也不能用entry代替consumption。当前没有已资格的lossless-ref解码合同。性能改进保完整canonical／业务IR、只读Native字段与模型精度；不靠删字段降低体积。

P68在其23:59:02Z交付截点只是外置候选／单样本通过，未部署；本页不预填后继R8安装或实机收益。下一必要维护的完整entry、归档预算与失败路径仍须Root/namespace资格，日期守卫另见[P70 V2](p70-first30-date-horizon-v2-2026-10-18.md)。首次30年仍未到raw53407320，到点永久MCP手动SAVE及整片没有因这些性能结果而完成。
