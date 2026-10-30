if(WIN32 AND MSVC AND BUILD_TESTING)
  get_filename_component(_sway_common_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
  add_executable(xar_ck3_sway_common_callsite_failure_12004_test
    "${_sway_common_root}/tests/sway_common_termination_callsite_12004_failure_test.cpp"
    "${_sway_common_root}/tests/sway_common_termination_callsite_12004_fault_api.cpp"
    "${_sway_common_root}/tests/sway_common_termination_callsite_12004_end_bindings_fixture.cpp"
    "${_sway_common_root}/src/ck3_12002_sway_completion_termination.cpp"
    "${_sway_common_root}/src/sway_completion_causal_observer_12004.cpp"
    "${_sway_common_root}/src/sway_child_end_causal_path_12004.cpp"
    "${_sway_common_root}/src/ck3_12004_sway.cpp"
    "${_sway_common_root}/src/ck3_12002.cpp"
    "${_sway_common_root}/src/ck3_12003_abi_profile.cpp"
    "${_sway_common_root}/src/ck3_12004_abi_profile.cpp")
  target_include_directories(xar_ck3_sway_common_callsite_failure_12004_test PRIVATE
    "${_sway_common_root}/include" "${_sway_common_root}/research")
  target_compile_features(xar_ck3_sway_common_callsite_failure_12004_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_sway_common_callsite_failure_12004_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN)
  target_compile_options(xar_ck3_sway_common_callsite_failure_12004_test PRIVATE
    /O2 /W4 /WX /EHsc /permissive- /utf-8 /Gy)
  target_link_options(xar_ck3_sway_common_callsite_failure_12004_test PRIVATE
    /OPT:REF /INCREMENTAL:NO)
  target_link_libraries(xar_ck3_sway_common_callsite_failure_12004_test PRIVATE kernel32)
  add_test(NAME xar_ck3_sway_common_callsite_failure_12004
    COMMAND xar_ck3_sway_common_callsite_failure_12004_test
      "${CMAKE_CURRENT_BINARY_DIR}/sway-common-callsite-failure-wire")
  set_tests_properties(xar_ck3_sway_common_callsite_failure_12004 PROPERTIES
    TIMEOUT 30)
  unset(_sway_common_root)
endif()
