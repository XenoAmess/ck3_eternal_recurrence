# One new actual4 candidate sibling; existing runtime/protocol providers are linked.
if(XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_clergy_candidate_terms.cpp")
endif()

if(BUILD_TESTING AND WIN32 AND XAR_CK3_ENABLE_G2_PLAYER_CLERGY_APPOINTMENT_PRIVATE_QUERY_V1)
  set(xar_clergy_terms4_target xar_ck3_12004_clergy_candidate_terms_whole_mailbox_test)
  add_executable(${xar_clergy_terms4_target}
    src/ck3_12004_clergy_candidate_terms_whole_mailbox_test.cpp)
  target_include_directories(${xar_clergy_terms4_target} PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include" "${CMAKE_CURRENT_SOURCE_DIR}/src")
  target_link_libraries(${xar_clergy_terms4_target} PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  target_compile_features(${xar_clergy_terms4_target} PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(${xar_clergy_terms4_target} PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
endif()
