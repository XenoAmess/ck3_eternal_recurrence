# Exact retained original reader for the finite baseline; excluded from production.
if(NOT BUILD_TESTING)
  message(FATAL_ERROR "B11 baseline requires selected finite targets")
endif()
add_executable(xar_ck3_12004_pilgrimage_full10_baseline_host_fixture EXCLUDE_FROM_ALL
  "${CMAKE_SOURCE_DIR}/tests/activity_typed_full_cost_v1_test.cpp"
  "${CMAKE_SOURCE_DIR}/tests/b11_stage5_owned/baseline_activity_typed_full_cost_v1.cpp"
  "${CMAKE_SOURCE_DIR}/src/activity_cost_slot12_passive_v1.cpp"
  "${CMAKE_SOURCE_DIR}/src/activity_planner_diag_v1.cpp")
target_compile_features(xar_ck3_12004_pilgrimage_full10_baseline_host_fixture PRIVATE cxx_std_20)
target_include_directories(xar_ck3_12004_pilgrimage_full10_baseline_host_fixture PRIVATE "${CMAKE_SOURCE_DIR}/include")
target_compile_definitions(xar_ck3_12004_pilgrimage_full10_baseline_host_fixture PRIVATE
  XAR_B10_EXPECT_BASELINE_HOST_GATE=1 NOMINMAX WIN32_LEAN_AND_MEAN)
set_property(TARGET xar_ck3_12004_pilgrimage_full10_baseline_host_fixture PROPERTY INTERPROCEDURAL_OPTIMIZATION FALSE)
if(MSVC)
  target_compile_options(xar_ck3_12004_pilgrimage_full10_baseline_host_fixture PRIVATE /Od /UNDEBUG /EHsc /utf-8)
endif()
