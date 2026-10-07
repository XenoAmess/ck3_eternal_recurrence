# Actual4 assigned-role quality uses the existing source-closed callback.
# Include after adopted_domains so the proven real Bridge closure is available.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_current_commander_base_quality.cpp)

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_current_commander_base_quality_test
    src/ck3_12004_current_commander_base_quality_test.cpp)
  target_include_directories(xar_ck3_12004_current_commander_base_quality_test
    PRIVATE include)
  target_compile_features(xar_ck3_12004_current_commander_base_quality_test
    PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_current_commander_base_quality_test
    PUBLIC NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_current_commander_base_quality_test
      PRIVATE /W4 /WX /permissive- /EHsc /Gy /UNDEBUG)
    target_link_options(xar_ck3_12004_current_commander_base_quality_test
      PRIVATE /OPT:REF)
  endif()
  target_link_libraries(xar_ck3_12004_current_commander_base_quality_test
    PRIVATE xar_ck3_12002_runtime user32)
  xar_ck3_12004_fixture_use_real_bridge(
    xar_ck3_12004_current_commander_base_quality_test)
  file(MAKE_DIRECTORY
    "${CMAKE_BINARY_DIR}/ck3_12004_current_commander_base_quality_wire")
  add_test(NAME xar_ck3_12004_current_commander_base_quality
    COMMAND xar_ck3_12004_current_commander_base_quality_test
      "${CMAKE_BINARY_DIR}/ck3_12004_current_commander_base_quality_wire")
endif()
