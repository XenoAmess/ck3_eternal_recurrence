# Same-query Army reader dependency, for runtime and isolated fixtures.
get_property(current_land_rate_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(current_land_rate_target IN LISTS current_land_rate_targets)
  get_target_property(current_land_rate_sources ${current_land_rate_target} SOURCES)
  if(("src/ck3_12002_army.cpp" IN_LIST current_land_rate_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST current_land_rate_sources) AND
     NOT "src/ck3_12003_current_land_supply_rate.cpp" IN_LIST current_land_rate_sources)
    target_sources(${current_land_rate_target} PRIVATE src/ck3_12003_current_land_supply_rate.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_current_land_supply_rate
    src/ck3_12002_army.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_current_province_supply_contributors.cpp
    src/ck3_12003_current_land_resupply.cpp
    src/ck3_12003_current_land_supply_rate.cpp
    src/ck3_12003_current_land_supply_rate_test.cpp)
  target_include_directories(xar_ck3_12003_current_land_supply_rate PRIVATE include)
  target_compile_features(xar_ck3_12003_current_land_supply_rate PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_land_supply_rate PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_land_supply_rate PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_current_land_supply_rate PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_land_supply_rate
    COMMAND xar_ck3_12003_current_land_supply_rate
      "${CMAKE_CURRENT_BINARY_DIR}/current-land-supply-rate-wire")
endif()
