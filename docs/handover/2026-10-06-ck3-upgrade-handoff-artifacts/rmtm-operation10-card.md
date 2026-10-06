# 重整河山 operation10：真实宋入组后单次夹具派发

SOURCE_ONLY 候选；NOT_ALLOCATED / NOT_RUN / NOT_PUBLISHED。R3 已证明原夹具执行前宋帝没有 dynastic_cycle 成员关系，尚未证明初始化时序是唯一原因。原版 `_on_actions.info:95` 明确 after_lobby effect 与子事件并发；`tgp_dynastic_cycle.txt:142–150` 的真实 hegemon_ruler.on_join 是本候选新增的条件派发节点。生产36没有 situation 定义，仍使用原 scripted-effect overrides；外置完整 stock situation 只插入该回调，移除插入块逐字节恢复 stock。core14→15、threshold18→19；原 aggregate/FAIL/36markers/业务事件/UI/规则/14日/400秒均未改。

after_lobby 只 arm；当前宋持 h_china、实际 character_situation 和实际 hegemon top group 全部存在时，disarm 在前，原 Robert→rqa120.1 仅派发一次。若大厅钩子先到，真实 on_join 会重新检测；若入组先到，大厅钩子检测现态。既不建组、补区域、重启 situation，也不等待任意游戏日。没有回调或真实关系仍缺失时，保持原400秒失败，不重 Start。该修改不证明回调一定发生，也不授予业务 PASS。

Root/唯一 foreoperator 从仓库 cwd 使用新未用 aNN：

```text
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -X utf8 C:/workspace/ck3-upgrade-20261006/rmtm-stock-join-dispatch-operation10-agent-01/allocate_rmtm_root_10.py core <新未用aNN> --lease-repo C:/workspace/ck3-live-screen-slot-20261005
```

分配后使用真实输出 live/task/sequence，沿 operation09 卡原 keeper→fresh offline+nonce→一次 Start→400秒内真实 intro 唯一 mapped 确认。本包明确绑定已有 `/root/rmtm_foreground09` metadata-only helper，须确实由该 agent 审阅；若实际操作者改变，仅外置修 reviewer 元数据并重新精确绑定，不能谎称 Root 审图。启动命令使用以下 helper，其余操作步骤、C1–C6、day-once、readonly plans、正常退出/lifecycle/CAS全部沿用下列09卡；09启动入口已由本卡替代。

```text
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -B -X utf8 C:/workspace/ck3-upgrade-20261006/rmtm-foreground09-agent-01/launch_rmtm_operator_no_bytecode_01.py --run-root <实际live> --keeper-root <实际keeper目录> --proof <新recovery目录/recovery.json> --challenge <新challenge目录/report.json> --observed-nonce <该操作者亲审nonce>
```

[原完整操作卡](C:/workspace/ck3-upgrade-20261006/rmtm-participant-probes-ministry-guard-operation09-agent-01/ROOT-OPERATION09.md)

新增只读诊断前缀：`RQA_INIT_DIAG_V1 stock_hegemon_on_join_song`、`waiting_song_real_membership`、`waiting_song_top_group`、`waiting_song_hegemon_type`、`real_song_membership_dispatch_once`。它们均不是 PASS marker。资格仍要求原两固定正项各1/FAIL0，加两当前同 frame 且 owner pump 递增，再首 full-root DTO/binder；Source09/HOST81/controller均原精确冻结。

正常关闭当前场并实际 OS/native0、cleanup、所有观察者/keeper实际退出和一次CAS空 resources之前，不得启动 threshold。threshold仍需 Root 单独授权。原50灰/51可用、九部院真实预算、两个臣服理由、Continue、实际继承/14日门禁完整保留。候选0.4.1未发布。
