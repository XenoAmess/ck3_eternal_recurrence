# Exact-build observed-current numeric refresh operands; new fixture only.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12003_current_post_admission_refresh_test src/ck3_12003_post_admission_refresh_test.cpp)
  target_link_libraries(xar_bridge_ck3_12003_current_post_admission_refresh_test PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_bridge_ck3_12003_current_post_admission_refresh_test PRIVATE include)
  target_compile_features(xar_bridge_ck3_12003_current_post_admission_refresh_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12003_current_post_admission_refresh_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12003_current_post_admission_refresh_test PRIVATE /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_ck3_12003_current_post_admission_refresh_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_ck3_12003_current_post_admission_refresh_test COMMAND xar_bridge_ck3_12003_current_post_admission_refresh_test --wire-dir
    "${CMAKE_CURRENT_BINARY_DIR}/current-post-admission-refresh-wire")
endif()
