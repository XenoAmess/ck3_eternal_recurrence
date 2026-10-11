# Windows FH4 转发研究夹具

此目录保存2026-10-11 source007的精确源码。它只在自身进程中生成和注册测试函数表，不连接CK3；不会被正式bridge构建自动采用。

实际MSVC编译结果及九模式边界见[专题](../../../../../docs/li-yu-dao/2026-10-11-b4-native-eh-source007.md)。普通、嵌套转发及直接调用对照已通过，两个碰撞模式异常退出，两个empty模式被真实metadata拒绝。无语言active模式只取得缺失cleanup的负对照观测。它不是已通过的通用EH组件。

构建复用仓库 `tools/run_native_msvc.py`：将此目录作为 `--source-dir`，提供新的外置 `--build-dir`、实际 `--vs-install`，目标为 `lyd_b4_resolve_eh_fixture_12004`，使用 `--configuration Release --jobs 2 --configure --build`。执行前沿用统一容量准入；项目EXE排除登记、编译和native测试分别记录。当前失败原件不重跑，修正后只验证必要的改变。

九个显式模式为 `direct`、`inplace-normal`、`inplace-nested`、`inplace-collided`、`copy-control-collided`、`empty-direct`、`inplace-empty`、`no-language-empty`、`no-language-active-control`。没有默认模式。可选 `empty-direct --exercise-empty-active-branch` 仅为真实cleanup分支的可达性见证，不计empty通过；本轮未执行。

源码SHA256：`2d6d653860d243f012fcb668fcc7904cd78013f29cec8e23082173070b55b656`。不提交EXE、PDB、build树或系统头文件；编译器工具链提供FH4头文件。剩余问题须依据原始结果继续修复，不能删去empty或collided要求来扩大资格。
