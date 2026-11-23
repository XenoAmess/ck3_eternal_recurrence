# CCC finite3subfamily current859 only. All newpublic capabilities defaultOFF.
option(XAR_CK3_ENABLE_121003_26785313_CCC_V1 "Enable fixed CCC actor/decision/event current267 family" OFF)
get_filename_component(_ccc_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(_ccc_units
 "src/ck3_121003_ccc_actor_transition26785313_raw_v1.cpp"
 "src/ck3_121003_ccc_actor_transition26785313_wire_v1.cpp"
 "src/ck3_121003_ccc_actor_transition26785313_owner_v1.cpp"
 "src/ck3_121003_ccc_actor_transition26785313_dispatch_v1.cpp"
 "src/ck3_121003_ccc_event26785313_raw_v1.cpp"
 "src/ck3_121003_ccc_event26785313_wire_v1.cpp"
 "src/ck3_121003_ccc_event26785313_owner_v1.cpp"
 "src/ck3_121003_ccc_event26785313_dispatch_v1.cpp"
 "src/ck3_121003_ccc_decision26785313_raw_v1.cpp"
 "src/ck3_121003_ccc_decision26785313_wire_v1.cpp"
 "src/ck3_121003_ccc_decision26785313_owner_v1.cpp"
 "src/ck3_121003_ccc_decision26785313_dispatch_v1.cpp"
 "src/ck3_121003_ccc_owner26785313_v1.cpp"
)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
 foreach(u IN LISTS _ccc_units)
  target_sources(xar_ck3_12002_runtime PRIVATE "${_ccc_root}/${u}")
 endforeach()
 if(XAR_CK3_ENABLE_121003_26785313_CCC_V1)
  if(NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_LYD_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_LETTER_V1)
   message(FATAL_ERROR "CCC requires qualified current Core/date/ordinary-event primitives, no LYD roles or TED public permission")
  endif()
  foreach(u IN LISTS _ccc_units ITEMS src/ck3_121003_readonly26785313_v1.cpp src/ck3_121003_core_route26785313_v1.cpp src/ck3_121003_personal_gold26785313_v2.cpp src/ck3_121003_date_advance26785313_v1.cpp src/ck3_1210_date_sentinel_v1.cpp)
   foreach(flag IN ITEMS CCC_V1 CCC_TRANSITION_V1 CCC_EVENT_V1 CCC_DECISION_V1)
    set_property(SOURCE "${_ccc_root}/${u}" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_${flag}=1>")
   endforeach()
  endforeach()
 endif()
endif()
if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_26785313_CCC_V1)
 foreach(flag IN ITEMS CCC_V1 CCC_TRANSITION_V1 CCC_EVENT_V1 CCC_DECISION_V1)
  set_property(SOURCE "${_ccc_root}/src/bridge.cpp" "${_ccc_root}/src/game_adapter.cpp" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_26785313_${flag}=1>")
 endforeach()
endif()

# Financial selected266 qualification needs only the actual linked CCC OFF
# StepEnabled negatives. This supplemental target never enables CCC or calls
# any owner/ABI/body transport; trap-only unused dependencies are in its source.
if(BUILD_TESTING AND WIN32)
 add_executable(xar_ck3_ccc_step_off_test EXCLUDE_FROM_ALL
  "${_ccc_root}/src/ck3_121003_ccc_step_enabled_v1_test.cpp"
  "${_ccc_root}/src/ck3_121003_ccc_actor_transition26785313_dispatch_v1.cpp"
  "${_ccc_root}/src/ck3_121003_ccc_event26785313_dispatch_v1.cpp"
  "${_ccc_root}/src/ck3_121003_ccc_decision26785313_dispatch_v1.cpp")
 target_include_directories(xar_ck3_ccc_step_off_test PRIVATE "${_ccc_root}/include")
 target_compile_features(xar_ck3_ccc_step_off_test PRIVATE cxx_std_20)
 target_compile_definitions(xar_ck3_ccc_step_off_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
 if(MSVC)
  target_compile_options(xar_ck3_ccc_step_off_test PRIVATE /W4 /WX /permissive- /EHsc)
 endif()
 add_test(NAME xar_ck3_ccc_step_off_test COMMAND xar_ck3_ccc_step_off_test)
endif()
