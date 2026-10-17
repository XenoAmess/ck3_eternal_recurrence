# Exact4 source candidate. No build or execution occurred in authoring this file.
option(XAR_ENABLE_COUNTY_PREVIEW_RELATION_INPUTS_12004
  "Observe a naturally reached relation entry/return inside the current county P stage" OFF)
if(XAR_ENABLE_COUNTY_PREVIEW_RELATION_INPUTS_12004)
  if(NOT XAR_ENABLE_COUNTY_PREVIEW_P_TRACE_12004)
    message(FATAL_ERROR "County relation inputs require the existing county P trace")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/ck3_12004_county_relation_inputs_hook.cpp
    src/ck3_12004_county_relation_inputs_reader.cpp)
  target_compile_definitions(xar_ck3_12002_runtime PUBLIC
    XAR_ENABLE_COUNTY_PREVIEW_RELATION_INPUTS_12004=1)
endif()

# Authored synthetic fixture only; never included in the default build/CTest.
if(BUILD_TESTING)
  add_executable(xar_ck3_county_relation_inputs_fixture EXCLUDE_FROM_ALL
    tests/ck3_12004_county_relation_inputs_context_test.cpp
    src/ck3_12004_county_relation_inputs_reader.cpp)
  target_include_directories(xar_ck3_county_relation_inputs_fixture PRIVATE include)
  target_compile_features(xar_ck3_county_relation_inputs_fixture PRIVATE cxx_std_20)
  target_link_libraries(xar_ck3_county_relation_inputs_fixture PRIVATE xar_ck3_12002_runtime)
  if(MSVC)
    target_compile_options(xar_ck3_county_relation_inputs_fixture PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
endif()
