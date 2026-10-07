# Source-defined current incoming whole-DATA prefix inputs; only new fixture.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_current_detachment_data src/ck3_12003_current_detachment_data_test.cpp)
  target_link_libraries(xar_ck3_12003_current_detachment_data PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12003_current_detachment_data PRIVATE include)
  target_compile_features(xar_ck3_12003_current_detachment_data PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_detachment_data PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_detachment_data PRIVATE /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_current_detachment_data PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_detachment_data COMMAND xar_ck3_12003_current_detachment_data
    "${CMAKE_CURRENT_BINARY_DIR}/current-detachment-data-wire")
endif()
