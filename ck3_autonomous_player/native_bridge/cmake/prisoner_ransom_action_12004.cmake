# New actual4 ordinary ransom action FIRST. Root includes this domain leaf
# after the shared runtime, current4 prisoner leaf and CTest are available.
# The actual4 command provider is a separate central adopted dependency.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_prisoner_ransom_action.cpp)

if(BUILD_TESTING)
  add_executable(ck3_12004_prisoner_ransom_action_test
    src/ck3_12004_prisoner_ransom_action_test.cpp
    src/player_prisoner_collection_query_v1_private.cpp
    src/player_prisoner_ransom_wire_v1.cpp)
  target_include_directories(ck3_12004_prisoner_ransom_action_test PRIVATE
    include src research)
  target_compile_features(ck3_12004_prisoner_ransom_action_test PRIVATE cxx_std_20)
  target_link_libraries(ck3_12004_prisoner_ransom_action_test PRIVATE
    xar_ck3_12002_runtime)
  if(MSVC)
    target_compile_options(ck3_12004_prisoner_ransom_action_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  else()
    target_compile_options(ck3_12004_prisoner_ransom_action_test PRIVATE
      -UNDEBUG -Wall -Wextra -Werror)
  endif()
  add_test(NAME ck3_12004_prisoner_ransom_action_test
    COMMAND $<TARGET_FILE:ck3_12004_prisoner_ransom_action_test>
      "${CMAKE_CURRENT_BINARY_DIR}/wire/ck3_12004_prisoner_ransom_action_whole5")
endif()
