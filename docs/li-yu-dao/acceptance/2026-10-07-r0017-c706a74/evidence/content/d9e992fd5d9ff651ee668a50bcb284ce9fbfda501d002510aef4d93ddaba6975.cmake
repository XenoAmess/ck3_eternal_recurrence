# Two new complete commander packets; genuine production runtime linked once.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_commander_movement_metadata_test
    src/ck3_12004_commander_movement_metadata_test.cpp)
  target_include_directories(xar_ck3_12004_commander_movement_metadata_test PRIVATE include)
  target_compile_features(xar_ck3_12004_commander_movement_metadata_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_commander_movement_metadata_test PUBLIC
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_commander_movement_metadata_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy)
    target_link_options(xar_ck3_12004_commander_movement_metadata_test PRIVATE /OPT:REF)
  endif()
  target_link_libraries(xar_ck3_12004_commander_movement_metadata_test PRIVATE
    xar_ck3_12002_runtime user32)
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12004_commander_movement_metadata_wire")
  add_test(NAME xar_ck3_12004_commander_movement_metadata
    COMMAND xar_ck3_12004_commander_movement_metadata_test
      "${CMAKE_BINARY_DIR}/ck3_12004_commander_movement_metadata_wire")
endif()
