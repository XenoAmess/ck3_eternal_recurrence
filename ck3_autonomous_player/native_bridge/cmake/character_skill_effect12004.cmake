# Reusable exact4 one-actor skill/devotion/original-text READ observer only.
option(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1
  "Compile exact4 character skill effect readonly observer (unqualified default OFF)" OFF)
if(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1)
  if(NOT WIN32)
    message(FATAL_ERROR "Character skill observer requires the exact Windows owner mailbox")
  endif()
  set(_actor_effect_sources
    src/character_skill_effect12004.cpp
    src/character_skill_effect12004_native.cpp
    src/character_skill_effect12004_json.cpp
    src/character_skill_effect12004_request.cpp
    src/character_skill_effect12004_mailbox.cpp)
  target_sources(xar_ck3_12002_runtime PRIVATE ${_actor_effect_sources})
  set_property(SOURCE ${_actor_effect_sources} src/bridge.cpp
    src/ck3_12002_nonwar_router.cpp src/ck3_12002_nonwar_mailbox.cpp
    APPEND PROPERTY COMPILE_DEFINITIONS
      XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1=1)
  if(BUILD_TESTING)
    add_executable(xar_ck3_character_skill_effect12004_owned_fixture EXCLUDE_FROM_ALL
      tests/character_skill_effect12004_owned_fixture.cpp src/character_skill_effect12004.cpp)
    add_executable(xar_ck3_character_skill_effect12004_wire_fixture EXCLUDE_FROM_ALL
      tests/character_skill_effect12004_wire_fixture.cpp src/character_skill_effect12004_json.cpp)
    add_executable(xar_ck3_character_skill_effect12004_request_fixture EXCLUDE_FROM_ALL
      tests/character_skill_effect12004_request_fixture.cpp src/character_skill_effect12004_request.cpp)
    target_link_libraries(xar_ck3_character_skill_effect12004_request_fixture PRIVATE xar_bridge_protocol)
    foreach(_actor_target IN ITEMS xar_ck3_character_skill_effect12004_owned_fixture
        xar_ck3_character_skill_effect12004_wire_fixture xar_ck3_character_skill_effect12004_request_fixture)
      target_compile_features(${_actor_target} PRIVATE cxx_std_20)
      target_include_directories(${_actor_target} PRIVATE include)
      target_compile_definitions(${_actor_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
      if(MSVC)
        target_compile_options(${_actor_target} PRIVATE /UNDEBUG /W4 /permissive- /EHsc)
      endif()
    endforeach()
  endif()
endif()

# Fixed actual-Character knight total/original-text observer. Reuses the five
# existing production TUs, the same default-OFF actor compile flag and the same
# typed owner executor. The new SDK capability remains independently opt-in.
if(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1 AND BUILD_TESTING)
  add_executable(xar_ck3_character_knight_effectiveness12004_owned_fixture EXCLUDE_FROM_ALL
    tests/character_knight_effectiveness12004_owned_fixture.cpp
    src/character_skill_effect12004.cpp
    src/character_skill_effect12004_json.cpp
    src/character_skill_effect12004_request.cpp)
  target_link_libraries(xar_ck3_character_knight_effectiveness12004_owned_fixture PRIVATE xar_bridge_protocol)
  add_executable(xar_ck3_character_knight_effectiveness12004_factory_fixture EXCLUDE_FROM_ALL
    tests/character_knight_effectiveness12004_factory_fixture.cpp
    src/character_skill_effect12004_native.cpp)
  target_link_libraries(xar_ck3_character_knight_effectiveness12004_factory_fixture PRIVATE xar_ck3_12002_runtime)
  target_compile_definitions(xar_ck3_character_knight_effectiveness12004_factory_fixture PRIVATE
    XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1=1)
  foreach(_knight_target IN ITEMS xar_ck3_character_knight_effectiveness12004_owned_fixture
      xar_ck3_character_knight_effectiveness12004_factory_fixture)
    target_compile_features(${_knight_target} PRIVATE cxx_std_20)
    target_include_directories(${_knight_target} PRIVATE include src research)
    target_compile_definitions(${_knight_target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(${_knight_target} PRIVATE /UNDEBUG /Od /GL- /W4 /permissive- /EHsc /utf-8)
    endif()
  endforeach()
endif()

if(XAR_CK3_ENABLE_CHARACTER_SKILL_EFFECTS12004_PRIVATE_QUERY_V1 AND BUILD_TESTING)
  add_executable(xar_ck3_12004_knight_installed_context_source_fixture EXCLUDE_FROM_ALL tests/knight_installed_context_source12004_fixture.cpp)
  target_link_libraries(xar_ck3_12004_knight_installed_context_source_fixture PRIVATE xar_ck3_12002_runtime)
  target_compile_features(xar_ck3_12004_knight_installed_context_source_fixture PRIVATE cxx_std_20)
  target_include_directories(xar_ck3_12004_knight_installed_context_source_fixture PRIVATE include src research)
  target_compile_definitions(xar_ck3_12004_knight_installed_context_source_fixture PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  set_property(TARGET xar_ck3_12004_knight_installed_context_source_fixture PROPERTY INTERPROCEDURAL_OPTIMIZATION FALSE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_knight_installed_context_source_fixture PRIVATE /UNDEBUG /Od /Ob0 /GL- /W4 /permissive- /EHsc /utf-8)
  endif()
endif()
