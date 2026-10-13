# G2 fresh12：录制信号回归与独立崩溃

接续[fresh11根查询超时及修复](g2-fresh11-root-timeout-2026-10-13.md)。`R = D:/codex-ck3-background-spill/g2-remediation-20261013`，本场源码固定 `80bb6ac592a9180ab1b960067d5f13bf835863c0`、未变B12；实际编号 `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0006`。1276个SDK文件硬链接，1个变化文件独立复制1,497,828 B。

## 实际运行边界

Game268028／creation `20261013105232.914747+000`实际冷载，Desktop1放置与独立OBS armed成功。Root从mutable latest复制为不可变 `ROOT-ARMED-REVIEW-003-{game,scene}.png`，亲审实际主菜单和决策窗后才写新start signal。期间未切用户Desktop2、未抢前台；Steam沿用明确用户离线保证，不声称新离线像素。

signal于10:55:42.791Z被观察，唯一StartRecord后10:55:43.072Z写started。随后录制器错误 `unexpected OBS output filename` 并关闭独立OBS，输入解除、engine实际exit0。真实原片759,308 B／1.233秒，SHA-256 `de0794aeeb9c89044bd496a10dabc20a2263ca6a18600952d45a854a827283a9`。配置额度不是实际产物大小，started不是录制完成。

**SDK_NOT_STARTED，零frontend／角色选择／游戏动作，普通回合和日期推进仍0。** Root的SDK增长探测先遇到视频尚未创建，再遇到空文件／无增长；这些检查发生于SDK创建之前，未重放StartRecord或启动第二个SDK。

## 精确录制根因与修复

worker启动时冻结recording_root已有文件集合；Root后来按新合同在同根创建精确的 `fresh12-start-1a9ac5ad9c544f6dbfdf32de51b66623.signal`，旧post-StartRecord目录检查把它当成意外输出。生产检查枚举目录，不读取 `GetRecordStatus.output_path`；“路径暂空”只是Root当时未查明的假设，已纠正，没有新增等待输出路径的协议。

窄修复只把job声明的start_signal完整解析路径加入允许集合，其他新.signal仍拒绝；错误同时保留实际意外文件完整路径。外置HOT01候选6项生产路径检查通过，其中旧源码精确复现当前故障；候选不改冻结repo。实际Game已退出后，才集成主树，并补生产run_worker中“声明signal成功／其他signal失败”的两项回归。

候选、原失败、源哈希及首次验证在 `R/resume08/m_recording/hot01/`；首次原28项检查未覆盖这个post-start目录阶段，不能把它们当作本次回归已被旧测试覆盖。修复后仍需新实机，未追认fresh12录像成功。

## Game退出与Crash

Game于10:58:53.814889Z闭场，supervisor先观察到自行exit1，随后清理原Job／watchdog并证tree_gone；没有正常关闭信用。keeper失败为空且线程退出，最后4002，Root实际CAS释放为4003。录像关闭与稍后的Game崩溃分别记账，不能把时间相邻当作同一故障因果。

原件 `state/profile/crashes/ck3_20261013_185843` 中，异常为线程9424在 `ck3.exe + 0x3EF8F4B` 的C0000005读取0x18。11:09清点minidump154,712,331 B，保留而不复制。研究仅读25,586 B模块／异常元数据，未导出stack或全量dump。同秒error.log记录DX11设备暂停、fence和纹理创建失败；debug.log及settings实际选中RTX3080，meta.yml的AMD条目不能代表实际适配器。

B12确已加载，故障指令不在Native模块；仍没有足够证据证明或排除注入关联，也不能宣布系统性Native阻点。小型出处与精确pins见 `R/resume08/m_root_query/fresh12-crash/REPORT.md`。本场 `ROOT-ACTUAL-CLOSED-EVIDENCE.json` 保留原真实退出、录像与零RPC结果。

## 后续

fresh13必须新attempt、pipe、profile和clean冻结，复用未变B12，重新取得actual main-menu／录制增长再开局，不重跑fresh12的旧helper。角色Start后的root等待修复仍待实机；B12完整owner-tree、首个普通回合、SAVE和完整演示均未完成。

原全组8GiB与16:58:39.018273Z复核期限不变。fresh12 crash、失败录像和SDK冻结受当前故障最小用途保护；新场重型写入前核当前去重占用和真实精确GC结果，不能用已登记但未消费的旧1.88GB峰值追认新场准入。
