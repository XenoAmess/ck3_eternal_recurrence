# Current Lifestyle source-demand pure helpers; each new provider belongs once to Runtime.
# Existing stock perk, formal wire and transport stay in lifestyle_12004.cmake.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/lifestyle_perk_predicate_inputs_12004.cpp
  src/lifestyle_perk_predicate_288b1b0_12004.cpp
  src/lifestyle_owned_perk_collection_2919340_12004.cpp
  src/construction_collection_predicate_a11cc0_12004.cpp
  src/lifestyle_character_scope_12004.cpp
  src/m4_factor_actor_inner_init_12004.cpp
  src/lifestyle_perk_truth_producer_12004.cpp
  src/lifestyle_perk_final_31ebe50_readonly_12004.cpp
  src/source_auto_accept_trigger_condition_12004.cpp
  src/trigger_scope_table_provider_3795a60_12004.cpp)

if(BUILD_TESTING AND WIN32)
  # Exact21 linked qualified sources;13f formal/transport remain production compile-only.
  add_executable(lifestyle_current_perk_12004_new_compound EXCLUDE_FROM_ALL
    src/lifestyle_perk_predicate_inputs_12004.cpp
    src/lifestyle_perk_predicate_288b1b0_12004.cpp
    tests/lifestyle_selected_perk_connected_12004_new_case.cpp
    tests/lifestyle_current_perk_12004_new_compound.cpp
    src/lifestyle_owned_perk_collection_2919340_12004.cpp
    tests/lifestyle_owned_perk_collection_2919340_12004_new_cases.cpp
    src/construction_collection_predicate_a11cc0_12004.cpp
    src/lifestyle_character_scope_12004.cpp
    tests/lifestyle_character_scope_new_cases_12004.cpp
    src/m4_factor_actor_inner_init_12004.cpp
    src/lifestyle_perk_truth_producer_12004.cpp
    tests/lifestyle_perk_truth_producer_12004_new_cases.cpp
    src/lifestyle_perk_final_31ebe50_readonly_12004.cpp
    src/lifestyle_perk_final_31ebe50_readonly_12004_case_export.cpp
    src/source_auto_accept_trigger_condition_12004.cpp
    src/source_auto_accept_trigger_condition_12004_generic_cases.cpp
    src/source_trigger_root_scope_gate_12004_cases.cpp
    src/trigger_scope_table_provider_3795a60_12004.cpp
    src/trigger_scope_table_provider_3795a60_12004_new_cases.cpp
    src/ck3_12004_stock_perk_legality.cpp
    tests/stock_perk_current_query_source_12004_focus.cpp)
  target_include_directories(lifestyle_current_perk_12004_new_compound PRIVATE include src tests)
  target_compile_features(lifestyle_current_perk_12004_new_compound PRIVATE cxx_std_20)
  target_compile_definitions(lifestyle_current_perk_12004_new_compound PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE WIN32 _WINDOWS
    _ITERATOR_DEBUG_LEVEL=0
    XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1=1)
  target_link_libraries(lifestyle_current_perk_12004_new_compound PRIVATE kernel32)
  if(MSVC)
    set_property(TARGET lifestyle_current_perk_12004_new_compound PROPERTY MSVC_RUNTIME_LIBRARY MultiThreadedDLL)
    target_compile_options(lifestyle_current_perk_12004_new_compound PRIVATE
      /O2 /EHsc /W4 /WX /permissive- /utf-8 /UNDEBUG)
  endif()
  # Sole argument is a fresh source-wire output path;explicit target selection only.
endif()
