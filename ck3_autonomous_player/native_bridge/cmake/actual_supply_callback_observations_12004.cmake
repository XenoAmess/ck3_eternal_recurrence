option(XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004
  "Observe thread-scoped natural supply callback/writer identity and writer-entry stock" OFF)
if(XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004)
  target_compile_definitions(xar_ck3_12002_runtime PRIVATE
    XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004=1)
endif()

# This small producer compiles the same two wrapper TUs with the join enabled.
# It does not link/launch the bridge DLL or invoke the native game EXE.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_supply_parent_join_whole_test EXCLUDE_FROM_ALL
    src/ck3_12004_supply_parent_join_whole_test.cpp
    src/ck3_12004_actual_supply_callback_journal.cpp
    src/ck3_12004_actual_loss_writer_journal.cpp)
  # The event-time province read uses the real resolver from the runtime archive.
  # Keep the two local join-enabled wrappers; no bridge DLL or game is launched.
  target_link_libraries(xar_ck3_12004_supply_parent_join_whole_test
    PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12004_supply_parent_join_whole_test PRIVATE include)
  target_compile_features(xar_ck3_12004_supply_parent_join_whole_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_supply_parent_join_whole_test PRIVATE
    XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004=1 NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_supply_parent_join_whole_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  set(XAR_SUPPLY_PARENT_JOIN_WIRE_12004
    "${CMAKE_CURRENT_BINARY_DIR}/supply-parent-join-whole-12004.json")
  add_test(NAME xar_ck3_12004_supply_parent_join_whole_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_supply_parent_join_whole_test>
      "${XAR_SUPPLY_PARENT_JOIN_WIRE_12004}")
  set_tests_properties(xar_ck3_12004_supply_parent_join_whole_test PROPERTIES
    FIXTURES_SETUP supply_parent_join_whole_12004)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  add_test(NAME xar_ck3_12004_supply_parent_join_preserved_wire_consumer
    COMMAND "${Python3_EXECUTABLE}" -B -O
      "${CMAKE_CURRENT_SOURCE_DIR}/../tests/unit/test_actual_supply_parent_join_12004.py"
      --native-wire "${XAR_SUPPLY_PARENT_JOIN_WIRE_12004}")
  set_tests_properties(xar_ck3_12004_supply_parent_join_preserved_wire_consumer PROPERTIES
    FIXTURES_REQUIRED supply_parent_join_whole_12004)
endif()

# The natural callback journal is installed by the same exact-build startup and
# consumed by the existing whole ArmyStrength serializer.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_actual_supply_callback_journal.cpp)

if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12004_actual_supply_callback_whole_test
    EXCLUDE_FROM_ALL src/ck3_12004_actual_supply_callback_whole_test.cpp)
  target_link_libraries(xar_bridge_ck3_12004_actual_supply_callback_whole_test
    PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_bridge_ck3_12004_actual_supply_callback_whole_test
    PRIVATE include)
  target_compile_features(xar_bridge_ck3_12004_actual_supply_callback_whole_test
    PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12004_actual_supply_callback_whole_test
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12004_actual_supply_callback_whole_test
      PRIVATE /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()

  set(XAR_ACTUAL_SUPPLY_CALLBACK_WIRE_12004
    "${CMAKE_CURRENT_BINARY_DIR}/wire/actual-supply-callback-12004/NATIVE-WHOLE.json")
  add_test(NAME xar_bridge_ck3_12004_actual_supply_callback_whole_test
    COMMAND $<TARGET_FILE:xar_bridge_ck3_12004_actual_supply_callback_whole_test>
      --wire-out "${XAR_ACTUAL_SUPPLY_CALLBACK_WIRE_12004}")
  set_tests_properties(xar_bridge_ck3_12004_actual_supply_callback_whole_test
    PROPERTIES FIXTURES_SETUP actual_supply_callback_whole_12004)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  add_test(NAME xar_bridge_ck3_12004_actual_supply_callback_registered_mcp
    COMMAND "${Python3_EXECUTABLE}" -B -X utf8
      "${CMAKE_CURRENT_SOURCE_DIR}/../tests/unit/test_actual_supply_callback_registered_mcp_12004.py"
      --source-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-wire "${XAR_ACTUAL_SUPPLY_CALLBACK_WIRE_12004}"
      --output-dir "${CMAKE_CURRENT_BINARY_DIR}/wire/actual-supply-callback-12004/registered-consumer")
  set_tests_properties(xar_bridge_ck3_12004_actual_supply_callback_registered_mcp
    PROPERTIES FIXTURES_REQUIRED actual_supply_callback_whole_12004)
endif()
