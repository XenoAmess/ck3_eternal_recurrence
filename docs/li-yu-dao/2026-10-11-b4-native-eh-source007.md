# B4：source007 Windows EH 夹具实跑

2026-10-11 10:30 CST，修正后的独立夹具完成一次编译和九个模式的原始进程等待；没有启动或连接 CK3。正式 B4 安装器资格仍未取得，一期仍为75% / NOT_GREEN。

源码修正将 FH4 状态查询绑定到实际 E8 调用的返回 PC，核实目标为真实 ThrowPrimary；x64 PC 不减1，首个状态条目之前使用 EMPTY(-1)。marker 状态与调用状态分别报告。empty 函数增加真实、默认不执行的 cleanup 分支，以保留编译器生成的 handler；没有伪造 EH 表。

| 模式 | 原退出码 | 实际边界 |
| --- | ---: | --- |
| direct / empty-direct | 0 / 0 | 直接调用对照通过 |
| inplace-normal | 0 | cleanup=1，原 dispatcher 可见更新后 ScopeIndex，原位转发通过 |
| inplace-nested | 0 | cleanup=1，嵌套处理继续，原位转发通过 |
| no-language-active-control | 0 | NEGATIVE_CONTROL_OBSERVED：缺失 active cleanup，只计负对照 |
| inplace-collided | 3762467842 | 0xE042B402，等于夹具 kCollision；异常退出，未通过 |
| copy-control-collided | 3221226505 | 0xC0000409；异常退出，未形成所需负对照资格 |
| inplace-empty / no-language-empty | 3 / 3 | handler已存在(flags2/codes3)，marker_state=0、projected_call_state=-1；metadata guard拒绝，尚未安装 |

两项碰撞模式的原 stdout/stderr 为0字节。现有 ring 只在 Run 返回后输出，无法据这些原件推断最后一次回调、collided flag 或 disposition。后续需先补耐久轨迹，再以改变后的二进制进行必要验证；不重跑原007。一次独立读取本夹具EXE确认empty的实际IP表为1753→0、17b0→-1；16字节marker位于17a0..17af，查询点17a8仍为0，调用返回点17b5为-1。因此是marker的实际状态拒绝；当前空状态区域仅6字节，后继须由真实C++布局产生足够的空状态区域，不能填入期望状态或删除守卫。

实际 EXE 为33792 B / SHA256 `c30e7d8bd8e6b3d3f7896fe76f24f38a9f89cde864101b410c4e5a52034609a8`。MSVC配置、编译、链接成功；原构建命令退出1，原因是独立的 Defender 排除登记失败。同机只读观察显示 WinDefend/WdNisSvc 当前停止且禁用，Winmgmt运行，preference及Add方法元数据可读；不能把当前状态倒推为原调用时点的完整状态，也未启用服务或改写设置。

可复用夹具源码已保存在[研究目录](../../ck3_autonomous_player/native_bridge/research/fixtures/resolve_eh_12004/README.md)。原构建、九模式及服务观察的小原件见[验收索引](acceptance/2026-10-11-b4-native-eh-source007/INDEX.actual.json)。源码与实际结果分别保存，剩余四项不以退出等待成功追认为业务通过。source007的192MiB预算另以实际闭账记录结束未来预留，既有缓存和配额期限不续。

10:45 CST追加：source007实际闭账0、未来预留0，保守carry=135261491305B。前两次闭账在解析混合编码stdout时拒绝，原失败保留；后继按字节定位并严格解码唯一终态JSON后成功，没有重编或重跑夹具。
