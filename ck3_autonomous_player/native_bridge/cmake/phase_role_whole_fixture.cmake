# Root includes only after shared hooks are integrated. No implicit CTest.
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(XAR_PHASE_ROLE_FIXTURE_DIR
  "${CMAKE_CURRENT_BINARY_DIR}/phase-role-whole-fixture"
  CACHE PATH "Root-only loaded-role FIRST seed and literal production wire")
set(_phase_role_seed "${XAR_PHASE_ROLE_FIXTURE_DIR}/phase-role-base-seed.inc")
set(_phase_role_wire "${XAR_PHASE_ROLE_FIXTURE_DIR}/production-whole-v2-serializer.cpp")
add_custom_command(OUTPUT "${_phase_role_seed}"
  COMMAND "${Python3_EXECUTABLE}" -B
    "${CMAKE_CURRENT_SOURCE_DIR}/../tools/prepare_phase_role_whole_fixture.py"
    --base "${CMAKE_CURRENT_SOURCE_DIR}/../tests/fixtures/combat/live_814_12003_general_battle_v2.json"
    --out-dir "${XAR_PHASE_ROLE_FIXTURE_DIR}"
  DEPENDS ../tools/prepare_phase_role_whole_fixture.py
    ../tools/prepare_phase_calendar_whole_fixture.py
    ../tests/fixtures/combat/live_814_12003_general_battle_v2.json VERBATIM)
add_custom_command(OUTPUT "${_phase_role_wire}"
  COMMAND "${Python3_EXECUTABLE}" -B
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/project_phase_role_whole_serializer.py"
    --source "${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp"
    --output "${_phase_role_wire}"
    --receipt "${XAR_PHASE_ROLE_FIXTURE_DIR}/SERIALIZER-PROJECTION.json"
  DEPENDS src/bridge.cpp tests/project_phase_role_whole_serializer.py
    tests/project_knight_context_serializer.py
    include/xar_bridge/phase_event_role_compatibility_v1_serializer.hpp VERBATIM)
add_executable(xar_ck3_12004_phase_role_whole_fixture EXCLUDE_FROM_ALL
  src/ck3_12004_phase_event_role_whole_fixture.cpp
  "${_phase_role_seed}" "${_phase_role_wire}")
target_include_directories(xar_ck3_12004_phase_role_whole_fixture PRIVATE
  include "${XAR_PHASE_ROLE_FIXTURE_DIR}")
target_compile_features(xar_ck3_12004_phase_role_whole_fixture PRIVATE cxx_std_20)
target_compile_definitions(xar_ck3_12004_phase_role_whole_fixture PRIVATE NOMINMAX)
if(MSVC)
  target_compile_options(xar_ck3_12004_phase_role_whole_fixture PRIVATE /W4 /WX /permissive- /EHsc)
endif()
