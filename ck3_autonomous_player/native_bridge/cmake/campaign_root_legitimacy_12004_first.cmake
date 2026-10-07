# Authored-only FIRST producer leaf. Root owns the sole shared include.
# The complete intended DLL/runtime must share Root's fresh strict build pin;
# this fixture links the genuine adopted runtime, not copied reader sources.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_campaign_root_legitimacy_12004_first_fixture
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/campaign_root_legitimacy_12004_fixture.cpp")
  target_link_libraries(xar_campaign_root_legitimacy_12004_first_fixture PRIVATE
    xar_ck3_12002_runtime)
  target_include_directories(xar_campaign_root_legitimacy_12004_first_fixture PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include")
  target_compile_features(xar_campaign_root_legitimacy_12004_first_fixture PRIVATE
    cxx_std_20)
  if(MSVC)
    target_compile_options(xar_campaign_root_legitimacy_12004_first_fixture PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME xar_campaign_root_legitimacy_12004_first
    COMMAND $<TARGET_FILE:xar_campaign_root_legitimacy_12004_first_fixture>
      "${CMAKE_CURRENT_BINARY_DIR}/fixtures/campaign_root_legitimacy_12004_first")
endif()
