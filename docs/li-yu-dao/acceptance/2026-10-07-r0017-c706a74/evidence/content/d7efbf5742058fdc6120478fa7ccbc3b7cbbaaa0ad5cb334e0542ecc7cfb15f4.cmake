if(BUILD_TESTING)
  add_executable(xar_ck3_12003_faction_county_culture_whole_query_test
    src/ck3_12002_faction_alerts.cpp
    src/county_faction_final_12003.cpp
    src/player_faction_alerts_v1.cpp
    src/player_faction_alerts_v1_serializer.cpp
    src/player_faction_county_culture_whole_query_fixture.cpp)
  target_include_directories(xar_ck3_12003_faction_county_culture_whole_query_test PRIVATE include src)
  target_compile_features(xar_ck3_12003_faction_county_culture_whole_query_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_faction_county_culture_whole_query_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_faction_county_culture_whole_query_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12003_faction_county_culture_whole_query
    COMMAND xar_ck3_12003_faction_county_culture_whole_query_test)
endif()
