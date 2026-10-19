# 入站联盟counterfactual score：独立collector源码

本包在[已冻结来源计划](research-plans/g2-m2-inbound-alliance-12004-20261019/plan.json)之后新增独立内部collector和no-main聚焦测试，未改旧closure、topic或plan包。机器`machine_id: xenoamess-full-tower-eb9d2c1186`，实际UTC、源SHA与状态见[源码回执](evidence/g2-m2-pending-alliance-counterfactual-collector-source-2026-10-19.json)。

当前状态为 **AUTHORED_NOTRUN**，没有编译、执行测试、部署或实机资格。

新增文件为`pending_alliance_counterfactual_score_12004.hpp/.cpp`与`pending_alliance_counterfactual_score_12004_focus.cpp`。collector只接受当前正常直接入站的`negotiate_alliance_interaction`、玩家作为human recipient和同一owner线程的暂停帧。复用现成`.4`绑定，核getter确为`module+307C440`，通过调用方已有guarded invoker最多调用一次。读取pending`+18`的borrowed context，核definition、actor和recipient，之后再次核完整帧与字段；不refresh、finalize或销毁pending context。

只有invoker成功、RAX返回原out指针且前后帧一致才发布signed Q64。负数、零和超过int32的值均保留；未知结果为null，不能把初始化的0当成读取成功。输出明确为`counterfactual_player_as_ai`，human的actual AI final为不适用；没有根据分数选择接受／拒绝或推断联盟价值。

no-main focus共12个场景，包括public/native revision不同、正／负／零／wide Q64、signed pending generation、错误build或入口、非human、内存／invoker失败、外来返回指针及getter后帧变化。测试回调只模拟Native I/O，未执行。源文件没有进入bridge.cpp、CMake、共享DTO、wire或策略；后续由owner接已有pending query的真实callbacks，并在验证后同步serializer与Python合同。

Root允许“研究预算有余时”唯一child不超过8MiB的一次`/c /W4 /WX`单object编译，不允许link／EXE或全构建。storage owner实际核到共享研究128MiB的剩余仍为null，未有精确child绑定，故条件未满足：本包没有启动vcvars／compiler或创建child。不能把global配额剩余或closed逻辑量计成可用physical信用；待Root明确分配后再做一次有界编译。

两项军力getter仍按冻结范围查既有metadata。`WORLD-PROFILE-SOURCE-CLOSED.json`与军事`FINITE-MANIFEST.json`未出现exact`.4`的`current_military_strength`／`max_military_strength` canonical registration或callback锚点，未读取EXE、猜地址或套版本差。下一请求仍只需已有cache owner给这两项明确`.4`锚点及各不超过256B的完整leaf；没有锚点不采字节。它们不阻碍先交付已闭ABI的score collector源码。

本次Game／RPC／Native调用、构建、link、EXE和动作均为0；未授业务或G2信用。只读源码／记录按统一策略复核，物理分配未知不产生空间信用。
