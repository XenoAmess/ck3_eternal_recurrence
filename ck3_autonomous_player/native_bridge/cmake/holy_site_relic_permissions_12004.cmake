# Narrow permission/candidate reader only; no action registration or new native flag.
target_sources(xar_ck3_12002_runtime PRIVATE
 src/ck3_12004_holy_site_relic_permissions.cpp
 src/ck3_12004_holy_site_relic_permissions_json.cpp)
if(BUILD_TESTING)
 add_executable(xar_ck3_12004_holy_site_relic_permissions_test
  src/ck3_12004_holy_site_relic_permissions_test.cpp
  src/ck3_12004_holy_site_relic_permissions.cpp
  src/ck3_12004_holy_site_relic_permissions_json.cpp
  src/ck3_12004_holy_site_relic_context.cpp)
 target_include_directories(xar_ck3_12004_holy_site_relic_permissions_test PRIVATE include)
 target_compile_features(xar_ck3_12004_holy_site_relic_permissions_test PRIVATE cxx_std_20)
 if(WIN32)
  target_compile_definitions(xar_ck3_12004_holy_site_relic_permissions_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
 endif()
 if(MSVC)
  target_compile_options(xar_ck3_12004_holy_site_relic_permissions_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
 endif()
 add_test(NAME xar_ck3_12004_holy_site_relic_permissions_test COMMAND xar_ck3_12004_holy_site_relic_permissions_test "${CMAKE_CURRENT_BINARY_DIR}/holy-site-relic-permissions-12004-wire")
endif()
