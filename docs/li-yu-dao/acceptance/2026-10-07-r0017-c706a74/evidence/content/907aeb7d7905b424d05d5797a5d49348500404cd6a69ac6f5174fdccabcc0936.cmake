if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12003_current_disembark_penalty_whole_test
    src/ck3_12003_current_disembark_penalty_whole_test.cpp)
  # The existing production source list owns ReadArmyStrengthsForScope. Keep the
  # fixture on that reader and the actual inline AppendArmyStrengthV1 serializer.
  target_link_libraries(xar_bridge_ck3_12003_current_disembark_penalty_whole_test
    PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_bridge_ck3_12003_current_disembark_penalty_whole_test
    PRIVATE include)
  target_compile_features(xar_bridge_ck3_12003_current_disembark_penalty_whole_test
    PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12003_current_disembark_penalty_whole_test
    PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12003_current_disembark_penalty_whole_test
      PRIVATE /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_ck3_12003_current_disembark_penalty_whole_test
      PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_ck3_12003_current_disembark_penalty_whole_test
    COMMAND xar_bridge_ck3_12003_current_disembark_penalty_whole_test
      --emit-wire "${CMAKE_CURRENT_BINARY_DIR}/current-disembark-penalty-days-12003-wire.json")
endif()
