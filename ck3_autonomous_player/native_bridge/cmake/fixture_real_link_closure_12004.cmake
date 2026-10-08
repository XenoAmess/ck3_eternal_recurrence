# The complete-domain strict04 build reached link and failed these 17 new
# fixtures. Fifteen share the runtime's real family and GameAdapter providers;
# Sway, Government, Clergy, Death and religion addons also reference production
# observer/action/GUI providers owned by xar_ck3_bridge. Use that same object
# closure as the already qualified actual-.4 Core, Snapshot and Army fixtures.
# This adds no feature option or test target and does not execute legacy tests.
function(xar_ck3_12004_fixture_use_real_bridge target)
  get_target_property(bridge_source_dir xar_ck3_bridge SOURCE_DIR)
  get_target_property(bridge_sources xar_ck3_bridge SOURCES)
  set(bridge_absolute_sources)
  foreach(source IN LISTS bridge_sources)
    get_filename_component(absolute_source "${source}" ABSOLUTE
      BASE_DIR "${bridge_source_dir}")
    list(APPEND bridge_absolute_sources "${absolute_source}")
  endforeach()

  # Some focused fixtures originally compiled production helper TUs directly.
  # Retain each owned fixture TU and any remaining provider; remove only exact
  # source duplicates before adding the already compiled Bridge objects.
  get_target_property(fixture_source_dir ${target} SOURCE_DIR)
  get_target_property(fixture_sources ${target} SOURCES)
  set(fixture_transport_sources)
  if(target STREQUAL "xar_ck3_12004_faction_adopted_whole_test")
    # These two TUs must call the fixture's aliased mailbox transport.
    foreach(source IN ITEMS
        src/ck3_12004_faction_mailbox.cpp
        src/ck3_12004_faction_gift_router.cpp)
      get_filename_component(absolute_source "${source}" ABSOLUTE
        BASE_DIR "${bridge_source_dir}")
      list(APPEND fixture_transport_sources "${absolute_source}")
    endforeach()
  endif()
  set(remaining_fixture_sources)
  foreach(source IN LISTS fixture_sources)
    get_filename_component(absolute_source "${source}" ABSOLUTE
      BASE_DIR "${fixture_source_dir}")
    if(NOT absolute_source IN_LIST bridge_absolute_sources OR
        absolute_source IN_LIST fixture_transport_sources)
      list(APPEND remaining_fixture_sources "${source}")
    endif()
  endforeach()
  set_property(TARGET ${target} PROPERTY SOURCES "${remaining_fixture_sources}")
  if(fixture_transport_sources)
    # Keep the production closure while replacing only these two handler
    # objects with the direct TUs compiled under the fixture's three aliases.
    target_sources(${target} PRIVATE
      "$<FILTER:$<TARGET_OBJECTS:xar_ck3_bridge>,EXCLUDE,(^|[/\\\\])ck3_12004_faction_(mailbox|gift_router)[.]cpp[.](obj|o)$>")
  else()
    target_sources(${target} PRIVATE $<TARGET_OBJECTS:xar_ck3_bridge>)
  endif()
  target_compile_definitions(${target} PRIVATE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  target_link_libraries(${target} PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
endfunction()

# Literal failed targets from strict04; no previously GREEN fixture is replayed
# or altered. The native producer argv and CTest declarations stay unchanged.
# The current-.3 event fixture shares this same real adapter closure.
foreach(target IN ITEMS
    xar_ck3_12002_event_window_context_test
    xar_ck3_12004_religion_bindings_mailbox_test
    xar_ck3_12004_religion_costs_eligibility_mailbox_test
    xar_ck3_12004_religion_draft_bindings_mailbox_test
    xar_ck3_12004_religion_adopted_observers_mailbox_test
    xar_ck3_12004_religion_adopted_addons_whole_test
    xar_ck3_12004_hired_troop_migration_test
    xar_ck3_12004_ordinary_holy_war_declaration_context_whole_mailbox_test
    ck3_12004_prisoner_collection_test
    ck3_12004_prisoner_release_material_whole_first
    ck3_12004_prisoner_ransom_action_test
    xar_ck3_12004_sway_whole_producer_test
    xar_ck3_12004_lifestyle_first_v1_test
    xar_ck3_12004_faction_adopted_whole_test
    xar_ck3_12004_government_whole_first
    xar_ck3_12004_clergy_appointment_whole_mailbox_test
    xar_ck3_12004_clergy_candidate_terms_whole_mailbox_test
    xar_ck3_12004_chaplain_council_action_whole_mailbox_test
    xar_ck3_12004_campaign_root_core_council_whole_test
    xar_ck3_12004_county_conversion_whole_mailbox_test
    xar_ck3_death_succession_modal_whole_fixture_12004
    xar_ck3_12004_commander_movement_metadata_test)
  if(TARGET ${target})
    xar_ck3_12004_fixture_use_real_bridge(${target})
  endif()
endforeach()
