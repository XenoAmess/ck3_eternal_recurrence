# Connected Entry provider symbols always compile once with existing Runtime dependencies.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/entry_final_getter_capture_12004.cpp
  src/entry_final_side_capture_12004.cpp
  src/entry_final_side_capture_12004_serializer.cpp
  src/entry_final_writer_capture_12004.cpp
  src/entry_final_writer_capture_12004_serializer.cpp
  src/entry_preceding_capture_12004.cpp
  src/entry_preceding_capture_12004_serializer.cpp)

option(XAR_ENABLE_ENTRY_FINAL_SIDE_CAPTURE_12004
  "Install connected Entry preceding, final Side and natural getter observers" ON)
if(XAR_ENABLE_ENTRY_FINAL_SIDE_CAPTURE_12004)
  target_compile_definitions(xar_ck3_bridge PRIVATE
    XAR_ENABLE_ENTRY_FINAL_SIDE_CAPTURE_12004=1)
endif()

if(BUILD_TESTING AND WIN32)
  add_executable(entry_final_side_capture_12004_connected_test EXCLUDE_FROM_ALL
    tests/entry_final_side_capture_12004_connected_test.cpp
    tests/entry_preceding_capture_12004_cases.cpp
    tests/entry_final_getter_capture_12004_new_cases.cpp)
  target_link_libraries(entry_final_side_capture_12004_connected_test PRIVATE
    xar_ck3_12002_runtime kernel32)
  target_include_directories(entry_final_side_capture_12004_connected_test PRIVATE include tests)
  target_compile_features(entry_final_side_capture_12004_connected_test PRIVATE cxx_std_20)
  target_compile_definitions(entry_final_side_capture_12004_connected_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(entry_final_side_capture_12004_connected_test PRIVATE
      /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()
  # Optional sole argv is a fresh wire output directory; no substitute Runtime methods.
endif()
