if(BUILD_TESTING AND WIN32)
  set(_cmd_result_generated "${CMAKE_CURRENT_BINARY_DIR}/command_result_json_v1-generated")
  file(MAKE_DIRECTORY "${_cmd_result_generated}")

  # Extract AppendJsonString and CommandResultFrame bodies from current src/bridge.cpp
  file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/bridge.cpp" _bridge_source)

  # Find AppendJsonString: signature to column-zero closing brace
  string(FIND "${_bridge_source}" "void AppendJsonString(std::string &result, std::string_view value) {" _append_start)
  if(_append_start LESS 0)
    message(FATAL_ERROR "AppendJsonString signature not found in src/bridge.cpp")
  endif()
  math(EXPR _append_next "${_append_start} + 1")
  string(SUBSTRING "${_bridge_source}" ${_append_next} -1 _append_rest)
  string(FIND "${_append_rest}" "void AppendJsonString(std::string &result, std::string_view value) {" _append_duplicate)
  if(NOT _append_duplicate LESS 0)
    message(FATAL_ERROR "AppendJsonString signature is not unique in src/bridge.cpp")
  endif()
  string(SUBSTRING "${_bridge_source}" ${_append_start} -1 _append_tail)
  string(FIND "${_append_tail}" "\n}" _append_end)
  if(_append_end LESS 0)
    message(FATAL_ERROR "AppendJsonString closing brace not found")
  endif()
  math(EXPR _append_len "${_append_end} + 2")
  string(SUBSTRING "${_append_tail}" 0 ${_append_len} _append_body)

  # Find CommandResultFrame: signature to column-zero closing brace
  string(FIND "${_bridge_source}" "std::string CommandResultFrame(std::string_view request_id," _cmd_start)
  if(_cmd_start LESS 0)
    message(FATAL_ERROR "CommandResultFrame signature not found in src/bridge.cpp")
  endif()
  math(EXPR _cmd_next "${_cmd_start} + 1")
  string(SUBSTRING "${_bridge_source}" ${_cmd_next} -1 _cmd_rest)
  string(FIND "${_cmd_rest}" "std::string CommandResultFrame(std::string_view request_id," _cmd_duplicate)
  if(NOT _cmd_duplicate LESS 0)
    message(FATAL_ERROR "CommandResultFrame signature is not unique in src/bridge.cpp")
  endif()
  string(SUBSTRING "${_bridge_source}" ${_cmd_start} -1 _cmd_tail)
  string(FIND "${_cmd_tail}" "\n}" _cmd_end)
  if(_cmd_end LESS 0)
    message(FATAL_ERROR "CommandResultFrame closing brace not found")
  endif()
  math(EXPR _cmd_len "${_cmd_end} + 2")
  string(SUBSTRING "${_cmd_tail}" 0 ${_cmd_len} _cmd_body)

  # Write generated include
  file(WRITE "${_cmd_result_generated}/command_result_body.inc"
    "${_append_body}\n${_cmd_body}\n")

  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    src/bridge.cpp)

  add_executable(xar_ck3_command_result_json_v1_test
    tests/command_result_json_v1_fixture.cpp)
  target_include_directories(xar_ck3_command_result_json_v1_test BEFORE PRIVATE
    include
    "${_cmd_result_generated}")
  target_compile_features(xar_ck3_command_result_json_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_command_result_json_v1_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_command_result_json_v1_test PRIVATE /O2 /W4 /WX /EHsc /utf-8 /UNDEBUG /MP1 /Gy)
    target_link_options(xar_ck3_command_result_json_v1_test PRIVATE /OPT:REF /INCREMENTAL:NO)
  endif()

  set(_golden_root "${CMAKE_CURRENT_SOURCE_DIR}/../../java/ck3-control/native-transport/src/test/resources/org/xar/ck3/control/nativebridge/command-result-json-v1")

  add_test(NAME xar_ck3_command_result_json_v1
    COMMAND xar_ck3_command_result_json_v1_test
      "${CMAKE_CURRENT_BINARY_DIR}/command_result_json_v1-output"
      "${_golden_root}")
  set_tests_properties(xar_ck3_command_result_json_v1 PROPERTIES TIMEOUT 10)
endif()
