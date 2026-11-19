# Independent partial read-only Council source. No advertised capability.
option(XAR_CK3_ENABLE_26757580_COUNCIL_OBSERVATION67 "Enable private BB3 owned Council task observation" OFF)
target_sources(xar_ck3_12002_runtime PRIVATE
  src/council_observation65.cpp src/ck3_26757580_council_frame67.cpp src/ck3_26757580_council_serialize67.cpp)
if(XAR_CK3_ENABLE_26757580_COUNCIL_OBSERVATION67)
  if(NOT XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1)
    message(FATAL_ERROR "Council observation requires exact BB3 basic owner/Core profile")
  endif()
  set_property(SOURCE src/ck3_1210_personal_gold_frame_v1.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_26757580_COUNCIL_OBSERVATION67=1>")
  set_property(SOURCE src/bridge.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_26757580_COUNCIL_OBSERVATION67=1>")
endif()
