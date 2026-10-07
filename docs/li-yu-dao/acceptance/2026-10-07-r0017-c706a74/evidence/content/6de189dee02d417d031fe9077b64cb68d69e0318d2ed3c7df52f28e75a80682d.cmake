# New actual4 whole prisoner FIRST; historical g104/12003 targets are untouched.
# Root/assembler includes this leaf after the shared runtime and CTest exist.
# The old runtime glob only selects ck3_12002*.cpp; add exactly the seven new
# domain TUs once here. Other actual4 core TUs remain centrally assembled.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_interaction_context.cpp
  src/ck3_12004_prisoner_release_preview.cpp
  src/ck3_12004_prisoner_named.cpp
  src/ck3_12004_prisoner_ransom.cpp
  src/ck3_12004_prisoner_collection.cpp
  src/ck3_12004_prisoner_wire.cpp
  src/ck3_12004_prisoner_mailbox.cpp)

if(BUILD_TESTING)
  add_executable(ck3_12004_prisoner_collection_test
    src/ck3_12004_prisoner_collection_test.cpp
    src/player_prisoner_collection_query_v1_private.cpp
    src/player_prisoner_ransom_wire_v1.cpp)
  target_include_directories(ck3_12004_prisoner_collection_test PRIVATE include src research)
  target_compile_features(ck3_12004_prisoner_collection_test PRIVATE cxx_std_20)
  target_link_libraries(ck3_12004_prisoner_collection_test PRIVATE xar_ck3_12002_runtime)
  if(MSVC)
    target_compile_options(ck3_12004_prisoner_collection_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  else()
    target_compile_options(ck3_12004_prisoner_collection_test PRIVATE
      -UNDEBUG -Wall -Wextra -Werror)
  endif()
  add_test(NAME ck3_12004_prisoner_collection_test
    COMMAND $<TARGET_FILE:ck3_12004_prisoner_collection_test>
      "${CMAKE_CURRENT_BINARY_DIR}/wire/ck3_12004_prisoner_collection_whole5")
endif()
