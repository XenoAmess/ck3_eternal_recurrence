# Same selected-seat private Council family; no new feature flag or MCP tool.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_council_task_owner_tax.cpp)

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_council_task_domain_tax_whole_test
    src/ck3_12004_council_task_domain_tax_whole_fixture.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  target_include_directories(xar_ck3_12004_council_task_domain_tax_whole_test PRIVATE include)
  target_compile_features(xar_ck3_12004_council_task_domain_tax_whole_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_council_task_domain_tax_whole_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  target_link_libraries(xar_ck3_12004_council_task_domain_tax_whole_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
  if(MSVC)
    target_compile_options(xar_ck3_12004_council_task_domain_tax_whole_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12004_council_task_domain_tax_whole_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_council_task_domain_tax_whole_test>
      "${CMAKE_CURRENT_BINARY_DIR}/wire/ck3_12004_council_task_domain_tax")
endif()
