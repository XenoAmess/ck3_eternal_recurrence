# D candidate: actual PlayerClaims semantic mailbox in owned software memory.
# This target deliberately disables only the unrelated war-overview special case
# in its private copy of main_thread_query_mailbox_v1.cpp. No public header/layout
# is conditional on this feature. All other runtime feature definitions are kept.
set(_xar_claims_semantic_target xar_ck3_12004_player_claims_semantic_mailbox_v1_test)
add_executable(${_xar_claims_semantic_target}
  tests/ck3_12004_player_claims_semantic_mailbox_v1_test.cpp
  src/ck3_12002_semantic_adapter.cpp
  src/ck3_12002_query_mailbox.cpp
  src/main_thread_query_mailbox_v1.cpp
  src/ck3_12004_player_claims_v1.cpp
  src/ck3_12004_abi_profile.cpp
  src/player_claims_v1_serializer.cpp
  src/current_first_heir_relationship_v1.cpp
  src/observed_heir_marriage_private_v1.cpp)
target_include_directories(${_xar_claims_semantic_target} PRIVATE include include/xar_bridge src research)
get_target_property(_xar_claims_semantic_defs xar_ck3_12002_runtime INTERFACE_COMPILE_DEFINITIONS)
if(_xar_claims_semantic_defs)
  list(FILTER _xar_claims_semantic_defs EXCLUDE REGEX "^XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1(=|$)")
  target_compile_definitions(${_xar_claims_semantic_target} PRIVATE ${_xar_claims_semantic_defs})
endif()
target_compile_definitions(${_xar_claims_semantic_target} PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1=0)
target_link_libraries(${_xar_claims_semantic_target} PRIVATE
  "$<LINK_ONLY:xar_ck3_12002_runtime>" "$<LINK_ONLY:xar_bridge_protocol>" user32 bcrypt)
if(MSVC)
  target_compile_options(${_xar_claims_semantic_target} PRIVATE /W4 /WX /Gy /bigobj /permissive- /EHsc /utf-8 /MP1)
  target_link_options(${_xar_claims_semantic_target} PRIVATE /OPT:REF)
endif()
add_test(NAME xar_ck3_12004_player_claims_semantic_mailbox_v1
  COMMAND ${_xar_claims_semantic_target}
    "${CMAKE_CURRENT_BINARY_DIR}/player-claims-semantic-mailbox-v1-wire")
add_test(NAME xar_ck3_12004_player_claims_semantic_mailbox_lifecycle_v1
  COMMAND ${_xar_claims_semantic_target}
    "${CMAKE_CURRENT_BINARY_DIR}/player-claims-semantic-mailbox-lifecycle-v1-wire"
    --lifecycle-only)
set_tests_properties(xar_ck3_12004_player_claims_semantic_mailbox_lifecycle_v1
  PROPERTIES TIMEOUT 15)
unset(_xar_claims_semantic_defs)
unset(_xar_claims_semantic_target)

# Separate EXE keeps the timer-import observation out of the ordinary fixture.
# All production sources and linked targets are resolved from this repository.
set(_xar_claims_internal_wait_target xar_ck3_12004_player_claims_internal_wait_v1_test)
add_executable(${_xar_claims_internal_wait_target}
  tests/ck3_12004_player_claims_internal_wait_v1_test.cpp
  src/ck3_12002_semantic_adapter.cpp
  src/ck3_12002_query_mailbox.cpp
  src/main_thread_query_mailbox_v1.cpp
  src/ck3_12004_player_claims_v1.cpp
  src/ck3_12004_abi_profile.cpp
  src/player_claims_v1_serializer.cpp
  src/current_first_heir_relationship_v1.cpp
  src/observed_heir_marriage_private_v1.cpp)
target_include_directories(${_xar_claims_internal_wait_target} PRIVATE include include/xar_bridge src research)
get_target_property(_xar_claims_semantic_defs xar_ck3_12002_runtime INTERFACE_COMPILE_DEFINITIONS)
if(_xar_claims_semantic_defs)
  list(FILTER _xar_claims_semantic_defs EXCLUDE REGEX "^XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1(=|$)")
  target_compile_definitions(${_xar_claims_internal_wait_target} PRIVATE ${_xar_claims_semantic_defs})
endif()
target_compile_definitions(${_xar_claims_internal_wait_target} PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1=0)
target_link_libraries(${_xar_claims_internal_wait_target} PRIVATE
  "$<LINK_ONLY:xar_ck3_12002_runtime>" "$<LINK_ONLY:xar_bridge_protocol>" user32 bcrypt)
if(MSVC)
  target_compile_options(${_xar_claims_internal_wait_target} PRIVATE /W4 /WX /Gy /bigobj /permissive- /EHsc /utf-8 /MP1)
  target_link_options(${_xar_claims_internal_wait_target} PRIVATE /OPT:REF)
endif()
add_test(NAME xar_ck3_12004_player_claims_internal_wait_v1
  COMMAND ${_xar_claims_internal_wait_target}
    "${CMAKE_CURRENT_BINARY_DIR}/player-claims-internal-wait-v1-wire"
    --internal-wait-only)
set_tests_properties(xar_ck3_12004_player_claims_internal_wait_v1
  PROPERTIES TIMEOUT 60)
unset(_xar_claims_semantic_defs)
unset(_xar_claims_internal_wait_target)
