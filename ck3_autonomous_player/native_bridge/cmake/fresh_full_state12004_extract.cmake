function(xar_generate_fresh_full_state12004_sources bridge_source output_dir)
  if(NOT EXISTS "${bridge_source}")
    message(FATAL_ERROR "Bridge source not found: ${bridge_source}")
  endif()

  file(READ "${bridge_source}" _bridge_raw)
  # Normalize CRLF to LF and strip BOM if present
  string(REPLACE "\r\n" "\n" _bridge_source "${_bridge_raw}")
  string(ASCII 239 187 191 _fresh_bom)
  string(REPLACE "${_fresh_bom}" "" _bridge_source "${_bridge_source}")

  # Helper to extract a definition starting with a unique prefix and ending at column-zero closing brace/semicolon
  function(_xar_extract_fresh_definition12004 source_text prefix end_marker out_var)
    string(FIND "${source_text}" "${prefix}" _start)
    if(_start LESS 0)
      message(FATAL_ERROR "Definition not found: ${prefix}")
    endif()
    # Check uniqueness
    math(EXPR _next "${_start} + 1")
    string(SUBSTRING "${source_text}" ${_next} -1 _rest)
    string(FIND "${_rest}" "${prefix}" _dup)
    if(NOT _dup LESS 0)
      message(FATAL_ERROR "Definition prefix is not unique: ${prefix}")
    endif()
    # Find end marker after start
    string(SUBSTRING "${source_text}" ${_start} -1 _tail)
    string(FIND "${_tail}" "${end_marker}" _end)
    if(_end LESS 0)
      message(FATAL_ERROR "Closing marker not found for: ${prefix}")
    endif()
    string(LENGTH "${end_marker}" _end_marker_len)
    math(EXPR _len "${_end} + ${_end_marker_len}")
    string(SUBSTRING "${_tail}" 0 ${_len} _body)
    set(${out_var} "${_body}" PARENT_SCOPE)
  endfunction()

  # Extract structs (end with \n};)
  _xar_extract_fresh_definition12004("${_bridge_source}" "struct CheckpointSubmission {" "\n};" _struct_checkpoint)
  _xar_extract_fresh_definition12004("${_bridge_source}" "struct SnapshotPublishDiagnostics {" "\n};" _struct_diag)
  _xar_extract_fresh_definition12004("${_bridge_source}" "struct CommandEntryTraceV1 {" "\n};" _struct_trace)
  _xar_extract_fresh_definition12004("${_bridge_source}" "struct CommandEntryTracesV1 {" "\n};" _struct_traces)
  _xar_extract_fresh_definition12004("${_bridge_source}" "struct WorkerState {" "\n};" _struct_worker)

  # Extract functions (end with \n})
  _xar_extract_fresh_definition12004("${_bridge_source}" "std::string Number(" "\n}" _fn_number)
  _xar_extract_fresh_definition12004("${_bridge_source}" "std::string SignedNumber(" "\n}" _fn_signed)
  _xar_extract_fresh_definition12004("${_bridge_source}" "void AppendJsonString(" "\n}" _fn_append_json)
  _xar_extract_fresh_definition12004("${_bridge_source}" "void AppendInt32Array(" "\n}" _fn_append_int32)
  _xar_extract_fresh_definition12004("${_bridge_source}" "std::string_view ArmyRouteReadStatusName(" "\n}" _fn_army_status)
  _xar_extract_fresh_definition12004("${_bridge_source}" "void AppendArmySnapshot(" "\n}" _fn_append_army)
  _xar_extract_fresh_definition12004("${_bridge_source}" "void AppendArmyArray(" "\n}" _fn_append_army_array)
  _xar_extract_fresh_definition12004("${_bridge_source}" "void AppendFixedPoint(" "\n}" _fn_append_fixed)
  _xar_extract_fresh_definition12004("${_bridge_source}" "void AppendWarObjectiveProvinceState(" "\n}" _fn_append_war_obj)
  _xar_extract_fresh_definition12004("${_bridge_source}" "void AppendWarObjectiveProvinceStates(" "\n}" _fn_append_war_objs)
  _xar_extract_fresh_definition12004("${_bridge_source}" "void AppendOneLifeSettlement(" "\n}" _fn_append_settlement)
  _xar_extract_fresh_definition12004("${_bridge_source}" "std::string StateSnapshotFrame(" "\n}" _fn_state_frame)
  _xar_extract_fresh_definition12004("${_bridge_source}" "bool PublishSnapshot(" "\n}" _fn_publish)
  _xar_extract_fresh_definition12004("${_bridge_source}" "std::string CommandResultFrame(" "\n}" _fn_cmd_result)
  _xar_extract_fresh_definition12004("${_bridge_source}" "bool RunFreshFullStateQuery12004(" "\n}" _fn_handler)

  # Write outputs only when current source content changes.
  file(MAKE_DIRECTORY "${output_dir}")
  file(CONFIGURE OUTPUT "${output_dir}/fresh_bridge_snapshot_support.inc" CONTENT
    "${_struct_checkpoint}\n${_struct_diag}\n${_fn_number}\n${_fn_signed}\n${_fn_append_json}\n${_fn_append_int32}\n${_fn_army_status}\n${_fn_append_army}\n${_fn_append_army_array}\n${_fn_append_fixed}\n${_fn_append_war_obj}\n${_fn_append_war_objs}\n${_fn_append_settlement}\n${_fn_state_frame}\n" @ONLY NEWLINE_STYLE LF)

  file(CONFIGURE OUTPUT "${output_dir}/fresh_bridge_worker_state.inc" CONTENT
    "${_struct_trace}\n${_struct_traces}\n${_struct_worker}\n" @ONLY NEWLINE_STYLE LF)

  file(CONFIGURE OUTPUT "${output_dir}/fresh_bridge_publish.inc" CONTENT
    "${_fn_publish}\n" @ONLY NEWLINE_STYLE LF)

  file(CONFIGURE OUTPUT "${output_dir}/fresh_bridge_command_result.inc" CONTENT
    "${_fn_cmd_result}\n" @ONLY NEWLINE_STYLE LF)

  file(CONFIGURE OUTPUT "${output_dir}/fresh_bridge_handler.inc" CONTENT
    "${_fn_handler}\n" @ONLY NEWLINE_STYLE LF)

  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${bridge_source}")
endfunction()
