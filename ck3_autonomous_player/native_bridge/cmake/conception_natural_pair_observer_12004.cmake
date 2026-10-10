# One natural parent/provider/sample instance lives in the Bridge DLL.
# The pure copied-input threshold is available in the existing shared runtime.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/conception_pair_threshold_consumer_12004.cpp)

option(XAR_NATIVE71_CONCEPTION_PAIR_PROVIDER_PASSIVE_12004
  "Install the natural conception parent, provider and sample observers" ON)
if(XAR_NATIVE71_CONCEPTION_PAIR_PROVIDER_PASSIVE_12004)
  target_sources(xar_ck3_bridge PRIVATE
    src/conception_pair_passive_12004.cpp
    src/conception_pair_passive_12004_serializer.cpp
    src/conception_pair_provider_passive_12004.cpp
    src/conception_pair_provider_passive_12004_serializer.cpp
    src/conception_sample_passive_12004.cpp)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_NATIVE71_CONCEPTION_PAIR_PROVIDER_PASSIVE_12004=1)
endif()

if(BUILD_TESTING AND WIN32)
  # One permanent main executes the four new exported groups in the authored batch.
  add_executable(xar_conception_pair_natural_connected_focus EXCLUDE_FROM_ALL
    tests/conception_pair_natural_connected_focus_12004.cpp
    src/conception_pair_passive_12004.cpp
    src/conception_pair_passive_12004_serializer.cpp
    src/conception_pair_passive_12004_test.cpp
    src/conception_sample_passive_12004.cpp
    src/conception_sample_passive_12004_fixture.cpp
    src/conception_pair_provider_passive_12004.cpp
    src/conception_pair_provider_passive_12004_serializer.cpp
    src/conception_pair_provider_passive_12004_test.cpp
    src/conception_pair_threshold_consumer_12004.cpp
    src/conception_pair_threshold_consumer_12004_connected_cases.cpp
    src/person_natural_lineage_clock_12004.cpp)
  target_include_directories(xar_conception_pair_natural_connected_focus PRIVATE include)
  target_compile_features(xar_conception_pair_natural_connected_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_conception_pair_natural_connected_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    set_property(TARGET xar_conception_pair_natural_connected_focus
      PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
    target_compile_options(xar_conception_pair_natural_connected_focus PRIVATE
      /EHsc /W4 /utf-8 /UNDEBUG $<$<NOT:$<CONFIG:Debug>>:/O2>)
  endif()
  # Root retains stdout JSON for the one authored owned-journal consumer.
endif()
