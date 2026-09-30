# Include only after xar_ck3_bridge has been created. The integration owner must
# separately wire the private registered application-main query executor.
option(XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1
  "Bind the private exact-build read-only H2743 stock predicate sources" OFF)
target_sources(xar_ck3_bridge PRIVATE
  "${CMAKE_CURRENT_LIST_DIR}/../src/h2743_stock_predicate_reader_v1.cpp"
  "${CMAKE_CURRENT_LIST_DIR}/../src/h2743_stock_native_source_adapter_v1.cpp")
target_compile_definitions(xar_ck3_bridge PRIVATE
  XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1=$<BOOL:${XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1}>)

option(XAR_CK3_BUILD_H2743_STOCK_PREDICATE_FIXTURE_V1
  "Build the isolated fake-memory fixture for the private H2743 reader" OFF)
if(XAR_CK3_BUILD_H2743_STOCK_PREDICATE_FIXTURE_V1)
  add_executable(xar_ck3_h2743_stock_predicate_reader_v1_test
    "${CMAKE_CURRENT_LIST_DIR}/../src/h2743_stock_predicate_reader_v1.cpp"
    "${CMAKE_CURRENT_LIST_DIR}/../src/h2743_stock_predicate_reader_v1_test.cpp")
  target_include_directories(xar_ck3_h2743_stock_predicate_reader_v1_test PRIVATE
    "${CMAKE_CURRENT_LIST_DIR}/../include")
  target_compile_features(xar_ck3_h2743_stock_predicate_reader_v1_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_h2743_stock_predicate_reader_v1_test PRIVATE
      /W4 /permissive- /EHsc)
  endif()
  if(BUILD_TESTING)
    add_test(NAME xar_ck3_h2743_stock_predicate_reader_v1
      COMMAND xar_ck3_h2743_stock_predicate_reader_v1_test)
  endif()
endif()
