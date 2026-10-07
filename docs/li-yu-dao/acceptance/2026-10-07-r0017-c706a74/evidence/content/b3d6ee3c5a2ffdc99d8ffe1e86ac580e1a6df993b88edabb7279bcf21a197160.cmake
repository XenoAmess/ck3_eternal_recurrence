# One new current 73C classification fixture; explicit target only, no legacy replay.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_army_province73c_current_classifier_v1_fixture EXCLUDE_FROM_ALL
    tests/army_province73c_current_classifier_v1_fixture.cpp)
  target_include_directories(xar_bridge_army_province73c_current_classifier_v1_fixture PRIVATE include)
  target_compile_features(xar_bridge_army_province73c_current_classifier_v1_fixture PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_army_province73c_current_classifier_v1_fixture PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_army_province73c_current_classifier_v1_fixture PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_army_province73c_current_classifier_v1_fixture PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_army_province73c_current_classifier_v1_fixture
    COMMAND xar_bridge_army_province73c_current_classifier_v1_fixture
      "${CMAKE_CURRENT_BINARY_DIR}/province73c-current-classifier-wire")
endif()
