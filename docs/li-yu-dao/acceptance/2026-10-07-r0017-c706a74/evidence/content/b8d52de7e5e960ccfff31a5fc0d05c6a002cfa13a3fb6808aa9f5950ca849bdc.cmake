# Produce the real collector/production command_result body for the sole
# Python wholewire FIRST consumer. Session sidecars are synthetic fixture data.
if(BUILD_TESTING AND WIN32)
  if(NOT DEFINED XAR_SEEK_INDULGENCES_TERMS_WIRE_DIR)
    set(XAR_SEEK_INDULGENCES_TERMS_WIRE_DIR
      "${CMAKE_BINARY_DIR}/player-seek-indulgences-terms-wholewire-first")
  endif()
  set(xar_seek_indulgences_terms_target
    xar_ck3_12003_player_seek_indulgences_terms_test)
  add_executable(${xar_seek_indulgences_terms_target}
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/player_seek_indulgences_terms_12003_test.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_seek_indulgences_terms.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_player_seek_indulgences_wire.cpp")
  target_include_directories(${xar_seek_indulgences_terms_target} PRIVATE include)
  target_compile_features(${xar_seek_indulgences_terms_target} PRIVATE cxx_std_20)
  target_compile_definitions(${xar_seek_indulgences_terms_target} PRIVATE
    NOMINMAX XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1)
  if(MSVC)
    target_compile_options(${xar_seek_indulgences_terms_target} PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  file(MAKE_DIRECTORY "${XAR_SEEK_INDULGENCES_TERMS_WIRE_DIR}")
  add_test(NAME xar_ck3_12003_player_seek_indulgences_terms_wholewire_first
    COMMAND ${xar_seek_indulgences_terms_target}
      "${XAR_SEEK_INDULGENCES_TERMS_WIRE_DIR}")
endif()
