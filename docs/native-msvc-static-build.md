# 原生 MSVC 后台构建入口

`tools/run_native_msvc.py` 从安装的 Visual Studio x64 工具链初始化一次子进程环境，然后用 Ninja 配置或增量构建选定 CMake targets。所有临时文件、编译日志及 Python/编译器 cache 位于 `--build-dir` 下；该入口只做本地静态构建。

现有 `ck3_autonomous_player/native_bridge/tools/build_fresh.py` 继续用于其已有的全新目录构建合同。此入口补齐普通命令行里的 vcvars 初始化和可重复增量构建，复用它的中文 MSVC `/showIncludes` 字节修复，不复制另一套依赖前缀逻辑。

## 使用

以下命令从选定源码工作树执行；构建目录放在当前机器的非 C 盘。默认 `--jobs 64`，默认目标为 bridge DLL 和 injector。

```cmd
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\run_native_msvc.py --build-dir Z:\ck3_mod_rewrite\artifacts\offline-nonwar-2026-10-01\build-native-msvc --configure --build --jobs 64 --target xar_ck3_bridge xar_ck3_bridge_injector
```

指定 CMake 定义可重复使用 `--cmake-define NAME=VALUE`，例如为离线 source-contract 测试绑定冻结 EXE；具体定义沿本次 adapter 的版本合同填写。含空格的参数通过 Python structured argv 原样转给 CMake。

```cmd
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\run_native_msvc.py --build-dir Z:\ck3_mod_rewrite\artifacts\offline-nonwar-2026-10-01\build-native-msvc --build --target xar_ck3_bridge --jobs 64
```

`--configure` 单独只配置，`--build` 单独只构建；两个选项均省略时执行配置和构建。`--source-dir` 可指定其他 native CMake 项目，`--configuration` 支持 Debug/Release/RelWithDebInfo/MinSizeRel，`--vs-install` 可覆盖自动找到的 VS 安装。

```cmd
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\run_native_msvc.py --build-dir Z:\ck3_mod_rewrite\artifacts\offline-nonwar-2026-10-01\native-msvc-probe --probe
```

每次执行留下 `native-msvc-result.json`，构建过程写入 `msvc-configure.log`、`msvc-build.log`；probe 留下三个工具版本日志。报告仅列出工具路径及所用输出位置，不转储 vcvars 捕获的完整环境。

## 2026-10-01 验证

- 实际工具 probe 通过：VS 18 Community，cl `19.51.36257`、CMake `4.3.1-msvc1`、Ninja `1.13.2`；制品为 `artifacts/offline-nonwar-2026-10-01/native-msvc-probe/native-msvc-result.json`。
- `py -B tools/test_run_native_msvc.py` 的两个测试通过：父进程 TEMP/TMP 保持不变；真实 C++ fixture 在含空格的 source/build 路径配置、编译、链接，CMake 字符串值保留空格；只改头文件再运行 `--build`，程序输出由 `7` 变为 `8`，证明增量依赖实际生效。
- fixture/编译器输出全部位于 `Z:\ck3_mod_rewrite\artifacts\offline-nonwar-2026-10-01\native-msvc-wrapper-tests`，结果为 `assessment.json`。首次测试缺少 C++17 以上标准导致编译 RED；修正 fixture 的 `cxx_std_20` 后通过，失败日志保留为 `initial-fixture-cxx-standard-red.log`。
- 本次验证只构建独立小型测试程序，未启动游戏、准备 profile 或并发构建项目 bridge DLL。集成 DLL 由协调者指定的唯一构建工作包执行。
