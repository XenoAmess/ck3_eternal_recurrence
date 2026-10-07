if(BUILD_TESTING)
  foreach(stage IN ITEMS 2921350 2921020)
    add_executable(xar_ck3_12003_person_following_${stage}_test
      src/ck3_12003_context_sources.cpp
      tests/person_following_${stage}_12003_test.cpp
      tests/person_following_${stage}_fixture.cpp)
    target_include_directories(xar_ck3_12003_person_following_${stage}_test PRIVATE include)
    target_compile_features(xar_ck3_12003_person_following_${stage}_test PRIVATE cxx_std_20)
    target_compile_definitions(xar_ck3_12003_person_following_${stage}_test PRIVATE NOMINMAX)
    if(MSVC)
      target_compile_options(xar_ck3_12003_person_following_${stage}_test PRIVATE
        /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME xar_ck3_12003_person_following_${stage}_test
      COMMAND xar_ck3_12003_person_following_${stage}_test
        "${CMAKE_BINARY_DIR}/ck3_12003_person_following_${stage}_wire")
  endforeach()
endif()
