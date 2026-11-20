cmake_minimum_required(VERSION 3.24)
project(current_full111_focused VERSION 0.1.0 LANGUAGES CXX)
include(CTest)
get_filename_component(_root "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
# This fixture uses the same production module and target names. Optional local
# include fallbacks support an isolated sparse source export; CI uses the repo.
set(XAR_FULL111_FOCUSED_FALLBACK_INCLUDE "" CACHE STRING "Existing read-only include closure for isolated qualification")
include_directories(BEFORE "${_root}/include" "${_root}/src")
if(XAR_FULL111_FOCUSED_FALLBACK_INCLUDE)
  include_directories(${XAR_FULL111_FOCUSED_FALLBACK_INCLUDE})
endif()
set(XAR_FULL111_FOCUSED_FALLBACK_RESEARCH "" CACHE STRING "Read-only research include closure for isolated qualification")
if(XAR_FULL111_FOCUSED_FALLBACK_RESEARCH)
  set_property(SOURCE "${_root}/src/ck3_12002_semantic_adapter.cpp"
    "${_root}/src/bridge.cpp" "${_root}/src/game_adapter.cpp"
    APPEND PROPERTY INCLUDE_DIRECTORIES
    ${XAR_FULL111_FOCUSED_FALLBACK_RESEARCH})
endif()
set(_sources
  ck3_1210_adapter.cpp ck3_1210_core.cpp ck3_1210_commands.cpp
  ck3_1210_core_frame_v1.cpp ck3_1210_thread_runtime.cpp
  ck3_1210_core_control_request_v1.cpp ck3_1210_core_control_v1.cpp
  ck3_1210_full_clock_request_v1.cpp ck3_1210_application_exit_v1.cpp
  ck3_1210_daily_final_hook_v1.cpp ck3_1210_date_sentinel_v1.cpp
  ck3_1210_date_worker_game_access_v1.cpp ck3_12002_semantic_adapter.cpp
  main_thread_query_mailbox_v1.cpp game_adapter.cpp game_adapter_capabilities.cpp)
set(_paths)
foreach(_name IN LISTS _sources)
  list(APPEND _paths "${_root}/src/${_name}")
endforeach()
add_library(xar_ck3_12002_runtime OBJECT ${_paths})
add_library(xar_ck3_bridge OBJECT "${_root}/src/bridge.cpp")
target_compile_definitions(xar_ck3_bridge PRIVATE XAR_BRIDGE_VERSION="${PROJECT_VERSION}")
foreach(_target IN ITEMS xar_ck3_12002_runtime xar_ck3_bridge)
  target_compile_features(${_target} PRIVATE cxx_std_20)
  target_compile_definitions(${_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(${_target} PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
endforeach()
if(XAR_CK3_ENABLE_121003_FULL111)
  set(_required XAR_CK3_ENABLE_1210_CORE_FRAME_V1 XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1
    XAR_CK3_ENABLE_1210_CORE_CONTROL_V1 XAR_CK3_ENABLE_1210_FULL_CLOCK_V1
    XAR_CK3_ENABLE_1210_APPLICATION_EXIT_V1 XAR_CK3_ENABLE_1210_DATE_SENTINEL_V1
    XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92)
  foreach(_feature IN LISTS _required)
    set(${_feature} ON)
    target_compile_definitions(xar_ck3_12002_runtime PRIVATE ${_feature}=1)
    target_compile_definitions(xar_ck3_bridge PRIVATE ${_feature}=1)
  endforeach()
endif()
include("${_root}/cmake/current_full111.cmake")
get_target_property(_runtime_sources xar_ck3_12002_runtime SOURCES)
file(GENERATE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/production-source-list.txt"
  CONTENT "$<JOIN:$<TARGET_PROPERTY:xar_ck3_12002_runtime,SOURCES>,\n>\n")
