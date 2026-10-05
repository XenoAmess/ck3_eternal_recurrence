# Root owns the only native compilation and first new CTest.
if(BUILD_TESTING AND WIN32)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  set(XAR_ORDINARY_STAT_WIRE_DIR "${CMAKE_BINARY_DIR}/ck3_12003_ordinary_stat_inputs_wire")
  set(XAR_ORDINARY_STAT_SERIALIZER "${XAR_ORDINARY_STAT_WIRE_DIR}/production_regiment_serializer.cpp")
  add_custom_command(
    OUTPUT "${XAR_ORDINARY_STAT_SERIALIZER}"
    COMMAND "${Python3_EXECUTABLE}" -B
      "${CMAKE_CURRENT_SOURCE_DIR}/tests/project_initialization_context_serializer.py"
      --source "${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp"
      --output "${XAR_ORDINARY_STAT_SERIALIZER}"
      --receipt "${XAR_ORDINARY_STAT_WIRE_DIR}/SERIALIZER-PROJECTION.json"
    DEPENDS src/bridge.cpp tests/project_initialization_context_serializer.py
      tests/project_knight_context_serializer.py VERBATIM)
  add_executable(xar_ck3_12003_ordinary_stat_inputs_test
    src/ck3_12002_combat.cpp tests/ordinary_stat_inputs_12003_test.cpp
    "${XAR_ORDINARY_STAT_SERIALIZER}")
  target_include_directories(xar_ck3_12003_ordinary_stat_inputs_test PRIVATE include)
  target_compile_features(xar_ck3_12003_ordinary_stat_inputs_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_ordinary_stat_inputs_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_ordinary_stat_inputs_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_ordinary_stat_inputs_test
    COMMAND xar_ck3_12003_ordinary_stat_inputs_test "${XAR_ORDINARY_STAT_WIRE_DIR}")
endif()
