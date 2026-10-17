option(XAR_CK3_ENABLE_G2_PLAYER_HOLY_SITE_CREATION_CONTEXT_PRIVATE_QUERY_V1
  "Exact4 original HolySite creation candidates and selected context; read-only" OFF)
option(XAR_ENABLE_HOLY_SITE_CREATION_UI12004
  "Exact4 typed HolySite creation UI open and selection; no Create command" OFF)
if(XAR_CK3_ENABLE_G2_PLAYER_HOLY_SITE_CREATION_CONTEXT_PRIVATE_QUERY_V1 OR
   XAR_ENABLE_HOLY_SITE_CREATION_UI12004)
  if(NOT XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1)
    message(FATAL_ERROR "HolySite creation requires the existing player religion owner mailbox")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/holy_site_creation12004.cpp
    src/holy_site_creation_create_once12004.cpp
    src/holy_site_creation12004_json.cpp
    src/holy_site_creation12004_mailbox.cpp)
endif()
# Source-specific opt-in definitions; keep the default OFF option.
# Keep the preceding option/dependency/core target_sources logic unchanged.
# The include runs after xar_ck3_12002_runtime exists. TARGET_DIRECTORY selects
# its declaration directory; the expression also excludes tests in that scope.
if(XAR_CK3_ENABLE_G2_PLAYER_HOLY_SITE_CREATION_CONTEXT_PRIVATE_QUERY_V1)
  get_filename_component(_xar_creation_native_dir
    "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
  set_property(SOURCE
    "${_xar_creation_native_dir}/src/ck3_12002_religion_mailbox.cpp"
    TARGET_DIRECTORY xar_ck3_12002_runtime
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_G2_PLAYER_HOLY_SITE_CREATION_CONTEXT_PRIVATE_QUERY_V1=1>")
  unset(_xar_creation_native_dir)
endif()
