# Independent finite current267 TED family; old v17 parser/state/layout stay strict.
option(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1 "Enable fixed TED before/after role and two-day actor epoch" OFF)
target_sources(xar_ck3_12002_runtime PRIVATE
 src/ck3_121003_ted_actor_transition26785313_wire_v1.cpp
 src/ck3_121003_ted_actor_transition26785313_owner_v1.cpp
 src/ck3_121003_ted_actor_transition26785313_raw_v1.cpp
 src/ck3_121003_ted_actor_transition26785313_dispatch_v1.cpp)
if(XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1)
 if(NOT XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1)
  message(FATAL_ERROR "TED fixed epoch requires existing current date runtime")
 endif()
 set_property(SOURCE src/bridge.cpp src/game_adapter.cpp
  src/ck3_121003_core_route26785313_v1.cpp src/ck3_121003_personal_gold26785313_v2.cpp
  src/ck3_121003_readonly26785313_v1.cpp src/ck3_1210_date_sentinel_v1.cpp
  src/ck3_121003_date_advance26785313_v1.cpp
  src/ck3_121003_ted_actor_transition26785313_wire_v1.cpp
  src/ck3_121003_ted_actor_transition26785313_owner_v1.cpp
  src/ck3_121003_ted_actor_transition26785313_raw_v1.cpp
  src/ck3_121003_ted_actor_transition26785313_dispatch_v1.cpp
  APPEND PROPERTY COMPILE_DEFINITIONS XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1=1)
endif()

if(BUILD_TESTING)
 add_executable(xar_ck3_current_ted_wire_test EXCLUDE_FROM_ALL src/ck3_121003_ted_actor_transition26785313_wire_v1.cpp src/ck3_121003_ted_actor_transition26785313_wire_v1_test.cpp)
 target_include_directories(xar_ck3_current_ted_wire_test PRIVATE include)
 target_compile_features(xar_ck3_current_ted_wire_test PRIVATE cxx_std_20)
 target_compile_definitions(xar_ck3_current_ted_wire_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
 target_compile_options(xar_ck3_current_ted_wire_test PRIVATE /W4 /WX /permissive- /EHsc)
 add_test(NAME xar_ck3_current_ted_wire_test COMMAND xar_ck3_current_ted_wire_test)
 foreach(kind IN ITEMS session off route)
  add_executable(xar_ck3_current_ted_${kind}_test EXCLUDE_FROM_ALL src/ck3_121003_ted_actor_transition26785313_${kind}_v1_test.cpp)
  target_include_directories(xar_ck3_current_ted_${kind}_test PRIVATE include src)
  target_compile_features(xar_ck3_current_ted_${kind}_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_current_ted_${kind}_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_compile_options(xar_ck3_current_ted_${kind}_test PRIVATE /W4 /WX /permissive- /EHsc)
  if(NOT kind STREQUAL "off")
   target_compile_definitions(xar_ck3_current_ted_${kind}_test PRIVATE XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1=1)
  endif()
  add_test(NAME xar_ck3_current_ted_${kind}_test COMMAND xar_ck3_current_ted_${kind}_test)
 endforeach()
 target_link_libraries(xar_ck3_current_ted_route_test PRIVATE xar_bridge_protocol)
 add_executable(xar_ck3_current_ted_custody_test EXCLUDE_FROM_ALL src/ck3_121003_date_family_custody26785313_v1_test.cpp)
 target_include_directories(xar_ck3_current_ted_custody_test PRIVATE include src)
 target_compile_features(xar_ck3_current_ted_custody_test PRIVATE cxx_std_20)
 target_compile_definitions(xar_ck3_current_ted_custody_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN XAR_CK3_ENABLE_121003_26785313_TED_TRANSITION_V1=1 XAR_TED_CUSTODY_EXPLICIT_NOGAME_MODEL=1)
 target_compile_options(xar_ck3_current_ted_custody_test PRIVATE /W4 /WX /permissive- /EHsc)
 add_test(NAME xar_ck3_current_ted_custody_test COMMAND xar_ck3_current_ted_custody_test)
 add_executable(xar_ck3_current_ted_role_native_test EXCLUDE_FROM_ALL src/ck3_121003_ted_role26785313_native_call_v1_test.cpp)
 target_include_directories(xar_ck3_current_ted_role_native_test PRIVATE include src)
 target_compile_features(xar_ck3_current_ted_role_native_test PRIVATE cxx_std_20)
 target_compile_definitions(xar_ck3_current_ted_role_native_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
 target_compile_options(xar_ck3_current_ted_role_native_test PRIVATE /W4 /WX /permissive- /EHsc)
 add_test(NAME xar_ck3_current_ted_role_native_test COMMAND xar_ck3_current_ted_role_native_test)
endif()
