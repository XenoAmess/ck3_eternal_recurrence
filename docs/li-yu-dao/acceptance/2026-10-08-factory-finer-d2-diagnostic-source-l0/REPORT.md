# Factory finer-D2：一次源码验证证据（L0）

这是已完成的外置源码检查归档，不是新的测试执行，也不提供实机或业务资格。原候选 [INDEX](INDEX.json)、[44项检查](STATIC-CHECK.actual.json)、[原验证请求](SOURCE-VALIDATION-REQUEST.actual.json) 与 [原执行结果](SOURCE-VALIDATION-RESULT.actual.json) 原字节复制；[stdout](source-validation.stdout.txt)、[stderr](source-validation.stderr.txt) 原样保留。检查 actual exit0、44/44 TRUE；stderr 为空。没有 native 构建、SDK/游戏、存档正文或进程调用。

唯一诊断操作顺序变化是把 create_title_and_vassal_change 的创建移到配置四属性之后，采用当前1.20.0.4原版 antipope 顺序；中间新增 `.20`/scope20=D2a，原`.2`/scope2=D2b。D2a先create＋两owner markers＋原四属性，无未决transaction；D2b将create-change＋holder＋resolve作为原子组，resolve前没有暂停。

一次检查证明完整success操作经恢复这一明确container移动后与原factory/commit AST相同；原授权、receipt、拒绝路径、postconditions及结果路径保留。另直接确认D1原guard、D3～D6原事件与effects及原三个身份/title/result trigger AST相同。六runtime文件按legacy `.txt/.yml/.mod` BOM策略覆盖。[最终补丁](FINAL-PATCH.diff)和[控制器source bindings](STAGE-CONTROLLER.source-only.json)冻结实际源码方案；[late-binding pending](ROOT-LATE-BINDING.inputs.pending.json)继续保所有未来实机值NULL。

源头是R30已观察D1cache45到D2cache40且五政治heir变化，并非推测SetHoF/Title95。D1/D2保存四realm laws完全相同、same_faith_succession_law两边不存在。新scope的未持有Title跨事件/SAVE生命周期仍UNKNOWN；如果实际丢失就保留RED，不猜T、不重create、不补授权或修改缓存。原生产71、87/88保护合同没有改变，整体NOT_GREEN。

本目录source/中保全了验证所用 [生成器](source/build_factory_diagnostic.py) 和 [validator](source/validate_factory_diagnostic.py) 的精确字节；对应维护源码由ROOT导入mod_li_yu_dao/tools。纯生成的source-validation-overlay只是历史FA0源码夹具，不授未来cleanHEAD、DLL、metadata或新run资格，也不作为正式production部署素材。本次映射只供ROOT create-only导入，未写MAIN/Git。

后续原CLI和风险边界见 [finer-D2说明](../../factory-finer-d2-diagnostic.md)。ROOT必须在真实正常闭场后，通过新actualHEAD/export/native/meta和合法signed-B3诊断seed绑定执行；历史B3通过不授新cold信用。
