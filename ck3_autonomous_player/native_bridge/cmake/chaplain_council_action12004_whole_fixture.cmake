if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1)
  set(xar_chaplain_action4_target xar_ck3_12004_chaplain_council_action_whole_mailbox_test)
  add_executable(${xar_chaplain_action4_target}
    src/ck3_12004_chaplain_council_action_whole_mailbox_test.cpp)
  target_include_directories(${xar_chaplain_action4_target} PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include" "${CMAKE_CURRENT_SOURCE_DIR}/src")
  target_link_libraries(${xar_chaplain_action4_target} PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  target_compile_features(${xar_chaplain_action4_target} PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(${xar_chaplain_action4_target} PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
endif()
