# Current selected prisoner quote source providers; pure symbols compile once in Runtime.
# Existing prisoner mailbox/query/transport keep their original registrations.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/prisoner_selected_quote_query_capture_12004.cpp
  src/prisoner_selected_quote_source_12004.cpp
  src/prisoner_answer_helpers_12004.cpp
  src/prisoner_cost_lane_9d7060_readonly_12004.cpp
  src/prisoner_cost_variant_3755500_readonly_12004.cpp
  src/prisoner_auto_accept_trigger_condition_12004.cpp
  src/prisoner_answer_predicate_3148bb0_12004.cpp
  src/prisoner_answer_control_inputs_12004.cpp
  src/negotiated_reply_reporter_null_path_12004.cpp
  src/prisoner_scope_vector_copy_260e040_12004.cpp
  src/prisoner_scope_clone_vector100_12004.cpp
  src/prisoner_support_predicate_3727580_readonly_12004.cpp
  src/prisoner_ransom_scope_clone_373acf0_12004.cpp)

# Exercise the shared mailbox seed helper, the production serializer and the
# existing SDK wire consumer. This fixture adds no runtime callbacks or actions.
if(BUILD_TESTING)
  add_executable(xar_prisoner_selected_quote_source_12004_test
    tests/prisoner_selected_quote_source_connected_12004.cpp
    src/ck3_12004_prisoner_collection_result.cpp
    src/player_prisoner_collection_query_v1_private.cpp
    src/player_prisoner_ransom_wire_v1.cpp
    src/protocol.cpp)
  target_include_directories(xar_prisoner_selected_quote_source_12004_test PRIVATE include src research)
  target_compile_features(xar_prisoner_selected_quote_source_12004_test PRIVATE cxx_std_20)
  target_link_libraries(xar_prisoner_selected_quote_source_12004_test PRIVATE xar_ck3_12002_runtime)
  if(MSVC)
    target_compile_options(xar_prisoner_selected_quote_source_12004_test PRIVATE
      /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8)
  else()
    target_compile_options(xar_prisoner_selected_quote_source_12004_test PRIVATE
      -UNDEBUG -Wall -Wextra -Werror)
  endif()
  add_test(NAME xar_prisoner_selected_quote_source_12004_test
    COMMAND xar_prisoner_selected_quote_source_12004_test --prisoner-selected-quote-source-wire-repair-12004)
endif()
