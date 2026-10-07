# Coordinator adopts after the candidate; child does not edit CMake/build/test.
get_property(besieging_reader_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(besieging_reader_target IN LISTS besieging_reader_targets)
  get_target_property(besieging_reader_sources ${besieging_reader_target} SOURCES)
  if(("src/ck3_12002_army.cpp" IN_LIST besieging_reader_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST besieging_reader_sources) AND
     NOT "src/ck3_12003_current_province_besieging_contributors.cpp" IN_LIST besieging_reader_sources)
    target_sources(${besieging_reader_target} PRIVATE
      src/ck3_12003_current_province_besieging_contributors.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  # Reuse only the existing qualified reader's production link context, never
  # its test main or prior case execution. This retains current optional TU hooks.
  get_target_property(besieging_production_sources
    xar_ck3_12003_current_province_supply_contributors SOURCES)
  list(FILTER besieging_production_sources EXCLUDE REGEX "_test\\.cpp$")
  list(APPEND besieging_production_sources
    src/ck3_12002_province.cpp
    src/ck3_12003_current_province_besieging_contributors_test.cpp)
  list(REMOVE_DUPLICATES besieging_production_sources)
  add_executable(xar_ck3_12003_current_province_besieging_contributors
    ${besieging_production_sources})
  target_include_directories(xar_ck3_12003_current_province_besieging_contributors PRIVATE include)
  target_compile_features(xar_ck3_12003_current_province_besieging_contributors PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_province_besieging_contributors PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_province_besieging_contributors PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_current_province_besieging_contributors PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_province_besieging_contributors
    COMMAND xar_ck3_12003_current_province_besieging_contributors
      "${CMAKE_CURRENT_BINARY_DIR}/current-province-besieging-contributors-wire")
endif()
