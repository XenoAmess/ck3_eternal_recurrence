#pragma once

#include "xar_bridge/campaign_root_context_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

// Caller-owned failure evidence only. Never part of root readiness or equality.
struct CampaignRootStateChangedDiagnostic12004 {
  std::string_view failed_conjunct;
  std::uint64_t expected_revision = 0;
  bool before_capture_completed = false;
  game::CampaignRootFrameV1 before{};
  bool after_capture_attempted = false;
  bool after_capture_completed = false;
  game::CampaignRootFrameV1 after{};
  std::uint32_t frame_diff_mask = 0;
  bool observation_compared = false;
  std::uint32_t observation_diff_mask = 0;
};

inline constexpr std::array<std::string_view, 7>
    kCampaignRootFrameDiagnosticFields12004{
        "snapshot_revision", "date_raw", "paused", "map_ready",
        "has_played_character", "played_character_alive", "played_character_id"};
inline constexpr std::array<std::string_view, 28>
    kCampaignRootObservationDiagnosticFields12004{
        "local_player_id", "player_character_id", "player_character_alive",
        "metrics", "council", "realm", "primary_title", "capital_province_id",
        "immediate_liege_character_id", "top_liege_character_id", "independent",
        "government", "selected_game_rule_tokens", "native_selected_game_rule_token_count",
        "selected_game_rule_tokens_available", "game_data", "player_character",
        "primary_title_pointer", "capital_province_pointer", "immediate_liege_pointer",
        "top_liege_pointer", "government_pointer", "government_flags_data",
        "selection_service", "selected_rule_set", "selected_rule_data",
        "selected_rule_token_pointers", "selected_rule_tokens_native_order"};

inline std::uint32_t CampaignRootFrameDifferenceMask12004(
    const game::CampaignRootFrameV1 &before,
    const game::CampaignRootFrameV1 &after) noexcept {
  return (before.snapshot_revision != after.snapshot_revision ? 1U << 0U : 0U) |
         (before.date_raw != after.date_raw ? 1U << 1U : 0U) |
         (before.paused != after.paused ? 1U << 2U : 0U) |
         (before.map_ready != after.map_ready ? 1U << 3U : 0U) |
         (before.has_played_character != after.has_played_character ? 1U << 4U : 0U) |
         (before.played_character_alive != after.played_character_alive ? 1U << 5U : 0U) |
         (before.played_character_id != after.played_character_id ? 1U << 6U : 0U);
}

inline void RecordCampaignRootStateChanged12004(
    std::optional<CampaignRootStateChangedDiagnostic12004> *diagnostic,
    std::string_view conjunct, std::uint64_t expected_revision,
    const game::CampaignRootFrameV1 &before, bool before_completed,
    const game::CampaignRootFrameV1 &after, bool after_attempted,
    bool after_completed, std::uint32_t frame_mask = 0,
    bool observation_compared = false, std::uint32_t observation_mask = 0) noexcept {
  if (diagnostic == nullptr) return;
  *diagnostic = CampaignRootStateChangedDiagnostic12004{
      conjunct, expected_revision, before_completed, before, after_attempted,
      after_completed, after, frame_mask, observation_compared, observation_mask};
}

template<class Capture>
bool CaptureCampaignRootBefore12004(
    Capture &&capture, std::uint64_t expected_revision,
    game::CampaignRootFrameV1 &before,
    std::optional<CampaignRootStateChangedDiagnostic12004> *diagnostic) {
  if (capture(before)) return true;
  RecordCampaignRootStateChanged12004(diagnostic, "capture_before_failed",
      expected_revision, before, false, {}, false, false);
  return false;
}

inline bool MatchCampaignRootExpectedRevision12004(
    std::uint64_t expected_revision, const game::CampaignRootFrameV1 &before,
    std::optional<CampaignRootStateChangedDiagnostic12004> *diagnostic) noexcept {
  if (before.snapshot_revision == expected_revision) return true;
  RecordCampaignRootStateChanged12004(diagnostic, "expected_revision_mismatch",
      expected_revision, before, true, {}, false, false);
  return false;
}

template<class Capture, class ObservationChanged, class ObservationDifference>
bool CaptureStableCampaignRootAfter12004(
    Capture &&capture, ObservationChanged &&observation_changed,
    ObservationDifference &&observation_difference, std::uint64_t expected_revision,
    const game::CampaignRootFrameV1 &before, game::CampaignRootFrameV1 &after,
    std::optional<CampaignRootStateChangedDiagnostic12004> *diagnostic) {
  if (!capture(after)) {
    RecordCampaignRootStateChanged12004(diagnostic, "capture_after_failed",
        expected_revision, before, true, after, true, false);
    return false;
  }
  if (after != before) {
    RecordCampaignRootStateChanged12004(diagnostic, "after_frame_changed",
        expected_revision, before, true, after, true, true,
        CampaignRootFrameDifferenceMask12004(before, after));
    return false;
  }
  if (observation_changed()) {
    const auto mask = diagnostic == nullptr ? 0U : observation_difference();
    RecordCampaignRootStateChanged12004(diagnostic, "observation_changed",
        expected_revision, before, true, after, true, true, 0U, true, mask);
    return false;
  }
  return true;
}

inline void AppendCampaignRootDiagnosticString12004(std::string &out,
                                                   std::string_view value) {
  out.push_back('"');
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') out.push_back('\\');
    if (byte < 0x20U) {
      constexpr char hex[] = "0123456789abcdef";
      out += "\\u00"; out.push_back(hex[byte >> 4U]); out.push_back(hex[byte & 15U]);
    } else out.push_back(static_cast<char>(byte));
  }
  out.push_back('"');
}

inline void AppendCampaignRootDiagnosticFrame12004(
    std::string &out, const game::CampaignRootFrameV1 &frame) {
  out += "{\"snapshot_revision\":" + std::to_string(frame.snapshot_revision);
  out += ",\"date_raw\":" + std::to_string(frame.date_raw);
  out += ",\"paused\":"; out += frame.paused ? "true" : "false";
  out += ",\"map_ready\":"; out += frame.map_ready ? "true" : "false";
  out += ",\"has_played_character\":"; out += frame.has_played_character ? "true" : "false";
  out += ",\"played_character_alive\":"; out += frame.played_character_alive ? "true" : "false";
  out += ",\"played_character_id\":" + std::to_string(frame.played_character_id) + "}";
}

template<std::size_t Size>
void AppendCampaignRootDiagnosticFields12004(std::string &out,
    std::uint32_t mask, const std::array<std::string_view, Size> &fields,
    bool changed_without_known_field = false) {
  out.push_back('[');
  bool first = true;
  for (std::size_t index = 0; index < Size; ++index) {
    if ((mask & (1U << index)) == 0U) continue;
    if (!first) out.push_back(',');
    AppendCampaignRootDiagnosticString12004(out, fields[index]); first = false;
  }
  if (first && changed_without_known_field) out += "\"unlisted_observation_field\"";
  out.push_back(']');
}

inline std::string SerializeCampaignRootStateChangedDiagnostic12004(
    const CampaignRootStateChangedDiagnostic12004 &detail) {
  std::string out = "{\"failed_conjunct\":";
  AppendCampaignRootDiagnosticString12004(out, detail.failed_conjunct);
  out += ",\"expected_revision\":" + std::to_string(detail.expected_revision);
  out += ",\"before_capture_completed\":"; out += detail.before_capture_completed ? "true" : "false";
  out += ",\"before\":";
  if (detail.before_capture_completed) AppendCampaignRootDiagnosticFrame12004(out, detail.before);
  else out += "null";
  out += ",\"after_capture_attempted\":"; out += detail.after_capture_attempted ? "true" : "false";
  out += ",\"after_capture_completed\":"; out += detail.after_capture_completed ? "true" : "false";
  out += ",\"after\":";
  if (detail.after_capture_completed) AppendCampaignRootDiagnosticFrame12004(out, detail.after);
  else out += "null";
  const bool frames_comparable = detail.before_capture_completed && detail.after_capture_completed;
  out += ",\"frame_diff_mask\":";
  if (frames_comparable) out += std::to_string(detail.frame_diff_mask);
  else out += "null";
  out += ",\"frame_diff_fields\":";
  if (frames_comparable) AppendCampaignRootDiagnosticFields12004(out, detail.frame_diff_mask, kCampaignRootFrameDiagnosticFields12004);
  else out += "null";
  out += ",\"observation_compared\":"; out += detail.observation_compared ? "true" : "false";
  out += ",\"observation_diff_mask\":";
  if (detail.observation_compared) out += std::to_string(detail.observation_diff_mask);
  else out += "null";
  out += ",\"observation_diff_fields\":";
  if (detail.observation_compared) AppendCampaignRootDiagnosticFields12004(out, detail.observation_diff_mask, kCampaignRootObservationDiagnosticFields12004, detail.failed_conjunct == "observation_changed" && detail.observation_diff_mask == 0U);
  else out += "null";
  return out + "}";
}

} // namespace xar::ck3_12004
