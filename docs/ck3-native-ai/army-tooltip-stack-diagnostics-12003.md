# CK3 1.20.0.3 Army 提示栈诊断

2026-10-05：R0163 实机的补给、损耗悬停均返回 action receipt，随后独立正文查询被 `tooltip_active_stack_unreadable_or_out_of_bounds` 拒绝。Root 直接审阅截图只见 Lewes 地图提示，没有 Army 补给或损耗正文。两个入口仍待验收；ACK、离线测试和正常原片均不闭合术语研究。

原版提示栈会动态增长容量，关闭后缩减有效条目数但保留分配容量。旧读取器同时限制 capacity 和 count 不超过 32，误拒绝了合法容量。本次只移除 capacity 的 32 上界，保留非负 header、count 不超过 32、count 不超过 capacity、非空 data 和每个实际条目的完整校验。实际读取预算仍由 count 决定。

失败响应增加实际读取成功的 capacity/count，以及 hover 为 null、bound、different 或 unreadable 的分类；条目失败附 index。悬停与栈顶的关联失败附实际 top source 分类和 lock 值，不暴露指针。读不到的值不假装为零。失败时正文、nonce、receipt binding 清空和 unavailable 语义继续保持。

R0163 未发布具体 header，因此本修正只证明消除了一处源码缺陷，尚不能解释该实机失败的唯一根因。原生鼠标处理能替换一次性悬停，但本轮没有证据证明发生过该替换；leave 被拒绝也不能证明地图覆盖。GUI update epoch 仍未知，cache 观测不外推为已刷新或已渲染。

冻结补丁 `C:/ck3-war-episode04-research-20261004-a01/army-tooltip-live-stack-diagnostic-a01/native-tooltip-stack-fix03.patch` SHA-256 `f4b060bf126cedfea6e4c570134c46fb900014e9f7f9a0d3a3c8118c07b98ff7`。实际生产生命周期和 serializer 合成夹具验证 capacity 64/count 0、1 可读，count 33 拒绝，以及既有两类提示回归。真实 native unavailable wire 经过现有 Python normalizer 保持原样。`ROOT-DELIVERY03.json` SHA-256 `6c28c612cdf13c6b7d3715e4c2b7c1e5a05479a61f3f361286ba1851acfc6edf` 记录完整来源与验证边界。`open_kaishek` 无法覆盖原生 ABI 和缓存读取，此项预验为 not-applicable。

下一步以新正式 DLL 冷载复拍，保存实际详细失败分支或缓存正文，并独立检查新桌面像素。五项额外 Army 提示入口未混入本补丁。
