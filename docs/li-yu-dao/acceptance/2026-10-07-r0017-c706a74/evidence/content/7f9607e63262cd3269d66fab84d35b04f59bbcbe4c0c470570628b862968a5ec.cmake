# Reuse the actual target scope in every production Army reader link closure.
get_property(target_preparation_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(target_preparation_target IN LISTS target_preparation_targets)
  get_target_property(target_preparation_sources ${target_preparation_target} SOURCES)
  if(("src/ck3_12002_army.cpp" IN_LIST target_preparation_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST target_preparation_sources) AND
     NOT "src/ck3_12003_ordered_besieging_fixed_chunk0_preparation.cpp" IN_LIST target_preparation_sources)
    target_sources(${target_preparation_target} PRIVATE
      src/ck3_12003_ordered_besieging_fixed_chunk0_preparation.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_ordered_besieging_fixed_chunk0_preparation_test
    src/ck3_12003_ordered_besieging_fixed_chunk0_preparation_test.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_scoped_ordered_refill_core.cpp
    src/ck3_12003_ordered_besieging_refill_inputs.cpp
    src/ck3_12003_fixed_chunk0_preparation.cpp
    src/ck3_12003_ordered_besieging_fixed_chunk0_preparation.cpp)
  target_include_directories(xar_ck3_12003_ordered_besieging_fixed_chunk0_preparation_test PRIVATE include)
  target_compile_features(xar_ck3_12003_ordered_besieging_fixed_chunk0_preparation_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_ordered_besieging_fixed_chunk0_preparation_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_ordered_besieging_fixed_chunk0_preparation_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_ordered_besieging_fixed_chunk0_preparation_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_ordered_besieging_fixed_chunk0_preparation_test
    COMMAND xar_ck3_12003_ordered_besieging_fixed_chunk0_preparation_test
      "${CMAKE_CURRENT_BINARY_DIR}/ordered-besieging-fixed-chunk0-preparation-wire")
endif()
