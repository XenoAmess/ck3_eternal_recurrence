# Focused source-closed first initialization stats; Root owns native compilation.
if(BUILD_TESTING AND WIN32)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
  set(XAR_INITIAL_CONTEXT_FIXTURE_DIR
    "${CMAKE_BINARY_DIR}/ck3_12003_initialization_context_stats_wire")
  set(XAR_INITIAL_CONTEXT_SERIALIZER
    "${XAR_INITIAL_CONTEXT_FIXTURE_DIR}/production_regiment_serializer.cpp")
  add_custom_command(
    OUTPUT "${XAR_INITIAL_CONTEXT_SERIALIZER}"
    COMMAND "${Python3_EXECUTABLE}" -B
      "${CMAKE_CURRENT_SOURCE_DIR}/tests/project_initialization_context_serializer.py"
      --source "${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp"
      --output "${XAR_INITIAL_CONTEXT_SERIALIZER}"
      --receipt "${XAR_INITIAL_CONTEXT_FIXTURE_DIR}/SERIALIZER-PROJECTION.json"
    DEPENDS src/bridge.cpp tests/project_initialization_context_serializer.py
      tests/project_knight_context_serializer.py
    VERBATIM)
  add_executable(xar_ck3_12003_initialization_context_stats_test
    src/ck3_12002_combat.cpp
    tests/initialization_context_stats_12003_test.cpp
    "${XAR_INITIAL_CONTEXT_SERIALIZER}")
  target_include_directories(xar_ck3_12003_initialization_context_stats_test PRIVATE include)
  target_compile_features(xar_ck3_12003_initialization_context_stats_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_initialization_context_stats_test PRIVATE NOMINMAX)
  if(MSVC)
    target_compile_options(xar_ck3_12003_initialization_context_stats_test PRIVATE
      /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_12003_initialization_context_stats_test
    COMMAND xar_ck3_12003_initialization_context_stats_test
      "${XAR_INITIAL_CONTEXT_FIXTURE_DIR}")
endif()
