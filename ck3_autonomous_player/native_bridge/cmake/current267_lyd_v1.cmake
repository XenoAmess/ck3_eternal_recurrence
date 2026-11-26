option(XAR_CK3_ENABLE_121003_26785313_LYD_V1 "Enable finite LYD decisions/events/personal ADD with actual owner source" OFF)
option(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1
 "Enable only the exact ordinary event census through the Full111 mailbox" OFF)
option(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1
 "Enable the same-owner Full111 ordinary event snapshot summary" OFF)
if(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1 AND
    NOT XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1)
 message(FATAL_ERROR "The Full111 ordinary event snapshot requires the exact Full111 ordinary event census")
endif()
if(XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1 AND
    (NOT XAR_CK3_ENABLE_121003_FULL111 OR NOT XAR_CK3_ENABLE_121003_26785313_LYD_V1))
 message(FATAL_ERROR "Full111 ordinary event read requires Full111 and the exact current LYD producer")
endif()
get_filename_component(_xar_courtier_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(_xar_courtier_new src/ck3_121003_lyd26785313_raw_v1.cpp src/ck3_121003_lyd26785313_wire_v1.cpp src/ck3_121003_lyd26785313_owner_v1.cpp src/ck3_121003_lyd26785313_dispatch_v1.cpp)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
 foreach(_xar_unit IN LISTS _xar_courtier_new)
  target_sources(xar_ck3_12002_runtime PRIVATE "${_xar_courtier_root}/${_xar_unit}")
 endforeach()
 if(XAR_CK3_ENABLE_121003_26785313_LYD_V1)
  if(NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2 OR NOT XAR_CK3_ENABLE_121003_26785313_LETTER_V1)
   message(FATAL_ERROR "LYD requires actual current owner/GUI/Letter primitives; no Full or generic script capability")
  endif()
  foreach(_xar_unit IN LISTS _xar_courtier_new ITEMS src/ck3_121003_readonly26785313_v1.cpp src/ck3_121003_core_route26785313_v1.cpp src/ck3_121003_personal_gold26785313_v2.cpp)
   set_property(SOURCE "${_xar_courtier_root}/${_xar_unit}" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_LYD_V1=1>")
  endforeach()
 endif()
endif()
if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_26785313_LYD_V1)
 set_property(SOURCE "${_xar_courtier_root}/src/bridge.cpp" "${_xar_courtier_root}/src/game_adapter.cpp" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_26785313_LYD_V1=1>")
endif()



if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1)
 foreach(_source IN ITEMS ck3_1210_adapter.cpp ck3_121003_lyd26785313_dispatch_v1.cpp
     ck3_121003_lyd26785313_owner_v1.cpp ck3_121003_lyd26785313_raw_v1.cpp)
  set_property(SOURCE "${_xar_courtier_root}/src/${_source}" APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1=1>")
 endforeach()
 set_property(SOURCE "${_xar_courtier_root}/src/bridge.cpp" APPEND PROPERTY COMPILE_DEFINITIONS
   "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1=1>")
endif()

if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1)
 foreach(_source IN ITEMS ck3_1210_adapter.cpp ck3_121003_readonly26785313_v1.cpp
     ck3_121003_lyd26785313_dispatch_v1.cpp ck3_121003_lyd26785313_owner_v1.cpp)
  set_property(SOURCE "${_xar_courtier_root}/src/${_source}" APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1=1>")
 endforeach()
 set_property(SOURCE "${_xar_courtier_root}/src/bridge.cpp" "${_xar_courtier_root}/src/game_adapter.cpp"
   APPEND PROPERTY COMPILE_DEFINITIONS
   "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1=1>")
endif()

if(BUILD_TESTING AND WIN32)
 add_executable(xar_ck3_current_lyd_wire_test EXCLUDE_FROM_ALL "${_xar_courtier_root}/src/ck3_121003_lyd26785313_wire_v1.cpp" "${_xar_courtier_root}/src/ck3_121003_lyd26785313_wire_v1_test.cpp")
 add_executable(xar_ck3_current_lyd_off_test EXCLUDE_FROM_ALL "${_xar_courtier_root}/src/ck3_121003_lyd26785313_raw_v1.cpp" "${_xar_courtier_root}/src/ck3_121003_lyd26785313_owner_v1.cpp" "${_xar_courtier_root}/src/ck3_121003_lyd26785313_off_v1_test.cpp")
 add_executable(xar_ck3_current_lyd_native_call_test EXCLUDE_FROM_ALL "${_xar_courtier_root}/src/ck3_121003_lyd26785313_native_call_v1_test.cpp")
 add_executable(xar_ck3_current_lyd_route_test EXCLUDE_FROM_ALL "${_xar_courtier_root}/src/ck3_121003_lyd26785313_route_v1_test.cpp")
 add_executable(xar_ck3_full111_event_renderer_test EXCLUDE_FROM_ALL "${_xar_courtier_root}/src/ck3_121003_full111_event_renderer_v1_test.cpp")
 foreach(t xar_ck3_current_lyd_wire_test xar_ck3_current_lyd_off_test xar_ck3_current_lyd_native_call_test
     xar_ck3_current_lyd_route_test xar_ck3_full111_event_renderer_test)
  target_include_directories(${t} PRIVATE "${_xar_courtier_root}/include" "${_xar_courtier_root}/src")
  target_compile_features(${t} PRIVATE cxx_std_20)
  target_compile_definitions(${t} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
   target_compile_options(${t} PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME ${t} COMMAND ${t})
 endforeach()
 target_compile_definitions(xar_ck3_current_lyd_off_test PRIVATE XAR_CK3_ENABLE_121003_26785313_LYD_V1=0)
 target_compile_definitions(xar_ck3_current_lyd_route_test PRIVATE XAR_CK3_ENABLE_121003_26785313_LYD_V1=1)
 target_link_libraries(xar_ck3_current_lyd_route_test PRIVATE xar_bridge_protocol)
endif()

if(BUILD_TESTING AND WIN32)
 add_executable(xar_ck3_current_lyd_session_test EXCLUDE_FROM_ALL "${_xar_courtier_root}/src/ck3_121003_lyd26785313_session_v1_test.cpp")
 target_include_directories(xar_ck3_current_lyd_session_test PRIVATE "${_xar_courtier_root}/include" "${_xar_courtier_root}/src")
 target_compile_features(xar_ck3_current_lyd_session_test PRIVATE cxx_std_20)
 target_compile_definitions(xar_ck3_current_lyd_session_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN
   XAR_CK3_ENABLE_121003_26785313_LYD_V1=1 XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1=1)
 if(MSVC)
  target_compile_options(xar_ck3_current_lyd_session_test PRIVATE /W4 /WX /permissive- /EHsc)
 endif()
 add_test(NAME xar_ck3_current_lyd_session_test COMMAND xar_ck3_current_lyd_session_test)
endif()

# Test the actual linked method, with independent positive and negative preprocessor profiles.
if(BUILD_TESTING AND WIN32)
 foreach(state IN ITEMS on off health_only full111)
  set(t xar_ck3_current_lyd_step_${state}_test)
  add_executable(${t} EXCLUDE_FROM_ALL "${_xar_courtier_root}/src/ck3_121003_lyd26785313_dispatch_v1.cpp" "${_xar_courtier_root}/src/ck3_121003_lyd26785313_step_enabled_v1_test.cpp")
  target_include_directories(${t} PRIVATE "${_xar_courtier_root}/include")
  target_compile_features(${t} PRIVATE cxx_std_20)
  target_compile_definitions(${t} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(state STREQUAL "on")
   target_compile_definitions(${t} PRIVATE XAR_CK3_ENABLE_121003_26785313_LYD_V1=1 XAR_LYD_STEP_TEST_EXPECT_ENABLED=1)
  elseif(state STREQUAL "full111")
   target_compile_definitions(${t} PRIVATE XAR_CK3_ENABLE_121003_26785313_LYD_V1=1
     XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_READ_V1=1
     XAR_CK3_ENABLE_121003_FULL111_ORDINARY_EVENT_SNAPSHOT_V1=1 XAR_LYD_STEP_TEST_EXPECT_ENABLED=1)
  elseif(state STREQUAL "off")
   target_compile_definitions(${t} PRIVATE XAR_CK3_ENABLE_121003_26785313_LYD_V1=0 XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1=0)
  else()
   target_compile_definitions(${t} PRIVATE XAR_CK3_ENABLE_121003_26785313_SUPERMAN_HEALTH_V1=1)
  endif()
  if(MSVC)
   target_compile_options(${t} PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME ${t} COMMAND ${t})
 endforeach()
endif()
