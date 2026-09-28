# H2743 退战选项查询零费用接收核验清单

状态：**待真实回执；两个批准表仍为空，五项正式战争现金仍为 `null`。**
此清单只针对 Robert 的 WarID `16777231` 和已执行的
`query-war-termination-options-16777231`。历史 H2743 退战合法性读数不自动成为
R0266 费用读数，更不能写到 H3770、H3774 或其后的检查点。

## 接收顺序

1. 把来源提供的文件按原字节复制到一个新的外置 attempt，记录每件文件名、大小、
   SHA-256、来源与接收时间；不覆盖既有 H2743 attempt 或 WAR 回执。先核原始
   save、driver、sidecar、EXE、DLL、injector 的来源身份；输出检查点必须有
   **其自身**的 receiver official rebind/no-launch 回执，不能沿用输入或邻帧配对。
2. 对一个新受管会话，独立核 PID 加进程创建时间、Steam 当次新鲜离线画面、
   独占屏幕与启动后实际装载的 EXE/DLL/injector 字节 SHA、driver state SHA。
   会话回执的自述字段还须与进程/文件证据逐项交叉；仅复制自述 JSON 不可批准。
3. 保全正式计划**查询前**的六字段帧与建设观测 `source_frame`：玩家、episode、
   snapshot ID、public/native revision、`date_raw` 必须完全一致；地图暂停、仅一场
   活跃战争且 WarID 为 `16777231`。正式计划要明确选中上述 exact step，包含
   typed `priced_command={kind:read_only_query,war_id:16777231,
   query_name:war_termination_options}`。历史查询不能事后补造此计划。
4. 保全原生查询请求、响应及查询前后快照的原始字节。响应必须属于同一 WarID 和
   exact step，前后六字段全同，query sequence 为正；受管计数应证明本次查询
   前后 gameplay submit 数相同，并与桥代码只读分支逐项核对。`accepted`、
   `available` 或余额未变，单独都不能证明整个查询没有现金副作用。
5. 独立审计该实际 DLL 的派发路径：精确源码 commit、driver/bridge/CK3 查询
   源文件 bytes、构建产物 DLL bytes、查询分支与下层调用、无 gameplay submit。
   审计需给出可复核的二进制/源码对应证据；仅有 40 位 commit 字符串、
   读口名称或自报 `status=verified` 不足以批准。
6. 将 EXE、save、driver、DLL、injector、官方 no-launch、受管会话、二进制审计、
   三份源码共 **11 件**传给
   `war_cash_termination_query_zero_fee_v1.observe_termination_query_zero_fee_v1`。
   先用两个批准表为空运行，应收到
   `receiver_runtime_receipt_not_promoted` 且费用 `null`；再人工审阅全部外部
   证据。只有来源、进程和只读派发都独立闭合，才在新审阅提交中批准精确
   运行回执 SHA 与 DLL→审计 SHA，重跑并记录输出。批准仅限这一个会话/查询，
   不把合成单测的 monkeypatch 或历史截图当作批准。

## 失败边界与可报告结果

任一证据缺失、不同帧、不同 DLL、计划未选中该查询、查询已发生提交、外部回执
与实际字节不符，均保留 `immediate_war_action_cost_raw=null` 并报告门禁的
`missing_reasons`。即使这一条已执行查询的 Q100000 即时费最终证明为 `0`，
`pending_war_cash_raw`、未来成本上界、风险预算、战争政策最低保留额仍是 `null`，
`formal_cash_receipt_eligible=false`；M5 建设支出门不会因此放行。

旧 H2743 `attempt-02` 已证明原生退战选项合法性与同帧只读后置快照
（见 [原生复验](h2743-native-exit-readonly-2026-09-28.md)），但它没有上述
R0266 typed 费用计划、独立 loaded-module/二进制审计批准。接收新回执时保留
该区别，不追认旧 attempt 为现金证据。
