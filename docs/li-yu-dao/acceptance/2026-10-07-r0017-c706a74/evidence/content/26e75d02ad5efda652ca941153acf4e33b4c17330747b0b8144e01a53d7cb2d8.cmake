# New .3 leaf is excluded by the existing runtime's ck3_12002*.cpp glob.
# Include this fragment after xar_ck3_12002_runtime has been declared/linked.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12003_prisoner_release_preview.cpp
  src/ck3_12003_prisoner_release_preview_serializer.cpp)

if(BUILD_TESTING)
  add_executable(ck3_12003_prisoner_release_preview_test
    src/ck3_12003_prisoner_release_preview_test.cpp
    src/player_prisoner_collection_query_v1_private.cpp
    src/player_prisoner_ransom_wire_v1.cpp)
  target_include_directories(ck3_12003_prisoner_release_preview_test PRIVATE include src research)
  target_compile_features(ck3_12003_prisoner_release_preview_test PRIVATE cxx_std_20)
  target_link_libraries(ck3_12003_prisoner_release_preview_test PRIVATE xar_ck3_12002_runtime)
  if(MSVC)
    target_compile_options(ck3_12003_prisoner_release_preview_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  else()
    target_compile_options(ck3_12003_prisoner_release_preview_test PRIVATE
      -UNDEBUG -Wall -Wextra -Werror)
  endif()
  add_test(NAME ck3_12003_prisoner_release_preview_test
    COMMAND ck3_12003_prisoner_release_preview_test
      "${CMAKE_CURRENT_BINARY_DIR}/ck3_12003_prisoner_release_preview_wire")
endif()
