# Independent exact BB3 read profiles. Neither option opens military actions.
option(XAR_CK3_ENABLE_26757580_ARMY_FULL58 "BB3 paused nonempty Army base Full with per-call owner admission" OFF)
option(XAR_CK3_ENABLE_26757580_WAR_IDENTITY58 "BB3 paused War identity and guarded score partial DATA" OFF)
if(XAR_CK3_ENABLE_26757580_ARMY_FULL58 OR XAR_CK3_ENABLE_26757580_WAR_IDENTITY58)
  if(NOT XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1)
    message(FATAL_ERROR "Military58 requires the exact BB3 basic Full owner profile")
  endif()
endif()
if(XAR_CK3_ENABLE_26757580_ARMY_FULL58)
  if(NOT XAR_CK3_ENABLE_1210_ARMY_BASE_FULL_V1)
    target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_1210_player_armies_v1.cpp src/ck3_1210_army_base_v1.cpp)
    set_property(SOURCE src/ck3_1210_adapter.cpp src/ck3_1210_full_snapshot_v1.cpp APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_1210_ARMY_BASE_FULL_V1=1>"
      "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_HOTFIX58_ONLY_ARMY_IMPLEMENTATION=1>")
    if(NOT XAR_CK3_ENABLE_1210_ACTIVE_WARS_IDENTITY_V1)
      target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_1210_active_wars_v1.cpp)
    endif()
  endif()
  set_property(SOURCE src/ck3_1210_adapter.cpp src/ck3_1210_full_snapshot_v1.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_26757580_ARMY_FULL58=1>")
endif()
if(XAR_CK3_ENABLE_26757580_WAR_IDENTITY58)
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_1210_active_wars_hotfix_frame58.cpp)
  if(NOT XAR_CK3_ENABLE_1210_ACTIVE_WARS_IDENTITY_V1)
    target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_1210_active_wars_frame_v1.cpp src/ck3_1210_active_wars_serialize_v1.cpp)
    if(NOT XAR_CK3_ENABLE_1210_ARMY_BASE_FULL_V1 AND NOT XAR_CK3_ENABLE_26757580_ARMY_FULL58)
      target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_1210_active_wars_v1.cpp)
    endif()
  endif()
  set_property(SOURCE src/ck3_1210_adapter.cpp src/ck3_1210_personal_gold_frame_v1.cpp src/ck3_1210_active_wars_frame_v1.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_26757580_WAR_IDENTITY58=1>")
  set_property(SOURCE src/bridge.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_26757580_WAR_IDENTITY58=1>")
endif()
