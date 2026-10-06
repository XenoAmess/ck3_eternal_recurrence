# Add the actual readonly collector to each existing army reader link closure.
get_property(ordered_besieging_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(ordered_besieging_target IN LISTS ordered_besieging_targets)
  get_target_property(ordered_besieging_sources ${ordered_besieging_target} SOURCES)
  if(("src/ck3_12002_army.cpp" IN_LIST ordered_besieging_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST ordered_besieging_sources) AND
     NOT "src/ck3_12003_ordered_besieging_refill_inputs.cpp" IN_LIST ordered_besieging_sources)
    target_sources(${ordered_besieging_target} PRIVATE
      src/ck3_12003_ordered_besieging_refill_inputs.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_bridge_ck3_12003_ordered_besieging_refill_inputs_test
    src/ck3_12003_ordered_besieging_refill_inputs_test.cpp
    src/ck3_12003_ordered_besieging_refill_inputs.cpp
    src/ck3_12003_scoped_ordered_refill_core.cpp)
  target_include_directories(xar_bridge_ck3_12003_ordered_besieging_refill_inputs_test PRIVATE include)
  target_compile_features(xar_bridge_ck3_12003_ordered_besieging_refill_inputs_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_bridge_ck3_12003_ordered_besieging_refill_inputs_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_bridge_ck3_12003_ordered_besieging_refill_inputs_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_bridge_ck3_12003_ordered_besieging_refill_inputs_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_bridge_ck3_12003_ordered_besieging_refill_inputs_test
    COMMAND xar_bridge_ck3_12003_ordered_besieging_refill_inputs_test
      "${CMAKE_CURRENT_BINARY_DIR}/ordered-besieging-refill-inputs-wire")
endif()
