option(XAR_CK3_ENABLE_26757580_OPENING_READONLY56 "BB3 exact current government scope and present LIFE readonly profile" OFF)
if(XAR_CK3_ENABLE_26757580_OPENING_READONLY56)
  if(NOT XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1)
    message(FATAL_ERROR "Opening56 requires the BB3 basic Full owner profile")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_1210_opening_readonly56.cpp src/ck3_1210_opening_frame56.cpp src/ck3_1210_opening_serialize56.cpp)
  set_property(SOURCE src/ck3_1210_adapter.cpp src/ck3_1210_personal_gold_frame_v1.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_26757580_OPENING_READONLY56=1>")
  set_property(SOURCE src/bridge.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_26757580_OPENING_READONLY56=1>")
endif()
