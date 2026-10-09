# New first-vector worlds only; no prior fixture producer is replayed.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_person_first_title_vector.cpp)

if(BUILD_TESTING)
  add_executable(xar_ck3_12004_person_first_title_vector_mcp_test
    tests/person_first_title_vector_12004_mcp_fixture.cpp)
  target_include_directories(xar_ck3_12004_person_first_title_vector_mcp_test PRIVATE
    include src research)
  target_compile_features(xar_ck3_12004_person_first_title_vector_mcp_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_person_first_title_vector_mcp_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_person_first_title_vector_mcp_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  xar_ck3_12004_fixture_use_real_bridge(xar_ck3_12004_person_first_title_vector_mcp_test)
  add_test(NAME xar_ck3_12004_person_first_title_vector_mcp_first
    COMMAND xar_ck3_12004_person_first_title_vector_mcp_test
      "${CMAKE_BINARY_DIR}/wire/ck3_12004_person_first_title_vector_mcp_first")
endif()
