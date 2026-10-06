# Coordinator applies once after adopting the child. No child configure/build.
# The additive strengths hook makes this TU a dependency of every army reader target.
get_property(current_province_supply_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(current_province_supply_target IN LISTS current_province_supply_targets)
  get_target_property(current_province_supply_sources ${current_province_supply_target} SOURCES)
  if("src/ck3_12002_army.cpp" IN_LIST current_province_supply_sources AND
     NOT "src/ck3_12003_current_province_supply_contributors.cpp" IN_LIST current_province_supply_sources)
    target_sources(${current_province_supply_target} PRIVATE
      src/ck3_12003_current_province_supply_contributors.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_current_province_supply_contributors
    src/ck3_12002_army.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_current_province_supply_contributors.cpp
    src/ck3_12003_current_province_supply_contributors_test.cpp)
  target_include_directories(xar_ck3_12003_current_province_supply_contributors PRIVATE include)
  target_compile_features(xar_ck3_12003_current_province_supply_contributors PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_province_supply_contributors PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_province_supply_contributors PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_current_province_supply_contributors PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_province_supply_contributors
    COMMAND xar_ck3_12003_current_province_supply_contributors
      "${CMAKE_CURRENT_BINARY_DIR}/current-province-supply-contributors-wire")
endif()
