if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_first_heir_descendants_test
    src/ck3_12004_first_heir_descendants_test.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  get_target_property(_descendants_bridge_libraries xar_ck3_bridge LINK_LIBRARIES)
  target_link_libraries(xar_ck3_12004_first_heir_descendants_test
    PRIVATE xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    ${_descendants_bridge_libraries})
  target_compile_features(xar_ck3_12004_first_heir_descendants_test PRIVATE cxx_std_20)
  get_target_property(_descendants_definitions xar_ck3_bridge COMPILE_DEFINITIONS)
  target_compile_definitions(xar_ck3_12004_first_heir_descendants_test
    PRIVATE ${_descendants_definitions})
  if(MSVC)
    target_compile_options(xar_ck3_12004_first_heir_descendants_test
      PRIVATE /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_first_heir_descendants_test
    COMMAND xar_ck3_12004_first_heir_descendants_test
      ${CMAKE_CURRENT_BINARY_DIR}/first-heir-descendants-wire)
  add_test(NAME xar_ck3_12004_current_first_heir_pregnancy_observer_test
    COMMAND xar_ck3_12004_first_heir_descendants_test
      --pregnancy-observer-wire-dir
      ${CMAKE_CURRENT_BINARY_DIR}/current-first-heir-pregnancy-wire)
endif()
