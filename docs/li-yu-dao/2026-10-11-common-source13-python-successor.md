# Source13 Python 薄继任：实际绑定与闭账完成

Source13 以 Source12 `05717072b70d4925f10b3d523b6663d2db89d791` 为单父，只投影选定的 Python、合同与测试文件，实际生成 `22cef1d93a81598935c6685ccef76d0a0c8d7bd7`，目录为 `C:/csr13` 与 `C:/workspace/ck3-common-runtime/20261011-013`。实际元数据另列 selected author `70e7c64d814c2ea9a58550f87ac735aa6cade26e`、queue author `92b43503461c037a68207d60b21ea3a6eb472a7f`。这不是最新 master 整树，也不是新 native build。[冻结与来源原件](acceptance/2026-10-11-common-source13-python-successor/PYTHON-SUCCESSOR.original.json)

首次 producer002 于2026-10-10 20:43:31.728174Z—20:43:34.802484Z返回1：独立 Git index/objects 的8MiB分项上界不足。实际仅形成3个 Git partial 文件、8,776,738 B，尚未复制源码；[失败 RESULT](acceptance/2026-10-11-common-source13-python-successor/materialize001-RESULT.original.json)与[原 stderr](acceptance/2026-10-11-common-source13-python-successor/materialize001-stderr.log)保持原样。

ROOT在同一007、同一192MiB总上界与原期限下追加[实际 amendment](acceptance/2026-10-11-common-source13-python-successor/RESUME-AMENDMENT.original.json)，将 Git 子项改为16MiB并计入已有 partial。producer003 于20:48:32.751460Z—20:48:41.493525Z实际返回0，只复用已完成 Git 阶段，没有重新执行该阶段或重复扣算 partial。[恢复 RESULT](acceptance/2026-10-11-common-source13-python-successor/materialize002-RESULT.original.json)

实际 source index共8,741文件、147,728,174 B：8,730文件继承 Source12 已验 hashes，11个选定 delta；未重做全树 hash。host、MCP和 native 编译输入保持 Source12 原字节关系，Cbr3 原 native 资格不能写成新 `22cef...` 编译所得。构建与资格边界回链[Source12专题](2026-10-11-common-source12-native-runtime.md)。大型源码索引、Git对象、DLL/EXE仍只以原路径及 pins 引用，沿原 TTL管理，不因复制或绑定续期。

binder002 于20:52:58.704351Z—20:52:59.120222Z实际返回0，形成 O13 manifest（25,159 B，SHA `69312f885d1a234ee059934f283e6a774b291cdbbd85b0d9d8a5da1359f9574f`）、runtime（2,015 B，SHA `26dfbb02b7627345a04645aa488a719d03618d9b68b58e97368a554ace0c82b9`）与[实际 binding](acceptance/2026-10-11-common-source13-python-successor/SOURCE13-BIND.original.json)。[绑定 command RESULT](acceptance/2026-10-11-common-source13-python-successor/bind-RESULT.original.json)保留精确参数与输出 pins。

007于20:53:24.726103Z实际闭账：已知留存159,672,946 B，未来预留归零，物理删除0；allocated bytes与历史峰值仍为NULL。原007准入、原失败及 amendment均未改写；原 quota、native/cache复核期限不续。[CLOSED](acceptance/2026-10-11-common-source13-python-successor/CLOSED-RESERVATION.original.json)、[MEASURE](acceptance/2026-10-11-common-source13-python-successor/MEASURE.original.json)与[关闭 command RESULT](acceptance/2026-10-11-common-source13-python-successor/closure007-RESULT.original.json)分别记录终态、测量范围和实际0。

后续独立008已实际准入2GiB，CASE5使用新目录 `C:/workspace/ck3-common-runtime/cases/lyd-i4-natural-expiry-20261011-005`。公共 prepare于20:53:50.440045Z返回0，plan于20:54:04.019775Z返回0，no-context preflight于20:54:05.135142Z返回0；原大型 stdout仅保留 RESULT中的精确外置 pins。[prepare](acceptance/2026-10-11-common-source13-python-successor/case5-prepare-RESULT.original.json)、[plan](acceptance/2026-10-11-common-source13-python-successor/case5-plan-RESULT.original.json)、[preflight](acceptance/2026-10-11-common-source13-python-successor/case5-preflight-RESULT.original.json)

本记录截止上述准备结果，新分配与启动均未执行。Source13没有新增构建、测试、SDK/native payload、live、B4、B5或完整I4验收信用；whole-product仍未通过，75%仍为工作量估计。文件清单及外置引用见[INDEX](acceptance/2026-10-11-common-source13-python-successor/INDEX.json)。
