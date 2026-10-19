option(XAR_CK3_ENABLE_CAMERA_TRACKING_V1 "One watched own-army action camera tracking" OFF)
if(XAR_CK3_ENABLE_CAMERA_TRACKING_V1)
  if(NOT XAR_ENABLE_NATIVE_MANDATORY_CHOICE_V1)
    message(FATAL_ERROR "Camera tracking requires the fresh native modal reader")
  endif()
  target_sources(xar_ck3_bridge PRIVATE src/camera_follow_readonly_12004.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_CK3_ENABLE_CAMERA_TRACKING_V1=1)
endif()
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_camera_follow_pending_v1_test tests/camera_follow_readonly_12004_fixture.cpp)
  target_compile_definitions(xar_ck3_camera_follow_pending_v1_test PRIVATE XAR_CAMERA_FOLLOW_READONLY_FIXTURE_EXE=1)
  add_executable(xar_ck3_camera_tracking_v1_test src/camera_tracking_v1_test.cpp)
  add_executable(xar_ck3_camera_settle_diagnostics_v1_test
    src/camera_settle_diagnostics_v1_test.cpp)
  add_executable(xar_ck3_realm_camera_geometry_v1_test src/realm_camera_geometry_v1_test.cpp)
  add_executable(xar_ck3_realm_camera_subrealm_v1_test
    src/realm_camera_subrealm_v1_test.cpp src/ck3_12002_faction_alerts.cpp
    src/county_faction_final_12003.cpp src/player_faction_alerts_v1.cpp
    src/player_faction_alerts_v1_serializer.cpp)
  # Compile the actual independent channel without linking or loading a DLL.
  add_library(xar_ck3_realm_camera_presentation_compile OBJECT src/camera_presentation_v1.cpp)
  add_library(xar_ck3_realm_camera_bridge_compile OBJECT src/bridge.cpp)
  target_include_directories(xar_ck3_realm_camera_bridge_compile PRIVATE
    $<TARGET_PROPERTY:xar_ck3_bridge,INCLUDE_DIRECTORIES>)
  target_compile_definitions(xar_ck3_realm_camera_bridge_compile PRIVATE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  target_compile_options(xar_ck3_realm_camera_bridge_compile PRIVATE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_OPTIONS>)
  target_compile_features(xar_ck3_realm_camera_bridge_compile PRIVATE cxx_std_20)
  foreach(target xar_ck3_camera_tracking_v1_test
                 xar_ck3_camera_follow_pending_v1_test
                 xar_ck3_camera_settle_diagnostics_v1_test
                 xar_ck3_realm_camera_geometry_v1_test
                 xar_ck3_realm_camera_subrealm_v1_test
                 xar_ck3_realm_camera_presentation_compile)
    target_include_directories(${target} PRIVATE include)
    target_compile_features(${target} PRIVATE cxx_std_20)
    target_compile_definitions(${target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(${target} PRIVATE /W4 /WX /Gy /permissive- /EHsc /utf-8)
      if(target MATCHES "_test$")
        target_compile_options(${target} PRIVATE /UNDEBUG)
      endif()
    endif()
  endforeach()
  if(MSVC)
    target_link_options(xar_ck3_realm_camera_subrealm_v1_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_camera_settle_diagnostics_v1
    COMMAND xar_ck3_camera_settle_diagnostics_v1_test)
  add_test(NAME xar_ck3_camera_tracking_v1 COMMAND xar_ck3_camera_tracking_v1_test)
  add_test(NAME xar_ck3_camera_follow_pending_v1 COMMAND xar_ck3_camera_follow_pending_v1_test)
  add_test(NAME xar_ck3_realm_camera_geometry_v1 COMMAND xar_ck3_realm_camera_geometry_v1_test)
  add_test(NAME xar_ck3_realm_camera_subrealm_v1 COMMAND xar_ck3_realm_camera_subrealm_v1_test)
  add_test(NAME xar_ck3_realm_camera_idle_mailbox_v1
    COMMAND xar_ck3_main_thread_query_mailbox_v1_test --idle-presentation-only)
endif()
