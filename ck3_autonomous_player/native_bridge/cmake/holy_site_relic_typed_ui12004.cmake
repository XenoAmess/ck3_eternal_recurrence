# Include after the bridge and optional focused test targets exist.
option(XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004 "Exact4 source-bound HolySite relic UI selection candidate" OFF)
option(XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004 "Exact4 original relic button actions with production preview adapter" OFF)
set(_xar_relic_ui_sources
 "${CMAKE_CURRENT_LIST_DIR}/../src/ck3_12004_holy_site_relic_actions.cpp"
 "${CMAKE_CURRENT_LIST_DIR}/../src/ck3_12004_holy_site_relic_actions_json.cpp"
 "${CMAKE_CURRENT_LIST_DIR}/../src/holy_site_relic_request12004.cpp"
 "${CMAKE_CURRENT_LIST_DIR}/../src/holy_site_relic_navigation12004.cpp")
foreach(_target xar_ck3_bridge xar_ck3_ingame_ui_navigation_v1_test)
 if(TARGET ${_target})
  target_sources(${_target} PRIVATE ${_xar_relic_ui_sources})
 endif()
endforeach()
if(XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004)
 set_property(SOURCE "${CMAKE_CURRENT_LIST_DIR}/../src/ck3_12004_holy_site_relic_actions.cpp"
  APPEND PROPERTY COMPILE_DEFINITIONS XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004=1)
endif()
if(XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004)
 if(NOT XAR_ENABLE_HOLY_SITE_RELIC_TYPED_UI12004)
  message(FATAL_ERROR "Original relic actions also require typed UI opt-in")
 endif()
 # Source scope keeps the existing bridge closure untouched. The target-name
 # generator expression prevents this shared source property enabling the
 # legacy navigation test's action lane without its production preview deps.
 set_property(SOURCE "${CMAKE_CURRENT_LIST_DIR}/../src/holy_site_relic_navigation12004.cpp"
  APPEND PROPERTY COMPILE_DEFINITIONS
  "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_ENABLE_HOLY_SITE_RELIC_BUTTON_ACTION12004=1>")
 if(TARGET xar_ck3_bridge)
  target_sources(xar_ck3_bridge PRIVATE "${CMAKE_CURRENT_LIST_DIR}/../src/holy_site_relic_action_preview_adapter12004.cpp")
 endif()
endif()
unset(_xar_relic_ui_sources)
