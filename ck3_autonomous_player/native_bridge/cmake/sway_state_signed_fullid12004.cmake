# Owned-memory coverage for canonical signed character IDs in the shared Sway reader.
# This is not coverage of the .4 factory or a complete native route.
# The gift fallback is an explicit test seam; it is not linked or credited here.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_sway_state_signed_fullid12004_test
    tests/sway_state_signed_fullid12004_test.cpp
    src/ck3_12002.cpp
    src/ck3_12002_sway_state.cpp)
  target_include_directories(xar_ck3_sway_state_signed_fullid12004_test PRIVATE include)
  target_compile_features(xar_ck3_sway_state_signed_fullid12004_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_sway_state_signed_fullid12004_test
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_sway_state_signed_fullid12004_test
      PRIVATE /W4 /WX /permissive- /EHsc /utf-8 /MP1)
  endif()
  add_test(NAME xar_ck3_sway_state_signed_fullid12004
    COMMAND xar_ck3_sway_state_signed_fullid12004_test)
endif()
