# R520/R521：scoreboard 缺失身份诊断 RED

## 结论

旧轮次 R520/PID `115936` 完成 authenticated Frontend warm-up 并终止；当前轮次
R521/PID `187720` 随后作为唯一 CK3 加载 autosave。R521 通过 loader、native
readiness、paused seed、HUD 与 feature manifest 门禁，随后首个 scoreboard source
query 仍返回 `widget_not_instantiated`。runner 在首段 clean span 前停止，没有继续八段
长跑；R520/R521 均已终止，CK3/FFmpeg 为零。

R521 使用单次最多 65,536 节点的 fixed-window 遍历，因此它否定了“8,192 上限仍太小”
这一修复方向。当前 native 结果在任一 widget 缺失时只保留总 reason，并把 15 个 widget
的 typed fields 全部重新初始化为 `snapshot_unavailable`；driver-state 因而不能回答哪一个
固定身份缺失，也不能区分完整遍历后的 miss 与中途内存读取失败。

下一工作包只保留首次 `DecodeWidgets` 已得到的逐 widget typed diagnostics，再设置同一个
top-level `widget_not_instantiated`。这不放宽可用性门禁、不执行输入、不提高 traversal bound；
它只让既有 15 项响应指出 `exists=true/false`。该 unavailable-response 语义变化要同步
open_kaishek 兼容说明，且在新的 DLL 与轮次前先以定向 native/Python 合同测试验证。

## 证据

- attempt：`Z:\\ck3_mod_rewrite\\_runtime\\p2-capture-r520-r527-5659b57-20260912`
- frozen plan：11,285 bytes，`4B473EDAE55DAE6C792F9BB038C7BF40A3C21BC75ED3401A69BFC102DEAAE0E3`
- outer report：4,369,664 bytes，`03231ED0894B638A71D32BD21DCAB7E0B1E9F75B694306BF1A49CCD1DF5B3859`
- inner report：4,314,844 bytes，`31C09283F06A74319133C0D06D1B8DEC79A5A9FAB72417A061DB959646FBAC53`
- driver state：38,193 bytes，`1DD8A0EFDB1902BF6F0C7907D596848D931DFF9EFA1BB1932B260DCE375D6693`
- cleanup：30,916 bytes，`8F4EBFEB6D90106C5CEA7D9640E0DF2C5B30828F25AC326808E1EDE8B466F8AE`
- failed take：3,592,022 bytes，`80C7F71F027833E72F37AD148D068CBFAD6DB190E4E65B790D7A2ABB2884C4C6`
- timeline：7,932 bytes，`091DFFDD457BB96E8A40B2777860A1FB4E3714E6784261D8CB297DF34CA40D51`
- provider session：`F8ADC44AD1C6BA7A1A66EFC4C3F05D7A`
- paused binding：revision `3`、date `53147016`、player `29037`

失败 take 没有 clean span，P2 素材仍为 `0/8`。P1 保持 `9/9 GREEN`，视频硬锁保持
解除；剪辑、导出与发布仍等待八段 clean footage 和内容审阅。

## 诊断补丁

native unavailable 分支现在只把首次解码出的 15 项 widget 数组移动到响应中，再把
top-level readiness 归零并保持 `widget_not_instantiated`。缺失项因此可由
`exists={status:available,value:false}` 直接定位；其余成功读取项不会被抹去。补丁不改变
schema shape、allowlist、动作、遍历或可用性判定。native fixture 模拟第 13 项缺失并断言
序列化仍有效；Python 合同测试断言同一 unavailable payload 可被严格 normalizer 接受。
