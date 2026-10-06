# Root alone builds and executes the first new CTest; no old cases are rerun.
if(BUILD_TESTING AND WIN32)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  set(XAR_PHASE_RITE_WIRE_DIR "${CMAKE_BINARY_DIR}/ck3_12003_phase_rite_parameters_wire")
  set(XAR_PHASE_RITE_SERIALIZER "${XAR_PHASE_RITE_WIRE_DIR}/production_candidate_serializer.cpp")
  add_custom_command(
    OUTPUT "${XAR_PHASE_RITE_SERIALIZER}"
    COMMAND "${Python3_EXECUTABLE}" -B
      "${CMAKE_CURRENT_SOURCE_DIR}/tests/project_phase_rite_parameters_serializer.py"
      --source "${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp"
      --output "${XAR_PHASE_RITE_SERIALIZER}"
      --receipt "${XAR_PHASE_RITE_WIRE_DIR}/SERIALIZER-PROJECTION.json"
    DEPENDS src/bridge.cpp tests/project_phase_rite_parameters_serializer.py
      tests/project_knight_context_serializer.py
      include/xar_bridge/phase_rite_parameters_v1_serializer.hpp
      include/xar_bridge/phase_warmonger_core_v1_serializer.hpp
      include/xar_bridge/phase_warmonger_core_v1.hpp
      include/xar_bridge/phase_berserker_validity_inputs_v1_serializer.hpp
      include/xar_bridge/phase_berserker_validity_inputs_v1.hpp VERBATIM)
  add_executable(xar_ck3_12003_phase_rite_parameters_test
    src/ck3_12002_combat.cpp tests/phase_rite_parameters_12003_test.cpp
    "${XAR_PHASE_RITE_SERIALIZER}")
  target_include_directories(xar_ck3_12003_phase_rite_parameters_test PRIVATE include)
  target_compile_features(xar_ck3_12003_phase_rite_parameters_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_phase_rite_parameters_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_phase_rite_parameters_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_phase_rite_parameters_test
    COMMAND xar_ck3_12003_phase_rite_parameters_test "${XAR_PHASE_RITE_WIRE_DIR}")
endif()
