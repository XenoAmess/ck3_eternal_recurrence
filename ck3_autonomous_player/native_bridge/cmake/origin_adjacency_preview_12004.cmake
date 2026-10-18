# One deliberate owned-memory fixture. No new production capability or option.
if(BUILD_TESTING)
  add_executable(xar_test_origin_adjacency_preview_12004 EXCLUDE_FROM_ALL
    tests/ck3_12004_origin_adjacency_test.cpp)
  target_include_directories(xar_test_origin_adjacency_preview_12004 PRIVATE include)
  target_compile_features(xar_test_origin_adjacency_preview_12004 PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_test_origin_adjacency_preview_12004 PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8)
  endif()
endif()
