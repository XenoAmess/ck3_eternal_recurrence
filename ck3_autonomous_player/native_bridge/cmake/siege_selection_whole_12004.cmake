# Source-prepared only. Root owns the single whole first build/run.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_siege_selection_whole_fixture EXCLUDE_FROM_ALL
    tests/ck3_12004_siege_selection_whole_fixture.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  target_link_libraries(xar_ck3_12004_siege_selection_whole_fixture PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
  target_include_directories(xar_ck3_12004_siege_selection_whole_fixture PRIVATE include)
  target_compile_features(xar_ck3_12004_siege_selection_whole_fixture PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_siege_selection_whole_fixture PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  if(MSVC)
    target_compile_options(xar_ck3_12004_siege_selection_whole_fixture PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
endif()
