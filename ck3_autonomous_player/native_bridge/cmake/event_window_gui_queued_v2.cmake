# Owned software coverage of the real request and versioned event reader.
# No Runtime/Bridge archive and no private external object is linked.
if(BUILD_TESTING AND WIN32)
  set(_xar_event_gui_queued_target xar_ck3_12004_event_window_gui_queued_v2_test)

  # Helper for generated core bind image
  include("${CMAKE_CURRENT_LIST_DIR}/event_window_gui_queued_core_bind12002.cmake")
  set(_xar_event_gui_queued_core_source "${CMAKE_CURRENT_BINARY_DIR}/generated/event_window_gui_queued_v2/core_bind_image_real12002.cpp")
  xar_event_gui_queued_core_bind12002("${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002.cpp" "${_xar_event_gui_queued_core_source}")

  add_executable(${_xar_event_gui_queued_target}
    tests/ck3_12004_event_window_gui_queued_v2_test.cpp
    tests/support/event_window_gui_queued_outer_v2.cpp
    src/ck3_12002_event_window_context_v2_mailbox.cpp
    src/ck3_12002_event_window_context.cpp
    src/ck3_12002_event_window_context_serializer.cpp
    src/ck3_12002_query_mailbox.cpp
    src/main_thread_query_mailbox_v1.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12004_abi_profile.cpp
    src/ck3_12004_event_window_context.cpp
    src/ck3_12004_events.cpp
    src/ck3_12004_snapshot_foundation.cpp
    src/ck3_12004_faction_alerts.cpp
    src/ck3_12002_faction_alerts.cpp
    src/player_faction_alerts_v1.cpp
    src/player_faction_alerts_v1_serializer.cpp
    src/ck3_12002_events.cpp
    src/ck3_12002_actor_resources.cpp
    src/ck3_12002_settlement.cpp
    src/player_event_trait_membership_12004.cpp
    src/ck3_12004_phase_character.cpp
    src/county_faction_final_12003.cpp
    src/ck3_12002_phase_character.cpp
    "${_xar_event_gui_queued_core_source}")

  target_include_directories(${_xar_event_gui_queued_target} PRIVATE include src research)
  target_compile_features(${_xar_event_gui_queued_target} PRIVATE cxx_std_20)
  target_compile_definitions(${_xar_event_gui_queued_target} PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_link_libraries(${_xar_event_gui_queued_target} PRIVATE user32 bcrypt)
  if(MSVC)
    target_compile_options(${_xar_event_gui_queued_target} PRIVATE
      /O2 /UNDEBUG /W4 /WX /Gy /permissive- /EHsc /utf-8 /MP1
      /UXAR_ENABLE_NATIVE_MANDATORY_CHOICE_V1
      /UXAR_CK3_ENABLE_G2_PREWAR_FORCE_COALITION_PRIVATE_QUERY12004_V1
      /UXAR_ENABLE_PREWAR_FORCE_COALITION_V2
      /UXAR_ENABLE_PREWAR_DECLARATION_NODE_IDENTITY_V1
      /UXAR_ENABLE_WAR_DECLARED_OVERVIEW_V1)
    target_link_options(${_xar_event_gui_queued_target} PRIVATE /OPT:REF)
    set_property(TARGET ${_xar_event_gui_queued_target} PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
  endif()
  add_test(NAME xar_ck3_12004_event_window_gui_queued_v2
    COMMAND ${_xar_event_gui_queued_target}
      "${CMAKE_CURRENT_BINARY_DIR}/wire/event-window-gui-queued-v2")
  set_tests_properties(xar_ck3_12004_event_window_gui_queued_v2 PROPERTIES TIMEOUT 15)
  unset(_xar_event_gui_queued_target)
  unset(_xar_event_gui_queued_core_source)
endif()
