# ordinary_async R45：原 FAIL 分支只读诊断

2026-10-10，SOURCE_ONLY / NOT_RUN。R45 原 case 的启动资格和第一自然日成功，但 day001-no-fail 实际命中两条原 FAIL：accepted=1/refused=1 复合，以及 low 的 catholic/Roman/refusal-opinion 复合。日志没有分量值，不能认定 2accept0refuse、faith 或 ROOT 为原因。原 RED、run/verify/v05 与旧 prepared 保留。

本次仅在两条原 FAIL 之后调用两个只读诊断 helper，记录原计数变量存在性和 0/1/2/other 分量；记录 low 引用、alive、原 faith/Rite/refusal opinion，以及实际 ROOT、真实 fullID 的 scope dump。ROOT 对照/宫廷状态只解释原失败，不替代原断言。诊断不 set 变量/flag/faith/Rite/traits/opinion，不 seed/dispatch/强制任何回复。

剥除两处诊断调用及两个新增 helper 后，完整 fixture 能逐字节还原 R45 的 5719 B / 495147a4e0bc79c5abf708d2e764b694c50a9ba583a081ec54f35aff1cfd11e8。仅更新 contract 的实际 fixture support bytes/SHA；原 original_sources、required/forbidden、compound predicates、30 steps/12自然日、4500/600预算和正式27文件不变。没有新门禁，也没有对任何原 FAIL 改判。下一 unused prepare/实机由 Root 单独安排；本改动没有重跑已验证单元，离线检查不授予业务 PASS。
