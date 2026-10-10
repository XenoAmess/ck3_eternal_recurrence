if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_council_task_owner_monthly_piety_test
    src/ck3_12004_council_task_owner_monthly_piety.cpp
    src/ck3_12004_council_task_owner_monthly_piety_test.cpp)
  target_include_directories(xar_ck3_12004_council_task_owner_monthly_piety_test PRIVATE include)
  target_compile_features(xar_ck3_12004_council_task_owner_monthly_piety_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_council_task_owner_monthly_piety_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12004_council_task_owner_monthly_piety_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_council_task_owner_monthly_piety
    COMMAND xar_ck3_12004_council_task_owner_monthly_piety_test)
endif()
