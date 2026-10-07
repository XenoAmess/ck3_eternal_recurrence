# New FIRST only; reuse held V2 seed, do not execute historical compounds.
if(NOT DEFINED _phase_role_seed)
  message(FATAL_ERROR "Include phase_role_whole_fixture.cmake before this target")
endif()
set(_commander_trigger_wire "${XAR_PHASE_ROLE_FIXTURE_DIR}/commander-trigger-production-whole-serializer.cpp")
add_custom_command(OUTPUT "${_commander_trigger_wire}"
  COMMAND "${Python3_EXECUTABLE}" -B
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/project_phase_commander_trigger_whole_serializer.py"
    --source "${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp"
    --output "${_commander_trigger_wire}"
    --receipt "${XAR_PHASE_ROLE_FIXTURE_DIR}/COMMANDER-TRIGGER-SERIALIZER-PROJECTION.json"
  DEPENDS src/bridge.cpp tests/project_phase_commander_trigger_whole_serializer.py
    tests/project_knight_context_serializer.py
    include/xar_bridge/phase_event_commander_trigger_conditions_v1_serializer.hpp VERBATIM)
add_executable(xar_ck3_12004_phase_commander_trigger_whole_fixture EXCLUDE_FROM_ALL
  src/ck3_12004_phase_event_commander_trigger_whole_fixture.cpp
  "${_phase_role_seed}" "${_commander_trigger_wire}")
target_include_directories(xar_ck3_12004_phase_commander_trigger_whole_fixture PRIVATE
  include "${XAR_PHASE_ROLE_FIXTURE_DIR}")
target_compile_features(xar_ck3_12004_phase_commander_trigger_whole_fixture PRIVATE cxx_std_20)
target_compile_definitions(xar_ck3_12004_phase_commander_trigger_whole_fixture PRIVATE NOMINMAX)
if(MSVC)
  target_compile_options(xar_ck3_12004_phase_commander_trigger_whole_fixture PRIVATE /W4 /WX /permissive- /EHsc)
endif()
