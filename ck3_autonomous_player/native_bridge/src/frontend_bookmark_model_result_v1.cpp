#include "xar_bridge/frontend_bookmark_model_result_v1.hpp"

#include <array>
#include <charconv>

namespace xar::ck3_11906 {
namespace {

std::string Number(std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

std::string SignedNumber(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}

void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}

} // namespace

std::string FrontendBookmarkModelPrivateResultFrameV1(
    std::string_view request_id, std::string_view step,
    const xar::ck3_11906::FrontendBookmarkModelProbeV1 &probe) {
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":";
  AppendJsonString(result, probe.candidate_identity_ready
                               ? "identity_ready" : "unavailable");
  result += ",\"private_scope\":\"exact-build-bookmarks-model-v1\"";
  result += ",\"gui_chain_vtable_rvas\":[";
  for (std::size_t i = 0; i < probe.gui_chain_vtable_rvas.size(); ++i) {
    if (i != 0) result += ',';
    result += Number(probe.gui_chain_vtable_rvas[i]);
  }
  result += "],\"interface_application_chain_level\":";
  result += SignedNumber(probe.interface_application_chain_level);
  result += ",\"owner_chain_vtable_rvas\":[";
  for (std::size_t i = 0; i < probe.owner_chain_vtable_rvas.size(); ++i) {
    if (i != 0) result += ',';
    result += Number(probe.owner_chain_vtable_rvas[i]);
  }
  result += "],\"owner_chain_rtti_type_rvas\":[";
  for (std::size_t i = 0; i < probe.owner_chain_rtti_type_rvas.size(); ++i) {
    if (i != 0) result += ',';
    result += Number(probe.owner_chain_rtti_type_rvas[i]);
  }
  result += ']';
  result += ",\"direct_owner_unavailable_reason\":";
  if (probe.direct_owner_unavailable_reason.empty()) {
    result += "null";
  } else {
    AppendJsonString(result, probe.direct_owner_unavailable_reason);
  }
  result += ",\"registry_owner_unavailable_reason\":";
  if (probe.registry_owner_unavailable_reason.empty()) {
    result += "null";
  } else {
    AppendJsonString(result, probe.registry_owner_unavailable_reason);
  }
  result += ",\"registry_owner_match_count\":";
  if (probe.registry_owner_match_count < 0) {
    result += "null";
  } else {
    result += SignedNumber(probe.registry_owner_match_count);
  }
  result += ",\"verified_owner_route\":";
  if (probe.verified_owner_route.empty()) {
    result += "null";
  } else {
    AppendJsonString(result, probe.verified_owner_route);
  }
  result += ",\"setup_view_vtable_rva\":";
  result += Number(probe.setup_view_vtable_rva);
  result += ",\"setup_view_matches_bookmarks_root\":";
  result += probe.setup_view_matches_bookmarks_root ? "true" : "false";
  result += ",\"selected_bookmark_group_key\":";
  if (probe.selected_bookmark_group_key_available) {
    AppendJsonString(result, probe.selected_bookmark_group_key);
  } else {
    result += "null";
  }
  result += ",\"selected_bookmark_key\":";
  if (probe.selected_bookmark_key_available) {
    AppendJsonString(result, probe.selected_bookmark_key);
  } else {
    result += "null";
  }
  result += ",\"selected_date_raw\":";
  result += probe.selected_date_raw_available
                ? Number(probe.selected_date_raw) : "null";
  result += ",\"selected_date_low_raw\":";
  result += probe.selected_date_raw_available
                ? Number(probe.selected_date_low_raw) : "null";
  result += ",\"selected_character_index\":";
  result += SignedNumber(probe.selected_character_index);
  result += ",\"hovered_character_index\":";
  result += SignedNumber(probe.hovered_character_index);
  result += ",\"bookmark_character_count\":";
  result += SignedNumber(probe.bookmark_character_count);
  result += ",\"bookmark_character_capacity_raw\":";
  result += Number(probe.bookmark_character_capacity_raw);
  result += ",\"bookmark_character_allocator_raw\":";
  result += SignedNumber(probe.bookmark_character_allocator_raw);
  result += ",\"candidate_keys\":[";
  if (probe.bookmark_character_keys_available) {
    for (std::int32_t i = 0; i < probe.bookmark_character_count; ++i) {
      if (i != 0) result += ',';
      AppendJsonString(result,
                       probe.bookmark_character_keys[
                           static_cast<std::size_t>(i)]);
    }
  }
  result += "],\"supported_1066_candidate_index\":";
  result += SignedNumber(probe.supported_1066_candidate_index);
  result += ",\"supported_1066_candidate_present\":";
  result += probe.supported_1066_candidate_present ? "true" : "false";
  result += ",\"supported_1066_government_key\":";
  if (probe.government_type_keys_available &&
      probe.supported_1066_candidate_index >= 0) {
    AppendJsonString(
        result,
        probe.government_type_keys[static_cast<std::size_t>(
            probe.supported_1066_candidate_index)]);
  } else {
    result += "null";
  }
  result += ",\"supported_1066_feudal\":";
  result += probe.supported_1066_candidate_feudal ? "true" : "false";
  result += ",\"supported_1066_date_matches\":";
  result += probe.supported_1066_date_matches ? "true" : "false";
  result += ",\"candidate_identity_ready\":";
  result += probe.candidate_identity_ready ? "true" : "false";
  result += ",\"unavailable_reason\":";
  AppendJsonString(result, probe.unavailable_reason);
  result += "}}";
  return result;
}

} // namespace xar::ck3_11906
