# Actual4 ports for two existing, unflagged routes.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_features.cpp
  src/ck3_12004_tactical_daily_sentinel.cpp
  src/ck3_12004_default_routes_mailbox.cpp
)

add_executable(xar_ck3_12004_default_manifest_sentinel_test
  src/ck3_12004_default_manifest_sentinel_test.cpp
  src/tactical_daily_sentinel_v1.cpp
)
target_include_directories(xar_ck3_12004_default_manifest_sentinel_test
  PRIVATE include)
target_compile_features(xar_ck3_12004_default_manifest_sentinel_test
  PRIVATE cxx_std_20)
# Uses the actual existing runtime and the actual existing sentinel TU.
# Runtime PUBLIC definitions propagate without copying private option lists.
target_link_libraries(xar_ck3_12004_default_manifest_sentinel_test
  PRIVATE xar_ck3_12002_runtime user32)
if(MSVC)
  target_compile_options(xar_ck3_12004_default_manifest_sentinel_test
    PRIVATE /W4 /WX /permissive- /EHsc /Gy)
  target_link_options(xar_ck3_12004_default_manifest_sentinel_test
    PRIVATE /OPT:REF)
endif()
add_test(NAME xar_ck3_12004_default_manifest_sentinel
  COMMAND xar_ck3_12004_default_manifest_sentinel_test
    "${CMAKE_BINARY_DIR}/ck3_12004_default_manifest_sentinel_wire")
