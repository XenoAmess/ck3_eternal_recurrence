# Exact-build readonly pre-date pending and dated inputs; FIRST fixture targets.
# External integration recipe only. Root owns applying this to the repository.
# Requires adopted entry roster963ff7f and pending-update DTO/query/serializer hooks.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12003_current_pre_date_pending_update_test
    src/ck3_12003_pre_date_pending_update_test.cpp)
  target_link_libraries(xar_bridge_ck3_12003_current_pre_date_pending_update_test
    PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_bridge_ck3_12003_current_pre_date_pending_update_test PRIVATE include)
  target_compile_features(xar_bridge_ck3_12003_current_pre_date_pending_update_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12003_current_pre_date_pending_update_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12003_current_pre_date_pending_update_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_ck3_12003_current_pre_date_pending_update_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_ck3_12003_current_pre_date_pending_update_test
    COMMAND xar_bridge_ck3_12003_current_pre_date_pending_update_test --wire-dir
      "${CMAKE_CURRENT_BINARY_DIR}/current-pre-date-pending-update-wire")
endif()

# External proposal only. Root owns integration/formal build; this is not in repo.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_pre_date_dated_append_12003_test
    src/ck3_12003_pre_date_dated_append_test.cpp)
  target_link_libraries(xar_bridge_pre_date_dated_append_12003_test PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_bridge_pre_date_dated_append_12003_test PRIVATE include)
  target_compile_features(xar_bridge_pre_date_dated_append_12003_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_pre_date_dated_append_12003_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_pre_date_dated_append_12003_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_pre_date_dated_append_12003_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_pre_date_dated_append_12003_test
    COMMAND xar_bridge_pre_date_dated_append_12003_test
      "${CMAKE_CURRENT_BINARY_DIR}/pre-date-dated-append-wire")
endif()
