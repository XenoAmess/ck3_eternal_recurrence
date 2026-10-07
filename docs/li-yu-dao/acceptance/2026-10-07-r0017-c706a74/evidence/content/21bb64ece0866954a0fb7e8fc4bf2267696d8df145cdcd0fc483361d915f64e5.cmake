# SOURCE_PREPARED/NOTRUN. Fresh whole preview target only; no old fixture replay.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_captured_target_land_supply_whole_preview_test
    tests/ck3_12003_captured_target_land_supply_whole_preview_test.cpp)
  target_link_libraries(xar_ck3_12003_captured_target_land_supply_whole_preview_test
    PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12003_captured_target_land_supply_whole_preview_test PRIVATE include)
  target_compile_features(xar_ck3_12003_captured_target_land_supply_whole_preview_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_captured_target_land_supply_whole_preview_test
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_captured_target_land_supply_whole_preview_test
      PRIVATE /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_captured_target_land_supply_whole_preview_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_captured_target_land_supply_whole_preview_test
    COMMAND xar_ck3_12003_captured_target_land_supply_whole_preview_test --wire-dir
      "${CMAKE_CURRENT_BINARY_DIR}/cache-observers/captured-target-land-supply-whole-preview-wire")
endif()
