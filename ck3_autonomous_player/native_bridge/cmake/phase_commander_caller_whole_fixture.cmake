# Root includes after phase_role_whole_fixture.cmake. Reuse its seed/wire
# preparation, but do not run its original three-scene executable/consumer.
if(NOT DEFINED _phase_role_seed OR NOT DEFINED _phase_role_wire)
  message(FATAL_ERROR "Include phase_role_whole_fixture.cmake before this new single-sample target")
endif()
add_executable(xar_ck3_12004_phase_commander_caller_whole_fixture EXCLUDE_FROM_ALL
  src/ck3_12004_phase_event_commander_caller_whole_fixture.cpp
  "${_phase_role_seed}" "${_phase_role_wire}")
target_include_directories(xar_ck3_12004_phase_commander_caller_whole_fixture PRIVATE
  include "${XAR_PHASE_ROLE_FIXTURE_DIR}")
target_compile_features(xar_ck3_12004_phase_commander_caller_whole_fixture PRIVATE cxx_std_20)
target_compile_definitions(xar_ck3_12004_phase_commander_caller_whole_fixture PRIVATE NOMINMAX)
if(MSVC)
  target_compile_options(xar_ck3_12004_phase_commander_caller_whole_fixture PRIVATE /W4 /WX /permissive- /EHsc)
endif()
