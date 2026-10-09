# The real startup hooks and V2 combat-input serializer share this owned ring.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_knight_stat_consumption.cpp
  src/ck3_12004_knight_stat_consumption_serializer.cpp)

if(BUILD_TESTING AND WIN32)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  set(XAR_KNIGHT_STAT_CONSUMPTION_WIRE_DIR_12004
    "${CMAKE_CURRENT_BINARY_DIR}/wire/knight-stat-consumption-12004")
  set(_knight_consumption_serializer
    "${XAR_KNIGHT_STAT_CONSUMPTION_WIRE_DIR_12004}/production-combat-inputs-serializer.cpp")
  add_custom_command(OUTPUT "${_knight_consumption_serializer}"
    COMMAND "${Python3_EXECUTABLE}" -B
      "${CMAKE_CURRENT_SOURCE_DIR}/tests/project_phase_effect_emptiness_whole_serializer.py"
      --source "${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp"
      --output "${_knight_consumption_serializer}"
      --receipt "${XAR_KNIGHT_STAT_CONSUMPTION_WIRE_DIR_12004}/SERIALIZER-PROJECTION.json"
    DEPENDS src/bridge.cpp tests/project_phase_effect_emptiness_whole_serializer.py
      tests/project_knight_context_serializer.py
      include/xar_bridge/phase_event_commander_chance_weights_v1_serializer.hpp
    VERBATIM)
  add_executable(xar_knight_stat_consumption_12004_whole EXCLUDE_FROM_ALL
    tests/knight_stat_consumption_12004_whole_fixture.cpp
    "${_knight_consumption_serializer}")
  target_link_libraries(xar_knight_stat_consumption_12004_whole PRIVATE
    xar_ck3_12002_runtime)
  target_include_directories(xar_knight_stat_consumption_12004_whole PRIVATE include)
  target_compile_features(xar_knight_stat_consumption_12004_whole PRIVATE cxx_std_20)
  target_compile_definitions(xar_knight_stat_consumption_12004_whole PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_knight_stat_consumption_12004_whole PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()

  add_test(NAME xar_knight_stat_consumption_12004_whole
    COMMAND $<TARGET_FILE:xar_knight_stat_consumption_12004_whole>
      "${XAR_KNIGHT_STAT_CONSUMPTION_WIRE_DIR_12004}")
  set_tests_properties(xar_knight_stat_consumption_12004_whole PROPERTIES
    FIXTURES_SETUP knight_stat_consumption_12004)
  add_test(NAME xar_knight_stat_consumption_12004_registered_mcp
    COMMAND "${Python3_EXECUTABLE}" -B -X utf8 -m pytest -q
      "${CMAKE_CURRENT_SOURCE_DIR}/../tests/unit/test_knight_stat_consumption_registered_mcp_12004.py::test_knight_stat_consumption_registered_mcp_12004_whole_packets")
  set_tests_properties(xar_knight_stat_consumption_12004_registered_mcp PROPERTIES
    FIXTURES_REQUIRED knight_stat_consumption_12004
    ENVIRONMENT "CK3_KNIGHT_STAT_CONSUMPTION_12004_MCP_WIRE_DIR=${XAR_KNIGHT_STAT_CONSUMPTION_WIRE_DIR_12004}"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../..")
endif()
