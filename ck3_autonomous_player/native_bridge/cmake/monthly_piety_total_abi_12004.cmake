if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_monthly_piety_total_abi_test
    src/ck3_12004_monthly_piety_total_abi_test.cpp
    src/ck3_12004_campaign.cpp
    src/ck3_12002_nonwar_metrics.cpp
    src/ck3_12004_council_task_owner_monthly_piety.cpp)
  target_include_directories(xar_ck3_12004_monthly_piety_total_abi_test PRIVATE include src)
  target_compile_features(xar_ck3_12004_monthly_piety_total_abi_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_monthly_piety_total_abi_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12004_monthly_piety_total_abi_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_monthly_piety_total_abi
    COMMAND xar_ck3_12004_monthly_piety_total_abi_test
      "${CMAKE_BINARY_DIR}/wire/ck3_12004_monthly_piety_total_abi")
  set_tests_properties(xar_ck3_12004_monthly_piety_total_abi PROPERTIES TIMEOUT 15)
endif()
