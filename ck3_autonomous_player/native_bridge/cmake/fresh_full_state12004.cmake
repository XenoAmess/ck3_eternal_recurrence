  # Extractor module is assumed to be present at cmake/fresh_full_state12004_extract.cmake
  # and defines xar_generate_fresh_full_state12004_sources(bridge_source output_dir).
  # This module only wires the generated sources into test targets.

function(xar_add_fresh_full_state12004_tests source_root fixture_root)
  if(NOT BUILD_TESTING OR NOT WIN32)
    return()
  endif()
    # Capture the directory of this CMakeLists.txt to locate the extractor module
    # and ensure relative paths in source_root/fixture_root resolve correctly.
    set(_module_dir "${CMAKE_CURRENT_FUNCTION_LIST_DIR}")
    set(_extractor_module "${_module_dir}/fresh_full_state12004_extract.cmake")

    if(NOT EXISTS "${_extractor_module}")
      message(FATAL_ERROR "Extractor module not found: ${_extractor_module}")
    endif()

    include("${_extractor_module}")

    # Resolve roots to absolute paths for safety
    if(NOT IS_ABSOLUTE "${source_root}")
      set(source_root "${CMAKE_CURRENT_SOURCE_DIR}/${source_root}")
    endif()
    if(NOT IS_ABSOLUTE "${fixture_root}")
      set(fixture_root "${CMAKE_CURRENT_SOURCE_DIR}/${fixture_root}")
    endif()

    # Generate sources into a binary directory
    set(_gen_dir "${CMAKE_CURRENT_BINARY_DIR}/fresh_full_state12004_generated")
    file(MAKE_DIRECTORY "${_gen_dir}")

    # Call the extractor function (defined in the included module)
    # It expects the bridge source and an output directory.
    # We assume the bridge source is at src/bridge.cpp relative to source_root
    # as per the existing command_result_json_v1 pattern.
    set(_bridge_src "${source_root}/src/bridge.cpp")
    if(NOT EXISTS "${_bridge_src}")
      message(FATAL_ERROR "Bridge source not found: ${_bridge_src}")
    endif()

    xar_generate_fresh_full_state12004_sources("${_bridge_src}" "${_gen_dir}")

    # Track dependencies for regeneration
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
      "${_bridge_src}"
      "${_extractor_module}"
    )

    # Define shared OBJECT libraries to avoid duplicate compilation of support TUs
    # Group 1: Core
    add_library(xar_fresh_core12004 OBJECT
      "${source_root}/src/game_adapter_capabilities.cpp"
      "${source_root}/src/ck3_12004_abi_profile.cpp"
    )
    target_include_directories(xar_fresh_core12004 PRIVATE
      "${source_root}/include"
      "${source_root}/src"
      "${source_root}/research"
      "${_gen_dir}"
    )
    target_compile_features(xar_fresh_core12004 PRIVATE cxx_std_20)
    target_compile_definitions(xar_fresh_core12004 PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      xar_ck3_bridge_EXPORTS
      XAR_BRIDGE_VERSION="0.1.0"
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1=1
      NDEBUG
    )
    if(MSVC)
      target_compile_options(xar_fresh_core12004 PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
    endif()

    # Group 2: Owner
    add_library(xar_fresh_owner12004 OBJECT
      "${source_root}/src/ck3_12002_semantic_adapter.cpp"
      "${source_root}/src/main_thread_query_mailbox_v1.cpp"
      "${source_root}/src/ck3_12002_query_mailbox.cpp"
      "${source_root}/src/ck3_12002_console_fixture.cpp"
      "${source_root}/src/ck3_12003_abi_profile.cpp"
      "${fixture_root}/fresh_full_state12004_nonfresh_abort_seams.cpp"
    )
    target_include_directories(xar_fresh_owner12004 PRIVATE
      "${source_root}/include"
      "${source_root}/src"
      "${source_root}/research"
      "${_gen_dir}"
    )
    target_compile_features(xar_fresh_owner12004 PRIVATE cxx_std_20)
    target_compile_definitions(xar_fresh_owner12004 PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      xar_ck3_bridge_EXPORTS
      XAR_BRIDGE_VERSION="0.1.0"
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1=1
      NDEBUG
    )
    if(MSVC)
      target_compile_options(xar_fresh_owner12004 PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
    endif()

    # Group 3: Wire
    add_library(xar_fresh_wire12004 OBJECT
      "${source_root}/src/protocol.cpp"
      "${source_root}/src/player_event_trait_membership_12004.cpp"
      "${source_root}/src/ck3_12002_phase_character.cpp"
      "${source_root}/src/ck3_12004_phase_character.cpp"
    )
    target_include_directories(xar_fresh_wire12004 PRIVATE
      "${source_root}/include"
      "${source_root}/src"
      "${source_root}/research"
      "${_gen_dir}"
    )
    target_compile_features(xar_fresh_wire12004 PRIVATE cxx_std_20)
    target_compile_definitions(xar_fresh_wire12004 PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      xar_ck3_bridge_EXPORTS
      XAR_BRIDGE_VERSION="0.1.0"
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1=1
      NDEBUG
    )
    if(MSVC)
      target_compile_options(xar_fresh_wire12004 PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
    endif()

    # 1. Owner Test
    add_executable(xar_ck3_fresh_full_state_owner12004_test
      "${fixture_root}/fresh_full_state_owner12004_fixture.cpp"
      $<TARGET_OBJECTS:xar_fresh_core12004>
      $<TARGET_OBJECTS:xar_fresh_owner12004>
    )
    target_include_directories(xar_ck3_fresh_full_state_owner12004_test PRIVATE
      "${source_root}/include"
      "${source_root}/src"
      "${source_root}/research"
      "${_gen_dir}"
    )
    target_compile_features(xar_ck3_fresh_full_state_owner12004_test PRIVATE cxx_std_20)
    target_compile_definitions(xar_ck3_fresh_full_state_owner12004_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      xar_ck3_bridge_EXPORTS
      XAR_BRIDGE_VERSION="0.1.0"
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1=1
      NDEBUG
    )
    if(MSVC)
      target_compile_options(xar_ck3_fresh_full_state_owner12004_test PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
      target_link_options(xar_ck3_fresh_full_state_owner12004_test PRIVATE /OPT:REF /INCREMENTAL:NO)
    endif()
    target_link_libraries(xar_ck3_fresh_full_state_owner12004_test PRIVATE kernel32 user32)
    add_test(NAME xar_ck3_fresh_full_state_owner12004 COMMAND xar_ck3_fresh_full_state_owner12004_test)
    set_tests_properties(xar_ck3_fresh_full_state_owner12004 PROPERTIES TIMEOUT 10)

    # 2. Publication Test
    add_executable(xar_ck3_fresh_full_state_publication12004_test
      "${fixture_root}/fresh_full_state_publication12004_fixture.cpp"
      $<TARGET_OBJECTS:xar_fresh_core12004>
      $<TARGET_OBJECTS:xar_fresh_wire12004>
    )
    target_include_directories(xar_ck3_fresh_full_state_publication12004_test PRIVATE
      "${source_root}/include"
      "${source_root}/src"
      "${source_root}/research"
      "${_gen_dir}"
    )
    target_compile_features(xar_ck3_fresh_full_state_publication12004_test PRIVATE cxx_std_20)
    target_compile_definitions(xar_ck3_fresh_full_state_publication12004_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      xar_ck3_bridge_EXPORTS
      XAR_BRIDGE_VERSION="0.1.0"
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1=1
      NDEBUG
    )
    if(MSVC)
      target_compile_options(xar_ck3_fresh_full_state_publication12004_test PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
      target_link_options(xar_ck3_fresh_full_state_publication12004_test PRIVATE /OPT:REF /INCREMENTAL:NO)
    endif()
    target_link_libraries(xar_ck3_fresh_full_state_publication12004_test PRIVATE kernel32 user32)
    add_test(NAME xar_ck3_fresh_full_state_publication12004 COMMAND xar_ck3_fresh_full_state_publication12004_test)
    set_tests_properties(xar_ck3_fresh_full_state_publication12004 PROPERTIES TIMEOUT 10)

    # 3. Handler Ack Test
    add_executable(xar_ck3_fresh_full_state_handler_ack12004_test
      "${fixture_root}/fresh_full_state_handler_ack12004_fixture.cpp"
      $<TARGET_OBJECTS:xar_fresh_core12004>
      $<TARGET_OBJECTS:xar_fresh_owner12004>
      $<TARGET_OBJECTS:xar_fresh_wire12004>
    )
    target_include_directories(xar_ck3_fresh_full_state_handler_ack12004_test PRIVATE
      "${source_root}/include"
      "${source_root}/src"
      "${source_root}/research"
      "${_gen_dir}"
    )
    target_compile_features(xar_ck3_fresh_full_state_handler_ack12004_test PRIVATE cxx_std_20)
    target_compile_definitions(xar_ck3_fresh_full_state_handler_ack12004_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      xar_ck3_bridge_EXPORTS
      XAR_BRIDGE_VERSION="0.1.0"
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_FORMAL_PRIVATE_ACTION_V1=1
      XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_QUERY_V1=1
      NDEBUG
    )
    if(MSVC)
      target_compile_options(xar_ck3_fresh_full_state_handler_ack12004_test PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
      target_link_options(xar_ck3_fresh_full_state_handler_ack12004_test PRIVATE /OPT:REF /INCREMENTAL:NO)
    endif()
    target_link_libraries(xar_ck3_fresh_full_state_handler_ack12004_test PRIVATE kernel32 user32)
    add_test(NAME xar_ck3_fresh_full_state_handler_ack12004 COMMAND xar_ck3_fresh_full_state_handler_ack12004_test)
    set_tests_properties(xar_ck3_fresh_full_state_handler_ack12004 PROPERTIES TIMEOUT 10)
    add_test(NAME xar_ck3_fresh_full_state_handler_ack12004_write_failure
      COMMAND xar_ck3_fresh_full_state_handler_ack12004_test --ack-write-failure-only)
    set_tests_properties(xar_ck3_fresh_full_state_handler_ack12004_write_failure
      PROPERTIES TIMEOUT 10)

endfunction()
