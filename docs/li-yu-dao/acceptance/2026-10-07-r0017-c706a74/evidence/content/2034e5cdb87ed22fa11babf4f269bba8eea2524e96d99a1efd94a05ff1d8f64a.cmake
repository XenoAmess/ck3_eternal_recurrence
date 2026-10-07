# Add the production dependency to both absolute runtime and relative fixtures.
get_property(current_land_resupply_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(current_land_resupply_target IN LISTS current_land_resupply_targets)
  get_target_property(current_land_resupply_sources ${current_land_resupply_target} SOURCES)
  if(("src/ck3_12002_army.cpp" IN_LIST current_land_resupply_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST current_land_resupply_sources) AND
     NOT "src/ck3_12003_current_land_resupply.cpp" IN_LIST current_land_resupply_sources)
    target_sources(${current_land_resupply_target} PRIVATE src/ck3_12003_current_land_resupply.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_current_land_resupply
    src/ck3_12002_army.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_current_province_supply_contributors.cpp
    src/ck3_12003_current_land_resupply.cpp
    src/ck3_12003_current_land_resupply_test.cpp)
  target_include_directories(xar_ck3_12003_current_land_resupply PRIVATE include)
  target_compile_features(xar_ck3_12003_current_land_resupply PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_land_resupply PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_land_resupply PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_current_land_resupply PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_land_resupply
    COMMAND xar_ck3_12003_current_land_resupply
      "${CMAKE_CURRENT_BINARY_DIR}/current-land-resupply-wire")
endif()
