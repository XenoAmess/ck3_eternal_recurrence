# Explicit-only OFF branch of the reviewed frontier fixture; never link runtime.
if(BUILD_TESTING)
  add_executable(xar_test_gui_refill_frontier_continuation_off_12004 EXCLUDE_FROM_ALL
    fixtures/gui_refill_frontier_continuation_12004_fixture.cpp)
  target_compile_features(xar_test_gui_refill_frontier_continuation_off_12004 PRIVATE cxx_std_20)
  target_include_directories(xar_test_gui_refill_frontier_continuation_off_12004 PRIVATE include)
  target_compile_definitions(xar_test_gui_refill_frontier_continuation_off_12004 PRIVATE
    XAR_ENABLE_GUI_REFILL_PARENT_PREFIX_12004=1 XAR_ENABLE_GUI_REFILL_FRONTIER_CONTINUATION_12004=0)
  if(MSVC)
    target_compile_options(xar_test_gui_refill_frontier_continuation_off_12004 PRIVATE /EHsc /W4 /WX)
  endif()
endif()
