# Existing actual4 owning-thread Snapshot -> actual state_snapshot publication.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/player_event_trait_membership_12004.cpp)

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_player_event_trait_pipeline_test
    src/player_event_trait_membership_12004_fixture.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  target_link_libraries(xar_ck3_12004_player_event_trait_pipeline_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
  target_include_directories(xar_ck3_12004_player_event_trait_pipeline_test PRIVATE include)
  target_compile_features(xar_ck3_12004_player_event_trait_pipeline_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_player_event_trait_pipeline_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  set_target_properties(xar_ck3_12004_player_event_trait_pipeline_test PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/fixtures")
  if(MSVC)
    target_compile_options(xar_ck3_12004_player_event_trait_pipeline_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_player_event_trait_pipeline_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_player_event_trait_pipeline_test>
      ${CMAKE_CURRENT_BINARY_DIR}/wire/player_event_trait_membership_12004)
endif()
