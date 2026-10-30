# resume90 两处旧规划测试夹具修正

machine_id: `xenoamess-full-tower-eb9d2c1186`；观察时间2026-10-30T17:55Z，Root D-only。运行与输出根为 `D:/ck3-state/resume90-root/fixture-followon`。本包只有两个既有测试源及说明；生产修改0，Game/模型请求0。

此前 source-contract-stop 的完整两类结果77方法75P/2F，两失败在原封旧源码/旧测试上均复现。本后继查清并修正夹具与现有生产接口的差异，保留这些真实红记录。

1. SessionControllerRegressionTest 的 extended deadline 用例仍用两参 ObservationPort 收到的 readinessDeadline+1ns。现生产区分等待就绪与批次规划 deadline，该值没有超过真正 planningDeadline，因此会合法保留捕获并进入离线分析；旧用例抛 no captured incident expected。测试使用既有三参接口明确传 planningDeadline+1ns，并让 fixture 装配的 observer 转发三参调用，仍断言 INTERNAL_FAILURE、无分析入队、无动作、无保存日。断言对应生产已存在的 observation extended batch planning deadline 文本；未恢复已撤销的旧短deadline限制。

2. FamilyRecordedBetrothalFulfillmentTest 的 changedPair 同时表示原betrothal候选2已成为当前primary spouse、当前另有betrothed5。生产先消费已观察到的原配偶婚姻并 Refresh。测试的 material port 却对 CURRENT_RELATION 一律调用不接受它的 FamilyResultReducer.reduce；诊断单方法实际显示 SOURCE_CONTRACT_REJECTED / not a family material result operation。现 fixture 按真实 FamilyMaterialStore 分派 CURRENT_RELATION 至 matureWarm，其他材料操作仍用 reduce；断言原候选2被记录为marriage、warm transition、旧alliance_result清除、仅读取CURRENT_RELATION且无提交命令。它不授新候选5婚约履行，也不拿Replace预期覆盖真实Refresh。

实际严格 javac all-lint/Werror exit0/4.466s；仅两失败方法定向2P/4.321s。最终五生产叶 source-contract-stop overlay 加两修正测试的完整两类80P/0F/0 skipped，17:54:08.555Z–17:54:27.568Z，exit0/19.013s。Java writer确认共享revision66真实编译03开始17:54:46.4728652Z，晚于该结束18.904秒，因此没有读写重叠，不为它重复绿测。

原测试/编译命令及结果各*.json，JUnit XML位于targeted-reports/full-reports，诊断红位于diagnostic-reports；TEST-SUMMARY.json保存独立分组，不把2P再叠加到80。原77/两继承失败记录仍在source-contract-stop目录，未改写。范围仅软件 fixture，不证明磁盘发布或Native/Game动作；不是全Maven/CI。源码前像与两叶LF diff在SOURCE.json/SOURCE.patch，唯一Java writer按DELIVERY.json采用。问题采用后于2026-11-07复核，优先回收可重建派生classes，保留必要小型源/诊断。
