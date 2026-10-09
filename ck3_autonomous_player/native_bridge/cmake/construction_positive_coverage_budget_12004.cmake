# Register the already qualified direct fixture against the production Runtime.
# Its two scenes run in one process and take no command-line arguments.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_construction_positive_coverage_budget_test
    tests/ck3_12004_construction_positive_coverage_budget_test.cpp)
  target_include_directories(xar_ck3_12004_construction_positive_coverage_budget_test
    PRIVATE include src research)
  target_compile_features(xar_ck3_12004_construction_positive_coverage_budget_test
    PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_construction_positive_coverage_budget_test
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_link_libraries(xar_ck3_12004_construction_positive_coverage_budget_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    kernel32 user32 gdi32 winspool shell32 ole32 oleaut32 uuid comdlg32 advapi32)
  if(MSVC)
    target_compile_options(xar_ck3_12004_construction_positive_coverage_budget_test
      PRIVATE /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_construction_positive_coverage_budget_first
    COMMAND xar_ck3_12004_construction_positive_coverage_budget_test)
endif()
