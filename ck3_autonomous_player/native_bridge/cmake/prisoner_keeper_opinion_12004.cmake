# Fresh actual4 keeper input; Root includes this leaf after runtime/CTest.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_prisoner_keeper_opinion.cpp)

if(BUILD_TESTING)
  add_executable(ck3_12004_prisoner_keeper_opinion_whole_first
    tests/ck3_12004_prisoner_keeper_opinion_whole_first.cpp)
  target_include_directories(ck3_12004_prisoner_keeper_opinion_whole_first
    PRIVATE include src research)
  target_compile_features(ck3_12004_prisoner_keeper_opinion_whole_first
    PRIVATE cxx_std_20)
  target_sources(ck3_12004_prisoner_keeper_opinion_whole_first PRIVATE
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  get_target_property(_keeper_bridge_link_libraries xar_ck3_bridge LINK_LIBRARIES)
  target_link_libraries(ck3_12004_prisoner_keeper_opinion_whole_first
    PRIVATE xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    ${_keeper_bridge_link_libraries})
  if(MSVC)
    target_compile_options(ck3_12004_prisoner_keeper_opinion_whole_first PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  else()
    target_compile_options(ck3_12004_prisoner_keeper_opinion_whole_first PRIVATE
      -UNDEBUG -Wall -Wextra -Werror)
  endif()
  add_test(NAME ck3_12004_prisoner_keeper_opinion_whole_first
    COMMAND $<TARGET_FILE:ck3_12004_prisoner_keeper_opinion_whole_first>
      "${CMAKE_CURRENT_BINARY_DIR}/wire/ck3_12004_prisoner_keeper_opinion_first")
endif()
