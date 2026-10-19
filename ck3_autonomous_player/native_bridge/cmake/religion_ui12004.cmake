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
