option(XAR_CK3_ENABLE_26757580_SAVE_MAPPED61 "Reviewed BB3 SAVE command mapping and owner admission" OFF)
target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_26757580_save_mapped61.cpp)
set_property(SOURCE src/ck3_1210_adapter.cpp src/ck3_1210_core_control_v1.cpp src/ck3_26757580_save_mapped61.cpp
  APPEND PROPERTY COMPILE_DEFINITIONS
  "$<$<AND:$<BOOL:${XAR_CK3_ENABLE_26757580_SAVE_MAPPED61}>,$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>>:XAR_CK3_ENABLE_26757580_SAVE_MAPPED61=1>")
