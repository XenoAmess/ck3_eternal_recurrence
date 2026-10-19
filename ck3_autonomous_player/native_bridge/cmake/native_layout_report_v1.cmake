# One header-only companion executable; never links or recompiles Bridge.
option(XAR_CK3_BUILD_NATIVE_LAYOUT_REPORT_V1 "Build exact current header ABI report" OFF)
if(NOT XAR_CK3_BUILD_NATIVE_LAYOUT_REPORT_V1)
  return()
endif()
if(NOT WIN32 OR NOT MSVC)
  message(FATAL_ERROR "Native layout report v1 requires the production Windows/MSVC toolchain")
endif()
add_executable(xar_ck3_native_layout_report_v1 src/native_layout_report_v1.cpp)
target_include_directories(xar_ck3_native_layout_report_v1 PRIVATE
  $<TARGET_PROPERTY:xar_ck3_bridge,INCLUDE_DIRECTORIES>
  "${CMAKE_CURRENT_BINARY_DIR}/native-layout-report-v1/$<CONFIG>")
target_compile_definitions(xar_ck3_native_layout_report_v1 PRIVATE
  $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
target_compile_options(xar_ck3_native_layout_report_v1 PRIVATE
  $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_OPTIONS>)
target_compile_features(xar_ck3_native_layout_report_v1 PRIVATE cxx_std_20)
get_target_property(_xar_layout_runtime xar_ck3_bridge MSVC_RUNTIME_LIBRARY)
if(_xar_layout_runtime)
  set_property(TARGET xar_ck3_native_layout_report_v1 PROPERTY
    MSVC_RUNTIME_LIBRARY "${_xar_layout_runtime}")
endif()
file(GENERATE
  OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/native-layout-report-v1/$<CONFIG>/native_layout_flags_v1.hpp"
  CONTENT "#pragma once
inline constexpr const char *kXarNativeLayoutSourceFlagsV1 = R\"xarlayout(
configuration=$<CONFIG>
compiler=${CMAKE_CXX_COMPILER}
compiler_id=${CMAKE_CXX_COMPILER_ID}
compiler_version=${CMAKE_CXX_COMPILER_VERSION}
global_flags=${CMAKE_CXX_FLAGS}
debug_flags=${CMAKE_CXX_FLAGS_DEBUG}
release_flags=${CMAKE_CXX_FLAGS_RELEASE}
relwithdebinfo_flags=${CMAKE_CXX_FLAGS_RELWITHDEBINFO}
minsizerel_flags=${CMAKE_CXX_FLAGS_MINSIZEREL}
bridge_definitions=$<JOIN:$<TARGET_GENEX_EVAL:xar_ck3_bridge,$<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>>,;>
bridge_options=$<JOIN:$<TARGET_GENEX_EVAL:xar_ck3_bridge,$<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_OPTIONS>>,;>
bridge_includes=$<JOIN:$<TARGET_GENEX_EVAL:xar_ck3_bridge,$<TARGET_PROPERTY:xar_ck3_bridge,INCLUDE_DIRECTORIES>>,;>
bridge_msvc_runtime=$<TARGET_GENEX_EVAL:xar_ck3_bridge,$<TARGET_PROPERTY:xar_ck3_bridge,MSVC_RUNTIME_LIBRARY>>
report_msvc_runtime=$<TARGET_GENEX_EVAL:xar_ck3_native_layout_report_v1,$<TARGET_PROPERTY:xar_ck3_native_layout_report_v1,MSVC_RUNTIME_LIBRARY>>
)xarlayout\";
"
  TARGET xar_ck3_native_layout_report_v1)

