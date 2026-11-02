# Scripted widget 查询的发布中采样

`machine_id: 4-8e1c2f1861`；实际故障时间2026-11-01T21:55:07Z，观察与修复日期为本机2026-11-02。用户已明确恢复宗教礼仪融合的CK3开发、测试及发布授权。

R0062 / a74的来源下一步按钮已由原生接口调用一次，返回同一暂停帧。随后`ck3_query_scripted_widget_controls_v1`在Python预检报`title-map native campaign lacks its current verified application owner`。原始wire确认失败调用期间没有向DLL发送query primitive；不能说该查询已执行，也不能重放先前按钮。受管流程保留失败并正常关闭Game：Game OS0、host1、public run2、verify2、keeper0，SCREEN释放15096；长名单业务未验。

原heartbeat1845记录pump17390、verified17389、owner/current_tid同13012、ready=true、installed=true、stop=false、failure0、日期53144352；但snapshot observer处于`read_in_progress=true`，started358933109大于completed358932859，snapshot_cached=false。既有稳定采样器只接受observer已读完的一泵发布间隙，因此直接拒绝了这个实际发布中状态。原heartbeat1846随后自然恢复pump=verified17411、read_in_progress=false、completed=started358933109。后一个heartbeat不是另一份完整live snapshot；回归中的后帧为同一原暂停帧与该heartbeat的明确测试投影。

最小修复维护共享`native_driver.py`中的既有稳定采样入口，仅对已观察的发布中状态重新读取。owner、PID、日期、暂停帧、场次和八次上限继续校验；原owner资格函数不变，等待不会授予资格，也不重派primitive或游戏动作。三个文件提交`f646907b3a311bcd003ca0b1c5356f02fcd94e81`。完整相关GUI合同回归26项、零跳过及有限范围strict检查已通过；新冻结SDK与修复后实机尚待完成，软件结果不抵扣实机。

后续在一次性初始化、持续复用的隔离源码`shared-sdk-source-a01`执行最终完整CI命令组，源码为`720c35b10a9ad9874ad1bf63809f772493cea75a`（原2ef基线只加入上述修复）。strict与26项实际回归均0，3464份源码before/after pins相同；不将前一次开发绿重复累计为52项。`FINAL-CI-step-a01/COMMAND-SOURCE-EXECUTION.actual.json`为1912058B / SHA256 `3b5ae0a568ac8f715929cd3a453f43f061f457d66ddb11d9564bb8dcbb5e2d65`。测试投影、实际独立子进程路径及来源限定均随证据保留；隔离源码未混入主线其它尚未编译的Native改动。

原件位于`C:/workspace/rrf-ui-release-20261102/runtime-repair-r62-a01`。`DIAGNOSIS.actual.json`为5164B / SHA256 `0c30f37c407019906b13fddfc110b80efe07fd5e55e65871e47024ba4e5e11c1`；实际样本为37264B / SHA256 `72453d17ab57e4dc57a9b3e9363b3297cee099e4e09cb50616838066103c0779`。只读采样修复的资格必须来自真实执行该路径的回归；不得扩大为对未知owner、其它帧或动作重试的许可。

## 冻结SDK后继与R0063/R0064实际结果

2026-11-02追加，`machine_id: 4-8e1c2f1861`。上文“新冻结SDK与修复后实机尚待完成”是开发检查结束时的状态；后继已通过既有freeze/六链qualify/build_runtime生成C/S独立绑定的运行图，S保持干净`720c35b10a9ad9874ad1bf63809f772493cea75a`。C的离线producer修复不改S proof覆盖字节，完整5484项Native输入与a09冻结源全等，原编译路径、DLL、对象及证明保留。细节见[共享来源绑定](ck3-shared-sdk-product-source-binding-2026-11-02.md)。

R0063 / a75实际采用该SDK后已进入三个编辑页和32行真实名单，原Native report最终GREEN、Game/Native/host/allocator/keeper退出0；Root phase仍因正常Quit reserve到达而超时，public/verify2。取消队列在原controls in flight时被拒绝，状态`BLOCKED_NEVER_REPLAY`，取消未派发，不能重放或把Native GREEN外推为该场GUI通过。闭场原件`W/R0063-CLOSED.actual.json`为15072B / SHA256 `9494d7c8bed0ae3cceaa96bd448e7c3b4e8873c14292024048b6b90a3f8d38b4`。

R0064 / a76复用相同S720与原a09 Native，采用新Prepared/state和3600秒hold，完成正式生产家属名单32行的首末/回顶、右侧与底部可见性、一次取消和原被动`rrfa.30`。Root前后snapshot/religion/doctrines/tenets语义比较均true；不可变debug快照中该被动marker恰一PASS、RRFAT零FAIL。Root五项assertions已被实际公共consumer接受，run/verify均0，Game retained OS0、Native0、host0、allocator0、keeper0，SCREEN释放15131。

本场Root不可变oracle为`W/R0064-ROOT-REVIEW.actual.json`，200238B / SHA256 `da03b5dadb187e45b3f126b48afe331dacbf2669c6b9c0e4f7224abf41cba2aa`；闭场原件`W/R0064-CLOSED.actual.json`为11186B / SHA256 `bda79025a914cf92a9f519c557be356f50a0384e6d3d5afb2ef18b400254b547`，W为`C:/workspace/rrf-ui-release-20261102`。实际公共case/gui边界通过，`business_pass`和`product_release_pass`仍false；它证明本次实际GUI消费链完成，不将稳定采样等待扩大为未知owner准入、动作重试或完整产品验收资格。

R0062原失败和测试投影、R0063 timeout、原S proof及5484项Frozen Native身份全部保留。R0064真实运行不把回归26项重复累计，也不追认所有潜在采样窗口已被实机覆盖。后续源码合并仍不能热改旧S或复用旧场PID、query_generation、widget_id作为新实例身份。
