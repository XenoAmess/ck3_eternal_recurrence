# Additive component in the existing conversion-input query; no new flag.
if(XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_bridge PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_conversion_fervor_inputs.cpp")
  # The old fixture target compiles the now-extended production mailbox. Add its
  # link dependency without rerunning that old suite as qualification of A.
  if(TARGET xar_r3_religion_conversion_inputs_named_test)
    target_sources(xar_r3_religion_conversion_inputs_named_test PRIVATE
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_conversion_fervor_inputs.cpp")
  endif()
endif()

if(BUILD_TESTING AND WIN32 AND XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1)
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/conversion-fervor-first-wire")
  add_executable(xar_conversion_fervor_inputs_first_test
    src/ck3_12002.cpp
    src/ck3_12002_query_mailbox.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12003_adapter.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12002_religion_context.cpp
    src/religion_rite_governance12002_state_rite.cpp
    src/ck3_12002_religion_conversion_gates.cpp
    src/ck3_12002_religion_conversion_ai_inputs.cpp
    src/ck3_12002_religion_conversion_inputs_mailbox.cpp
    src/ck3_12003_conversion_fervor_inputs.cpp
    # The imported runtime's family closure needs these real M5 helpers.
    src/current_first_heir_relationship_v1.cpp
    src/observed_heir_marriage_private_v1.cpp
    src/ck3_12003_conversion_fervor_inputs_test.cpp)
  target_include_directories(xar_conversion_fervor_inputs_first_test PRIVATE include)
  # The actual identity renderer references the existing adapter/binder closure.
  # Linking runtime also preserves its PUBLIC feature/layout definitions.
  target_link_libraries(xar_conversion_fervor_inputs_first_test PRIVATE
    xar_bridge_protocol xar_ck3_12002_runtime user32)
  target_compile_definitions(xar_conversion_fervor_inputs_first_test PRIVATE
    XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1
    XAR_RELIGION_CONVERSION_INPUTS_MAILBOX_STANDALONE_ADAPTER=1)
  if(MSVC)
    # Keep actual production identity-renderer code and its real runtime closure.
    target_compile_options(xar_conversion_fervor_inputs_first_test PRIVATE
      /O2 /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy /Gw)
    target_link_options(xar_conversion_fervor_inputs_first_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_conversion_fervor_inputs_first_test
    COMMAND xar_conversion_fervor_inputs_first_test
      "${CMAKE_BINARY_DIR}/conversion-fervor-first-wire")
endif()
