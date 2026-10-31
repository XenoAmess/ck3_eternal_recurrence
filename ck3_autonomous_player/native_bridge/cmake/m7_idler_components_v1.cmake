target_sources(xar_ck3_12002_runtime PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}/../src/m7_idler_components_v1.cpp")

if(BUILD_TESTING AND WIN32)
  set(_xar_m7_idler_target xar_ck3_12004_m7_idler_components_v1_test)

  add_executable(${_xar_m7_idler_target}
    tests/m7_idler_components_v1_test.cpp
    src/m7_idler_components_v1.cpp)

  target_include_directories(${_xar_m7_idler_target} PRIVATE include src research)
  target_compile_features(${_xar_m7_idler_target} PRIVATE cxx_std_20)
  target_compile_definitions(${_xar_m7_idler_target} PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)

  if(MSVC)
    target_compile_options(${_xar_m7_idler_target} PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()

  add_test(NAME xar_ck3_12004_m7_idler_components_v1
    COMMAND ${_xar_m7_idler_target})
  set_tests_properties(xar_ck3_12004_m7_idler_components_v1 PROPERTIES TIMEOUT 10)

  unset(_xar_m7_idler_target)
endif()
