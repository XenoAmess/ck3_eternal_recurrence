# Owned leaf: the fixture links the real production runtime and protocol.
# No configure, build, native fixture or consumer has run for this source commit.
target_sources(xar_ck3_12002_runtime PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}/../src/ordinary_holy_war_cb_cost_v1.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/../src/ordinary_holy_war_declaration_context12003_mailbox.cpp")
if(BUILD_TESTING AND WIN32 AND XAR_CK3_ENABLE_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
  add_executable(xar_ck3_12003_ordinary_holy_war_declaration_context_whole_mailbox_test
    "${CMAKE_CURRENT_LIST_DIR}/../src/ordinary_holy_war_declaration_context12003_whole_mailbox_test.cpp")
  target_link_libraries(xar_ck3_12003_ordinary_holy_war_declaration_context_whole_mailbox_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  if(MSVC)
    target_compile_options(xar_ck3_12003_ordinary_holy_war_declaration_context_whole_mailbox_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
endif()
