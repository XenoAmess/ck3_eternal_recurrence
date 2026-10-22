# A narrow selection of the existing whole owner-mailbox producer. It links
# the real context implementation without enabling catalogue or conversion.
if(BUILD_TESTING AND WIN32 AND XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
  add_executable(xar_ck3_12004_player_pilgrimage_traits_test
    src/ck3_12004_religion_adopted_addons_whole_test.cpp)
  target_link_libraries(xar_ck3_12004_player_pilgrimage_traits_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol)
  target_include_directories(xar_ck3_12004_player_pilgrimage_traits_test PRIVATE include)
  target_compile_features(xar_ck3_12004_player_pilgrimage_traits_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_player_pilgrimage_traits_test PRIVATE
    NOMINMAX XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1
    XAR_CK3_PILGRIMAGE_TRAITS_ONLY_FIXTURE_V1=1)
  if(MSVC)
    target_compile_options(xar_ck3_12004_player_pilgrimage_traits_test PRIVATE /UNDEBUG /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_player_pilgrimage_traits_test
    COMMAND xar_ck3_12004_player_pilgrimage_traits_test
      "${CMAKE_CURRENT_BINARY_DIR}/wire/player_pilgrimage_traits12004.json")
endif()
