# One new connected application -> actual loss journal -> ArmyStrength wire.
# Runtime providers are reused from the coordinator's canonical increment.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_battle_casualty_observer.cpp)

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_battle_casualty_physical_debit_whole
    tests/battle_casualty_physical_debit_whole_fixture.cpp)
  target_include_directories(xar_ck3_12004_battle_casualty_physical_debit_whole
    PRIVATE include)
  target_link_libraries(xar_ck3_12004_battle_casualty_physical_debit_whole
    PRIVATE xar_ck3_12002_runtime)
  target_compile_features(xar_ck3_12004_battle_casualty_physical_debit_whole
    PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_battle_casualty_physical_debit_whole
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_battle_casualty_physical_debit_whole
      PRIVATE /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_battle_casualty_physical_debit_whole
    COMMAND xar_ck3_12004_battle_casualty_physical_debit_whole --wire-out
      "${CMAKE_BINARY_DIR}/wire/battle-casualty-physical-debit-12004-whole.json")
  find_package(Python3 COMPONENTS Interpreter QUIET)
  if(Python3_Interpreter_FOUND)
    add_test(NAME xar_ck3_12004_battle_casualty_physical_debit_registered_mcp
      COMMAND "${CMAKE_COMMAND}" -E env
        "CK3_BATTLE_CASUALTY_PHYSICAL_DEBIT_12004_MCP_WIRE_DIR=${CMAKE_BINARY_DIR}/wire"
        "${Python3_EXECUTABLE}" -B
        "${CMAKE_CURRENT_SOURCE_DIR}/../tests/unit/test_battle_casualty_physical_debit_registered_mcp_12004.py")
    set_tests_properties(
      xar_ck3_12004_battle_casualty_physical_debit_registered_mcp PROPERTIES
      DEPENDS xar_ck3_12004_battle_casualty_physical_debit_whole)
  endif()
endif()
