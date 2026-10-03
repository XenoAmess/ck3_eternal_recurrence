# R0005 简体中文实机验收（2026-10-03）

结论：**本机固定 CK3 1.20.0.3／Steam build 25652598 的简体中文实机验收 GREEN**。新 Workshop 发布尚未执行。执行者为 `Codex /root/holding_conversion`。

源提交 `3f023e5ff00f87f8df3a8adde1a72400c36851ec`，正式运行文件17个，独立 run `bf-202609141645-5434332d4d--change-holding-types--R0005`，execution UUID `20fb3714-9bc0-42cb-89f9-a88eacaf974e`，PID19216。EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。完整 profile、运行副本、输入存档、请求、日志、截图、wire 与执行脚本均永久保留在 `C:/workspace/two-mod-maintenance-20261003/bf-202609141645-5434332d4d--change-holding-types--R0005`，本报告只索引实际字节，不复制大证据树。[机器报告](report.json)／[逐文件证据索引](evidence-index.json)。

## 实际结果

| 检查 | 结果及证据 |
| --- | --- |
| 启动准入 | 新鲜 CK3 inventory为空；当次 Steam 位移取证原图由执行者亲阅“离线模式”；简体中文 profile和保存源哈希已绑定。 |
| 保存状态 | 只读 inbox新增两项PASS：Rossano为玩家直辖城市，未选中首都仍为城堡。输入存档 SHA `47a1178c8373eb79ab8ca7071e5c14b0e30218c43a493d2f5e49c2230915a35a`，68,962,340 bytes。 |
| fixture02组合矩阵 | 新增原生日志依次证明两项保存状态、六种转换、同类拒绝／保持不变、AI效果阻止、非男爵领拒绝，共12项唯一PASS；START／END及AI actor标记完整，零FAIL。 |
| 暂停／日期／金币 | ready003、矩阵前005、界面后007均为玩家runtime31254、日期raw53144328（界面1066-09-15）、paused=true、金币846；未推进日期，未重复触发延迟on_game_start矩阵。 |
| 中文决议列表 | 原图 `cn-holding-list-02.png` 六名称完整可读，无产品key泄漏。 |
| 中文城市详情 | 原图 `cn-city-full-warning-01.png` 显示特拉尼／Trani、400费用、选择与执行按钮，以及完整无tooltip遮挡的“不兼容的建筑可能丢失。地产仍受政府兼容性及继承规则约束。” |
| 产品错误 | 只读前后、矩阵前后、界面后五次捕获error.log均0bytes；空文件SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。 |
| 清理 | harness exit0；受管CK3终止码1原样记录；Job tree_gone=true／cleanup_proven=true／final0，fresh native及psutil CK3均[]；CAS2475 done／resources[]。 |

## 结论边界

R0005没有再次点击执行决议或扣款；400为本次界面显示。R0002实际GUI选择Rossano并扣除400金币（1246→846）的独立证据仍保留。fixture调用生产effect，不能冒称决议执行或成本验证。Transport回执 `marker_confirmed=false` 也原样保留，PASS来自新增debug.log中的实际state断言。

最初001／002在冷载中返回“game state unavailable”；随后003为ready，并非产品脚本错误。离线审阅模板的generic root标签以外置追加记录更正实际审阅人为本子代理。中文产品字段正常，原版自动生成的一行条件仍显示 `Is not AI`，不将整张原版界面全部中文化写成事实。

只验简体中文，其他八语仅格式检查；历史英文过程不替代本次中文签核。本结论只适用上述1.20.0.3 EXE，不外推整个1.20系列。R0001／R0002／R0003／R0004历史失败、勘误及原始证据不覆盖。Workshop上传、完整Change Notes公开回读、fresh订阅缓存和永久changelog尚待父任务完成。
