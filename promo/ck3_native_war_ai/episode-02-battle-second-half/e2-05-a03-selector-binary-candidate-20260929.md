# E2-05 a03 私有 selector DLL：静态构建与精确字节门

2026-09-29，在独立工作树 `D:/w/e205_selector_test` 从 native 源码提交 `29be03f5879f0e3fb402f1c2d0e998ce0e6ad5e9` 构建候选。外置 append-only 构建根为 `D:/ck3-research-artifacts/e2-05-a03-selector-build-20260929-a02/`，包含 `CMakeCache.txt`、`build.ninja`、`.ninja_log`、CTest JUnit、DLL、injector 和 create-exclusive no-launch 回执。构建采用 MSVC 19.51.36256.0、Release/Ninja、`BUILD_TESTING=ON`、`XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1=ON`。没有启动 CK3、注入或录屏；a02 旧 DLL 与失败 attempt 保持原样。

| 冻结项 | 字节 / SHA-256 |
| --- | --- |
| CK3 1.19.0.6 EXE | 95,206,008 B / `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；PE x64，RVA `0x33E8D40` 的文件原字节为 `4C89442418488954241048894C2408`。 |
| `xar_ck3_bridge.dll` | 3,229,184 B / `1FB7F34161AEEE1A581865A87E24098733A5DD1A575A0416B1AA5DCD0997D196`。 |
| `xar_ck3_bridge_injector.exe` | 39,936 B / `2C5846A9C72A0FA6B09837F07BFF8BDC3A3058E0E7AF5229933AD03EB39CCFC6`。 |
| `CMakeCache.txt` | 26,842 B / `20F3DC00E648096E5C27025D293A3F59E2FBEB59DD13209A7C30C9664DEDE04B`；`CMAKE_HOME_DIRECTORY` 指向上述独立源码树。 |
| native 源码 fingerprint | `260EF759FDF60453CC7EDDED2BC4FC81C694D0E794CD4E59D4E1BBE8A4F72029`，按 `native_bridge/tools/build_fresh.py` 的 CMakeLists/include/src 算法在构建后重算；尚无构建前后双 fingerprint 自动回执。 |
| 聚焦 CTest JUnit | `selector-focused-ctest-a01.xml`，1,666 B / `B6DD95F41309FFFCAD789F3502C3046337595A0D2EFC0D59BB53E51A6818E4C5`。六项 source/ring/detour/wire/managed **6/6 passed**；未运行完整 offline CTest。 |
| 新 no-launch 回执 | `selector-no-launch-a03.json` / `5A540C0C5DBE80731DB3A34D78FDD8E9B1C05F331C5A77CE84479A13F5D70BA1`。更早 a01/a02 回执保留为历史；a03 与 a02 的内容哈希恰好相同，但分别由收紧前后的 gate 生成，不能据此追认旧检查。 |

新的 [精确字节 gate](e2_05_a03_selector_binary_gate.py)重哈希 d26 immutable save 与自己的 `d26-save.json`、候选 DLL/injector、EXE、CMakeCache 以及**同一构建目录**的聚焦 JUnit；另核对 PE、RVA/prologue、构建开关、CMake 来源与源码 fingerprint。`knight_selects` 字面存在只是辅助检查，不足以证明 hook 可用。[gate 测试](test_e2_05_a03_selector_binary_gate.py)在普通 Python 和 `-O` 各 4/4 通过；负例覆盖错误 PE/RVA、关闭 managed flag、JUnit 错 SHA 和错构建目录。no-launch 回执 `source_ready=true`、`selector_abi_static_bytes_checked=true` 仅代表静态字节门，且显式 `selector_abi_reviewed=false`、`live_admission=false`、`postframe_character_status=UNKNOWN`。

起点仍是精确 d26 存档 `C1276153435766A875B0984F1A3AD426CB3AFCFB6EC33061CEE6650538CFFD2B` 与自身保存回执 `78931511D31E8400334D28DAD276F4CCDFBB342A901FC00B0BAFDCDEDA29584C`；当前**没有**新的 a03 d27 暂停存档或 CharacterID 33437 死亡事实。下一门是独立 ABI 审查、按新二进制 SHA 冻结的 a03 helper，再由新 run 产生 hook 安装、同源 begin→唯一一次推进→finish 与 d27 paused checkpoint。DLL 的 selector 行只给 candidate count/index、RNG counter/salt 前后态和 opaque token；CharacterID 33437 要在 d27 保存后用[严格离线读器](e2-05-a03-offline-character-reader-20260929.md)单独判定。没有原始 RNG draw、全部候选 CharacterID、opaque token→人物身份映射；不能借旧 run 宣称 a03 抽签为 14/8 或某人已死亡。
