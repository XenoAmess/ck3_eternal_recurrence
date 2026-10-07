# Header-only current-table collector is compiled with the existing army reader.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_daily_assault_active_table_12003_test
    src/ck3_12003_daily_assault_active_table_test.cpp)
  target_link_libraries(xar_bridge_daily_assault_active_table_12003_test PRIVATE
    xar_ck3_12002_runtime)
  target_compile_features(xar_bridge_daily_assault_active_table_12003_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_bridge_daily_assault_active_table_12003_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_daily_assault_active_table_12003_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_daily_assault_active_table_12003_test
    COMMAND xar_bridge_daily_assault_active_table_12003_test
      "${CMAKE_CURRENT_BINARY_DIR}/daily-assault-active-table-wire")
endif()
