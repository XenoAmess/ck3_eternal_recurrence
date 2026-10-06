# Actual4 owned leaf. Root integrates this once after the actual4 adapter borrow
# and overall declarations composition. Old cost/mailbox TUs are already owned
# by ordinary_holy_war_cb_cost_first_fixture.cmake.
target_sources(xar_ck3_12002_runtime PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}/../src/ck3_12004_holy_war.cpp")
if(BUILD_TESTING AND WIN32 AND XAR_CK3_ENABLE_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
  add_executable(xar_ck3_12004_ordinary_holy_war_declaration_context_whole_mailbox_test
    "${CMAKE_CURRENT_LIST_DIR}/../src/ordinary_holy_war_declaration_context12004_whole_mailbox_test.cpp")
  target_link_libraries(xar_ck3_12004_ordinary_holy_war_declaration_context_whole_mailbox_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  if(MSVC)
    target_compile_options(xar_ck3_12004_ordinary_holy_war_declaration_context_whole_mailbox_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  set(XAR_ORDINARY_HOLY_WAR_12004_FIRST_OUTPUT_DIR "" CACHE PATH
    "Fresh output directory for the sole actual4 ordinary holy-war whole FIRST case")
  if(XAR_ORDINARY_HOLY_WAR_12004_FIRST_OUTPUT_DIR)
    add_test(NAME xar_ck3_12004_ordinary_holy_war_declaration_context_whole_first
      COMMAND xar_ck3_12004_ordinary_holy_war_declaration_context_whole_mailbox_test
        "${XAR_ORDINARY_HOLY_WAR_12004_FIRST_OUTPUT_DIR}")
  endif()
endif()
