if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_army_regiment_character_role_test
    tests/army_regiment_character_role_12004_fixture.cpp
    src/ck3_12003_army_replenishment_records.cpp)
  target_include_directories(xar_ck3_12004_army_regiment_character_role_test PRIVATE include)
  target_compile_features(xar_ck3_12004_army_regiment_character_role_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_army_regiment_character_role_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_army_regiment_character_role_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_army_regiment_character_role
    COMMAND xar_ck3_12004_army_regiment_character_role_test)
endif()
