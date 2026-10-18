# Include after xar_ck3_bridge and xar_ck3_12002_runtime exist. Default OFF.
option(XAR_ENABLE_RITE_CREATION_ACTIONS12004
  "Exact 1.20.0.4 original RiteCreationWindow private action candidate" OFF)
if(XAR_ENABLE_RITE_CREATION_ACTIONS12004)
  if(NOT WIN32)
    message(FATAL_ERROR "Rite creation actions require the exact Windows image")
  endif()
  target_sources(xar_ck3_bridge PRIVATE
    "${CMAKE_CURRENT_LIST_DIR}/../src/rite_creation_actions12004.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../src/rite_creation_actions12004_wire.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../src/rite_creation_actions12004_mailbox.cpp")
  # Limit the new define to its consumers. Avoid changing every existing bridge
  # translation unit just to enable one new finite dispatcher and controller.
  set_property(SOURCE
    "${CMAKE_CURRENT_LIST_DIR}/../src/bridge.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../src/rite_creation_actions12004.cpp"
    APPEND PROPERTY COMPILE_DEFINITIONS XAR_ENABLE_RITE_CREATION_ACTIONS12004=1)
  target_link_libraries(xar_ck3_bridge PRIVATE bcrypt)
  if(BUILD_TESTING)
    add_executable(xar_ck3_12004_rite_creation_request_test
      "${CMAKE_CURRENT_LIST_DIR}/../tests/rite_creation_actions12004_contract_test.cpp"
      "${CMAKE_CURRENT_LIST_DIR}/../src/rite_creation_actions12004.cpp"
      "${CMAKE_CURRENT_LIST_DIR}/../src/religion_ui12004.cpp")
    target_include_directories(xar_ck3_12004_rite_creation_request_test PRIVATE include)
    target_compile_features(xar_ck3_12004_rite_creation_request_test PRIVATE cxx_std_20)
    target_compile_definitions(xar_ck3_12004_rite_creation_request_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE XAR_ENABLE_RITE_CREATION_ACTIONS12004=1)
    target_link_libraries(xar_ck3_12004_rite_creation_request_test PRIVATE
      xar_bridge_protocol xar_ck3_12002_runtime user32 bcrypt)
    if(MSVC)
      target_compile_options(xar_ck3_12004_rite_creation_request_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
      target_link_options(xar_ck3_12004_rite_creation_request_test PRIVATE /OPT:REF)
    endif()
    add_test(NAME xar_ck3_12004_rite_creation_request_test COMMAND xar_ck3_12004_rite_creation_request_test)
    add_executable(xar_ck3_12004_rite_creation_wire_test
      "${CMAKE_CURRENT_LIST_DIR}/../tests/rite_creation_actions12004_wire_test.cpp"
      "${CMAKE_CURRENT_LIST_DIR}/../src/rite_creation_actions12004_wire.cpp"
      "${CMAKE_CURRENT_LIST_DIR}/../src/rite_creation_actions12004.cpp"
      "${CMAKE_CURRENT_LIST_DIR}/../src/religion_ui12004.cpp")
    target_include_directories(xar_ck3_12004_rite_creation_wire_test PRIVATE include)
    target_compile_features(xar_ck3_12004_rite_creation_wire_test PRIVATE cxx_std_20)
    target_compile_definitions(xar_ck3_12004_rite_creation_wire_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE XAR_ENABLE_RITE_CREATION_ACTIONS12004=1)
    target_link_libraries(xar_ck3_12004_rite_creation_wire_test PRIVATE
      xar_bridge_protocol xar_ck3_12002_runtime user32 bcrypt)
    if(MSVC)
      target_compile_options(xar_ck3_12004_rite_creation_wire_test PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
      target_link_options(xar_ck3_12004_rite_creation_wire_test PRIVATE /OPT:REF)
    endif()
    add_test(NAME xar_ck3_12004_rite_creation_wire_test COMMAND xar_ck3_12004_rite_creation_wire_test)
    # Request/formatter fixtures do not execute original game controller code.
  endif()
endif()
