# Include once after xar_ck3_bridge is defined. No older build fallback.
option(XAR_ENABLE_RELIGION_UI12004_PRESENTATION "Exact 1.20.0.4 typed Faith/Character presentation candidate" OFF)
target_sources(xar_ck3_bridge PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}/../src/religion_ui12004.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/../src/religion_ui12004_navigation.cpp")
if(XAR_ENABLE_RELIGION_UI12004_PRESENTATION)
  target_compile_definitions(xar_ck3_bridge PRIVATE XAR_ENABLE_RELIGION_UI12004_PRESENTATION=1)
  if(NOT XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1)
    # Context lifecycle only. Do not enable/register the ordinary mailbox or Send.
    target_sources(xar_ck3_12002_runtime PRIVATE
      "${CMAKE_CURRENT_LIST_DIR}/../src/ordinary_character_interaction_v1.cpp"
      "${CMAKE_CURRENT_LIST_DIR}/../src/ordinary_interaction_request_v1.cpp")
  endif()
endif()
if(TARGET xar_ck3_ingame_ui_navigation_v1_test)
  target_sources(xar_ck3_ingame_ui_navigation_v1_test PRIVATE
    "${CMAKE_CURRENT_LIST_DIR}/../src/religion_ui12004.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../src/religion_ui12004_navigation.cpp")
  if(XAR_ENABLE_RELIGION_UI12004_PRESENTATION)
    target_compile_definitions(xar_ck3_ingame_ui_navigation_v1_test PRIVATE XAR_ENABLE_RELIGION_UI12004_PRESENTATION=1)
  endif()
endif()

# The enabled war-overview registry compiles the same production navigation TU.
if(TARGET xar_ck3_adapter_registry_test AND XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1)
  target_sources(xar_ck3_adapter_registry_test PRIVATE
    "${CMAKE_CURRENT_LIST_DIR}/../src/religion_ui12004.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../src/religion_ui12004_navigation.cpp")
  if(XAR_ENABLE_RELIGION_UI12004_PRESENTATION)
    target_compile_definitions(xar_ck3_adapter_registry_test PRIVATE XAR_ENABLE_RELIGION_UI12004_PRESENTATION=1)
  endif()
endif()

# Read-only Title observation uses the shared query route without enabling actions.
# Navigation is also an optional runtime source. All production navigation
# consumers already link this runtime; keep the implementation in that one library.
target_sources(xar_ck3_12002_runtime PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}/../src/title_window12004.cpp")
if(TARGET xar_ck3_ingame_ui_navigation_v1_test)
  add_executable(xar_ck3_title_window12004_test
    "${CMAKE_CURRENT_LIST_DIR}/../src/title_window12004.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../tests/title_window12004_test.cpp")
  target_include_directories(xar_ck3_title_window12004_test PRIVATE "${CMAKE_CURRENT_LIST_DIR}/../include")
  target_compile_features(xar_ck3_title_window12004_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_title_window12004_test PRIVATE /W4 /WX /UNDEBUG /utf-8 /permissive- /EHsc)
  else()
    target_compile_options(xar_ck3_title_window12004_test PRIVATE -UNDEBUG)
  endif()
  add_test(NAME xar_ck3_title_window12004_test COMMAND xar_ck3_title_window12004_test)
endif()
