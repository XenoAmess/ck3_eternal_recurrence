include_guard(GLOBAL)
# Explicit, excluded compile qualification for the two existing own-RAM inputs.
# These object targets neither load the DLL nor launch an application.
option(XAR_CK3_BUILD_OWNED_SENTINEL142_QUALIFICATION
  "Compile portable current owned-army/sentinel qualification inputs" OFF)
if(NOT BUILD_TESTING OR NOT XAR_CK3_BUILD_OWNED_SENTINEL142_QUALIFICATION)
  return()
endif()
if(NOT XAR_CK3_ENABLE_121003_FULL111 OR NOT XAR_CK3_ENABLE_121003_OWNED_ARMY123)
  message(FATAL_ERROR "Owned sentinel142 qualification requires explicit Full111 and owned identities")
endif()
get_filename_component(_owned142_root "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
set(_owned142_common
  XAR_CK3_ENABLE_121003_FULL111=1 XAR_CK3_ENABLE_121003_OWNED_ARMY123=1
  XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1 XAR_CK3_ENABLE_1210_FULL_SNAPSHOT_V1=1
  XAR_CK3_ENABLE_1210_CORE_CONTROL_V1=1 XAR_CK3_ENABLE_1210_FULL_CLOCK_V1=1
  XAR_CK3_ENABLE_1210_APPLICATION_EXIT_V1=1 XAR_CK3_ENABLE_1210_DATE_SENTINEL_V1=1
  XAR_CK3_ENABLE_26757580_OBSERVER_SCOPE92=1 NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
foreach(_kind IN ITEMS bridge owned owner)
  add_library(xar_owned142_${_kind}_fixture OBJECT
    "${_owned142_root}/src/qualification/${_kind}142_fixture.cpp")
  set_target_properties(xar_owned142_${_kind}_fixture PROPERTIES EXCLUDE_FROM_ALL TRUE)
  target_include_directories(xar_owned142_${_kind}_fixture PRIVATE
    "${_owned142_root}/include" "${_owned142_root}/src" "${_owned142_root}/research")
  target_compile_features(xar_owned142_${_kind}_fixture PRIVATE cxx_std_20)
  target_compile_definitions(xar_owned142_${_kind}_fixture PRIVATE ${_owned142_common}
    XAR_BRIDGE_VERSION="${PROJECT_VERSION}")
  if(NOT _kind STREQUAL "owner")
    target_compile_definitions(xar_owned142_${_kind}_fixture PRIVATE XAR_CK3_ENABLE_ADMISSION_DIAG125=1)
  endif()
  if(MSVC)
    target_compile_options(xar_owned142_${_kind}_fixture PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
endforeach()
add_custom_target(xar_ck3_121003_owned_sentinel142_fixture_compile
  DEPENDS xar_owned142_bridge_fixture xar_owned142_owned_fixture xar_owned142_owner_fixture)
# Executable qualification links these inputs against the exact normal
# production object graph. See the pinned source recipe; this compile target
# alone makes no NoGame execution, DLL, CTest or whole-build claim.
unset(_owned142_root)
unset(_owned142_common)
