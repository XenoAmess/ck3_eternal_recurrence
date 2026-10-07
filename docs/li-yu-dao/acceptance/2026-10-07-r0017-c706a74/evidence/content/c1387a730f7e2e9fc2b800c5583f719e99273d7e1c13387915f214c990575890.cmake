# Source prepared only. Entry owner includes this after runtime target creation.
set(XAR_CK3_12004_LIFESTYLE_DOMAIN_SOURCES
  src/ck3_12004_lifestyle_bindings.cpp
  src/ck3_12004_lifestyle_state.cpp
  src/ck3_12004_stock_focus_legality.cpp
  src/ck3_12004_stock_perk_legality.cpp
  src/ck3_12004_lifestyle_selection_native_commands.cpp
  src/ck3_12004_lifestyle_selection_action.cpp
  src/ck3_12004_lifestyle_formal_wire.cpp
  src/ck3_12004_lifestyle_transport.cpp)
if(XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE ${XAR_CK3_12004_LIFESTYLE_DOMAIN_SOURCES})
endif()
if(BUILD_TESTING AND WIN32 AND XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1)
  add_executable(xar_ck3_12004_lifestyle_first_v1_test
    tests/ck3_12004_lifestyle_first_v1_test.cpp
    src/player_lifestyle_snapshot_v1.cpp
    src/player_lifestyle_window_candidates_v1.cpp
    src/player_lifestyle_window_source_adapter_v1.cpp
    src/player_lifestyle_selection_action_v1.cpp
    src/player_lifestyle_selection_native_adapter_v1.cpp
    src/player_lifestyle_stock_perk_legality_v1.cpp
    src/player_lifestyle_stock_focus_legality_v1.cpp
    src/player_lifestyle_formal_precondition_v1.cpp
    src/player_lifestyle_formal_wire_v1.cpp)
  target_link_libraries(xar_ck3_12004_lifestyle_first_v1_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt)
  target_include_directories(xar_ck3_12004_lifestyle_first_v1_test PRIVATE include)
  target_compile_features(xar_ck3_12004_lifestyle_first_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_lifestyle_first_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_lifestyle_first_v1_test PRIVATE
      /W4 /permissive- /EHsc /UNDEBUG /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_lifestyle_first_v1
    COMMAND xar_ck3_12004_lifestyle_first_v1_test --wire-dir
      "${CMAKE_CURRENT_BINARY_DIR}/lifestyle-first-12004-wire")
endif()
