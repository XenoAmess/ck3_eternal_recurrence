# Fresh mapped-PC worlds only; no previous producer is invoked by this target.
if(BUILD_TESTING)
  add_executable(xar_ck3_12004_person_mapped_pc_42127e0_mcp_test
    tests/person_mapped_pc_42127e0_12004_mcp_fixture.cpp)
  target_include_directories(xar_ck3_12004_person_mapped_pc_42127e0_mcp_test PRIVATE
    include src research)
  target_compile_features(xar_ck3_12004_person_mapped_pc_42127e0_mcp_test PRIVATE
    cxx_std_20)
  target_compile_definitions(xar_ck3_12004_person_mapped_pc_42127e0_mcp_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_person_mapped_pc_42127e0_mcp_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  xar_ck3_12004_fixture_use_real_bridge(
    xar_ck3_12004_person_mapped_pc_42127e0_mcp_test)
  add_test(NAME xar_ck3_12004_person_mapped_pc_42127e0_mcp_first
    COMMAND xar_ck3_12004_person_mapped_pc_42127e0_mcp_test
      "${CMAKE_BINARY_DIR}/wire/ck3_12004_person_mapped_pc_42127e0_mcp_first")
endif()
