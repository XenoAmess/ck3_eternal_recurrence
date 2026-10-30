# Owned software coverage of the real request and versioned event reader.
# No Runtime/Bridge archive and no private external object is linked.
if(BUILD_TESTING AND WIN32)
  set(_xar_event_gui_dispatch_target xar_ck3_12004_event_window_gui_dispatch_v2_test)
  add_executable(${_xar_event_gui_dispatch_target}
    tests/ck3_12004_event_window_gui_dispatch_v2_test.cpp
    tests/support/event_window_gui_unused_outer_v2.cpp
    src/ck3_12002_event_window_context.cpp
    src/ck3_12002_event_window_context_serializer.cpp
    src/ck3_12002_query_mailbox.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12004_abi_profile.cpp)
  target_include_directories(${_xar_event_gui_dispatch_target} PRIVATE include src research)
  target_compile_features(${_xar_event_gui_dispatch_target} PRIVATE cxx_std_20)
  target_compile_definitions(${_xar_event_gui_dispatch_target} PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_link_libraries(${_xar_event_gui_dispatch_target} PRIVATE user32 bcrypt)
  if(MSVC)
    target_compile_options(${_xar_event_gui_dispatch_target} PRIVATE
      /O2 /UNDEBUG /W4 /WX /Gy /permissive- /EHsc /utf-8 /MP1)
    target_link_options(${_xar_event_gui_dispatch_target} PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12004_event_window_gui_dispatch_v2
    COMMAND ${_xar_event_gui_dispatch_target}
      "${CMAKE_CURRENT_BINARY_DIR}/wire/event-window-gui-dispatch-v2")
  set_tests_properties(xar_ck3_12004_event_window_gui_dispatch_v2 PROPERTIES TIMEOUT 15)
  unset(_xar_event_gui_dispatch_target)
endif()
