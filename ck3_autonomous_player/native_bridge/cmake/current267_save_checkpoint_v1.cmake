# Independent current267 Core checkpoint route. Include after current267_commands_v1.cmake.
option(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1
  "Enable exact current267 Core-only checkpoint submission (not physical SAVE/Full)" OFF)
get_filename_component(_xar_current267_save_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
  if(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1 AND
      NOT XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1)
    message(FATAL_ERROR "current267 Core SAVE requires the reviewed independent current267 command binder")
  endif()
  if(XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1 AND NOT XAR_CK3_ENABLE_121003_26785313_CORE_ROUTE_V1)
    message(FATAL_ERROR "current267 Core SAVE requires the exact current267 Core route")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE
    "${_xar_current267_save_root}/src/ck3_121003_save_checkpoint26785313_v1.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_save_checkpoint26785313_wire_v1.cpp")
  # Do not churn every runtime TU. Only these two TUs implement this feature.
  set_property(SOURCE
    "${_xar_current267_save_root}/src/ck3_121003_save_checkpoint26785313_v1.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_readonly26785313_v1.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_core_route26785313_v1.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_personal_gold26785313_v2.cpp"
    "${_xar_current267_save_root}/src/ck3_1210_adapter.cpp"
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1=$<BOOL:${XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1}>>")
endif()
if(WIN32 AND TARGET xar_ck3_bridge)
  set_property(SOURCE "${_xar_current267_save_root}/src/bridge.cpp"
    "${_xar_current267_save_root}/src/game_adapter.cpp" APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1=$<BOOL:${XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1}>>")
endif()
if(BUILD_TESTING AND WIN32)
  set(target xar_ck3_121003_26785313_save_checkpoint_claim_wire_test)
  add_executable(${target}
    "${_xar_current267_save_root}/src/ck3_121003_save_checkpoint26785313_test.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_save_checkpoint26785313_v1.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_save_checkpoint26785313_wire_v1.cpp")
  target_include_directories(${target} PRIVATE "${_xar_current267_save_root}/include")
  target_compile_features(${target} PRIVATE cxx_std_20)
  target_compile_definitions(${target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1=0)
  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME ${target} COMMAND ${target})
endif()

if(BUILD_TESTING AND WIN32)
  set(target xar_ck3_121003_26785313_save_actual_owner_ON_test)
  add_executable(${target}
    "${_xar_current267_save_root}/src/ck3_121003_save_checkpoint26785313_owner_test.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_commands26785313_v1.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_save_checkpoint26785313_v1.cpp"
    "${_xar_current267_save_root}/src/ck3_121003_readonly26785313_v1.cpp"
    "${_xar_current267_save_root}/src/ck3_1210_commands.cpp"
    "${_xar_current267_save_root}/src/ck3_1210_core.cpp"
    "${_xar_current267_save_root}/src/ck3_1210_thread_runtime.cpp")
  target_include_directories(${target} PRIVATE "${_xar_current267_save_root}/include" "${_xar_current267_save_root}/src")
  target_compile_features(${target} PRIVATE cxx_std_20)
  target_compile_definitions(${target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_26785313_COMMANDS_OFFLINE_FIXTURE=1
    XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1=1
    XAR_CK3_ENABLE_121003_26785313_CORE_CHECKPOINT_SAVE_V1=1)
  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME ${target} COMMAND ${target})
endif()
