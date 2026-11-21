option(XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1 "Enable readonly current selected DJC named-currency costs" OFF)
get_filename_component(_xar_cost_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
 target_sources(xar_ck3_12002_runtime PRIVATE
  "${_xar_cost_root}/src/ck3_121003_djc_selected_cost26785313_raw_v1.cpp"
  "${_xar_cost_root}/src/ck3_121003_djc_selected_cost26785313_wire_v1.cpp")
 if(XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1)
  if(NOT XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_DJC_DECLARATIONS_V1)
   message(FATAL_ERROR "Selected DJC costs require current fixed resident UI/query/owner bindings")
  endif()
  foreach(_xar_cost_unit IN ITEMS src/ck3_121003_djc_selected_cost26785313_raw_v1.cpp
   src/ck3_121003_djc_declaration_ui26785313_owner_v1.cpp src/ck3_121003_djc_declaration_ui26785313_dispatch_v1.cpp
   src/ck3_121003_personal_gold26785313_v2.cpp)
   set_property(SOURCE "${_xar_cost_root}/${_xar_cost_unit}" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1=1>")
  endforeach()
 endif()
endif()
if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1)
 set_property(SOURCE "${_xar_cost_root}/src/bridge.cpp" "${_xar_cost_root}/src/game_adapter.cpp" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1=1>")
endif()
if(BUILD_TESTING AND WIN32)
 add_executable(xar_ck3_current_djc_selected_cost_wire_test EXCLUDE_FROM_ALL
  "${_xar_cost_root}/src/ck3_121003_djc_selected_cost26785313_wire_v1.cpp"
  "${_xar_cost_root}/src/ck3_121003_djc_selected_cost26785313_wire_v1_test.cpp")
 add_executable(xar_ck3_current_djc_selected_cost_off_test EXCLUDE_FROM_ALL
  "${_xar_cost_root}/src/ck3_121003_djc_selected_cost26785313_off_test.cpp"
  "${_xar_cost_root}/src/ck3_121003_djc_selected_cost26785313_raw_v1.cpp"
  "${_xar_cost_root}/src/ck3_121003_djc_selected_cost26785313_wire_v1.cpp"
  "${_xar_cost_root}/src/ck3_121003_djc_declaration_ui26785313_owner_v1.cpp")
 foreach(_xar_cost_test IN ITEMS xar_ck3_current_djc_selected_cost_wire_test xar_ck3_current_djc_selected_cost_off_test)
  target_include_directories(${_xar_cost_test} PRIVATE "${_xar_cost_root}/include" "${_xar_cost_root}/src")
  target_compile_features(${_xar_cost_test} PRIVATE cxx_std_20)
  target_compile_definitions(${_xar_cost_test} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN XAR_CK3_ENABLE_121003_26785313_DJC_UI_V1=0 XAR_CK3_ENABLE_121003_26785313_DJC_COST_V1=0)
  if(MSVC)
   target_compile_options(${_xar_cost_test} PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME ${_xar_cost_test} COMMAND ${_xar_cost_test})
 endforeach()
endif()
