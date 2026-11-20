# Explicit current-build V2; old personal Gold V1 and all old tuples stay closed.
option(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2 "Enable exact267 paused personal Gold V2 signed64-string candidate" OFF)
if(XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2)
  if(NOT XAR_CK3_ENABLE_121003_26785313_READONLY_V1 OR NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
    message(FATAL_ERROR "Exact267 Gold V2 requires its reviewed readonly and Core route")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_personal_gold26785313_v2.cpp)
  # Affect only these actual dispatch/profile TUs; do not invalidate every runtime/bridge OBJ.
  set_property(SOURCE src/ck3_121003_personal_gold26785313_v2.cpp src/ck3_1210_adapter.cpp
      src/game_adapter.cpp src/bridge.cpp APPEND PROPERTY COMPILE_DEFINITIONS
      "$<$<OR:$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>,$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>>:XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2=1>")
endif()
if(BUILD_TESTING)
  foreach(_variant IN ITEMS on off)
    add_executable(xar_ck3_121003_26785313_personal_gold_v2_${_variant}_test EXCLUDE_FROM_ALL
      src/ck3_121003_personal_gold26785313_v2_test.cpp src/ck3_121003_personal_gold26785313_v2.cpp
      src/ck3_1210_core_frame_v1.cpp src/ck3_1210_thread_runtime.cpp src/game_adapter_capabilities.cpp)
    set(_gold_target xar_ck3_121003_26785313_personal_gold_v2_${_variant}_test)
    target_include_directories(${_gold_target} PRIVATE include src)
    target_compile_features(${_gold_target} PRIVATE cxx_std_20)
    target_compile_definitions(${_gold_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN
      XAR_CK3_26785313_OFFLINE_FIXTURE=1 XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1=1)
    if(_variant STREQUAL "on")
      target_compile_definitions(${_gold_target} PRIVATE XAR_CK3_ENABLE_121003_26785313_PERSONAL_GOLD_V2=1)
    endif()
    target_link_libraries(${_gold_target} PRIVATE bcrypt)
    if(MSVC)
      target_compile_options(${_gold_target} PRIVATE /W4 /WX /permissive- /EHsc)
    endif()
    add_test(NAME ${_gold_target} COMMAND ${_gold_target} --synthetic-image)
  endforeach()
endif()
