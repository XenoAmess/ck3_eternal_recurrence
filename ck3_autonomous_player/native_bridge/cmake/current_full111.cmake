include_guard(GLOBAL)
# This exact profile is independent from the partial26785313 Core/Gold route.
option(XAR_CK3_ENABLE_121003_FULL111
  "Enable reviewed exact26785313 Full/owned observation/basic clock and mapped SAVE" OFF)
get_filename_component(_full111_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(_full111_core_sources
  ck3_1210_adapter.cpp ck3_1210_core.cpp ck3_1210_commands.cpp
  ck3_1210_core_frame_v1.cpp ck3_1210_thread_runtime.cpp
  ck3_1210_core_control_request_v1.cpp ck3_1210_core_control_v1.cpp
  ck3_1210_full_clock_request_v1.cpp ck3_1210_application_exit_v1.cpp
  ck3_1210_daily_final_hook_v1.cpp ck3_1210_date_sentinel_v1.cpp
  ck3_1210_date_worker_game_access_v1.cpp ck3_12002_semantic_adapter.cpp
  main_thread_query_mailbox_v1.cpp game_adapter.cpp game_adapter_capabilities.cpp
  ck3_121003_full111.cpp ck3_121003_save_mapped111.cpp
  ck3_121003_readonly26785313_v1.cpp)

# Closed OFF definitions remain available to the existing runtime and standalone
# tests. This supplies link closure; it grants no enabled profile or capability.
target_sources(xar_ck3_12002_runtime PRIVATE
  "${_full111_root}/src/ck3_121003_full111.cpp"
  "${_full111_root}/src/ck3_121003_save_mapped111.cpp")
get_property(_full111_existing_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(_target IN LISTS _full111_existing_targets)
  if(_target STREQUAL "xar_ck3_12002_runtime")
    continue()
  endif()
  get_target_property(_sources ${_target} SOURCES)
  set(_needs_full FALSE)
  set(_needs_save FALSE)
  foreach(_source IN LISTS _sources)
    get_filename_component(_name "${_source}" NAME)
    if(_name STREQUAL "ck3_1210_adapter.cpp" OR
       _name STREQUAL "ck3_1210_adapter_body_v1.cpp")
      set(_needs_full TRUE)
    elseif(_name STREQUAL "ck3_1210_core_control_v1.cpp")
      set(_needs_save TRUE)
    endif()
  endforeach()
  if(_needs_full)
    target_sources(${_target} PRIVATE "${_full111_root}/src/ck3_121003_full111.cpp")
  endif()
  if(_needs_save)
    target_sources(${_target} PRIVATE "${_full111_root}/src/ck3_121003_save_mapped111.cpp")
  endif()
endforeach()

if(XAR_CK3_ENABLE_121003_FULL111)
  foreach(_required IN ITEMS XAR_CK3_ENABLE_1210_CORE_FRAME_V1
      XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1 XAR_CK3_ENABLE_1210_CORE_CONTROL_V1
      XAR_CK3_ENABLE_1210_FULL_CLOCK_V1 XAR_CK3_ENABLE_1210_APPLICATION_EXIT_V1
      XAR_CK3_ENABLE_1210_DATE_SENTINEL_V1 XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92)
    if(NOT ${_required})
      message(FATAL_ERROR "Full111 requires explicit ${_required}")
    endif()
  endforeach()
  if(NOT XAR_CK3_ENABLE_121003_26785313_READONLY_V1 AND
      NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
    target_sources(xar_ck3_12002_runtime PRIVATE
      "${_full111_root}/src/ck3_121003_readonly26785313_v1.cpp")
  endif()
  foreach(_source IN LISTS _full111_core_sources)
    set_property(SOURCE "${_full111_root}/src/${_source}" APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>,$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>>:XAR_CK3_ENABLE_121003_FULL111=1>")
  endforeach()
  set_property(SOURCE "${_full111_root}/src/bridge.cpp" APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_FULL111=1>")
endif()

if(BUILD_TESTING)
  set(_full111_on_sources "${_full111_root}/src/bridge.cpp")
  foreach(_source IN LISTS _full111_core_sources)
    list(APPEND _full111_on_sources "${_full111_root}/src/${_source}")
  endforeach()
  # Keep object paths short on Windows while retaining stable public CI targets.
  add_library(xar_full111_on_obj OBJECT ${_full111_on_sources})
  add_custom_target(xar_ck3_121003_full111_on_compile DEPENDS xar_full111_on_obj)
  add_library(xar_full111_off_obj OBJECT
    "${_full111_root}/src/ck3_1210_adapter.cpp"
    "${_full111_root}/src/ck3_121003_full111.cpp")
  add_custom_target(xar_ck3_121003_full111_off_compile DEPENDS xar_full111_off_obj)
  set(_full111_on_definitions
    XAR_CK3_ENABLE_121003_FULL111=1 XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1
    XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1=1 XAR_CK3_ENABLE_1210_CORE_CONTROL_V1=1
    XAR_CK3_ENABLE_1210_FULL_CLOCK_V1=1 XAR_CK3_ENABLE_1210_APPLICATION_EXIT_V1=1
    XAR_CK3_ENABLE_1210_DATE_SENTINEL_V1=1 XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92=1)
  target_compile_definitions(xar_full111_on_obj PRIVATE ${_full111_on_definitions})
  target_compile_definitions(xar_full111_on_obj PRIVATE XAR_BRIDGE_VERSION="${PROJECT_VERSION}")
  # Type the preserved foreign Core/Gold branch independently of Full111.
  target_compile_definitions(xar_full111_off_obj PRIVATE
    XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1=1
    XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2=1)
  add_executable(xar_ck3_121003_full111_static_test
    "${_full111_root}/src/ck3_121003_full111_static_test.cpp"
    "${_full111_root}/src/ck3_121003_full111.cpp"
    "${_full111_root}/src/ck3_1210_core.cpp"
    "${_full111_root}/src/ck3_121003_readonly26785313_v1.cpp"
    "${_full111_root}/src/ck3_1210_pending_snapshot_v1.cpp"
    "${_full111_root}/src/ck3_1210_military_empty_v1.cpp")
  target_compile_definitions(xar_ck3_121003_full111_static_test PRIVATE XAR_CK3_ENABLE_121003_FULL111=1)
  target_link_libraries(xar_ck3_121003_full111_static_test PRIVATE bcrypt)
  add_executable(xar_ck3_121003_full111_disabled_test
    "${_full111_root}/src/ck3_121003_full111_disabled_test.cpp")
  foreach(_target IN ITEMS xar_full111_on_obj
      xar_full111_off_obj xar_ck3_121003_full111_static_test
      xar_ck3_121003_full111_disabled_test)
    set_target_properties(${_target} PROPERTIES EXCLUDE_FROM_ALL TRUE)
    target_include_directories(${_target} PRIVATE "${_full111_root}/include" "${_full111_root}/src"
      "${_full111_root}/research")
    target_compile_features(${_target} PRIVATE cxx_std_20)
    target_compile_definitions(${_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(${_target} PRIVATE /W4 /WX /permissive- /EHsc)
    endif()
  endforeach()
  add_test(NAME xar_ck3_121003_full111_synthetic COMMAND xar_ck3_121003_full111_static_test)
  add_test(NAME xar_ck3_121003_full111_disabled COMMAND xar_ck3_121003_full111_disabled_test)
  set_tests_properties(xar_ck3_121003_full111_synthetic xar_ck3_121003_full111_disabled
    PROPERTIES TIMEOUT 30)
endif()
unset(_full111_root)
unset(_full111_core_sources)
unset(_full111_existing_targets)
unset(_full111_on_sources)
unset(_full111_on_definitions)
