# Independent narrow reader; existing HolySite/adoption DTO sources unchanged.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_holy_site_relic_context.cpp
  src/ck3_12004_holy_site_modifier_aggregate.cpp
  src/ck3_12004_holy_site_modifier_aggregate_json.cpp
  src/ck3_12004_holy_site_relic_recognition_matrix.cpp
  src/ck3_12004_holy_site_relic_recognition_matrix_json.cpp
  src/ck3_12004_holy_site_relic_context_json.cpp)
if(BUILD_TESTING)
  add_executable(xar_ck3_12004_holy_site_relic_context_test
    src/ck3_12004_holy_site_relic_context_test.cpp
    src/ck3_12004_holy_site_relic_context.cpp
    src/ck3_12004_holy_site_modifier_aggregate.cpp
    src/ck3_12004_holy_site_modifier_aggregate_json.cpp
    src/construction_character_modifier_2c4d1d0_12004.cpp
    src/conception_modifier_context_12004.cpp
    src/construction_scaled_key_2c4d530_12004.cpp
    src/ck3_12004_holy_site_relic_recognition_matrix.cpp
    src/ck3_12004_holy_site_relic_recognition_matrix_json.cpp
    src/ck3_12004_holy_site_relic_context_json.cpp)
  target_include_directories(xar_ck3_12004_holy_site_relic_context_test PRIVATE include)
  target_compile_features(xar_ck3_12004_holy_site_relic_context_test PRIVATE cxx_std_20)
  if(WIN32)
    target_compile_definitions(xar_ck3_12004_holy_site_relic_context_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  endif()
  if(MSVC)
    target_compile_options(xar_ck3_12004_holy_site_relic_context_test PRIVATE /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME xar_ck3_12004_holy_site_relic_context_test
    COMMAND xar_ck3_12004_holy_site_relic_context_test "${CMAKE_CURRENT_BINARY_DIR}/holy-site-relic-12004-wire")

  # One bounded new-reader qualification. Existing relic suites are not repeated.
  add_executable(xar_ck3_12004_holy_site_relic_recognition_matrix_test
    src/ck3_12004_holy_site_relic_recognition_matrix_test.cpp
    src/ck3_12004_holy_site_relic_recognition_matrix.cpp
    src/ck3_12004_holy_site_relic_recognition_matrix_json.cpp
    src/ck3_12004_holy_site_relic_context.cpp
    src/ck3_12004_holy_site_modifier_aggregate.cpp
    src/ck3_12004_holy_site_modifier_aggregate_json.cpp
    src/construction_character_modifier_2c4d1d0_12004.cpp
    src/conception_modifier_context_12004.cpp
    src/construction_scaled_key_2c4d530_12004.cpp
    src/ck3_12004_holy_site_relic_context_json.cpp
    src/ck3_12004_holy_site_relic_action_context.cpp
    src/ck3_12004_holy_site_relic_action_context_json.cpp
    src/ck3_12004_holy_site_relic_permissions.cpp
    src/ck3_12004_holy_site_relic_permissions_json.cpp)
  target_include_directories(xar_ck3_12004_holy_site_relic_recognition_matrix_test PRIVATE include)
  target_compile_features(xar_ck3_12004_holy_site_relic_recognition_matrix_test PRIVATE cxx_std_20)
  set_target_properties(xar_ck3_12004_holy_site_relic_recognition_matrix_test PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/effect-observation-tests")
  if(WIN32)
    target_compile_definitions(xar_ck3_12004_holy_site_relic_recognition_matrix_test PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    target_link_libraries(xar_ck3_12004_holy_site_relic_recognition_matrix_test PRIVATE bcrypt)
  endif()
  if(MSVC)
    target_compile_options(xar_ck3_12004_holy_site_relic_recognition_matrix_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8)
  endif()
endif()
