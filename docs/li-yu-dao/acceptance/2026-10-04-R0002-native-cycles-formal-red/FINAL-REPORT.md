# R0002 最终分项结论

**原生三轮分合 PASS；正式入口和朱熹礼仪选择 RED。** 没有整体产品 GREEN、零错误日志、保存后重载或发布通过的结论。

欢迎事件选项 native 后置条件通过（rev308）；九个中文礼仪选项显示正确；取消第九项通过（rev311），金币、虔诚、威望、压力不变且可再次选择。但欢迎之后的保存态 db281... 玩家31254仍在原型 rite150／faith33，只增加 lyd_enabled。

朱熹选项提交之后的独立保存态 **8dfe5f9eb6f084f081ce078d73e1a68cfd7e98ccf56512e5130359627a2eafd5** 仍为 rite150／faith33，增加 lyd_school_cooldown（tick365），没有 lyd_study_cooldown。实际朱熹目标是 rite158／faith32；该保存对象 convert=no。这个 convert 值只是调查候选，不能直接当作失败原因。修习要求八种正式礼仪之一，正确拒绝当前原型礼仪；本轮没有成功修习。见 [独立保存态比较](formal-ui-v2/saved/zhuxi-choice.comparison.json)、[朱熹 native 选项回执](formal-ui-v2/native/0101-0028-choose-zhuxi.native-01.json) 与 [最终分项状态](formal-ui-v2/final-state.json)。

原型同一玩家三轮合流／分立的 D1、D30 断言各3次、终点一次、无 FAIL／REJECTED，最终保存态的 faith／rite／领袖／郡对应关系独立读回通过；旧 faith 对象仍留存，不推断它们无追随者。见 [原型断言 v2](primitive/native-primitive-attestation-candidate-v2.json) 与 [保存态 summary](saved-objects/three-rounds.summary.json)。

最终退出后的 error.log 与三轮冻结副本逐字节相同：3 条 perspective、165 条 formatter、1 条 AI coronation、27 条 bp3_roaming invalid activity。正式界面的粉色 tooltip 错误见 [实机截图](screenshots/formal-study-requirements.png)。这些是真实错误；未知 formatter／coronation 的归因尚未闭合，不能为了收口称作无害原版错误。完整小型错误原件见 [退出后 error.log](lifecycle/error.log)，详细分类见 [增补](primitive/error-classification-addendum.json)。

根代理执行正常保存并退出；CK3 PID7564在 [退出回执](lifecycle/normal-exit-desktop-confirmed.json) 中不再存在。[keeper FINAL](lifecycle/keeper-FINAL.json) 记录无 failure、线程退出、最后 seq2626；[CAS release](lifecycle/screen-release-completed.json) 实际以2626匹配释放至2627，resources为空。MCP客户端 [close回执](lifecycle/mcp-client-close.response.json) 是 CLIENT_CLOSE_REQUESTED；服务进程15206和keeper68845均已停止由根代理报告，未将 close ACK 单独升格成独立进程终止证明。

现行索引为 [index-v3.json](index-v3.json)。README、report-state和formal-ui-v1保留生成时的待验状态；本文件及formal-ui-v2只追加最终结论，没有覆盖旧证据。初始身份、当前1.20 SDK接入、两次源码修订、CI提交区别、输入失败和物理按键修正的细节见 [初期报告](README.md)。完整debug日志、全部MCP时间线和四份大存档留在原永久外置树，以索引哈希绑定；仓库只收小型原始回执、源码、对象摘录与三张必要截图。
