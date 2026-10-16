# Explicit cold test for the shared native preview typed failure branches.
# It never binds/opens CK3; run only the new three-case selector deliberately.
if(BUILD_TESTING)
  add_executable(xar_test_military_preview_unavailable_reasons EXCLUDE_FROM_ALL
    src/ck3_12002_military_test.cpp
    src/ck3_12002_military.cpp
    src/ck3_12002_commands.cpp
    src/ck3_12002.cpp)
  target_include_directories(xar_test_military_preview_unavailable_reasons PRIVATE include)
  target_compile_features(xar_test_military_preview_unavailable_reasons PRIVATE cxx_std_20)
  target_compile_definitions(xar_test_military_preview_unavailable_reasons PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_test_military_preview_unavailable_reasons PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  else()
    target_compile_options(xar_test_military_preview_unavailable_reasons PRIVATE -UNDEBUG)
  endif()
endif()
