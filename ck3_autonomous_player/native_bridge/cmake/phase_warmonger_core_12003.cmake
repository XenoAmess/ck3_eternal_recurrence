if(BUILD_TESTING AND WIN32)
  set(XAR_PHASE_WARMONGER_WIRE_DIR "${CMAKE_BINARY_DIR}/ck3_12003_phase_warmonger_core_wire")
  add_executable(xar_ck3_12003_phase_warmonger_core_test
    tests/phase_warmonger_core_12003_test.cpp)
  target_include_directories(xar_ck3_12003_phase_warmonger_core_test PRIVATE include)
  target_compile_features(xar_ck3_12003_phase_warmonger_core_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_phase_warmonger_core_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_phase_warmonger_core_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_phase_warmonger_core_test
    COMMAND xar_ck3_12003_phase_warmonger_core_test "${XAR_PHASE_WARMONGER_WIRE_DIR}")
endif()
