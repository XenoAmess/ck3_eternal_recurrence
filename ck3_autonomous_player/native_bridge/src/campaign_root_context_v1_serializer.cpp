#include "xar_bridge/campaign_root_context_v1.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {
namespace {

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto encoded =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (encoded.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), encoded.ptr);
  return true;
}

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[(character >> 4U) & 0x0FU]);
      output.push_back(hex[character & 0x0FU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

bool ValidToken(std::string_view value) noexcept {
  return !value.empty() && value.size() <= 1'024 &&
         std::none_of(value.begin(), value.end(), [](unsigned char character) {
           return character == 0 || character < 0x20U;
         });
}

bool ReadinessAll(const game::CampaignRootReadinessV1 &value,
                  bool expected) noexcept {
  return value.player_identity_ready == expected &&
         value.primary_title_ready == expected &&
         value.capital_ready == expected && value.lieges_ready == expected &&
         value.government_ready == expected &&
         value.selected_game_rule_tokens_ready == expected &&
         value.same_frame_ready == expected && value.ready == expected;
}

std::string_view TierKey(std::int32_t raw) noexcept {
  switch (raw) {
  case 1:
    return "barony";
  case 2:
    return "county";
  case 3:
    return "duchy";
  case 4:
    return "kingdom";
  case 5:
    return "empire";
  case 6:
    return "hegemony";
  default:
    return {};
  }
}

bool ValidUnavailableReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 14> reasons = {
      "unsupported_build",
      "requires_application_main",
      "requires_paused",
      "map_not_ready",
      "player_identity_unavailable",
      "player_character_generation_mismatch",
      "primary_title_unavailable",
      "capital_unavailable",
      "lieges_unavailable",
      "government_flags_unavailable",
      "selected_game_rule_tokens_unavailable",
      "state_changed",
      "internal_error",
  };
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool Utf8BytewiseLess(std::string_view left,
                      std::string_view right) noexcept {
  return std::lexicographical_compare(
      left.begin(), left.end(), right.begin(), right.end(),
      [](char left_byte, char right_byte) noexcept {
        return static_cast<unsigned char>(left_byte) <
               static_cast<unsigned char>(right_byte);
      });
}

bool SortedTokens(const std::vector<std::string> &values) noexcept {
  return std::is_sorted(values.begin(), values.end(), Utf8BytewiseLess) &&
         std::all_of(values.begin(), values.end(), [](const auto &value) {
           return ValidToken(value);
         });
}

bool ValidAvailable(const game::CampaignRootContextV1 &context) noexcept {
  if (context.snapshot_revision == 0 ||
      !context.local_player_id.has_value() || *context.local_player_id < 0 ||
      !context.player_character_id.has_value() ||
      *context.player_character_id <= 0 ||
      !context.player_character_alive.has_value() ||
      !context.top_liege_character_id.has_value() ||
      *context.top_liege_character_id <= 0 ||
      !context.independent.has_value() ||
      context.native_selected_game_rule_token_count < 0 ||
      static_cast<std::size_t>(
          context.native_selected_game_rule_token_count) !=
          context.selected_game_rule_tokens.size() ||
      !SortedTokens(context.selected_game_rule_tokens) ||
      !ReadinessAll(context.readiness, true) ||
      !context.unavailable_reason.empty()) {
    return false;
  }
  if (context.primary_title.has_value()) {
    const auto &title = *context.primary_title;
    if (title.title_id <= 0 || TierKey(title.tier_raw) != title.tier_key) {
      return false;
    }
  }
  if (context.capital_province_id.has_value() &&
      *context.capital_province_id <= 0) {
    return false;
  }
  if (context.immediate_liege_character_id.has_value() &&
      (*context.immediate_liege_character_id <= 0 ||
       *context.immediate_liege_character_id ==
           *context.player_character_id)) {
    return false;
  }
  if (*context.independent !=
          !context.immediate_liege_character_id.has_value() ||
      (*context.independent &&
       *context.top_liege_character_id != *context.player_character_id) ||
      (!*context.independent &&
       *context.top_liege_character_id == *context.player_character_id)) {
    return false;
  }
  if (context.government.has_value()) {
    const auto &government = *context.government;
    if (!ValidToken(government.key) || government.native_flag_count < 0 ||
        static_cast<std::size_t>(government.native_flag_count) !=
            government.flags.size() ||
        !SortedTokens(government.flags)) {
      return false;
    }
  }
  return true;
}

bool ValidUnavailable(const game::CampaignRootContextV1 &context) noexcept {
  return context.snapshot_revision > 0 &&
         !context.local_player_id.has_value() &&
         !context.player_character_id.has_value() &&
         !context.player_character_alive.has_value() &&
         !context.primary_title.has_value() &&
         !context.capital_province_id.has_value() &&
         !context.immediate_liege_character_id.has_value() &&
         !context.top_liege_character_id.has_value() &&
         !context.independent.has_value() && !context.government.has_value() &&
         context.selected_game_rule_tokens.empty() &&
         context.native_selected_game_rule_token_count == 0 &&
         ReadinessAll(context.readiness, false) &&
         ValidUnavailableReason(context.unavailable_reason);
}

bool AppendStringArray(std::string &output,
                       const std::vector<std::string> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    AppendJsonString(output, values[index]);
  }
  output.push_back(']');
  return true;
}

void AppendOptionalInt32(std::string &output,
                         const std::optional<std::int32_t> &value) {
  if (value.has_value()) {
    (void)AppendNumber(output, *value);
  } else {
    output += "null";
  }
}

void AppendOptionalBool(std::string &output,
                        const std::optional<bool> &value) {
  if (!value.has_value()) {
    output += "null";
  } else {
    output += *value ? "true" : "false";
  }
}

void AppendReadiness(std::string &output,
                     const game::CampaignRootReadinessV1 &value) {
  output += "{\"player_identity_ready\":";
  output += value.player_identity_ready ? "true" : "false";
  output += ",\"primary_title_ready\":";
  output += value.primary_title_ready ? "true" : "false";
  output += ",\"capital_ready\":";
  output += value.capital_ready ? "true" : "false";
  output += ",\"lieges_ready\":";
  output += value.lieges_ready ? "true" : "false";
  output += ",\"government_ready\":";
  output += value.government_ready ? "true" : "false";
  output += ",\"selected_game_rule_tokens_ready\":";
  output += value.selected_game_rule_tokens_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += value.same_frame_ready ? "true" : "false";
  output += ",\"ready\":";
  output += value.ready ? "true" : "false";
  output.push_back('}');
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.19.0.6\",";
  output += "\"executable_sha256\":\"";
  output += kCampaignRootContextV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kCampaignRootContextV1BackendId;
  output += "\",\"primary_title_rva\":\"0x25F3350\",";
  output += "\"capital_province_rva\":\"0x2606760\",";
  output += "\"immediate_liege_rva\":\"0x2613480\",";
  output += "\"top_liege_rva\":\"0x2613600\",";
  output += "\"government_rva\":\"0x26165B0\",";
  output += "\"selected_game_rule_service_slot_rva\":\"0x5754B48\"}";
}

} // namespace

std::string SerializeCampaignRootContextV1(
    const game::CampaignRootContextV1 &context) {
  const bool available =
      context.status == game::CampaignRootContextStatusV1::available;
  if ((available && !ValidAvailable(context)) ||
      (!available && !ValidUnavailable(context))) {
    return {};
  }

  std::string output;
  output.reserve(1'024 + context.selected_game_rule_tokens.size() * 48);
  output += "{\"schema_version\":1,\"status\":\"";
  output += available ? "available" : "unavailable";
  output += "\",\"snapshot_revision\":";
  if (!AppendNumber(output, context.snapshot_revision)) {
    return {};
  }
  output += ",\"date_raw\":";
  if (!AppendNumber(output, context.date_raw)) {
    return {};
  }
  output += ",\"local_player_id\":";
  AppendOptionalInt32(output, context.local_player_id);
  output += ",\"player_character_id\":";
  AppendOptionalInt32(output, context.player_character_id);
  output += ",\"player_character_alive\":";
  AppendOptionalBool(output, context.player_character_alive);
  output += ",\"primary_title\":";
  if (!context.primary_title.has_value()) {
    output += "null";
  } else {
    output += "{\"title_id\":";
    if (!AppendNumber(output, context.primary_title->title_id)) {
      return {};
    }
    output += ",\"tier_raw\":";
    if (!AppendNumber(output, context.primary_title->tier_raw)) {
      return {};
    }
    output += ",\"tier_key\":";
    AppendJsonString(output, context.primary_title->tier_key);
    output.push_back('}');
  }
  output += ",\"capital_province_id\":";
  AppendOptionalInt32(output, context.capital_province_id);
  output += ",\"immediate_liege_character_id\":";
  AppendOptionalInt32(output, context.immediate_liege_character_id);
  output += ",\"top_liege_character_id\":";
  AppendOptionalInt32(output, context.top_liege_character_id);
  output += ",\"independent\":";
  AppendOptionalBool(output, context.independent);
  output += ",\"government\":";
  if (!context.government.has_value()) {
    output += "null";
  } else {
    output += "{\"key\":";
    AppendJsonString(output, context.government->key);
    output += ",\"flags\":";
    (void)AppendStringArray(output, context.government->flags);
    output += ",\"native_flag_count\":";
    if (!AppendNumber(output, context.government->native_flag_count)) {
      return {};
    }
    output.push_back('}');
  }
  output += ",\"selected_game_rule_tokens\":";
  (void)AppendStringArray(output, context.selected_game_rule_tokens);
  output += ",\"native_selected_game_rule_token_count\":";
  if (!AppendNumber(output,
                    context.native_selected_game_rule_token_count)) {
    return {};
  }
  output += ",\"readiness\":";
  AppendReadiness(output, context.readiness);
  output += ",\"unavailable_reason\":";
  if (available) {
    output += "null";
  } else {
    AppendJsonString(output, context.unavailable_reason);
  }
  output += ",\"provenance\":";
  AppendProvenance(output);
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
