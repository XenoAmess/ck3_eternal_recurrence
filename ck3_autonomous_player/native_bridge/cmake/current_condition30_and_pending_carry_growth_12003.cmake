# New exact-build current condition observation and conditional physical pending placement.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12003_army_condition30_inputs_test
    src/ck3_12003_army_condition30_inputs_test.cpp)
  target_link_libraries(xar_bridge_ck3_12003_army_condition30_inputs_test PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_bridge_ck3_12003_army_condition30_inputs_test PRIVATE include)
  target_compile_features(xar_bridge_ck3_12003_army_condition30_inputs_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12003_army_condition30_inputs_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12003_army_condition30_inputs_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_ck3_12003_army_condition30_inputs_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_ck3_12003_army_condition30_inputs_test
    COMMAND xar_bridge_ck3_12003_army_condition30_inputs_test --wire-dir
      "${CMAKE_CURRENT_BINARY_DIR}/army-condition30-inputs-wire")
endif()

# External integration recipe only; Root owns repository CMake/CI edits.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12003_pre_date_pending_carry_growth_test
    src/ck3_12003_pre_date_pending_carry_growth_test.cpp)
  target_link_libraries(xar_bridge_ck3_12003_pre_date_pending_carry_growth_test
    PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_bridge_ck3_12003_pre_date_pending_carry_growth_test PRIVATE include)
  target_compile_features(xar_bridge_ck3_12003_pre_date_pending_carry_growth_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12003_pre_date_pending_carry_growth_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12003_pre_date_pending_carry_growth_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_ck3_12003_pre_date_pending_carry_growth_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_ck3_12003_pre_date_pending_carry_growth_test
    COMMAND xar_bridge_ck3_12003_pre_date_pending_carry_growth_test --wire-dir
      "${CMAKE_CURRENT_BINARY_DIR}/pre-date-pending-carry-growth-wire")
endif()
