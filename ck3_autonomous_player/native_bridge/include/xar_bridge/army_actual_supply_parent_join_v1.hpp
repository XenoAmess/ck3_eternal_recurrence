#pragma once

#include <charconv>
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {

struct ArmyActualSupplyParentInvocationV1 {
  std::uint64_t invocation_token = 0;
  std::uint32_t native_thread_id = 0;
  std::uint32_t nesting_depth = 0;
  std::optional<std::uint64_t> parent_invocation_token;
  std::optional<std::uint64_t> callback_caller_return_rva;
};

struct ArmyActualSupplyParentWriterContextV1 {
  ArmyActualSupplyParentInvocationV1 invocation;
  std::optional<std::int32_t> army_id;
  std::optional<std::int32_t> native_carmy_id;
  std::optional<std::uint64_t> passed_date_raw64;
  // Read from the actual scoped CArmy receiver at writer entry, never reused
  // from callback.before, callback.after, query state, or a projected stock.
  std::optional<std::int64_t> stock_at_writer_entry_raw;
  bool receiver_identity_matches = false;
  std::uint32_t capture_failure_flags = 0;
};

namespace army_actual_supply_parent_json_v1 {
template <typename T> inline void Number(std::string &output, T value) {
  char buffer[32]{};
  const auto converted = std::to_chars(buffer, buffer + sizeof(buffer), value);
  output.append(buffer, converted.ptr);
}
template <typename T> inline void Optional(std::string &output, const std::optional<T> &value) {
  if (value) Number(output, *value);
  else output += "null";
}
} // namespace army_actual_supply_parent_json_v1

inline void AppendArmyActualSupplyParentInvocationV1(
    std::string &output, const ArmyActualSupplyParentInvocationV1 &value) {
  using namespace army_actual_supply_parent_json_v1;
  output += "{\"invocation_token\":";
  Number(output, value.invocation_token);
  output += ",\"native_thread_id\":";
  Number(output, value.native_thread_id);
  output += ",\"nesting_depth\":";
  Number(output, value.nesting_depth);
  output += ",\"parent_invocation_token\":";
  Optional(output, value.parent_invocation_token);
  output += ",\"callback_caller_return_rva\":";
  Optional(output, value.callback_caller_return_rva);
  output += ",\"callback_entry_rva\":38679568,"
            "\"receiver_basis\":\"actual_24E3410_rcx_carmy\"}";
}

inline void AppendArmyActualSupplyParentWriterContextV1(
    std::string &output, const ArmyActualSupplyParentWriterContextV1 &value) {
  using namespace army_actual_supply_parent_json_v1;
  output += "{\"invocation\":";
  AppendArmyActualSupplyParentInvocationV1(output, value.invocation);
  output += ",\"army_id\":";
  Optional(output, value.army_id);
  output += ",\"native_carmy_id\":";
  Optional(output, value.native_carmy_id);
  output += ",\"passed_date_raw64\":";
  Optional(output, value.passed_date_raw64);
  output += ",\"stock_at_writer_entry_raw\":";
  Optional(output, value.stock_at_writer_entry_raw);
  output += ",\"stock_scale\":100000,\"receiver_identity_matches\":";
  output += value.receiver_identity_matches ? "true" : "false";
  output += ",\"capture_failure_flags\":";
  Number(output, value.capture_failure_flags);
  output += '}';
}

} // namespace xar::game
