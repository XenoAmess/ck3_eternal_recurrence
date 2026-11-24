# Original Living0.1.3 finite zero-day consumer. All options remain OFF.
option(XAR_CK3_ENABLE_121003_26785313_LIVING_V1 "Enable fixed Living original8 consumer" OFF)
get_filename_component(_living_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(_living_units
 "src/ck3_121003_living_inventory26785313_raw_v1.cpp"
 "src/ck3_121003_living_inventory26785313_verify_v1.cpp"
 "src/ck3_121003_living_inventory26785313_wire_v1.cpp"
 "src/ck3_121003_living_inventory26785313_owner_v1.cpp"
 "src/ck3_121003_living_inventory26785313_dispatch_v1.cpp"
 "src/ck3_121003_living_owner26785313_v1.cpp"
 "src/ck3_121003_living_ui26785313_wire_v1.cpp"
 "src/ck3_121003_living_ui26785313_owner_v1.cpp"
 "src/ck3_121003_living_ui26785313_dispatch_v1.cpp"
 "src/ck3_121003_living_manage26785313_raw_v1.cpp"
 "src/ck3_121003_living_entry26785313_wire_v1.cpp"
 "src/ck3_121003_living_entry26785313_owner_v1.cpp"
 "src/ck3_121003_living_entry26785313_dispatch_v1.cpp"
)
set(_living_flags LIVING_V1 LIVING_INVENTORY_V1 LIVING_UI_V1 LIVING_WEAPON_V1 LIVING_EVENT_V1 LIVING_DETAIL_V1 LIVING_ENTRY_V1 LYD_V1)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
 foreach(u IN LISTS _living_units)
  target_sources(xar_ck3_12002_runtime PRIVATE "${_living_root}/${u}")
 endforeach()
 target_link_libraries(xar_ck3_12002_runtime PRIVATE bcrypt)
 if(XAR_CK3_ENABLE_121003_26785313_LIVING_V1)
  foreach(dependency IN ITEMS CORE_ROUTE_V1 LYD_V1)
   if(NOT XAR_CK3_ENABLE_121003_26785313_${dependency})
    message(FATAL_ERROR "Living original8 needs actual current ${dependency} mechanics; historical permissions cannot substitute")
   endif()
  endforeach()
  set(_living_shared_runtime src/ck3_121003_readonly26785313_v1.cpp src/ck3_121003_core_route26785313_v1.cpp src/ck3_121003_personal_gold26785313_v2.cpp)
  foreach(u IN LISTS _living_units _living_shared_runtime)
   foreach(f IN LISTS _living_flags)
    set_property(SOURCE "${_living_root}/${u}" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_${f}=1>")
   endforeach()
  endforeach()
 endif()
endif()
if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_26785313_LIVING_V1)
 foreach(u IN ITEMS src/bridge.cpp src/game_adapter.cpp)
  foreach(f IN LISTS _living_flags)
   set_property(SOURCE "${_living_root}/${u}" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_26785313_${f}=1>")
  endforeach()
 endforeach()
endif()
