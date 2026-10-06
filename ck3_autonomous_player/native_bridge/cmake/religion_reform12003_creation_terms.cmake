# Same-query .3 leaf only; no new query switch or permission.
if(XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/religion_reform12003_creation_terms.cpp)
endif()

if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1)
  add_executable(xar_ck3_religion_reform12003_creation_terms_test
    tests/religion_reform12003_creation_terms_test.cpp)
  # The .3 adapter and mailbox use these existing production helper definitions.
  target_sources(xar_ck3_religion_reform12003_creation_terms_test PRIVATE
    src/current_first_heir_relationship_v1.cpp
    src/observed_heir_marriage_private_v1.cpp)
  target_link_libraries(xar_ck3_religion_reform12003_creation_terms_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  target_include_directories(xar_ck3_religion_reform12003_creation_terms_test PRIVATE include)
  target_compile_features(xar_ck3_religion_reform12003_creation_terms_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_religion_reform12003_creation_terms_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1)
  if(MSVC)
    target_compile_options(xar_ck3_religion_reform12003_creation_terms_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_religion_reform12003_creation_terms_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_religion_reform12003_creation_terms_first_six
    COMMAND xar_ck3_religion_reform12003_creation_terms_test
      "${CMAKE_CURRENT_BINARY_DIR}/religion-creation-terms-first-wire")
endif()
