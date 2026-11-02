# 共享SDK、产品源码与冻结Native的独立绑定

`machine_id: 4-8e1c2f1861`，2026-11-02。W为`C:/workspace/rrf-ui-release-20261102`，P为`W/shared-sdk-recovery-r63-a01/metadata/runtime-preparation-a01`。本记录覆盖来源绑定、实际软件资格及R63/R64的有限GUI后继，不代表完整产品矩阵完成。

## C/S与Native身份

产品仓库C为`C:/workspace/ck3_eternal_recurrence`，离线producer最终干净提交`8c9136e94f84fad847f6c2220c1aa44a70605993`；产品正式90文件staging仍绑定SourceA`99462364158fc0165cd2cf2b2d4813bb572920f9`。这次C/S修复未再次发射fixture，也未重建正式载荷来追认新的身份。共享SDK源码S为`W/shared-sdk-source-a01`，保持干净`720c35b10a9ad9874ad1bf63809f772493cea75a`：已资格2ef基线仅加入`f646907b3a311bcd003ca0b1c5356f02fcd94e81`的Python driver、回归及R62样本修复。

一次初始化的稀疏S持续复用，不吸入C中178项尚未编译Native差异。Native relocation核对完整5484项跟踪路径集合、实际文件集合及逐项bytes/SHA，要求S与a09冻结原件全等；任何Native差异仍拒绝。原compile commit`cbacd3373427ffc9dca016584dffe8baf89d80b6`、CMake/config原路径、对象、archive、DLL及编译proof不改。a09 qualification为7495B / SHA `bd134c711a09ede1e54d526dbcf92446cf6155b2d8177564c968e82acb84cc78`；原DLL为15751680B / SHA `17e85f17620875866a4c0845463c3a2ff6868ccdfef3dcdce42e4a64d2dc83c6`，没有重编Native。

## 现有生产链的最小接线

既有freezer新增显式`--shared-source-root`，在新输出内产出绑定parent runtime/manifest/source-index的派生base及relocation回执，原输入不热改。既有builder新增显式`--product-repository`与`--product-source-commit`；默认C=S行为保留。最终runtime沿既有repo_root/source_root等合同分别表达产品C与SDK S，不向旧S的严格runtime顶层悄加新schema。

既有Java SourceQualificationEmitter以绑定父图的明确C→S关系解析旧source pins，逐项比较S实际字节，原Q和证明不改。实际COMMAND_SOURCE_EXECUTION仍须cwd=S、真实before/after源表及原Popen waits，不能由路径投影伪造；同一真实proof用于两条相关chain，不重复计算执行次数。

Native existing-plan只读重放原先两层硬编码读取当前C，真实BUILD1保留。修复仅允许显式S用于已存在的v3计划，继续要求干净checkout、原compile commit祖先关系、完整Native集合与字节全等；新plan/build的ROOT选择不变。参数贯穿artifact/fixture-link/configured-link/verified_fixture_object_bindings/Producer.plan全链。没有平行runner或例外放宽。

提交`e5d08b7fd8fd20a59fb52d994bf6e7d576296b44`负责C/S及资格接线，`be3f104c7b544c7820ea073cf0463152d625ac6f`负责v3原计划源根，`8c9136e94f84fad847f6c2220c1aa44a70605993`补齐fixture内层转发。`P/BUILD-RUNTIME/`及`P/BUILD-RUNTIME-b03/`两次原wait1、首次SIXQ GAP和局部测试签名笔误失败均保留。

## 真实资格与检查边界

S最终完整CI step为contract strict0、26 tests/0skip，3464项源码before/after pins全等、两条原Popen waits均0。原proof `W/runtime-repair-r62-a01/FINAL-CI-step-a01/COMMAND-SOURCE-EXECUTION.actual.json`为1912058B / SHA `3b5ae0a568ac8f715929cd3a453f43f061f457d66ddb11d9564bb8dcbb5e2d65`。原S720保持不变。

12项OTHER是未选入SDK/Native的历史产品文件CRLF/LF差异；以实际旧/S/Git pins及精确CRLF转换相等的SOURCE_REVIEW/UNSELECTED_SOURCE_ONLY消费，`execution_qualified=false`，不能标RAW_EQUAL或授执行信用。`P/UNSELECTED-S-CRLF-SOURCE-REVIEW.actual.json`为4763B / SHA `c37783c460f5fa9dc5238bb8196a13c607db20923d2c8701ae4fa4b8628fd7c0`；六链b02实际结果为SOURCE_BOUND_NOT_LIVE。

Python基础builder suite90项0，随后新增C/S两项正向检查0，最终完整V3局部消费链10项0，不累计重复子集。freezer/native-binding和既有Native生产工具Python模块strict0，builder新增typed范围提取strict0；整旧builder check-untyped-defs仍有6项真实诊断：RegistrationOnlyDriver缺属性、SDK import未找到、ModuleSpec可空相关3项、bodies缺注解，原日志保留，不宣称全模块类型检查绿。

Java局部SourceQualificationTest10项0，随后Root复用save/RRF两模块最终verify为save10+RRF121=131项，0失败/错误/跳过，76.67秒，四compile入口Nothing-to-compile。未跑Java55或Native构建。原摘要`W/FINAL-RRF-SAVE-VERIFY.actual.json`为7061B / SHA `3b2e92e64bd68b5e5a335b83df1822a1e82410c49e944e0907a71c7c721c5342`。

最终BUILD-RUNTIME-b04原wait0、345.314秒；公共prepare0、plan0、preflight0，外层session24238原wait0已消费。`P/runtime-a01/runtime.local-W-live.json`为16135B / SHA `3ab40c057b8d93d81dc34f02bce2cc107cbc20d78a7e26b73de7a0cee15dfdf0`；只在新local JSON显式映射artifacts_root至W/live，原runtime.local保留。准备闭证为5320B / SHA `a27a2363ff20f6dc564eaac4f9a381f5f5fa26ed722f6bea33b37ac7306fe5b6`。

## 实际运行后继

R0063/a75已实际采用S720并显示32行真实家属名单；Native/Game/host/allocator/keeper正常0，但Root phase在正常Quit reserve到达时超时，public/verify2。取消队列BLOCKED_NEVER_REPLAY、未派发；原GREEN生命周期不授该场GUI通过。`W/R0063-CLOSED.actual.json`为15072B / SHA `9494d7c8bed0ae3cceaa96bd448e7c3b4e8873c14292024048b6b90a3f8d38b4`，原timeout和旧准备/失败回执不改。

R0064/a76复用同一runtime与原a09，使用独立Prepared/state、3600秒hold。Root逐行观察重叠全幅图得到当场32行顺序：首fixture24/ID65862、末fixture30/ID65868；先探索确定列表，再记录同一暂停名单身份与近似有限几何，完成最后到底与回顶。Native whole-list仍truncated，不声称完整模型导出。Root确认三个页签正文、右预览及底部控件可读，有限视口滚动不外撑或裁切。

一次取消隐藏窗口；选定snapshot/religion/doctrines/tenets的语义前后比较均true，观测epoch/revision明确排除。不可变debug快照原rrfa.30 no_product_change_readback恰一PASS、RRFAT零FAIL；无创建、付费、日期推进或新checkpoint。Root response6890B / SHA `32ed89586c9b75fd2d6d539cf22984fe44a4757ab6267f980e81dc53671ba2e0`、accepted6772B / SHA `45333ad3fbc1dcc2d1e87038ef463d78ef2207f49f8864736980cdc9c040e13b`，五项assertions真实被公共consumer接受。

R64 run0/verify0，1710.040105秒public原墙钟；Game retained OS0、Native0、host0、allocator0、keeper0，SCREEN释放15131。Root oracle为200238B / SHA `da03b5dadb187e45b3f126b48afe331dacbf2669c6b9c0e4f7224abf41cba2aa`；`W/R0064-CLOSED.actual.json`为11186B / SHA `bda79025a914cf92a9f519c557be356f50a0384e6d3d5afb2ef18b400254b547`，逐项绑定原件与退出。

公共case/gui/qualified-boundary为true，结果边界SOURCE_CASE_OBSERVED_PENDING_PRODUCT_AGGREGATION，business_pass和product_release_pass仍false。R64只授长名单/首末回顶/可见性/取消读回五项局部cell，不替代原12/20产品矩阵或R65缓存结果。更多画面与历史边界见[布局记录](../mod_religious_ritual_fusion/docs/ui-layout-2026-11-02.md)和[owner采样故障](ck3-scripted-widget-owner-sampling-2026-11-02.md)。
