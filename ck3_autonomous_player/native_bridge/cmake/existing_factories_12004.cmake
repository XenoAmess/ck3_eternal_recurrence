# Root includes this file once after adopting all actual .4 factory TUs.
# One fresh compound producer; historical factory tests are not registered here.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12004_existing_factories_whole_test
    src/ck3_12004_existing_factories_whole_fixture.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  target_include_directories(xar_bridge_ck3_12004_existing_factories_whole_test PRIVATE include)
  target_compile_features(xar_bridge_ck3_12004_existing_factories_whole_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12004_existing_factories_whole_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  target_link_libraries(xar_bridge_ck3_12004_existing_factories_whole_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt user32
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12004_existing_factories_whole_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_bridge_ck3_12004_existing_factories_whole_test
    COMMAND $<TARGET_FILE:xar_bridge_ck3_12004_existing_factories_whole_test>
      --emit-wire ${CMAKE_CURRENT_BINARY_DIR}/wire/existing_factories_12004)
endif()
