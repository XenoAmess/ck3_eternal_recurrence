# Actual original roster and conditional current standalone admission.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_daily_assault_roster_admission_12003_test
    src/ck3_12003_daily_assault_roster_admission_test.cpp)
  target_link_libraries(xar_bridge_daily_assault_roster_admission_12003_test PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_bridge_daily_assault_roster_admission_12003_test PRIVATE include)
  target_compile_features(xar_bridge_daily_assault_roster_admission_12003_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_daily_assault_roster_admission_12003_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_daily_assault_roster_admission_12003_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_daily_assault_roster_admission_12003_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_daily_assault_roster_admission_12003_test
    COMMAND xar_bridge_daily_assault_roster_admission_12003_test
      "${CMAKE_CURRENT_BINARY_DIR}/daily-assault-roster-wire")
endif()
