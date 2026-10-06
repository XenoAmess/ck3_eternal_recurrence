#pragma once
// Included inside xar::game. All values are owned source metadata.
struct ArmyCurrentRule24SourcePinsV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  std::int32_t schema_version = 1;
  std::string source = "native_current_rule24_source_pins";
  bool pins_captured_ready = false, provider_array_borrowed = true;
  std::string rule_receiver_identity;
  std::optional<std::string> rule_vtable_identity;
  std::optional<std::uint8_t> condition_mode_raw_u8;
  std::optional<std::string> expected_scope_function_identity;
  std::optional<std::uint32_t> expected_scope_function_rva;
  std::optional<std::string> scope_mask_function_identity;
  std::optional<std::uint32_t> scope_mask_function_rva;
  std::optional<std::string> rule_evaluator_function_identity;
  std::optional<std::uint32_t> rule_evaluator_function_rva;
  bool vtable_read_ready = false, mode_read_ready = false;
  bool expected_scope_pin_read_ready = false, scope_mask_pin_read_ready = false;
  bool rule_evaluator_pin_read_ready = false;
  std::uint32_t pin_requested_bytes_u32 = 0, pin_captured_bytes_u32 = 0;
  std::uint32_t native_calls_executed = 0, native_writes_executed = 0;
  friend bool operator==(const ArmyCurrentRule24SourcePinsV1 &,
                         const ArmyCurrentRule24SourcePinsV1 &) = default;
};
