option(XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1 "Reviewed bb3 build26757580 Core/empty Full/clock/exit profile" OFF)
if(XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1)
  if(NOT XAR_CK3_ENABLE_1210_CORE_FRAME_V1 OR NOT XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1 OR
     NOT XAR_CK3_ENABLE_1210_CORE_CONTROL_V1 OR NOT XAR_CK3_ENABLE_1210_FULL_CLOCK_V1 OR
     NOT XAR_CK3_ENABLE_1210_DATE_SENTINEL_V1 OR NOT XAR_CK3_ENABLE_1210_APPLICATION_EXIT_V1)
    message(FATAL_ERROR "bb3 basic profile requires the existing Core/Full/clock/date/exit implementations")
  endif()
  set_property(SOURCE src/ck3_1210_adapter.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1=1>")
endif()
if(BUILD_TESTING)
  # The real Full formatter references this optional legacy serializer. Keep
  # its exact two function bodies without linking unrelated old native readers.
  file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/player_event_trait_membership_12004.cpp" _hf36_traits)
  string(REPLACE "\r\n" "\n" _hf36_traits "${_hf36_traits}")
  string(FIND "${_hf36_traits}" "std::string SerializePlayerEventTraitMembershipV1(" _hf36_traits_at)
  if(_hf36_traits_at LESS 0)
    message(FATAL_ERROR "Actual trait serializer source not found")
  endif()
  string(SUBSTRING "${_hf36_traits}" ${_hf36_traits_at} -1 _hf36_traits_body)
  file(CONFIGURE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/hotfix36_traits_serializer.cpp" CONTENT
    "#include \"xar_bridge/player_event_trait_membership_12004.hpp\"\nnamespace xar::ck3_12004::person_events {\n${_hf36_traits_body}" @ONLY NEWLINE_STYLE LF)
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/player_event_trait_membership_12004.cpp")
  add_executable(xar_ck3_1210_hotfix26757580_basic_test
    src/ck3_1210_hotfix26757580_basic_test.cpp
    src/ck3_1210_core.cpp src/ck3_1210_full_snapshot_v1.cpp
    src/ck3_1210_ingame_ready_v1.cpp
    src/ck3_1210_actor_foundation_v1.cpp src/ck3_1210_current_event_snapshot_v1.cpp
    src/ck3_1210_pending_snapshot_v1.cpp src/ck3_1210_military_empty_v1.cpp
    src/ck3_1210_core_frame_v1.cpp src/ck3_1210_thread_runtime.cpp
    src/ck3_1210_commands.cpp src/ck3_1210_core_control_v1.cpp
    src/ck3_1210_core_control_request_v1.cpp src/ck3_1210_full_clock_request_v1.cpp
    src/ck3_1210_application_exit_v1.cpp src/ck3_1210_daily_final_hook_v1.cpp
    src/ck3_1210_date_sentinel_v1.cpp src/tactical_daily_sentinel_v1.cpp
    src/game_adapter_capabilities.cpp "${CMAKE_CURRENT_BINARY_DIR}/hotfix36_traits_serializer.cpp")
  target_include_directories(xar_ck3_1210_hotfix26757580_basic_test PRIVATE include
    "${CMAKE_CURRENT_BINARY_DIR}/fresh_full_state12004_generated")
  target_compile_definitions(xar_ck3_1210_hotfix26757580_basic_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_1210_hotfix26757580_basic_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
endif()
