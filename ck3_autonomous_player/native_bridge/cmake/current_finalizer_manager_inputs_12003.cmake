# Additive current manager source. Root integrates this include last, once.
# g104 first link failed; this source-only closure repair has not been built/run.
get_property(finalizer_manager_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(finalizer_manager_target IN LISTS finalizer_manager_targets)
  get_target_property(finalizer_manager_sources ${finalizer_manager_target} SOURCES)
  if(("src/ck3_12002_battle.cpp" IN_LIST finalizer_manager_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_battle.cpp" IN_LIST finalizer_manager_sources) AND
     NOT "src/battle_current_finalizer_manager_inputs_reader_12003.cpp" IN_LIST finalizer_manager_sources)
    target_sources(${finalizer_manager_target} PRIVATE
      src/battle_current_finalizer_manager_inputs_reader_12003.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  add_executable(xar_ck3_12003_current_finalizer_manager_inputs
    src/battle_control_snapshot_v1_mailbox.cpp
    # The actual mailbox references these ck3_11906 adapter implementations.
    # Reuse their existing game-access source closure, without fixture facades.
    src/ck3_11906.cpp
    src/battle_terminal_journal_v1.cpp
    src/g2_truce_preview_entry_observer_v1.cpp
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_surrender_truce_v1.cpp
    src/raiktor_actual_truce_expiry_v1.cpp
    src/ck3_12003_battle_finalizer_manager_inputs_test.cpp)
  target_link_libraries(xar_ck3_12003_current_finalizer_manager_inputs PRIVATE
    xar_ck3_12002_runtime user32)
  target_include_directories(xar_ck3_12003_current_finalizer_manager_inputs PRIVATE include)
  target_compile_features(xar_ck3_12003_current_finalizer_manager_inputs PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_finalizer_manager_inputs PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE NDEBUG)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_finalizer_manager_inputs PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /utf-8)
    target_link_options(xar_ck3_12003_current_finalizer_manager_inputs PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_finalizer_manager_inputs_first
    COMMAND xar_ck3_12003_current_finalizer_manager_inputs
      "${CMAKE_CURRENT_BINARY_DIR}/current-finalizer-manager-inputs-wire")
  set_tests_properties(xar_ck3_12003_current_finalizer_manager_inputs_first PROPERTIES
    FIXTURES_SETUP current_finalizer_manager_inputs_wire)
  add_test(NAME xar_ck3_12003_current_finalizer_manager_inputs_service_compound
    COMMAND ${Python3_EXECUTABLE} -B -X utf8
      "${CMAKE_CURRENT_SOURCE_DIR}/../tests/unit/test_current_finalizer_manager_inputs_v1_compound.py"
      --projection-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-dir "${CMAKE_CURRENT_BINARY_DIR}/current-finalizer-manager-inputs-wire"
      --output-dir "${CMAKE_CURRENT_BINARY_DIR}/current-finalizer-manager-inputs-service")
  set_tests_properties(xar_ck3_12003_current_finalizer_manager_inputs_service_compound PROPERTIES
    FIXTURES_REQUIRED current_finalizer_manager_inputs_wire)
endif()
