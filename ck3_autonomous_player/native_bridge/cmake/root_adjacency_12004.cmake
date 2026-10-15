# Owned memory only; includes the exact production reader in a separate test TU.
if(BUILD_TESTING AND WIN32 AND MSVC)
  add_executable(xar_ck3_12004_root_adjacency_focused_test
    src/ck3_12004_root_adjacency_focused_test.cpp)
  target_include_directories(xar_ck3_12004_root_adjacency_focused_test PRIVATE include src)
  target_compile_features(xar_ck3_12004_root_adjacency_focused_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_root_adjacency_focused_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  target_compile_options(xar_ck3_12004_root_adjacency_focused_test PRIVATE
    /W4 /WX /permissive- /EHsc /utf-8 /Gy /Gw)
  target_link_options(xar_ck3_12004_root_adjacency_focused_test PRIVATE /OPT:REF /INCREMENTAL:NO)
  add_test(NAME xar_ck3_12004_root_adjacency_focused_test
    COMMAND xar_ck3_12004_root_adjacency_focused_test)
endif()
