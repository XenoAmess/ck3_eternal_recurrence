if(BUILD_TESTING AND WIN32)
  set(xar_root_core_council4_target xar_ck3_12004_campaign_root_core_council_whole_test)
  add_executable(${xar_root_core_council4_target}
    src/ck3_12004_campaign_root_core_council_whole_test.cpp)
  target_include_directories(${xar_root_core_council4_target} PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include" "${CMAKE_CURRENT_SOURCE_DIR}/src")
  target_link_libraries(${xar_root_core_council4_target} PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol user32)
  target_compile_features(${xar_root_core_council4_target} PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(${xar_root_core_council4_target} PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  endif()
endif()
