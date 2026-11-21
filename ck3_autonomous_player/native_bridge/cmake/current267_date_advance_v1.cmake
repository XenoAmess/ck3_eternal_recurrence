# Existing Core/date sentinel machinery, independently bound to exact current267.
option(XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1
  "Bind current267 daily-final/worker/pause ABI" OFF)
option(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1
  "Enable bounded current267 one-day Core owner route" OFF)
get_filename_component(_xar_date267_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(_xar_date267_new
  src/ck3_121003_date_postday26785313_v1.cpp
  src/ck3_121003_date_worker_access26785313_v2.cpp
  src/ck3_121003_date_advance26785313_v1.cpp
  src/ck3_121003_date_advance26785313_wire_v1.cpp)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
  foreach(_xar_unit IN LISTS _xar_date267_new)
    target_sources(xar_ck3_12002_runtime PRIVATE "${_xar_date267_root}/${_xar_unit}")
  endforeach()
  foreach(_xar_unit IN ITEMS src/ck3_121003_date_postday26785313_v1.cpp src/ck3_1210_date_sentinel_v1.cpp)
    set_property(SOURCE "${_xar_date267_root}/${_xar_unit}" APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1=$<BOOL:${XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1}>>")
  endforeach()
  if(XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1)
    if(NOT XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1 OR
       NOT XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1 OR
       NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
      message(FATAL_ERROR "Current one-day route requires exact current postday, command and Core bindings")
    endif()
    set(_xar_date267_existing src/ck3_121003_readonly26785313_v1.cpp
      src/ck3_121003_core_route26785313_v1.cpp src/ck3_121003_personal_gold26785313_v2.cpp
      src/ck3_1210_adapter.cpp)
    foreach(_xar_unit IN LISTS _xar_date267_existing _xar_date267_new)
      set_property(SOURCE "${_xar_date267_root}/${_xar_unit}" APPEND PROPERTY COMPILE_DEFINITIONS
        "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1=1>")
    endforeach()
    # Route compile-time dependency checks are local; do not churn all runtime flags.
    set_property(SOURCE "${_xar_date267_root}/src/ck3_121003_date_advance26785313_v1.cpp"
      APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1=1>"
      "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1=1>")
  endif()
endif()
if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1)
  set_property(SOURCE "${_xar_date267_root}/src/bridge.cpp" "${_xar_date267_root}/src/game_adapter.cpp"
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1=1>")
endif()
if(BUILD_TESTING AND WIN32)
  set(_xar_test xar_ck3_121003_26785313_date_advance_wire_test)
  add_executable(${_xar_test} EXCLUDE_FROM_ALL
    "${_xar_date267_root}/src/ck3_121003_date_advance26785313_wire_v1_test.cpp"
    "${_xar_date267_root}/src/ck3_121003_date_advance26785313_wire_v1.cpp"
    "${_xar_date267_root}/src/ck3_121003_date_advance26785313_v1.cpp"
    "${_xar_date267_root}/src/ck3_1210_date_sentinel_v1.cpp"
    "${_xar_date267_root}/src/ck3_1210_core.cpp"
    "${_xar_date267_root}/src/tactical_daily_sentinel_v1.cpp")
  target_include_directories(${_xar_test} PRIVATE "${_xar_date267_root}/include" "${_xar_date267_root}/src")
  target_compile_features(${_xar_test} PRIVATE cxx_std_20)
  target_compile_definitions(${_xar_test} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN
    XAR_CK3_ENABLE_121003_26785313_DATE_ADVANCE_V1=0
    XAR_CK3_ENABLE_121003_26785313_DATE_POSTDAY_BINDINGS_V1=0
    XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1=0)
  if(MSVC)
    target_compile_options(${_xar_test} PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME ${_xar_test} COMMAND ${_xar_test})
endif()
