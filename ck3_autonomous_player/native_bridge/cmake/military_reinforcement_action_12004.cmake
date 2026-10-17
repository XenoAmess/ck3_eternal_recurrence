# Fixed actual .4 stock checkbox action; no provider execution API.
option(XAR_ENABLE_FIXED_MILITARY_REINFORCEMENT_ACTION_12004
  "Admit fixed stock reinforcement checkbox dispatch with independent source-owner postread" OFF)
if(XAR_ENABLE_FIXED_MILITARY_REINFORCEMENT_ACTION_12004)
  if(NOT XAR_CK3_ENABLE_INGAME_MILITARY_OPEN_PRIVATE_V1 OR
     NOT XAR_ENABLE_GUI_REFILL_STATIC_OWNER_SWITCH_12004)
    message(FATAL_ERROR "Fixed reinforcement action requires existing military owner route and static source-owner switch reader")
  endif()
  target_compile_definitions(xar_ck3_12002_runtime PUBLIC
    XAR_ENABLE_FIXED_MILITARY_REINFORCEMENT_ACTION_12004=1)
endif()
target_sources(xar_ck3_12002_runtime PRIVATE src/military_reinforcement_action_12004.cpp)
add_executable(xar_test_military_reinforcement_action_12004
  tests/test_military_reinforcement_action_12004.cpp)
target_link_libraries(xar_test_military_reinforcement_action_12004 PRIVATE xar_ck3_12002_runtime)
target_compile_features(xar_test_military_reinforcement_action_12004 PRIVATE cxx_std_20)
if(MSVC)
  target_compile_options(xar_test_military_reinforcement_action_12004 PRIVATE /EHsc /W4 /WX)
endif()
