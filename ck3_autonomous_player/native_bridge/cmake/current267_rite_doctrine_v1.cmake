# Existing current Rite/Core family; independently opt in to fixed native actions.
option(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1
  "Enable bounded current Rite Dynastic category/select/confirm owner route" OFF)
get_filename_component(_xar_rite267_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(_xar_rite267_new
  src/ck3_121003_rite_doctrine26785313_v1.cpp
  src/ck3_121003_rite_doctrine26785313_wire_v1.cpp
  src/ck3_121003_rite_doctrine26785313_dispatch_v1.cpp
  src/ck3_121003_doctrine_category26785313_v1.cpp
  src/ck3_121003_doctrine_select26785313_v1.cpp
  src/ck3_121003_doctrine_knowledge26785313_v1.cpp)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
  foreach(_xar_unit IN LISTS _xar_rite267_new)
    target_sources(xar_ck3_12002_runtime PRIVATE "${_xar_rite267_root}/${_xar_unit}")
  endforeach()
  if(XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1)
    if(NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1 OR
       NOT XAR_CK3_ENABLE_121003_26785313_GUI_CONTROLS_V2 OR
       NOT XAR_CK3_ENABLE_121003_26785313_RITE_DRAFT_V2)
      message(FATAL_ERROR "Current Rite actions require existing exact Core, named-window and native Rite/Controls routes")
    endif()
    set(_xar_rite267_existing src/ck3_121003_readonly26785313_v1.cpp
      src/ck3_121003_core_route26785313_v1.cpp src/ck3_121003_personal_gold26785313_v2.cpp
      src/ck3_1210_adapter.cpp)
    foreach(_xar_unit IN LISTS _xar_rite267_existing _xar_rite267_new)
      set_property(SOURCE "${_xar_rite267_root}/${_xar_unit}" APPEND PROPERTY COMPILE_DEFINITIONS
        "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1=1>")
    endforeach()
  endif()
  foreach(_xar_pair IN ITEMS
      "ck3_121003_doctrine_category26785313_v1.cpp:DOCTRINE_CATEGORY_OPEN_V1"
      "ck3_121003_doctrine_select26785313_v1.cpp:DOCTRINE_SELECT_BINDINGS_V1"
      "ck3_121003_doctrine_knowledge26785313_v1.cpp:KNOWN_DOCTRINE_GATE_V1")
    string(REPLACE ":" ";" _xar_parts "${_xar_pair}")
    list(GET _xar_parts 0 _xar_file)
    list(GET _xar_parts 1 _xar_flag)
    set_property(SOURCE "${_xar_rite267_root}/src/${_xar_file}" APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_${_xar_flag}=$<BOOL:${XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1}>>")
  endforeach()
endif()
if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1)
  set_property(SOURCE "${_xar_rite267_root}/src/bridge.cpp" "${_xar_rite267_root}/src/game_adapter.cpp"
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_26785313_RITE_DOCTRINE_V1=1>")
endif()
if(BUILD_TESTING AND WIN32)
  set(_xar_test xar_ck3_121003_26785313_rite_doctrine_wire_test)
  add_executable(${_xar_test} EXCLUDE_FROM_ALL
    "${_xar_rite267_root}/src/ck3_121003_rite_doctrine26785313_wire_v1_test.cpp"
    "${_xar_rite267_root}/src/ck3_1210_thread_runtime.cpp"
    "${_xar_rite267_root}/src/game_adapter_capabilities.cpp")
  target_include_directories(${_xar_test} PRIVATE "${_xar_rite267_root}/include" "${_xar_rite267_root}/src")
  target_compile_features(${_xar_test} PRIVATE cxx_std_20)
  target_compile_definitions(${_xar_test} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_link_libraries(${_xar_test} PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(${_xar_test} PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME ${_xar_test} COMMAND ${_xar_test})
endif()
