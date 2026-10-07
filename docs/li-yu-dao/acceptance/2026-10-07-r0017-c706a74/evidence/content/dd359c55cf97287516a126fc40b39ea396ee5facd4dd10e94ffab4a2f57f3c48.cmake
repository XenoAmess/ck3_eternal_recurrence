# Authored only. The coordinator owns the single actual build and execution.
if(BUILD_TESTING)
  add_executable(xar_ck3_death_succession_modal_whole_fixture_12004
    src/ck3_12004_abi_profile.cpp
    src/ck3_12004_succession_modal.cpp
    src/current_timeline_blocker_context_v1.cpp
    src/death_succession_modal_continue_v1.cpp
    src/current_timeline_blocker_12004_whole_fixture.cpp)
  target_include_directories(xar_ck3_death_succession_modal_whole_fixture_12004 PRIVATE include)
  target_compile_definitions(xar_ck3_death_succession_modal_whole_fixture_12004 PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_death_succession_modal_whole_fixture_12004 PRIVATE
      /W4 /WX /permissive- /EHsc /Gy)
    target_link_options(xar_ck3_death_succession_modal_whole_fixture_12004 PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_death_succession_modal_whole_fixture_12004
    COMMAND xar_ck3_death_succession_modal_whole_fixture_12004
      "${CMAKE_BINARY_DIR}/death-succession-12004-whole-fixture.json")
endif()
