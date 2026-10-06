# Run the full production DLL build before this focused synthetic wire case.
# It compiles the actual collection/provider/profile/serializer implementations
# but does not manufacture a private command_result or whole-service receipt.
if(BUILD_TESTING)
  add_executable(xar_ck3_12003_realm_law_succession_profile_wire_test
    tests/ck3_12003_realm_law_succession_profile_fixture.cpp
    src/ck3_12002_realm_law.cpp
    src/ck3_12002_realm_law_candidate_collection.cpp
    src/ck3_12002_realm_law_active_collection.cpp
    src/ck3_12002_realm_law_final_terms.cpp
    src/ck3_12002_realm_law_components.cpp
    src/realm_law_candidate_collection_11906.cpp
    src/realm_law_active_collection_11906.cpp)
  target_include_directories(xar_ck3_12003_realm_law_succession_profile_wire_test
    PRIVATE include)
  target_compile_features(xar_ck3_12003_realm_law_succession_profile_wire_test
    PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_12003_realm_law_succession_profile_wire_test
      PRIVATE /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME xar_ck3_12003_realm_law_succession_profile_wire_test
    COMMAND xar_ck3_12003_realm_law_succession_profile_wire_test
      "${CMAKE_CURRENT_BINARY_DIR}/realm_law_succession_profile_12003.synthetic.json")
endif()
