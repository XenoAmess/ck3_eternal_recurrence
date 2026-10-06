# FIRST actual-role total martial through the production whole Army query.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_current_commander_total_martial_test
    src/ck3_12003_current_commander_martial_test.cpp)
  target_include_directories(xar_ck3_12003_current_commander_total_martial_test PRIVATE include)
  target_compile_features(xar_ck3_12003_current_commander_total_martial_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_commander_total_martial_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_commander_total_martial_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy)
    target_link_options(xar_ck3_12003_current_commander_total_martial_test PRIVATE /OPT:REF)
  endif()
  target_link_libraries(xar_ck3_12003_current_commander_total_martial_test PRIVATE
    xar_ck3_12002_runtime user32)
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_current_commander_total_martial_wire")
  add_test(NAME xar_ck3_12003_current_commander_total_martial
    COMMAND xar_ck3_12003_current_commander_total_martial_test
      "${CMAKE_BINARY_DIR}/ck3_12003_current_commander_total_martial_wire")
endif()
