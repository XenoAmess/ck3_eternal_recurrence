# Exact .3 loaded battle cap observation in every actual battle-control reader.
get_property(current_warscore_caps_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(current_warscore_caps_target IN LISTS current_warscore_caps_targets)
  get_target_property(current_warscore_caps_sources ${current_warscore_caps_target} SOURCES)
  if(("src/ck3_12002_battle.cpp" IN_LIST current_warscore_caps_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_battle.cpp" IN_LIST current_warscore_caps_sources) AND
     NOT "src/battle_current_warscore_caps_v1.cpp" IN_LIST current_warscore_caps_sources)
    target_sources(${current_warscore_caps_target} PRIVATE
      src/battle_current_warscore_caps_v1.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  add_executable(xar_ck3_12003_current_warscore_caps
    # Compile this new capture path directly, including its new optional leaf.
    # Do not qualify it through an older runtime archive's battle reader.
    src/ck3_12002_battle.cpp
    src/battle_current_warscore_caps_v1.cpp
    src/battle_control_snapshot_v1_mailbox.cpp
    # Actual mailbox adapter/helper closure already proved by the manager FIRST.
    src/ck3_11906.cpp
    src/battle_terminal_journal_v1.cpp
    src/g2_truce_preview_entry_observer_v1.cpp
    src/raiktor_war_bound_regiment_v1.cpp
    src/raiktor_surrender_truce_v1.cpp
    src/raiktor_actual_truce_expiry_v1.cpp
    src/current_first_heir_relationship_v1.cpp
    src/marriage_candidate_alliance_projection_v1.cpp
    src/marriage_native_outcome_classifier_v1.cpp
    tests/ck3_12003_battle_current_warscore_caps_test.cpp)
  target_link_libraries(xar_ck3_12003_current_warscore_caps PRIVATE
    xar_ck3_12002_runtime user32)
  target_include_directories(xar_ck3_12003_current_warscore_caps PRIVATE include)
  target_compile_features(xar_ck3_12003_current_warscore_caps PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_warscore_caps PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE NDEBUG)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_warscore_caps PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /utf-8)
    target_link_options(xar_ck3_12003_current_warscore_caps PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_warscore_caps_first
    COMMAND xar_ck3_12003_current_warscore_caps
      "${CMAKE_CURRENT_BINARY_DIR}/current-warscore-caps-wire")
  set_tests_properties(xar_ck3_12003_current_warscore_caps_first PROPERTIES
    FIXTURES_SETUP current_warscore_caps_wire)
  add_test(NAME xar_ck3_12003_current_warscore_caps_service_compound
    COMMAND ${Python3_EXECUTABLE} -B -X utf8
      "${CMAKE_CURRENT_SOURCE_DIR}/../tests/unit/test_current_warscore_caps_v1_compound.py"
      --source-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-dir "${CMAKE_CURRENT_BINARY_DIR}/current-warscore-caps-wire"
      --output-dir "${CMAKE_CURRENT_BINARY_DIR}/current-warscore-caps-service")
  set_tests_properties(xar_ck3_12003_current_warscore_caps_service_compound PROPERTIES
    FIXTURES_REQUIRED current_warscore_caps_wire)
endif()
