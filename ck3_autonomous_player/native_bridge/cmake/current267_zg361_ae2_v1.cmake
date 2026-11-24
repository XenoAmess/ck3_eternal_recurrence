# Independent current859 AE2 finite consumer. Disabled by default.
option(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1 "Enable exact current267 finite AE2 consumer" OFF)
get_filename_component(_zg_ae2_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(_zg_ae2_units
 src/ck3_121003_zg361_ae226785313_wire_v1.cpp
 src/ck3_121003_zg361_ae226785313_raw_v1.cpp
 src/ck3_121003_zg361_ae226785313_owner_v1.cpp
 src/ck3_121003_zg361_ae226785313_dispatch_v1.cpp)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
 foreach(u IN LISTS _zg_ae2_units)
  target_sources(xar_ck3_12002_runtime PRIVATE "${_zg_ae2_root}/${u}")
 endforeach()
 if(XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1)
  foreach(dependency IN ITEMS CORE_ROUTE_V1 LETTER_V1 LETTER_SET_V1)
   if(NOT XAR_CK3_ENABLE_121003_26785313_${dependency})
    message(FATAL_ERROR "AE2 requires actual current ${dependency} DATA mechanics")
   endif()
  endforeach()
  # The same mailbox storage is used exclusively by each exact image profile.
  # Current859 slot36 must be empty before this one typed callback is installed;
  # neither legacy major-decision capability nor callback is made available.
  set(_zg_ae2_runtime_shared src/ck3_121003_readonly26785313_v1.cpp src/ck3_121003_core_route26785313_v1.cpp src/ck3_121003_personal_gold26785313_v2.cpp)
  foreach(u IN LISTS _zg_ae2_units _zg_ae2_runtime_shared)
   set_property(SOURCE "${_zg_ae2_root}/${u}" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1=1>")
  endforeach()
 endif()
endif()
if(WIN32 AND TARGET xar_ck3_bridge AND XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1)
 foreach(u IN ITEMS src/bridge.cpp src/game_adapter.cpp)
  set_property(SOURCE "${_zg_ae2_root}/${u}" APPEND PROPERTY COMPILE_DEFINITIONS "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_26785313_ZG361_AE2_V1=1>")
 endforeach()
endif()
