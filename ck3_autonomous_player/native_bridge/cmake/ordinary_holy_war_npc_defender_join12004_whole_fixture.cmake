# Held exact3 software reader plus actual4 image factory, FIRST_NOTRUN.
target_sources(xar_ck3_12002_runtime PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}/../src/ck3_12003_holy_war_defender_join_inputs.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/../src/ck3_12004_holy_war_defender_join_inputs.cpp")

if(BUILD_TESTING AND WIN32 AND XAR_CK3_ENABLE_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
  add_executable(xar_ck3_12004_holy_war_npc_defender_join_whole_mailbox_test
    "${CMAKE_CURRENT_LIST_DIR}/../src/ordinary_holy_war_npc_defender_join12004_whole_mailbox_test.cpp")
  target_link_libraries(xar_ck3_12004_holy_war_npc_defender_join_whole_mailbox_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  if(MSVC)
    target_compile_options(xar_ck3_12004_holy_war_npc_defender_join_whole_mailbox_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
endif()
