# Original actual4 Stop public Handler, dedicated action slot58 and real pump.
# Owned native I/O bindings are seams; original pure factories are also tested.
# No source archive, copied renderer, Game process or native execute is required.
if(BUILD_TESTING AND WIN32)
  set(_sway_stop_generated "${CMAKE_CURRENT_BINARY_DIR}/sway-stop-public-route12004-generated")
  file(MAKE_DIRECTORY "${_sway_stop_generated}")
  foreach(_kind IN ITEMS stop terminal)
    file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_sway_${_kind}.cpp" _source)
    if(_kind STREQUAL "stop")
      set(_definition "SwayStopBindings12004 BindSwayStopImage12004(")
      set(_real_definition "SwayStopBindings12004 RealBindSwayStopImage12004(")
    else()
      set(_definition "ck3_12002::SwayCompletionBindings12002 BindSwayTerminalImage12004(")
      set(_real_definition "ck3_12002::SwayCompletionBindings12002 RealBindSwayTerminalImage12004(")
    endif()
    string(FIND "${_source}" "${_definition}" _definition_at)
    if(_definition_at LESS 0)
      message(FATAL_ERROR "Stop test binding seam definition changed: ${_kind}")
    endif()
    # Rename only the definition. Public handler acquisition calls stay intact.
    string(REPLACE "${_definition}" "${_real_definition}" _source "${_source}")
    file(WRITE "${_sway_stop_generated}/${_kind}_fixture_variant.cpp" "${_source}")
  endforeach()

  # Retain original include preamble, private identity helper and descriptor,
  # then the original renderer suffix. Omit unrelated adapter/image readers.
  file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_adapter.cpp" _adapter)
  file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_snapshot_foundation.cpp" _foundation)
  string(ASCII 239 187 191 _utf8_bom)
  string(REPLACE "${_utf8_bom}" "" _adapter "${_adapter}")
  string(REPLACE "${_utf8_bom}" "" _foundation "${_foundation}")
  string(FIND "${_adapter}" "Ck3_12004AdapterBindings BindCk3_12004AdapterImage(" _adapter_image)
  string(FIND "${_adapter}" "std::string Render12004BuildIdentity(" _renderer)
  string(FIND "${_foundation}" "\nnamespace {" _foundation_readers)
  if(_adapter_image LESS 0 OR _renderer LESS _adapter_image OR _foundation_readers LESS 0)
    message(FATAL_ERROR "Stop test original identity/factory source boundaries changed")
  endif()
  string(SUBSTRING "${_adapter}" 0 ${_adapter_image} _identity_prefix)
  string(SUBSTRING "${_adapter}" ${_renderer} -1 _renderer_suffix)
  string(SUBSTRING "${_foundation}" 0 ${_foundation_readers} _command_factory)
  file(WRITE "${_sway_stop_generated}/required_identity_factory.cpp"
    "${_identity_prefix}${_renderer_suffix}\n${_command_factory}\n} // namespace xar::ck3_12004\n")
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    src/ck3_12004_sway_stop.cpp src/ck3_12004_sway_terminal.cpp
    src/ck3_12004_adapter.cpp src/ck3_12004_snapshot_foundation.cpp)

  add_executable(xar_ck3_sway_stop_public_route12004_test
    tests/sway_stop_public_route12004_test.cpp
    "${_sway_stop_generated}/stop_fixture_variant.cpp"
    "${_sway_stop_generated}/terminal_fixture_variant.cpp"
    "${_sway_stop_generated}/required_identity_factory.cpp"
    src/ck3_12004_sway.cpp
    src/ck3_12002_sway_completion_serializer.cpp
    src/ck3_12002_commands.cpp
    src/ck3_12002_query_mailbox.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12004_abi_profile.cpp
    src/ck3_12002.cpp
    src/protocol.cpp)
  target_include_directories(xar_ck3_sway_stop_public_route12004_test BEFORE PRIVATE include research)
  target_compile_features(xar_ck3_sway_stop_public_route12004_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_sway_stop_public_route12004_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_link_libraries(xar_ck3_sway_stop_public_route12004_test PRIVATE kernel32 user32 version)
  if(MSVC)
    target_compile_options(xar_ck3_sway_stop_public_route12004_test PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
    target_link_options(xar_ck3_sway_stop_public_route12004_test PRIVATE /OPT:REF /INCREMENTAL:NO)
  endif()
  add_test(NAME xar_ck3_sway_stop_public_route12004
    COMMAND xar_ck3_sway_stop_public_route12004_test candidate
      "${CMAKE_CURRENT_BINARY_DIR}/sway-stop-public-route12004-wire")
  set_tests_properties(xar_ck3_sway_stop_public_route12004 PROPERTIES TIMEOUT 30)
endif()
