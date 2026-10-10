# Full conditional provider; the default resolver is registered in the parent M5 list.
if(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/conception_pair_provider_12004.cpp
    src/conception_reverse_close_or_extended_12004.cpp)
endif()

if(BUILD_TESTING AND WIN32)
  # One new six-TU compound.17 exports cases into55's sole permanent main.
  add_executable(xar_current_household_conception_provider_focus EXCLUDE_FROM_ALL
    tests/current_household_conception_provider_focus.cpp
    src/current_first_heir_relationship_v1.cpp
    src/conception_pair_provider_12004.cpp
    src/conception_pair_provider_12004_test.cpp
    src/conception_reverse_close_or_extended_12004.cpp
    src/conception_secondary_context_12004.cpp)
  target_include_directories(xar_current_household_conception_provider_focus PRIVATE include)
  target_compile_features(xar_current_household_conception_provider_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_current_household_conception_provider_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1)
  if(MSVC)
    target_compile_options(xar_current_household_conception_provider_focus PRIVATE
      /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()
  # Root captures stdout for the authored new Python strict consumer.
endif()
