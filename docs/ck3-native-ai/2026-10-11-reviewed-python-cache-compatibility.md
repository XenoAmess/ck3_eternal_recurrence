# 纯 Python 更新后的显式 v2 着色器缓存兼容审阅

共享缓存键包含host和完整源码索引。原合同会因暂停诊断等纯Python变化拒绝旧缓存，即便同一游戏、DLL、素材和图形设置均未变化。本次增加一条显式审阅收据入口；未提供收据时仍严格要求原key全等。

`prepare` 的输入可同时提供 `shader_cache_seed` 与 `shader_cache_python_compatibility` 两个ref3。兼容收据必须绑定旧seed、旧origin、新旧manifest、完整source/native索引与两个完整key。只有v2 seed可用；完整索引差异须全部为 `.py`，实际host须在索引中认证，游戏EXE、DLL/injector、host features、entry environment、profile features、图形/GUI/descriptor/DLC/settings投影须严格相等。执行者须直接审阅实际差异并填写理由；它不自动判断Python改动的用途。

原来源闭场、冻结输入、缓存快照及完整性检查继续执行。旧seed/origin和key不会改写成新来源；准备结果同时保留两个key、完整差异与收据。分配前重新核验并冻结该收据，变化时拒绝。收据不授予引擎缓存命中、启动、业务或实机信用；复制和审阅不延长原缓存期限。

2026-10-10T22:32:42.475232Z记录的候选定向检查实际exit0、6 PASS，覆盖显式审阅与索引绑定、游戏/native/素材差异拒绝、非Python差异、未索引host、默认key拒绝、v1拒绝与原origin错误传播。检查全部为合成内存数据，没有读取真实缓存、EXE或SAVE。永久测试仅替换导入方式；夹具和6方法AST等价，ROOT没有重跑这些场景。新测试已接入官方CI，并紧接退出码守卫。[原回执、等价证明及采用源码pins](acceptance/2026-10-11-reviewed-python-cache-compatibility/INDEX.json)

Source14将完整继承O13的host features；stock grant缺项的公共解析默认OFF，下一I4不会附带其私有启用flag。旧009准入已于22:31:01.087080Z—22:31:01.463253Z实际取消，未来预约0，Source14/O14与物化命令目录均不存在。释放192MiB预约不计物理删除；最终源码选择与新准入另建，不覆盖9e的失败或旧计划。

本包尚未建立真实兼容收据、复制缓存或启动CK3；实际应用需继续走公共plan/prepare/allocate/preflight/run/verify。唯一新增资格为上述合成软件合同，一期仍75% / NOT_GREEN。
