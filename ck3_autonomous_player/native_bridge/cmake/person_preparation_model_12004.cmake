# Existing person_native_six_stage_capture_12004.cmake supplies the production TU.
# This leaf adds only the three new historical Model association worlds.
if(BUILD_TESTING)
  add_executable(xar_ck3_12004_person_preparation_model_mcp_test
    tests/person_preparation_model_12004_mcp_fixture.cpp)
  target_include_directories(xar_ck3_12004_person_preparation_model_mcp_test PRIVATE
    include src research)
  target_compile_features(xar_ck3_12004_person_preparation_model_mcp_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_person_preparation_model_mcp_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_person_preparation_model_mcp_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  xar_ck3_12004_fixture_use_real_bridge(xar_ck3_12004_person_preparation_model_mcp_test)
  add_test(NAME xar_ck3_12004_person_preparation_model_mcp_first
    COMMAND xar_ck3_12004_person_preparation_model_mcp_test
      "${CMAKE_BINARY_DIR}/wire/ck3_12004_person_preparation_model_mcp_first")
endif()
