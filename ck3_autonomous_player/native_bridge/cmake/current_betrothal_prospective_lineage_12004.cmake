if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_current_betrothal_prospective_lineage_test
    src/ck3_12004_current_betrothal_prospective_lineage_test.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  get_target_property(_lineage_bridge_libraries xar_ck3_bridge LINK_LIBRARIES)
  target_link_libraries(xar_ck3_12004_current_betrothal_prospective_lineage_test
    PRIVATE xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    ${_lineage_bridge_libraries})
  target_compile_features(xar_ck3_12004_current_betrothal_prospective_lineage_test
    PRIVATE cxx_std_20)
  get_target_property(_lineage_definitions xar_ck3_bridge COMPILE_DEFINITIONS)
  target_compile_definitions(xar_ck3_12004_current_betrothal_prospective_lineage_test
    PRIVATE ${_lineage_definitions})
  if(MSVC)
    target_compile_options(xar_ck3_12004_current_betrothal_prospective_lineage_test
      PRIVATE /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_current_betrothal_prospective_lineage_test
    COMMAND xar_ck3_12004_current_betrothal_prospective_lineage_test
      ${CMAKE_CURRENT_BINARY_DIR}/current-betrothal-prospective-lineage-wire)
endif()
