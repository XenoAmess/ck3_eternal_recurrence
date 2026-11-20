# Candidate fragment: include after xar_ck3_12002_runtime exists. This selects
# only the independent current binder; it adds no Bridge handler or capability.
option(XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1
  "Enable exact 26785313 command-image bindings (not control/Full admission)" OFF)
get_filename_component(_xar_current267_commands_native_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
if(WIN32 AND TARGET xar_ck3_12002_runtime)
  target_sources(xar_ck3_12002_runtime PRIVATE
    "${_xar_current267_commands_native_root}/src/ck3_121003_commands26785313_v1.cpp")
  # Scope the switch to this one TU and this production target. The same
  # binder source in NoGame targets keeps each test target's own 0/1 setting.
  set_property(SOURCE
    "${_xar_current267_commands_native_root}/src/ck3_121003_commands26785313_v1.cpp"
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1=$<BOOL:${XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1}>>")
endif()
if(BUILD_TESTING AND WIN32)
  foreach(mode IN ITEMS off on)
    if(mode STREQUAL "on")
      set(enabled 1)
    else()
      set(enabled 0)
    endif()
    set(target xar_ck3_121003_26785313_commands_v1_${mode}_test)
    add_executable(${target}
      "${_xar_current267_commands_native_root}/src/ck3_121003_commands26785313_v1_test.cpp"
      "${_xar_current267_commands_native_root}/src/ck3_121003_commands26785313_v1.cpp"
      "${_xar_current267_commands_native_root}/src/ck3_1210_commands.cpp")
    target_include_directories(${target} PRIVATE "${_xar_current267_commands_native_root}/include")
    target_compile_features(${target} PRIVATE cxx_std_20)
    target_compile_definitions(${target} PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      XAR_CK3_26785313_COMMANDS_OFFLINE_FIXTURE=1
      XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1=${enabled})
    if(MSVC)
      target_compile_options(${target} PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
    endif()
    add_test(NAME ${target} COMMAND ${target})
  endforeach()
endif()
