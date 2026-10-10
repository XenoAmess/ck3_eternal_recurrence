# Qualified dynamic Piety copied-input providers; static providers remain registered once.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/piety_price_numeric_31d9930_dynamic_12004.cpp
  src/piety_price_numeric_31df3b0_dynamic_12004.cpp
  src/piety_price_a0f0b0_dynamic_readonly_12004.cpp
  src/piety_price_named_definition_37540b0_readonly_12004.cpp
  src/piety_fixed_rounded_i32_37498a0_12004.cpp
  src/compiled_expression_variant_3755500_readonly_12004.cpp
  src/compiled_expression_variant_3755500_provider_metadata_12004.cpp
  src/religion_owned_edit_dynamic_base_price_12004.cpp)

# Five case-only TUs and the header-only evaluator are not production sources.
