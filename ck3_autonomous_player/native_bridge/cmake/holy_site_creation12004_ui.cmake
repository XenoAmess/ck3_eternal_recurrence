# Default OFF; the read-only query flag never enables UI actions.
# The core cmake file declares this option before selecting the core sources.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/holy_site_creation12004_navigation.cpp)
# Source-specific opt-in definitions; keep the default OFF option.
# Keep the unconditional runtime adapter target_sources and default OFF option.
# The adapter is a runtime source; the original UI serializer is a bridge source.
# Both targets must already exist before this include is processed.
if(XAR_ENABLE_HOLY_SITE_CREATION_UI12004)
  get_filename_component(_xar_creation_native_dir
    "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
  set_property(SOURCE
    "${_xar_creation_native_dir}/src/holy_site_creation12004_navigation.cpp"
    TARGET_DIRECTORY xar_ck3_12002_runtime
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_ENABLE_HOLY_SITE_CREATION_UI12004=1>")
  set_property(SOURCE
    "${_xar_creation_native_dir}/src/ingame_ui_navigation_v1.cpp"
    TARGET_DIRECTORY xar_ck3_bridge
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_ENABLE_HOLY_SITE_CREATION_UI12004=1>")
  unset(_xar_creation_native_dir)
endif()
