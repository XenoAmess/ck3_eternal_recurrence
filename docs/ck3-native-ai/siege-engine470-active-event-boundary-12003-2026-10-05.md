# CK3 1.20.0.3：围城普通日循环的真实事件边界

2026-10-05。Readiness 为有限 **production-live loop**：接续 [470到场后的20日实机流](siege-engine470-post-arrival-live-flow-12003-2026-10-05.md)，本批又保存4个完整普通日，然后按实际active event停于Root。前批52日只历史回链，不读旧cache或重复增量。

Runtime仍 **v72/g77/R45/source `f26be866fcb1642b81ffbac4707fdc447db1e068`**；Robert29829/episode `native-29829-2bc2d599f7f9`、ordinary campaign/XAR off、environment SHA `ae8140b0e434747c57b2a6223b0602b34c9d49e2ba60df5619f8057bed4aeef9`。Exact build为CK3 1.20.0.3/Steam25652598/EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

- SDK **59917 CLOSED0 GREEN**，stop=`actual_active_event_requires_root`。计划max20仅实际 **4 whole/calendar/bounded日、96 raw小时、partial0**，raw53264376→53264472；余16日未执行、信用0。28 GREEN工具叶＋4 day results＝32新daily原JSON，各轮独立paused/map_ready与真正normal SAVE匹配实际24h。
- 正式 **5002→5006/36524**、resumed1849→1853、Oct5/W41 +344→+348；P0恢复至今56＝此前52＋本4仅账目汇总，不补planned日或重授已有器械交付/贡献。
- 前3日final activeevent均null。day4实际before raw53264448仍null，独立after/final **raw53264472**出现 **instance28/option_count3**，indices0/1/2均enabled=true，title与labels仍null。这里只保留generic可见边界，不猜事件内容、效益或最优选项。
- 末帧 **native242/public17/raw53264472**，Robert alive、paused/map_ready=true、pendinginteraction null。事件在本保存边界仍待处理，Root独立event-rich SDK57783由其他owner消费；本lane没有读取该原件、选择选项、解决事件或自动继续余16日。
- 末whole normal **h8932/raw53264472/98902155 bytes/SHA `b013ca645b6021f16dcc6b3591031e9c2d90024bd0aa46641c49345ae93d2d1e`**，取自本轮 `save.observed.checkpoint`，不拿pre-save final里的上一日lastcheckpoint替代。
- 末470仍未占领：B3001、work36272855/rem18727145、progress65950/Q100000＝65.950%、ETA76仅当帧估计；breach1/CanStartAssault=true/assault_in_progress=false。3711仍未占领，B2912/work12708240/ETA435；War117440524 active/+25、owncombat0。围城work与assault合法性是观测，未执行冲锋或授围城完成/战胜信用。
- **新增K/M/D测量、贡献归因、事件选择/解决、冲锋执行、battle、natural succession、completed family信用均0**；daily丰富null不以旧rich基线回填。旧R44 zero-day map-unavailable RED及具体拒绝类别unknown仍保留，不把后续实际恢复解释为旧根因全部闭合。

唯一本批输入：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v72/root-results/v72-current8751-01/ordinary-r45-post-arrival-siege-four-consumed01/FULL-POST-ARRIVAL-DAYS-CACHE.json`，**3006478 bytes / SHA `24f47bb3856dc8eaabe63a64819d3d2c1f4a31552984833404862c93a13c4a33`**。同目录 `receipt-topic-lane/report-fields.json` / `RECEIPT-LEDGER.json`保留4轮日期、SAVE、七叶pin与event transition；父32原daily JSON各完整消费一次，本lane完整读本FULL一次。无TOP/event-rich/旧cache/共享专题读取，0SDK/窗口/进程/共享/Git/测试/fullbuild。
