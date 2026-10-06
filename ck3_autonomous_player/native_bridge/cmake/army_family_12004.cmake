# Root registers this file once after adopting the mapped family TUs.
# One new producer; do not schedule historical Army family tests here.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_army_family_test
    src/ck3_12004_army_family_fixture.cpp)
  target_link_libraries(xar_ck3_12004_army_family_test PRIVATE
    xar_ck3_12002_runtime bcrypt)
  target_include_directories(xar_ck3_12004_army_family_test PRIVATE include)
  target_compile_features(xar_ck3_12004_army_family_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_army_family_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_army_family_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_army_family_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_army_family_test>
      ${CMAKE_CURRENT_BINARY_DIR}/wire/ck3_12004_army_family)
endif()
