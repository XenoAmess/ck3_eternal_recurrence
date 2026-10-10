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
