# Same-query current daily assault operands and bounded loss fixture.
get_property(daily_loss_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(daily_loss_target IN LISTS daily_loss_targets)
  get_target_property(daily_loss_sources ${daily_loss_target} SOURCES)
  if(("src/ck3_12002_army.cpp" IN_LIST daily_loss_sources OR
      "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST daily_loss_sources) AND
     NOT "src/ck3_12003_current_daily_assault_loss.cpp" IN_LIST daily_loss_sources)
    target_sources(${daily_loss_target} PRIVATE src/ck3_12003_current_daily_assault_loss.cpp)
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  get_target_property(daily_loss_production_sources
    xar_ck3_12003_current_province_besieging_contributors SOURCES)
  list(FILTER daily_loss_production_sources EXCLUDE REGEX "_test\\.cpp$")
  list(APPEND daily_loss_production_sources
    src/ck3_12003_current_daily_assault_loss.cpp
    src/ck3_12003_current_daily_assault_loss_test.cpp)
  list(REMOVE_DUPLICATES daily_loss_production_sources)
  add_executable(xar_ck3_12003_current_daily_assault_loss ${daily_loss_production_sources})
  target_include_directories(xar_ck3_12003_current_daily_assault_loss PRIVATE include)
  target_compile_features(xar_ck3_12003_current_daily_assault_loss PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_daily_assault_loss PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_daily_assault_loss PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_current_daily_assault_loss PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_daily_assault_loss
    COMMAND xar_ck3_12003_current_daily_assault_loss
      "${CMAKE_CURRENT_BINARY_DIR}/current-daily-assault-loss-wire")
endif()
