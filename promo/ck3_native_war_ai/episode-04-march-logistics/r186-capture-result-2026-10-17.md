# R186拍摄结果：事件提前停录，十四日与36.700秒原片分别保留

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0186`。观察时间为2026-10-16 UTC／北京时间10月17日，runtime/native源 `d05b0c780b615faa714fdf0535403bb2e6941faf`，a29、CK3 `1.20.0.4`／build25734779。

本场完成14份自然日回执，date **53148432→53148768（03-05→03-19）**。第15日实际到03-20时出现事件，提前正常finish；该日没有完成回执，28日计划未完成。原片 **36.700秒／1101帧**正常封装、完整AV解码exit0无诊断，wall40.390308秒，均未达到100秒最低要求。业务、连续clean、完整1×及human signoff仍false，动态 **0/11**、研究 **6/14（42.9%）**、业务 **4/11（36.4%）** 不变。

| 项目 | 真实范围 |
| --- | --- |
| 捕获 | 2560×1440桌面中CK3客户区`[640,360,1920,1080]`的1280×720区域；gdigrab desktop区域，非独立HWND、非整桌面 |
| 原片 | `raw-window-a01/raw.mkv`，23,147,412B；SHA `7ca4edbcac4f46bd9dda6d796dadb20b619ad22cbdb5ec0333f18c1f23fda0bc` |
| 编码 | H.264／30fps，无音轨；末PTS36.667秒、末帧结束36.700秒；完整decode无诊断、不截断 |
| 开拍衔接 | ready→resume ACK **3.8324387秒**；不可沿用R185的3.272059 |
| 提前结束 | d15原生modal，跳过最低wall等待；不是达到100秒或录满180秒计划上限 |
| 闭场 | 正常保存date53148792；17:15:44 UTC游戏exit0；17:17:54屏幕seq5814 done/resources[] |

Root对三张原尺寸抽帧的直接审阅只支持：首帧03-05暂停、1173兵／1%图标／300/300；中帧03-11运行中、仍1173；尾帧03-20暂停，中央“礼仪变化”事件框出现且正文当帧仍空。画面内未见桌面或Steam等外部像素。详见[限定三帧回执](../../../docs/ck3-native-ai/evidence/episode04-r0186-20261017/root-three-frame-review.reported.json)，它不认证整段无冻结/无遮挡，也不推导未测人数变化或损耗因果。

事件由原生context识别为 `pam_bull_events.0004`、instance2，第一实际显示项“就这样吧。”。17:06 UTC仅提交一次原生option1，postcondition verified且独立after读回事件消失；选择在录像结束后，不能剪成片内已拍动作。初始未知registry、实际context、ACK与消失后验均保存，未用OCR或鼠标替代事件接口。

研发观测也有新的有限事实：R06两个widget的local mode0条目已独立双读，但无direct/provider/合法RVA，full父链仍depth8 exhausted，不能声称已补员。付款4条raw均属其他军队、qualified0；自然parent30与Army18在roster出现不等于Army18是caller。payment无覆盖不能外推到loss writer，后者全局overwritten3238必须保留，详见[共享研究专题](../../../docs/ck3-native-ai/episode04-r186-window-capture-12004.md)。这些结果不增加业务或成片分子。

正常checkpoint74,262,421B、SHA `934aa1b99cc59874eb7365eb997f520753c4db4e31afd91a2d416e28a0244aef`。选择性[证据与verifier](../../../docs/ck3-native-ai/evidence/episode04-r0186-20261017/README.md)可供其他机器复用；raw、PNG、save及完整Driver/大GUI树没有复制，不宣称完整closure replay。录像如要剪用，须另审精确连续区间并绑定raw SHA＋帧范围；当前未批准clean clip。屏幕释放不替代容量预留返还，素材时效按[统一存储策略](../../../docs/storage-retention-policy.md)另行复核。
