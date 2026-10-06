# Include after runtime and CTest initialization. The two .inc files live in
# the already linked release reader/serializer translation units.
if(BUILD_TESTING)
  add_executable(ck3_12003_prisoner_native_kinship_test
    src/ck3_12003_prisoner_native_kinship_test.cpp
    src/player_prisoner_collection_query_v1_private.cpp
    src/player_prisoner_ransom_wire_v1.cpp)
  target_include_directories(ck3_12003_prisoner_native_kinship_test PRIVATE include src research)
  target_compile_features(ck3_12003_prisoner_native_kinship_test PRIVATE cxx_std_20)
  target_link_libraries(ck3_12003_prisoner_native_kinship_test PRIVATE xar_ck3_12002_runtime)
  if(MSVC)
    target_compile_options(ck3_12003_prisoner_native_kinship_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  else()
    target_compile_options(ck3_12003_prisoner_native_kinship_test PRIVATE
      -UNDEBUG -Wall -Wextra -Werror)
  endif()
  add_test(NAME ck3_12003_prisoner_native_kinship_test
    COMMAND ck3_12003_prisoner_native_kinship_test ck3_12003_prisoner_native_kinship_wire)
endif()
