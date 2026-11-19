option(XAR_CK3_ENABLE_26757580_SAVE_MAPPED61 "Reviewed BB3 SAVE command mapping and owner admission" OFF)
target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_26757580_save_mapped61.cpp)
# These standalone tests compile CoreControl directly instead of linking
# the runtime archive, so its SAVE admission provider is also a direct source.
# This adds symbol closure only; the runtime-only feature definition below
# remains default OFF for these test targets.
foreach(_save_mapped61_test_target IN ITEMS
    xar_ck3_1210_core_control_test xar_ck3_1210_hotfix26757580_basic_test)
  if(TARGET ${_save_mapped61_test_target})
    target_sources(${_save_mapped61_test_target} PRIVATE src/ck3_26757580_save_mapped61.cpp)
  endif()
endforeach()
set_property(SOURCE src/ck3_1210_adapter.cpp src/ck3_1210_core_control_v1.cpp src/ck3_26757580_save_mapped61.cpp
  APPEND PROPERTY COMPILE_DEFINITIONS
  "$<$<AND:$<BOOL:${XAR_CK3_ENABLE_26757580_SAVE_MAPPED61}>,$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>>:XAR_CK3_ENABLE_26757580_SAVE_MAPPED61=1>")
