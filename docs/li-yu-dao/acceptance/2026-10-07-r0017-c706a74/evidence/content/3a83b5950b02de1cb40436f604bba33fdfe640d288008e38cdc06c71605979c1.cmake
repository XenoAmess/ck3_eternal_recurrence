# Every existing Army-reader object closure needs the new production collector TU.
get_property(removal_context_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(removal_context_target IN LISTS removal_context_targets)
  get_target_property(removal_context_sources ${removal_context_target} SOURCES)
  if(("src/ck3_12002_army.cpp" IN_LIST removal_context_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST removal_context_sources) AND
     NOT "src/ck3_12003_current_assault_removal_reference.cpp" IN_LIST removal_context_sources AND
     NOT "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_current_assault_removal_reference.cpp" IN_LIST removal_context_sources)
    target_sources(${removal_context_target} PRIVATE src/ck3_12003_current_assault_removal_reference.cpp)
  endif()
endforeach()

# Actual current receiver identities and conditional first-removal manager context.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_current_assault_removal_references
    src/ck3_12003_current_assault_removal_reference_test.cpp)
  target_link_libraries(xar_ck3_12003_current_assault_removal_references PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12003_current_assault_removal_references PRIVATE include)
  target_compile_features(xar_ck3_12003_current_assault_removal_references PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_assault_removal_references PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_assault_removal_references PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_current_assault_removal_references PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_assault_removal_references
    COMMAND xar_ck3_12003_current_assault_removal_references
      "${CMAKE_CURRENT_BINARY_DIR}/current-assault-removal-reference-wire")
endif()
