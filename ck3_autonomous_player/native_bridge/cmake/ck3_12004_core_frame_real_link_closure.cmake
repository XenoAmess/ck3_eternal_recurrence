# Replacement for ck3_12004_core_frame_real_link_closure.cmake.
# Include after the original xar_ck3_12004_core_frame_v1_test declaration.
# Preparation only; no configure, build, import or test has been run.
#
# Keep the original fixture TU and reuse the real production bridge objects.
# Setting SOURCES removes the previous partial production TU additions.
set_property(TARGET xar_ck3_12004_core_frame_v1_test PROPERTY SOURCES
  "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12004_core_frame_v1_test.cpp"
  "$<TARGET_OBJECTS:xar_ck3_bridge>"
)

# TARGET_OBJECTS does not transfer the bridge's PRIVATE link dependencies.
# These are the actual bridge dependencies in the strict03 source and Ninja rule.
# Normal Windows system libraries remain supplied by the existing MSVC toolchain.
set_property(TARGET xar_ck3_12004_core_frame_v1_test PROPERTY LINK_LIBRARIES
  xar_bridge_protocol xar_ck3_12002_runtime bcrypt
)

# The original target retains its include path, C++20, platform definitions,
# /W4 /WX /permissive- /EHsc /UNDEBUG and registered CTest command.
# Apply function packaging only to the fixture TU, never to production targets.
if(MSVC)
  target_compile_options(xar_ck3_12004_core_frame_v1_test PRIVATE /Gy)
  target_link_options(xar_ck3_12004_core_frame_v1_test PRIVATE /OPT:REF)
endif()

