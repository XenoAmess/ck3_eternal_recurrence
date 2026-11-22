# Q51 本机 Native 增量资格实际结果

Q51 在 944d1c815b693b6c32e78c565d01f4531bbeb00e 完成原始离线资格，外层原等待退出码 0，耗时 146.0754907 秒，公共消费者 PASS。本次范围为 machine4 的 CK3 1.21.0 / build26622941 / exact2F2B；不授予 current267 ABI、Game 行为或完整金融产品资格。

实际 profile 为 248 flags，DES_INIT_GUARD 为 OFF。归档 FileAPI 的三个选中目标实际 TU 数为 268/628/1，合计 897；仅计有 compileGroupIndex 的行。完整源码快照文件数、header 行及 recipe/元数据行分别记账。

原 production 日志实际出现 13 条 CXX 编译及 4 条链接，-j2；其中生产目标编译 9 条，补充 OFF 目标编译 4 条。这是同一 native-event-build01 缓存的真实增量。原日志保留本地编码和完整 SHA，未改写。

正式 22 fixtures 实际新执行 0 项、按原依赖 reducer 严格复用 22 项。reducer 中 112 是检查的 object 闭包规模，不能称为本次重新编译数。新 DES OFF 与受影响 frontend seed OFF 各实际执行一次并返回 0；其余 12 项历史 OFF 仅在源码、literal include、命令及 EXE 一致的原门通过后复用，新增执行 0。

发布 DLL 为 13536256 字节，SHA-256 4367b7bcb4af4f946ea96384ccd24e552ea901a034ed7eeed7338115b03dd76b。旧 Q50、失败、源窗口与原件保持历史事实；本次事实表没有执行新的构建、测试、资格或现场查询。

原始引用、原构建日志与全部逐目标名单见[实际事实表](../../docs/maintenance/evidence/2026-11-23-financial-markets-native-q51.json)。
