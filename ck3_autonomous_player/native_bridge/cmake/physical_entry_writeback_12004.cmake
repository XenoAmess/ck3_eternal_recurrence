target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_physical_entry_writeback.cpp)

if(BUILD_TESTING AND WIN32)
  set(XAR_PHYSICAL_ENTRY_WRITEBACK_WIRE_DIR_12004
    "${CMAKE_CURRENT_BINARY_DIR}/wire/physical-entry-writeback-12004")
  # The preceding consumption leaf owns this production serializer projection.
  add_executable(xar_physical_entry_writeback_12004_whole EXCLUDE_FROM_ALL
    tests/physical_entry_writeback_12004_whole_fixture.cpp
    "${_knight_consumption_serializer}")
  target_link_libraries(xar_physical_entry_writeback_12004_whole PRIVATE
    xar_ck3_12002_runtime)
  target_include_directories(xar_physical_entry_writeback_12004_whole PRIVATE include)
  target_compile_features(xar_physical_entry_writeback_12004_whole PRIVATE cxx_std_20)
  target_compile_definitions(xar_physical_entry_writeback_12004_whole PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_physical_entry_writeback_12004_whole PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME xar_physical_entry_writeback_12004_whole
    COMMAND $<TARGET_FILE:xar_physical_entry_writeback_12004_whole>
      "${XAR_PHYSICAL_ENTRY_WRITEBACK_WIRE_DIR_12004}")
  set_tests_properties(xar_physical_entry_writeback_12004_whole PROPERTIES
    FIXTURES_SETUP physical_entry_writeback_12004)
  add_test(NAME xar_physical_entry_writeback_12004_registered_mcp
    COMMAND "${Python3_EXECUTABLE}" -B -X utf8 -m pytest -q -s
      "${CMAKE_CURRENT_SOURCE_DIR}/../tests/unit/test_physical_entry_writeback_registered_mcp_12004.py::test_physical_entry_writeback_registered_mcp_12004_whole")
  set_tests_properties(xar_physical_entry_writeback_12004_registered_mcp PROPERTIES
    FIXTURES_REQUIRED physical_entry_writeback_12004
    ENVIRONMENT "CK3_PHYSICAL_ENTRY_WRITEBACK_12004_MCP_WIRE_DIR=${XAR_PHYSICAL_ENTRY_WRITEBACK_WIRE_DIR_12004}"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../..")
endif()
