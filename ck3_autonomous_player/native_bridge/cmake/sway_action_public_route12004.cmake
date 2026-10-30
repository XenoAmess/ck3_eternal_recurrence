# Public Sway action Handler -> registered slot58 -> real queue/pump -> shared action -> fresh receipt/serializer.
# Native bindings/callbacks are owned-memory test seams; Game and actual4 image factory are not exercised.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_sway_action_public_route12004_test
    tests/sway_action_public_route12004_test.cpp
    src/ck3_12002.cpp
    src/ck3_12002_context.cpp
    src/ck3_12002_commands.cpp
    src/active_scheme_semantic_action_v1_private.cpp
    src/ck3_12002_sway_command.cpp
    src/ck3_12002_sway_state.cpp
    src/ck3_12002_sway_handler.cpp
    src/ck3_12002_sway_mailbox.cpp
    src/ck3_12002_sway_serializer.cpp
    src/ck3_12002_query_mailbox.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12004_abi_profile.cpp
    src/protocol.cpp
  )
  target_include_directories(xar_ck3_sway_action_public_route12004_test BEFORE PRIVATE include research)
  target_compile_features(xar_ck3_sway_action_public_route12004_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_sway_action_public_route12004_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_link_libraries(xar_ck3_sway_action_public_route12004_test PRIVATE kernel32 user32 version)
  if(MSVC)
    target_compile_options(xar_ck3_sway_action_public_route12004_test PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
    target_link_options(xar_ck3_sway_action_public_route12004_test PRIVATE /OPT:REF /INCREMENTAL:NO)
  endif()
  add_test(NAME xar_ck3_sway_action_public_route12004
    COMMAND xar_ck3_sway_action_public_route12004_test "${CMAKE_CURRENT_BINARY_DIR}/sway-action-public-route12004-wire")
  set_tests_properties(xar_ck3_sway_action_public_route12004 PROPERTIES TIMEOUT 30)
endif()

# Real actual4 Sway canonical target routing, before image binding or queue.
if(BUILD_TESTING AND WIN32)
  # Keep the real legacy parsers without linking their unexecuted transport executors.
  # Both complete declarations must be unique; copy the original functions verbatim.
  function(xar_extract_sway_router_parser12004 src_file begin_decl end_decl out_var)
    file(READ "${src_file}" _source)
    string(FIND "${_source}" "${begin_decl}" _begin)
    string(FIND "${_source}" "${end_decl}" _end)
    if(_begin LESS 0 OR _end LESS 0 OR NOT _end GREATER _begin)
      message(FATAL_ERROR "Sway router parser boundaries missing or out of order: ${src_file}")
    endif()
    math(EXPR _begin_next "${_begin} + 1")
    string(SUBSTRING "${_source}" ${_begin_next} -1 _begin_tail)
    string(FIND "${_begin_tail}" "${begin_decl}" _begin_duplicate)
    math(EXPR _end_next "${_end} + 1")
    string(SUBSTRING "${_source}" ${_end_next} -1 _end_tail)
    string(FIND "${_end_tail}" "${end_decl}" _end_duplicate)
    if(NOT _begin_duplicate LESS 0 OR NOT _end_duplicate LESS 0)
      message(FATAL_ERROR "Sway router parser boundaries are not unique: ${src_file}")
    endif()
    math(EXPR _length "${_end} - ${_begin}")
    string(SUBSTRING "${_source}" ${_begin} ${_length} _parser)
    set(${out_var} "${_parser}" PARENT_SCOPE)
  endfunction()
  xar_extract_sway_router_parser12004(
    "${CMAKE_CURRENT_SOURCE_DIR}/src/active_scheme_sway_private_transport_v1.cpp"
    [=[bool ParseActiveSchemeSwayPrivateQueryStepV1(std::string_view step,
                                             std::uint32_t &target_id) noexcept {]=]
    [=[bool ExecuteActiveSchemeSwayPrivateQueryV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {]=]
    _sway_private_parser)
  xar_extract_sway_router_parser12004(
    "${CMAKE_CURRENT_SOURCE_DIR}/src/active_scheme_sway_formal_private_transport_v1.cpp"
    [=[bool ParseActiveSchemeSwayFormalStepV1(std::string_view step,
                                       ActiveSchemeSwayFormalModeV1 &mode,
                                       std::uint32_t &target_id) noexcept {]=]
    [=[bool ExecuteActiveSchemeSwayFormalPrivateCommandV1(
    void *opaque, const MainThreadExecutionStampV1 &stamp) noexcept {]=]
    _sway_formal_parser)
  set(_sway_parser_generated "${CMAKE_CURRENT_BINARY_DIR}/generated/sway_router_legacy_parsers12004.cpp")
  file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/generated")
  file(CONFIGURE OUTPUT "${_sway_parser_generated}" CONTENT
    "#include <charconv>\n#include \"active_scheme_sway_private_transport_v1.hpp\"\n#include \"active_scheme_sway_formal_private_transport_v1.hpp\"\nnamespace xar::ck3_11906 {\n${_sway_private_parser}${_sway_formal_parser}}\n"
    @ONLY NEWLINE_STYLE LF)
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    src/active_scheme_sway_private_transport_v1.cpp
    src/active_scheme_sway_formal_private_transport_v1.cpp)
  add_library(xar_ck3_sway_router_canonical_common12004 OBJECT
    src/ck3_12002_sway_handler.cpp
    "${_sway_parser_generated}"
    src/ck3_12003_abi_profile.cpp
    src/ck3_12004_abi_profile.cpp
    src/protocol.cpp)
  target_include_directories(xar_ck3_sway_router_canonical_common12004 PRIVATE include src research)
  target_compile_features(xar_ck3_sway_router_canonical_common12004 PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_sway_router_canonical_common12004 PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_sway_router_canonical_common12004 PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
  endif()
  foreach(_sway_router_variant IN ITEMS default query formal)
    set(_sway_router_target "xar_ck3_sway_router_canonical_targets12004_${_sway_router_variant}_test")
    add_executable(${_sway_router_target}
      tests/sway_router_canonical_targets12004_test.cpp
      src/ck3_12002_nonwar_router.cpp
      $<TARGET_OBJECTS:xar_ck3_sway_router_canonical_common12004>)
    target_include_directories(${_sway_router_target} PRIVATE include src research)
    target_compile_features(${_sway_router_target} PRIVATE cxx_std_20)
    target_compile_definitions(${_sway_router_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
    if(NOT _sway_router_variant STREQUAL "default")
      target_compile_definitions(${_sway_router_target} PRIVATE XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1)
    endif()
    if(_sway_router_variant STREQUAL "formal")
      target_compile_definitions(${_sway_router_target} PRIVATE XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1)
    endif()
    if(MSVC)
      target_compile_options(${_sway_router_target} PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
      target_link_options(${_sway_router_target} PRIVATE /OPT:REF /INCREMENTAL:NO)
    endif()
    target_link_libraries(${_sway_router_target} PRIVATE kernel32)
    add_test(NAME ${_sway_router_target} COMMAND ${_sway_router_target})
    set_tests_properties(${_sway_router_target} PROPERTIES TIMEOUT 10)
  endforeach()
endif()
