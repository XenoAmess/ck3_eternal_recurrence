# Natural compiled-effect observer shares the already registered incoming-context copier.
option(XAR_CK3_ENABLE_G2_ARMY_COMPILED_EFFECT_OBSERVER_V1
  "Observe actual4 Army compiled-effect entry dispatches and original results" ON)
if(XAR_CK3_ENABLE_G2_ARMY_COMPILED_EFFECT_OBSERVER_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/actual_army_compiled_effect_observer_12004.cpp)
  target_compile_definitions(xar_ck3_12002_runtime PUBLIC
    XAR_CK3_ENABLE_G2_ARMY_COMPILED_EFFECT_OBSERVER_V1=1)
endif()

if(BUILD_TESTING AND WIN32)
  if(XAR_CK3_ENABLE_G2_ARMY_COMPILED_EFFECT_OBSERVER_V1)
    add_executable(actual_army_compiled_effect_observer_fixture EXCLUDE_FROM_ALL
      src/actual_army_compiled_effect_observer_12004_fixture.cpp)
    target_link_libraries(actual_army_compiled_effect_observer_fixture PRIVATE
      xar_ck3_12002_runtime kernel32)
    target_include_directories(actual_army_compiled_effect_observer_fixture PRIVATE include)
    target_compile_features(actual_army_compiled_effect_observer_fixture PRIVATE cxx_std_20)
    target_compile_definitions(actual_army_compiled_effect_observer_fixture PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(actual_army_compiled_effect_observer_fixture PRIVATE
        /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
    endif()
    add_test(NAME actual_army_compiled_effect_observer_fixture
      COMMAND $<TARGET_FILE:actual_army_compiled_effect_observer_fixture>)

    # Root captures this new whole-query packet and runs the authored Python consumer.
    add_executable(native71_army_compiled_effect_service_wire_test EXCLUDE_FROM_ALL
      tests/native71_army_compiled_effect_service_wire_test.cpp)
    target_link_libraries(native71_army_compiled_effect_service_wire_test PRIVATE
      xar_ck3_12002_runtime kernel32)
    target_include_directories(native71_army_compiled_effect_service_wire_test PRIVATE include)
    target_compile_features(native71_army_compiled_effect_service_wire_test PRIVATE cxx_std_20)
    target_compile_definitions(native71_army_compiled_effect_service_wire_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(native71_army_compiled_effect_service_wire_test PRIVATE
        /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
    endif()
  endif()

  if(XAR_CK3_ENABLE_G2_ARMY_LATE_EVENT_OBSERVER_V1)
    add_executable(native71_army_late_event_service_wire_test EXCLUDE_FROM_ALL
      tests/native71_army_late_event_service_wire_test.cpp)
    target_link_libraries(native71_army_late_event_service_wire_test PRIVATE
      xar_ck3_12002_runtime kernel32)
    target_include_directories(native71_army_late_event_service_wire_test PRIVATE include)
    target_compile_features(native71_army_late_event_service_wire_test PRIVATE cxx_std_20)
    target_compile_definitions(native71_army_late_event_service_wire_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(native71_army_late_event_service_wire_test PRIVATE
        /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
    endif()
  endif()
endif()
