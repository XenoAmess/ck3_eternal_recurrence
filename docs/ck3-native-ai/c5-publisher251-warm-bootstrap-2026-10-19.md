# C5 same-Game publisher251 暖转接

machine_id: `xenoamess-full-tower-eb9d2c1186`。2026-10-19 UTC，来源为实际C4 FULL202闭合包、M0冻结的251 before-submit proof与POST-C4-CLOSE；本说明的软件资格不代表未来C5实机通过。

C4普通循环实际推进74→98完整周期、61→107游戏日。AUTO251的首callback计划为`query-war-results-window-v1`；child替换文本时Win5退出，未写文字ACK，父callback等待5秒超时。SRC04 Service先调用before_submit再走该查询分支，因此选定query未dispatch；规划阶段先前可能已有只读观测，不能宣称整个AUTO绝无Native读取，也不能计query完成或完整AUTO99。实际错误、计划、ACK缺失及不可变源码见M0 `p51-c4-child-text-retry-review01/META.json`15547B/SHA`dfe9834d06efecba05681f18746108b8de8891c535db2702a3f7c7736774de33`。

旧SDK已实际关闭：Queue42800/birth134368610358548563退出1，App150132/birth134368610381151161退出0，二者kernel signaled、owner1、normal=false；Game153556/birth134368602545256920保留。`POST-C4-CLOSE.json`5824B/SHA`fd2a83b0fffbdf8c98551306a91463a9ab76ea08db202448f89cb87c94a4a4f7`绑定closed Driver1308498B/SHA`1413f3c7f8c799a01be9e55d3b2aea805092cf8d7bc6f0981366d2007961579e`。factory仅读小receipt，不重新读取大Driver。该receipt的`checkpoint_dirty:null`是摘要未投影字段；实际冻结state明确`checkpoint_dirty_since_save:true`，factory以精确state为准，保lastSaved61/cb385/history122，不能称已SAVE107。

[薄factory](../../tools/g2_saved_campaign/publisher251_warm_queue_v1.py)使用严格C5 admission和以上两份固定proof，精确接受本次1/0退出原因，不放宽一般关闭守卫。新Q首请求必须SEM252/CAP253；首SEM经公共readiness真实顺序处理，显式注入C5 relay，observer读取已存在的READINESS attempt，canonical252在consume后发布。评分继续使用同一physicalGame的`root_score_month_samples_c4`，T0和旧月份保持原件。首SEM核同Game/pipe/lifecycle、原actor/episode/date107、Native≥60、paused living map、goal及无未处理选择。CAP必须实际`same_pid_hot/active_resumed/driver_state_restored:true`且无错误，不能接受cold load。

两次新只读结果通过后，仅按来源证明清未提交pending99，并用实际新App opening更新普通`before`及source；保98完整计数、T0、lastSaved61和dirtytrue。分类器source filename/SHA继续核当前C5 pin；current-map与原recording/storage/guard、完整`generated/full_loop`均继承原代码，FULL254才开始新AUTO。没有旧结果重消费、没有MET110 once、没有SAVE107、没有query或AUTO99业务信用。旧错误与去重账保留。

[软件资格工具](../../tools/g2_saved_campaign/qualify_publisher251_warm_v1.py)使用实际C5候选Queue0752acc、原call/consume/persist/Ready MRO、公共readiness及明确标为软件构造的未来107 SEM/hotCAP，验证`check_after(next252/attempt存在/canonical未存在)→consume→canonical发布→C5relay→ordinary CAP`完整顺序；source offset0，计数/lastSave/dirty/T0保留。错误actor、Game、日期、Native回退和coldCAP均拒绝。没有新现场RPC、没有未来C5 preflight/录像/实机通过声明。[冻结资格](evidence/c5-publisher251-warm-software01.json)记录输入pins、顺序与边界。

旧失败只读allowlist另有两个陈旧digest。经Root批准，[适配工具](../../tools/g2_saved_campaign/prepare_c4_readonly_registry_pin_v1.py)只修改`handlers[3].sha256`和`handlers[6].sha256`，绑定已审当前函数字节；函数及旧src02/MODE/generation守卫不变，不迁移C4资格。实际251从SHA异常变为None，仍不能由通用registry自动恢复；没有新增251 rule。[两字段资格](evidence/c4-readonly-registry-two-pins01.json)单独保存。

保留期限在本次维护闭场后7日复核，按统一存储策略保护活跃输入、回收过期派生副本；本包不复制大Driver/SAVE或删除原错误。
