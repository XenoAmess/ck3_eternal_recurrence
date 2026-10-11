# B4：source008 Windows EH夹具的实际边界

2026-10-11 11:31:42—11:32:24 CST，独立source008夹具完成一次MSVC配置、编译、链接和九个原始模式等待。六个模式返回`FIXTURE_CASE_PASS`，一个返回`NEGATIVE_CONTROL_OBSERVED`，两个collision模式异常退出；九个等待均未超时。没有启动或调用CK3，正式B4安装器与保护bug修复资格仍未取得，一期仍为75% / NOT_GREEN。

源码26945 B，SHA256 `9b99e5301b8fda84bd2f05543d7b41f751627e0c42759476019703d6acd2c70f`，已绑定到本次实际构建。source008使真实empty函数布局覆盖marker与实际调用的空状态，并持久记录已有EH事件；没有删除FH4、handler、frame、ScopeIndex或返回PC守卫。原source007的源码与失败记录继续由Git历史保留；本篇不重写其当时结论。

| 原始模式 | 退出码 | 本次实际结果 |
| --- | ---: | --- |
| direct / empty-direct | 0 / 0 | 直接调用对照通过 |
| inplace-normal / inplace-nested | 0 / 0 | cleanup各1，原位转发通过，实际dispatcher可见更新后的ScopeIndex |
| inplace-empty / no-language-empty | 0 / 0 | marker与调用状态均-1；cleanup各1；分别有1次/0次handler调用，移除成功 |
| no-language-active-control | 0 | 缺失active cleanup的负对照，只计`NEGATIVE_CONTROL_OBSERVED` |
| inplace-collided | 3762467842 (`0xE042B402`) | 未通过；最后耐久记录为cleanup_entry，实际/转发dispatcher相同，ScopeIndex为1/1 |
| copy-control-collided | 3221226505 (`0xC0000409`) | 未通过；cleanup时dispatcher不同，ScopeIndex为0/1；随后新handler到达并在验证中拒绝 |

两项empty成功证明本次具体布局和continuation可运行，不证明可普遍省略语言handler。inplace碰撞在最后cleanup记录之后的Windows分派路径未知；copy碰撞的kind9由两条拒绝分支共用，实际拒绝谓词仍未知。没有据此认定getter lazy refresh、B4缓存writer或真实CK3安装接点已经闭合。小诊断中的`TRACE.future.diff`仅是未编译后继，本次不采用、不导入canonical源码，也不授其任何结果。

原build命令在03:31:47.883921Z退出1；终态native-msvc明确`built=true/build_succeeded=true`，状态`built_defender_registration_failed`，Defender实际`settings_failed`，登记未验。编译成功和设置失败分别记录；本次不重查服务、不重试登记、不把设置失败解释为collision原因。EXE为34816 B / SHA256 `4a942a9e925c98812b5f30dbdff93b3e25a6447548d35ff84af42de46564c37c`，身份取自原mode INDEX，本次归档未读取或重哈希PE。

11:36:26.178083 CST，独立192MiB预算实际闭账0：carry **136064394857 B**，future reservation与other reservation均0；preparation19874 B未重复计费，未增加清理credit，原quota与TTL不续。闭账结束写入预留，不是native/B4通过。

可复用源码见[夹具目录](../../ck3_autonomous_player/native_bridge/research/fixtures/resolve_eh_12004/README.md)。[小原件索引](acceptance/2026-10-11-b4-native-eh-source008/INDEX.actual.json)收录原九模式stdout/stderr/RESULT与INDEX、实际build/native-msvc、诊断REPORT/FACTS/INDEX及实际准入/闭账和原command；不包含EXE、PDB、build树、cache或SAVE。导入映射保存精确来源和目标，旧失败未改写。
