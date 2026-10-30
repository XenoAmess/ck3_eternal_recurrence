# Real actual4 full-ID resource proxy/reader regression. Native memory is fixture-owned.
# Old .2/.3 five-argument positive domain is preserved; actual4 opts into explicit signed full32.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_actor_resource_canonical_domain12004_test
    tests/actor_resource_canonical_domain12004_test.cpp
    src/ck3_12004_snapshot_foundation.cpp
    src/ck3_12002_actor_resources.cpp
    src/ck3_12004_abi_profile.cpp)
  target_include_directories(xar_ck3_actor_resource_canonical_domain12004_test BEFORE PRIVATE include research)
  target_compile_features(xar_ck3_actor_resource_canonical_domain12004_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_actor_resource_canonical_domain12004_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_link_libraries(xar_ck3_actor_resource_canonical_domain12004_test PRIVATE kernel32 user32)
  if(MSVC)
    target_compile_options(xar_ck3_actor_resource_canonical_domain12004_test PRIVATE /O2 /W4 /WX /permissive- /EHsc /utf-8 /MP1 /Gy)
    target_link_options(xar_ck3_actor_resource_canonical_domain12004_test PRIVATE /OPT:REF /INCREMENTAL:NO)
  endif()
  add_test(NAME xar_ck3_actor_resource_canonical_domain12004
    COMMAND xar_ck3_actor_resource_canonical_domain12004_test "${CMAKE_CURRENT_BINARY_DIR}/actor-resource-canonical-domain12004-wire")
  set_tests_properties(xar_ck3_actor_resource_canonical_domain12004 PROPERTIES TIMEOUT 30)
endif()
