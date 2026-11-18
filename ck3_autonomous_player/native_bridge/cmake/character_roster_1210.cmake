option(XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1 "Enable exact Actor readonly maintained-member roster DATA" OFF)
if(XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1)
  if(NOT XAR_CK3_ENABLE_1210_CORE_FRAME_V1 OR NOT XAR_CK3_ENABLE_1210_PERSONAL_GOLD_V1)
    message(FATAL_ERROR "Character roster requires the existing exact Core/Actor owner slot")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_1210_character_manager_v1.cpp
    src/ck3_1210_character_manager_candidate_data_v1.cpp src/ck3_1210_character_roster_frame_v1.cpp
    src/ck3_1210_character_roster_serialize_v1.cpp)
  # Target-specific source opt-in. No PUBLIC/global runtime define.
  set_property(SOURCE src/ck3_1210_adapter.cpp src/ck3_1210_personal_gold_frame_v1.cpp
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1=1>")
  set_property(SOURCE src/bridge.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1=1>")
endif()
if(BUILD_TESTING)
  add_executable(xar_ck3_1210_character_roster_test src/ck3_1210_character_roster_frame_v1_test.cpp
    src/ck3_1210_character_roster_frame_v1.cpp src/ck3_1210_character_roster_serialize_v1.cpp
    src/ck3_1210_character_manager_v1.cpp src/ck3_1210_character_manager_candidate_data_v1.cpp
    src/ck3_1210_core.cpp src/ck3_1210_personal_gold_v1.cpp src/ck3_1210_personal_gold_frame_v1.cpp
    src/ck3_1210_actor_foundation_v1.cpp src/ck3_1210_core_frame_v1.cpp
    src/ck3_1210_thread_runtime.cpp src/game_adapter_capabilities.cpp)
  if(XAR_CK3_ENABLE_1210_ACTIVE_WARS_IDENTITY_V1)
    target_sources(xar_ck3_1210_character_roster_test PRIVATE src/ck3_1210_active_wars_frame_v1.cpp
      src/ck3_1210_active_wars_serialize_v1.cpp src/ck3_1210_active_wars_v1.cpp)
  endif()
  if(XAR_CK3_ENABLE_1210_PERSONAL_CASH_V1)
    target_sources(xar_ck3_1210_character_roster_test PRIVATE src/ck3_1210_personal_cash_frame_v1.cpp
      src/ck3_1210_personal_cash_v1.cpp src/ck3_1210_monthly_flow_v1.cpp)
  endif()
  target_include_directories(xar_ck3_1210_character_roster_test PRIVATE include src)
  target_compile_features(xar_ck3_1210_character_roster_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_1210_character_roster_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN XAR_CK3_ENABLE_1210_CHARACTER_ROSTER_V1=1)
  if(MSVC)
    target_compile_options(xar_ck3_1210_character_roster_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_1210_character_roster COMMAND xar_ck3_1210_character_roster_test)
endif()

if(BUILD_TESTING)
  add_executable(xar_ck3_1210_actor_readonly_request_test tests/ck3_1210_actor_readonly_request_v1_test.cpp)
  target_include_directories(xar_ck3_1210_actor_readonly_request_test PRIVATE include)
  target_compile_features(xar_ck3_1210_actor_readonly_request_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_1210_actor_readonly_request_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_1210_actor_readonly_request COMMAND xar_ck3_1210_actor_readonly_request_test)
endif()
