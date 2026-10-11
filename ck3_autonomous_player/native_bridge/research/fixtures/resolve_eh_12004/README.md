# Windows FH4转发研究夹具

本目录保存2026-10-11 source008的精确源码。它仅生成独立测试EXE，不启动或连接CK3，不由正式bridge自动调用。原007源码与结果保留在Git历史和[原专题](../../../../../docs/li-yu-dao/2026-10-11-b4-native-eh-source007.md)。

[source008实际专题](../../../../../docs/li-yu-dao/2026-10-11-b4-native-eh-source008.md)记录六项正例通过、一项active负对照和两项collision异常退出。empty的实际marker/call状态均-1，其具体continuation通过；碰撞路径、CK3安装器与正式B4保护修复仍未通过。未编译的`TRACE.future.diff`不属于本目录。

使用仓库`tools/run_native_msvc.py`，将本目录作为`--source-dir`，提供新的外置`--build-dir`与实际`--vs-install`。原目标`lyd_b4_resolve_eh_fixture_12004`，参数`--configuration Release --jobs 2 --configure --build`。执行前先取得独立存储准入；编译、项目EXE Defender登记和native结果分别记录。本次build成功、producer退出1由`settings_failed`导致，登记未验；不能拿它代替或否定native结果。

九个正式模式：`direct`、`inplace-normal`、`inplace-nested`、`inplace-collided`、`copy-control-collided`、`empty-direct`、`inplace-empty`、`no-language-empty`、`no-language-active-control`。没有默认模式。可选`empty-direct --exercise-empty-active-branch`与`empty-direct --exercise-empty-frame-throw`仅是可达性witness，本次均未排程，不取得empty PASS。

CPP SHA256：`9b99e5301b8fda84bd2f05543d7b41f751627e0c42759476019703d6acd2c70f`；CMake原681 B字节不变。勿提交EXE/PDB/build或系统头文件。本机MSVC提供FH4头；不得为通过测试修改真实EH表、删除empty/collision条件或填入期望状态。后继改变源码必须重新准入并只验证必要变化，本次九模式不能重标为全通过。
