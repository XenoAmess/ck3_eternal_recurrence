if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_phase_berserker_chance_inputs_test
    tests/phase_berserker_chance_12003_test.cpp
    src/ck3_12002_phase_character.cpp)
  target_include_directories(xar_ck3_12003_phase_berserker_chance_inputs_test PRIVATE include)
  target_compile_features(xar_ck3_12003_phase_berserker_chance_inputs_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_phase_berserker_chance_inputs_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_12003_phase_berserker_chance_inputs_test PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12003_phase_berserker_chance_inputs_test
    COMMAND xar_ck3_12003_phase_berserker_chance_inputs_test
      "${CMAKE_CURRENT_BINARY_DIR}/ck3_12003_phase_berserker_chance_inputs_wire")
endif()
