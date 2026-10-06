# Root includes this after the protocol target in the selected native tree.
# The fixture source is part of that same tree; no external source is needed.
if(NOT DEFINED XAR_CLERGY_WHOLE_NATIVE_ROOT)
  set(XAR_CLERGY_WHOLE_NATIVE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
endif()
if(NOT DEFINED XAR_CLERGY_WHOLE_WIRE_DIR)
  set(XAR_CLERGY_WHOLE_WIRE_DIR "${CMAKE_BINARY_DIR}/clergy-candidate-terms-native-whole-first")
endif()

set(xar_clergy_whole_target xar_ck3_12003_clergy_candidate_terms_whole_mailbox_test)
add_executable(${xar_clergy_whole_target}
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12002.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12002_query_mailbox.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12003_abi_profile.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12003_adapter.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/main_thread_query_mailbox_v1.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/religion_rite_governance12002_clergy.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/religion_rite_governance12002_clergy_mailbox.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12003_county_conversion.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12002_council_candidates.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12002_council_gates.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12003_clergy_candidate_terms.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/council_composition_candidates_public_v1.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/council_composition_candidates_public_v1_serializer.cpp"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src/ck3_12003_clergy_candidate_terms_whole_mailbox_test.cpp")
target_include_directories(${xar_clergy_whole_target} PRIVATE
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/include"
  "${XAR_CLERGY_WHOLE_NATIVE_ROOT}/src")
# The real Crozier adapter references existing runtime binders. Import their
# actual definitions and PUBLIC usage requirements rather than fixture stubs.
target_link_libraries(${xar_clergy_whole_target} PRIVATE
  xar_bridge_protocol xar_ck3_12002_runtime user32)
target_compile_features(${xar_clergy_whole_target} PRIVATE cxx_std_20)
target_compile_definitions(${xar_clergy_whole_target} PRIVATE
  XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1=1)
if(MSVC)
  target_compile_options(${xar_clergy_whole_target} PRIVATE
    /O2 /UNDEBUG /W4 /WX /Gy /permissive- /EHsc /utf-8)
  target_link_options(${xar_clergy_whole_target} PRIVATE /OPT:REF)
endif()
file(MAKE_DIRECTORY "${XAR_CLERGY_WHOLE_WIRE_DIR}")
add_test(NAME xar_ck3_12003_clergy_candidate_terms_whole_mailbox_first
  COMMAND ${xar_clergy_whole_target} "${XAR_CLERGY_WHOLE_WIRE_DIR}")
