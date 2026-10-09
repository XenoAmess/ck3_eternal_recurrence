# The actual4 startup hook and ArmyStrength serializer share this owned journal.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_actual_loss_writer_journal.cpp)

if(BUILD_TESTING AND WIN32)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  add_executable(xar_ck3_12004_actual_loss_writer_whole_test EXCLUDE_FROM_ALL
    src/ck3_12004_actual_loss_writer_whole_test.cpp)
  target_link_libraries(xar_ck3_12004_actual_loss_writer_whole_test PRIVATE
    xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12004_actual_loss_writer_whole_test PRIVATE
    include)
  target_compile_features(xar_ck3_12004_actual_loss_writer_whole_test PRIVATE
    cxx_std_20)
  target_compile_definitions(xar_ck3_12004_actual_loss_writer_whole_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_actual_loss_writer_whole_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()

  set(XAR_ACTUAL_LOSS_WRITER_WIRE_12004
    "${CMAKE_CURRENT_BINARY_DIR}/wire/actual-loss-writer-12004/NATIVE-WHOLE.json")
  add_test(NAME xar_ck3_12004_actual_loss_writer_whole_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_actual_loss_writer_whole_test>
      --wire-out "${XAR_ACTUAL_LOSS_WRITER_WIRE_12004}")
  set_tests_properties(xar_ck3_12004_actual_loss_writer_whole_test PROPERTIES
    FIXTURES_SETUP actual_loss_writer_whole_12004)

  add_test(NAME xar_ck3_12004_actual_loss_writer_registered_mcp
    COMMAND "${Python3_EXECUTABLE}" -B -X utf8
      "${CMAKE_CURRENT_SOURCE_DIR}/../tests/unit/test_actual_loss_writer_registered_mcp_12004.py"
      --source-root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
      --native-wire "${XAR_ACTUAL_LOSS_WRITER_WIRE_12004}"
      --output-dir "${CMAKE_CURRENT_BINARY_DIR}/wire/actual-loss-writer-12004/registered-consumer")
  set_tests_properties(xar_ck3_12004_actual_loss_writer_registered_mcp PROPERTIES
    FIXTURES_REQUIRED actual_loss_writer_whole_12004)
endif()
