# The actual4 startup hook and ArmyStrength serializer share this owned journal.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_actual_loss_writer_journal.cpp
  src/county_primary_direct_owner_at_writer_12004.cpp)

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

# One source-exact nonzero allocator scope, separate from the default writer.
option(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004
  "Observe actual4 residual request source inside the existing loss journal" OFF)
if(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_12004_residual_parent_hook.cpp)
  target_compile_definitions(xar_ck3_12002_runtime PRIVATE XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004=1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004=1)
endif()
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_residual_parent_context_test EXCLUDE_FROM_ALL
    src/ck3_12004_residual_parent_context_test.cpp)
  target_link_libraries(xar_ck3_12004_residual_parent_context_test PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12004_residual_parent_context_test PRIVATE include)
  target_compile_features(xar_ck3_12004_residual_parent_context_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_residual_parent_context_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
    target_compile_definitions(xar_ck3_12004_residual_parent_context_test PRIVATE XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004=1)
  endif()
  if(XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004)
    target_compile_definitions(xar_ck3_12004_residual_parent_context_test PRIVATE XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004=1)
  endif()
  if(MSVC)
    target_compile_options(xar_ck3_12004_residual_parent_context_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_residual_parent_context_test
    COMMAND xar_ck3_12004_residual_parent_context_test
      "${CMAKE_CURRENT_BINARY_DIR}/wire/residual-parent-12004/NATIVE-WIRE.json")
endif()

# Captures the actual county primary caller registers at the existing writer
# entry; no additional native detour. Legacy/default writer remains unchanged.
option(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004
  "Observe actual county primary invocation Army at the existing writer" OFF)
if(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
  if(NOT MSVC OR NOT WIN32 OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "County primary entry capture requires Windows x64 MSVC/MASM")
  endif()
  enable_language(ASM_MASM)
  # Avoid inheriting Runtime CXX-only /std,/EHsc options into ml64.
  add_library(xar_county_primary_writer_thunk_12004 OBJECT src/county_primary_writer_entry_12004.asm)
  target_sources(xar_ck3_12002_runtime PRIVATE src/county_primary_owner_at_writer_12004.cpp
    $<TARGET_OBJECTS:xar_county_primary_writer_thunk_12004>)
  target_compile_definitions(xar_ck3_12002_runtime PRIVATE XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004=1)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004=1)
endif()

# New focused cold target; no CK3 loading/patching. Requires new owner code ON.
if(BUILD_TESTING AND XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
  add_executable(xar_test_county_primary_direct_owner_v2_12004 EXCLUDE_FROM_ALL
    src/county_primary_direct_owner_v2_12004_test.cpp src/county_primary_writer_fixture_entry_12004.asm)
  target_link_libraries(xar_test_county_primary_direct_owner_v2_12004 PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_test_county_primary_direct_owner_v2_12004 PRIVATE include)
  target_compile_features(xar_test_county_primary_direct_owner_v2_12004 PRIVATE cxx_std_20)
  target_compile_definitions(xar_test_county_primary_direct_owner_v2_12004 PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_compile_options(xar_test_county_primary_direct_owner_v2_12004 PRIVATE
    "$<$<COMPILE_LANGUAGE:CXX>:/W4;/WX;/permissive-;/EHsc;/utf-8;/UNDEBUG>")
  add_test(NAME xar_test_county_primary_direct_owner_v2_12004
    COMMAND xar_test_county_primary_direct_owner_v2_12004
      "${CMAKE_CURRENT_BINARY_DIR}/wire/county-primary-direct-owner-v2/NATIVE-WIRE.json")
  add_executable(xar_test_county_primary_owner_12004 EXCLUDE_FROM_ALL
    src/county_primary_owner_12004_test.cpp src/county_primary_writer_fixture_entry_12004.asm)
  target_link_libraries(xar_test_county_primary_owner_12004 PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_test_county_primary_owner_12004 PRIVATE include)
  target_compile_features(xar_test_county_primary_owner_12004 PRIVATE cxx_std_20)
  target_compile_definitions(xar_test_county_primary_owner_12004 PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_compile_options(xar_test_county_primary_owner_12004 PRIVATE
    "$<$<COMPILE_LANGUAGE:CXX>:/W4;/WX;/permissive-;/EHsc;/utf-8;/UNDEBUG>")
  add_test(NAME xar_test_county_primary_owner_12004
    COMMAND xar_test_county_primary_owner_12004)
endif()
