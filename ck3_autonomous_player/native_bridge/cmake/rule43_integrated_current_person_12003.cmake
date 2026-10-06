# The integrated current-person collector calls both production source readers.
get_property(rule43_input_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(rule43_input_target IN LISTS rule43_input_targets)
  get_target_property(rule43_input_sources ${rule43_input_target} SOURCES)
  if("src/ck3_12003_context_sources.cpp" IN_LIST rule43_input_sources OR
     "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_context_sources.cpp" IN_LIST rule43_input_sources)
    foreach(rule43_dependency IN ITEMS ck3_12003_rule43_diac_sources.cpp diac_literal_numeric_inputs_12003.cpp)
      if(NOT "src/${rule43_dependency}" IN_LIST rule43_input_sources AND
         NOT "${CMAKE_CURRENT_SOURCE_DIR}/src/${rule43_dependency}" IN_LIST rule43_input_sources)
        target_sources(${rule43_input_target} PRIVATE "src/${rule43_dependency}")
      endif()
    endforeach()
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_rule43_integrated_current_person_test
    tests/rule43_integrated_current_person_12003_test.cpp
    src/ck3_12003_context_sources.cpp
    src/ck3_12003_current_stored_context.cpp
    src/ck3_12003_rule43_diac_sources.cpp
    src/diac_literal_numeric_inputs_12003.cpp)
  target_include_directories(xar_ck3_12003_rule43_integrated_current_person_test PRIVATE include)
  target_compile_features(xar_ck3_12003_rule43_integrated_current_person_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_rule43_integrated_current_person_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_12003_rule43_integrated_current_person_test PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12003_rule43_integrated_current_person_test
    COMMAND xar_ck3_12003_rule43_integrated_current_person_test
      "${CMAKE_CURRENT_BINARY_DIR}/rule43_integrated_current_person_12003_wire.json")
endif()
