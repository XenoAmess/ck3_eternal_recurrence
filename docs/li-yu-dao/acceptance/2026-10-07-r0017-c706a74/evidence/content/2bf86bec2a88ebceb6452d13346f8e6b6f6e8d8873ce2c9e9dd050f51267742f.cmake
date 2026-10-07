# Actual raw vector headers for conditional normal-return record release.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_daily_assault_release_headers
    src/ck3_12003_daily_assault_release_headers_test.cpp)
  target_link_libraries(xar_ck3_12003_daily_assault_release_headers PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12003_daily_assault_release_headers PRIVATE include)
  target_compile_features(xar_ck3_12003_daily_assault_release_headers PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_daily_assault_release_headers PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_daily_assault_release_headers PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_daily_assault_release_headers PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_daily_assault_release_headers
    COMMAND xar_ck3_12003_daily_assault_release_headers
      "${CMAKE_CURRENT_BINARY_DIR}/daily-assault-release-header-wire")
endif()
