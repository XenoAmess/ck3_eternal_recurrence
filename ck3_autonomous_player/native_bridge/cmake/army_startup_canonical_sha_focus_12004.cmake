# One new canonical-digest startup regression; selected explicitly without older cases.
# Existing producer/scope production registrations and startup guards are unchanged.
if(BUILD_TESTING AND WIN32)
  add_executable(army_startup_canonical_sha_focus EXCLUDE_FROM_ALL
    tests/army_startup_canonical_sha_focus.cpp
    src/actual_army_pre_date_prefix_observer_12004.cpp
    src/actual_army_daily_assault_preparation_observer_12004.cpp
    src/actual_army_assault_placement_observer_12004.cpp
    src/army_natural_phase_scope_12004.cpp)
  target_include_directories(army_startup_canonical_sha_focus PRIVATE include)
  target_compile_features(army_startup_canonical_sha_focus PRIVATE cxx_std_20)
  target_compile_definitions(army_startup_canonical_sha_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE _ITERATOR_DEBUG_LEVEL=0)
  target_link_libraries(army_startup_canonical_sha_focus PRIVATE xar_ck3_12002_runtime kernel32)
  if(MSVC)
    set_property(TARGET army_startup_canonical_sha_focus PROPERTY MSVC_RUNTIME_LIBRARY MultiThreadedDLL)
    target_compile_options(army_startup_canonical_sha_focus PRIVATE
      /EHsc /W4 /WX /permissive- /utf-8 /UNDEBUG)
  endif()
endif()
