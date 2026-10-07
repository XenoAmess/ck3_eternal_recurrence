# Actual army response write diagnosis, without changing the existing frame cap.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_army_strength_result_write_diagnostic_v1_test
    src/army_strength_result_write_diagnostic_v1_test.cpp
    src/protocol.cpp)
  target_include_directories(xar_bridge_army_strength_result_write_diagnostic_v1_test PRIVATE include)
  target_compile_features(xar_bridge_army_strength_result_write_diagnostic_v1_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_army_strength_result_write_diagnostic_v1_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_army_strength_result_write_diagnostic_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_army_strength_result_write_diagnostic_v1_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_army_strength_result_write_diagnostic_v1
    COMMAND xar_bridge_army_strength_result_write_diagnostic_v1_test)
endif()
