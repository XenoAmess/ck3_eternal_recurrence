# 宗主续跑前的 CMake 配置修复

新 clean source `c2bd0c38da34b78187f47a82552007ec707e430a` 的 native 构建在 CMake 配置阶段失败，未编译 DLL，也未执行 focused tests。新增 crown-authority whole fixture 在 BUILD_TESTING/Windows 下无条件进入子目录，并要求 realm-law 私有开关开启；《礼与道》的实际十二项配置将该开关关闭，因此触发 FATAL_ERROR。本次属于构建入口故障，不是新的游戏实机结果。R24 尚未分配或启动。

最小修复只给父级 add_subdirectory 加上对应 `XAR_CK3_ENABLE_G2_REALM_LAW_PAUSED_PRIVATE_QUERY_V1` 条件。realm-law 开启时仍执行原测试目录及校验；关闭时不加入该专属测试。未改变生产业务字节或《礼与道》配置，没有为了消除错误启用无关能力。

一次实际 configure-only 验证以相同十二项私有开关、BUILD_TESTING=ON、realm-law=OFF 运行，原执行退出码0，配置成功。不把 configure-only 当编译、fixture运行或实机通过。原 configure失败、原producer误导性的configured/built启动标记及original wrapper1保留，能力状态依据实际process结果和actual_compilation_pass=false。

原始失败和验证 argv/stdio/producer/log 在 INDEX 逐字节绑定。下一步将修复提交推送后，导出新的 clean HEAD，在新 build 目录完成实际编译和 focused tests，再恢复真实withdraw存档。旧C:/lr24s1、C:/lr24b1、C:/lr24cf1及所有原过程保留。
