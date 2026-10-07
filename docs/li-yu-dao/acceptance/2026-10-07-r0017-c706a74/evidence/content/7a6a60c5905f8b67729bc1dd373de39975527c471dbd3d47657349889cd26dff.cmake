# The Strength collector calls the scoped ordered-core reader after DATA capture.
get_property(ordered_refill_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(ordered_refill_target IN LISTS ordered_refill_targets)
  get_target_property(ordered_refill_sources ${ordered_refill_target} SOURCES)
  if("src/ck3_12002_army.cpp" IN_LIST ordered_refill_sources OR
     "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST ordered_refill_sources)
    if(NOT "src/ck3_12003_scoped_ordered_refill_core.cpp" IN_LIST ordered_refill_sources AND
       NOT "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_scoped_ordered_refill_core.cpp" IN_LIST ordered_refill_sources)
      target_sources(${ordered_refill_target} PRIVATE src/ck3_12003_scoped_ordered_refill_core.cpp)
    endif()
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12003_scoped_ordered_refill_core_test
    src/ck3_12003_scoped_ordered_refill_core_test.cpp
    src/ck3_12003_scoped_ordered_refill_core.cpp)
  target_include_directories(xar_bridge_ck3_12003_scoped_ordered_refill_core_test PRIVATE include)
  target_compile_features(xar_bridge_ck3_12003_scoped_ordered_refill_core_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12003_scoped_ordered_refill_core_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12003_scoped_ordered_refill_core_test PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_bridge_ck3_12003_scoped_ordered_refill_core_test
    COMMAND xar_bridge_ck3_12003_scoped_ordered_refill_core_test
      --wire-dir "${CMAKE_CURRENT_BINARY_DIR}/scoped-ordered-refill-wire")
endif()
