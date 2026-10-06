# Actual .4 binders use the existing software readers and unchanged DTOs.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_religion_bindings.cpp)

if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1)
  add_executable(xar_ck3_12004_religion_bindings_mailbox_test
    src/ck3_12004_religion_bindings_mailbox_test.cpp)
  target_include_directories(xar_ck3_12004_religion_bindings_mailbox_test
    PRIVATE include)
  target_compile_features(xar_ck3_12004_religion_bindings_mailbox_test
    PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1=1
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1=1)
  target_link_libraries(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
    xar_bridge_protocol xar_ck3_12002_runtime user32 bcrypt)
  if(MSVC)
    target_compile_options(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
    target_link_options(xar_ck3_12004_religion_bindings_mailbox_test PRIVATE
      /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12004_religion_bindings_mailbox_test
    COMMAND xar_ck3_12004_religion_bindings_mailbox_test
      "${CMAKE_CURRENT_BINARY_DIR}/religion-12004-wire")
endif()
