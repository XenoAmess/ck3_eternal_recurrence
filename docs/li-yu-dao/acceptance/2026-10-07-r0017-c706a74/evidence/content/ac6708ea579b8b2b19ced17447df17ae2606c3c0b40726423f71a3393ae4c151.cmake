# One source-only FIRST target for the actual .4 full Snapshot reader.
# Root includes this leaf after the production bridge/runtime targets exist.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_snapshot_foundation_test
    src/ck3_12004_snapshot_foundation_fixture.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  target_link_libraries(xar_ck3_12004_snapshot_foundation_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
  target_include_directories(xar_ck3_12004_snapshot_foundation_test PRIVATE include)
  target_compile_features(xar_ck3_12004_snapshot_foundation_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_snapshot_foundation_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  set_target_properties(xar_ck3_12004_snapshot_foundation_test PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/fixtures")
  if(MSVC)
    target_compile_options(xar_ck3_12004_snapshot_foundation_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_snapshot_foundation_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_snapshot_foundation_test>
      ${CMAKE_CURRENT_BINARY_DIR}/wire/ck3_12004_snapshot_foundation)
endif()
