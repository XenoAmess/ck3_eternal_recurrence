# Whole production object closure matches the actual successful joined FIRST.
if(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_sway_terminal.cpp")
  if(WIN32 AND BUILD_TESTING)
    add_executable(xar_ck3_12004_sway_terminal_first
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_sway_terminal_first.cpp"
      $<TARGET_OBJECTS:xar_ck3_bridge>)
    target_link_libraries(xar_ck3_12004_sway_terminal_first PRIVATE
      xar_ck3_12002_runtime xar_bridge_protocol bcrypt
      $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
    target_include_directories(xar_ck3_12004_sway_terminal_first PRIVATE include)
    target_compile_features(xar_ck3_12004_sway_terminal_first PRIVATE cxx_std_20)
    target_compile_definitions(xar_ck3_12004_sway_terminal_first PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
    if(MSVC)
      target_compile_options(xar_ck3_12004_sway_terminal_first PRIVATE
        /O2 /W4 /WX /EHsc /permissive- /utf-8 /Gy)
      target_link_options(xar_ck3_12004_sway_terminal_first PRIVATE /OPT:REF /INCREMENTAL:NO)
    endif()
  endif()
endif()
