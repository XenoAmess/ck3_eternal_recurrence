# R10 增量证据 ledger：截止 SDK150（2026-10-06）

这是一次外置增量索引，**IN_PROGRESS／NOT_GREEN，0个本轮成功JOIN，fullcycle=false**；不重写完整验收报告，不改冻结草稿001–004，最终报告仍等实际正常退出与ROOT最终cutoff。

SDK1–55继承004封存索引；只新增读取SDK56–150，共95项真实MCP结果，逐项绑定request／started／response／原SDK／native-copy的bytes和SHA。读取原件不调用任何工具服务，未执行AST解析、旧测试、Client／pipe／游戏／总线／Git操作。

本次保存与独立后验追加：第二提案nonce8签署拒绝result2；第三nonce9正常选取消、保存result3；第四nonce10、第五nonce11均正常native选择取消、独立保存result3。各轮开案、取消及source签署状态各有自己的sealed包，NPC票identity省略保留NULL，旧票不沿用到新nonce；钱与prior completed history未新增成功业务。原保存中的joins1／detaches2属于本局加载的既有历史，不能计为R10成功循环。

第六nonce12开案129独立包32checks已封。SDK146（ROOT0147）在event76选择public option5／native index4 withdraw→event77；SDK147 typed query明确lyd.228，SDK148 ACK后无event，SDK149实际保存 **91,537,192B／SHA `5ab8d308bd2f3858388f86cc34289683c30cf8efa43515283c001421c40affe1`**。第六post-cancel独立AST尚未sealed，本ledger不使用reader初报，保存result、保护检查及最后独立业务结果维持pending／NULL。

SDK150（ROOT0151）真实fresh ordinary query **SHA `27fff1d1a7533e83d39b72684a33f43a637c1dbb56110f0d9fe1c8cbfb8534ee`**，public70／native69／date53144712，PID13436，钱包1543G／5650P／2200prestige，CanSend／ready=true、active／incoming=false。可发资格不自动给下一次host release、permit消费或新提案信用。

SDK142与本地等待的边界：ROOT request0143通过v3实际入队一次。20秒只读等待的原stdout为`RESPONSE_STILL_PENDING_NO_RETRY`，v3随后要求MCP_RESULT_RECORDED的本地调用失败仍保留；没有单独raw caller退出回执时，不伪造exitcode或错误文件。原SDK142在 **34.057316秒** 后实际完成，**5,894,299B／SHA `654b00c7336b0c1c7b7806cc74f107f44c907fbb9631cbcce1ee5eacd16d4957`**，native结果verified_selected_detail；没有重发原选择。

ROOT0144后来是新的只读detail query（SDK143），ROOT0145才是新的confirm（SDK144）。0144原confirm arguments文件留存但没入queue／SDK。v4只把只读等待20→45秒，源码SHA **`79a011ccaf87a5626a3d42034316cbc558a2f5d649a1381c6897c4fdddd411f8`**；延长本地观察不等于重试或改变业务。

helper002源码独立审查拒绝HELPER_QUERY_METADATA_GATES_INCOMPLETE：4项无效metadata被接受，缺少同frame provenance／正actor及alive、ctx alive门禁，还有output alias缺口；旧作者PASS与真实独立拒绝均保留，002不作为live proofs。003追加修正、作者28项定向检查PASS，但独立审查仍pending，尚未实际prepare／assemble任何live refs。源码检查不外推为真实permit／业务执行。

追加实际emit/release与ordinal继承的独立索引，按各自save nonce变化和旧claim／permit不可变SHA记录；没有把pending ACK写成JOIN。日志证据仍只到checkpoint108的138,556B快照：578条I4 unused诊断，cap／truncation／后续持续coverage未知，不补造后续日志覆盖。

Client、profile与lease未关闭，normalexit NOT_RUN，keeper FINAL／sourcefreeze解除未发生。本索引封存后保持原样，之后真实第六AST或退出收据应另追加证据包。
