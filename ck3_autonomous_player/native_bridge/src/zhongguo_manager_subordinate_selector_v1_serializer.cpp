#include "xar_bridge/zhongguo_manager_subordinate_selector_v1.hpp"

#include <array>
#include <charconv>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20U) {
        output += "\\u00";
        output.push_back(hex[(character >> 4U) & 0x0FU]);
        output.push_back(hex[character & 0x0FU]);
      } else {
        output.push_back(static_cast<char>(character));
      }
      break;
    }
  }
  output.push_back('"');
}

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto converted =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) return false;
  output.append(buffer.data(), converted.ptr);
  return true;
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char character = value[index];
    const bool alpha = (character >= 'a' && character <= 'z') ||
                       (character >= 'A' && character <= 'Z');
    const bool digit = character >= '0' && character <= '9';
    const bool punctuation = character == '.' || character == '_' ||
                             character == ':' || character == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) {
      return false;
    }
  }
  return true;
}

bool ValidUnavailableReason(std::string_view value) noexcept {
  constexpr std::array<std::string_view, 9> values{
      "unsupported_build",
      "requires_application_main",
      "requires_paused",
      "map_not_ready",
      "native_relationship_enumeration_unavailable",
      "no_bounded_ai_direct_manager",
      "bounded_ai_manager_has_no_direct_subordinate",
      "state_changed",
      "internal_error"};
  for (const auto candidate : values) {
    if (candidate == value) return true;
  }
  return false;
}

bool ValidSnapshot(
    const game::ZhongguoManagerSubordinateSelectorSnapshotV1 &snapshot)
    noexcept {
  if (snapshot.selector_kind != kZhongguoManagerSubordinateSelectorV1Kind ||
      !ValidNonce(snapshot.request_nonce) || snapshot.snapshot_revision == 0) {
    return false;
  }
  const bool available =
      snapshot.status ==
      game::ZhongguoManagerSubordinateSelectorStatusV1::available;
  if (!available) {
    return ValidUnavailableReason(snapshot.unavailable_reason) &&
           !snapshot.readiness.ready;
  }
  const auto &selection = snapshot.selection;
  return snapshot.unavailable_reason.empty() && snapshot.paused &&
         snapshot.player_character_id > 0 && snapshot.readiness.ready &&
         snapshot.readiness.exact_build_ready &&
         snapshot.readiness.player_binding_ready &&
         snapshot.readiness.relationship_enumeration_ready &&
         snapshot.readiness.manager_eligibility_ready &&
         snapshot.readiness.direct_subordinate_ready &&
         snapshot.readiness.same_frame_ready &&
         selection.manager_character_id > 0 &&
         selection.subordinate_character_id > 0 &&
         selection.manager_character_id != selection.subordinate_character_id &&
         selection.manager_contract_id > 0 &&
         selection.subordinate_contract_id > 0 &&
         selection.manager_primary_title_id > 0 &&
         selection.manager_primary_title_tier_raw >= 3 &&
         selection.manager_primary_title_tier_raw <= 6 &&
         !selection.manager_primary_title_tier_key.empty() &&
         selection.manager_government_key == "celestial_government";
}

void AppendReadiness(
    std::string &output,
    const game::ZhongguoManagerSubordinateSelectorReadinessV1 &value) {
  output += "{\"exact_build_ready\":";
  output += value.exact_build_ready ? "true" : "false";
  output += ",\"player_binding_ready\":";
  output += value.player_binding_ready ? "true" : "false";
  output += ",\"relationship_enumeration_ready\":";
  output += value.relationship_enumeration_ready ? "true" : "false";
  output += ",\"manager_eligibility_ready\":";
  output += value.manager_eligibility_ready ? "true" : "false";
  output += ",\"direct_subordinate_ready\":";
  output += value.direct_subordinate_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += value.same_frame_ready ? "true" : "false";
  output += ",\"ready\":";
  output += value.ready ? "true}" : "false}";
}

} // namespace

std::string SerializeZhongguoManagerSubordinateSelectorV1(
    const game::ZhongguoManagerSubordinateSelectorSnapshotV1 &snapshot) {
  if (!ValidSnapshot(snapshot)) return {};
  const bool available =
      snapshot.status ==
      game::ZhongguoManagerSubordinateSelectorStatusV1::available;
  std::string output;
  output.reserve(1'200);
  output += "{\"schema_version\":1,\"status\":\"";
  output += available ? "available" : "unavailable";
  output += "\",\"selector_kind\":";
  AppendJsonString(output, snapshot.selector_kind);
  output += ",\"request_nonce\":";
  AppendJsonString(output, snapshot.request_nonce);
  output += ",\"snapshot_revision\":";
  if (!AppendNumber(output, snapshot.snapshot_revision)) return {};
  output += ",\"date_raw\":";
  if (!AppendNumber(output, snapshot.date_raw)) return {};
  output += ",\"paused\":";
  output += snapshot.paused ? "true" : "false";
  output += ",\"player_character_id\":";
  if (!AppendNumber(output, snapshot.player_character_id)) return {};
  output += ",\"provider_observed\":";
  output += available ? "true" : "false";
  output += ",\"selection\":";
  if (!available) {
    output += "null";
  } else {
    const auto &selection = snapshot.selection;
    output += "{\"manager_character_id\":";
    if (!AppendNumber(output, selection.manager_character_id)) return {};
    output += ",\"subordinate_character_id\":";
    if (!AppendNumber(output, selection.subordinate_character_id)) return {};
    output += ",\"manager_contract_id\":";
    if (!AppendNumber(output, selection.manager_contract_id)) return {};
    output += ",\"subordinate_contract_id\":";
    if (!AppendNumber(output, selection.subordinate_contract_id)) return {};
    output += ",\"manager_primary_title_id\":";
    if (!AppendNumber(output, selection.manager_primary_title_id)) return {};
    output += ",\"manager_primary_title_tier_raw\":";
    if (!AppendNumber(output, selection.manager_primary_title_tier_raw))
      return {};
    output += ",\"manager_primary_title_tier_key\":";
    AppendJsonString(output, selection.manager_primary_title_tier_key);
    output += ",\"manager_government_key\":";
    AppendJsonString(output, selection.manager_government_key);
    output.push_back('}');
  }
  output += ",\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null";
  } else {
    AppendJsonString(output, snapshot.unavailable_reason);
  }
  output += ",\"provenance\":{\"game_version\":\"1.19.0.6\",";
  output += "\"executable_sha256\":\"";
  output += kZhongguoCaseSnapshotV1ExecutableSha256;
  output += "\",\"subject_contract_storage_slot_rva\":\"0x570CCA0\",";
  output += "\"subject_contract_fallback_slot_rva\":\"0x570CC50\",";
  output += "\"immediate_liege_rva\":\"0x2613480\",";
  output += "\"primary_title_rva\":\"0x25F3350\",";
  output += "\"effective_government_rva\":\"0x26165B0\",";
  output += "\"is_human_player_rva\":\"0x28BCEB0\"}}";
  return output;
}

} // namespace xar::ck3_11906
