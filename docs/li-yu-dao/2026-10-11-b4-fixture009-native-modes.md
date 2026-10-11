# B4 fixture009：九模式终态与未闭合边界

2026-10-11，ROOT 对 source009 的纯 native fixture 九模式各执行一次并实际闭账。本轮 **六PASS、一个expected NEGATIVE、两RED**，不是 CK3/game installer 或业务资格；Phase I 保持 **75%估计 / NOT_GREEN**。

| 模式 | 原终态 | 范围 |
| --- | --- | --- |
| direct、inplace-normal、inplace-nested | PASS / exit0 | 既定正例 |
| empty-direct、inplace-empty、no-language-empty | PASS / exit0 | 既定空路径正例 |
| no-language-active-control | expected NEGATIVE / exit0 | 预期拒绝控制，不计作第七正例 |
| inplace-collided | RED / 0xE042B402 | 未观测到新 target 或 collision filter |
| copy-control-collided | RED / 0xC0000409 | 有效data读之后到达 composite identity guard 拒绝 |

009 新增的外层 target 在两个失败路径均未到达，因此不能把其改动写成已修复碰撞路径。inplace 最后为seq7/kind14，没有持久的第二 handler/filter 到达证据，实际逃逸边界 UNKNOWN；copy 在seq9读取data、seq10/kind12到达既有identity拒绝，但具体失败子谓词仍 UNKNOWN。当前材料也不证明“C++ double-throw terminate”是原因。

source010仅为诊断候选，原 INDEX 标为 `SOURCE_ONLY_NOT_A_FIX_QUALIFICATION`，未编译、未执行模式；其分析保留上述 source009 原失败，不授修复成功。CPP/patch只沿原 INDEX外置引用，本包不复制源码或重新执行。

本轮 native 构建实际成功；构建外层exit1是 Defender `settings_failed`，必须独立记录。原回执 admin=true、Add 内层0x80041001 (`WBEM_E_FAILED`)，没有精确路径设置生效读回。既存只读观察为 WinDefend DISABLED/STOPPED，runtime status provider也WBEM失败，本机固定broker及policy不存在；这些说明当前运行边界与失败一致，精确provider内部因果仍UNKNOWN。不能写永久排除已成功；本轮归档没有重试Add、启动服务、安装broker或修改系统设置，既存观察UTC未记录处继续NULL。

009于09:53:44 UTC实际CLOSED：known2,305,126字节另加1MiB closing bound，保守carry **133,774,939,451**；future/other预约均0，无新cleanup credit，旧source/native/cache/quota review及TTL均未续期。闭账仅结束预约，不是物理回收，也不授native game installer或CK3业务资格。

两个已存在的 exact CI 终态分别为 `c5d81519e06a9c221885b642608c95b2b994690f`（Official38128106446、Linear38128106418）及 `6ccba583bf3ade10d6a63861a39228764c2ab108`（Official38128484791、Linear38128484777），均BOTH SUCCESS/attempt1。本包只复用原元数据，未查询或重跑CI，不将其外推为009实机，也不替后来dafe57f01预填CI结果。

精确小原件和原路径映射见 [INDEX.actual.json](acceptance/2026-10-11-b4-fixture009-native-modes/INDEX.actual.json)。仅入库九模式RESULT/小stdio、原mode INDEX、build/Defender小回执、source分析、CLOSED/close及两CI小终态；measure、EXE、CPP/patch和大构建日志保现成外置ref，不读或复制body。raw以`-text`保字节。此候选新增实际bytes由下一CASE11独立准入预收费一次，不回写已CLOSED的009账本。
