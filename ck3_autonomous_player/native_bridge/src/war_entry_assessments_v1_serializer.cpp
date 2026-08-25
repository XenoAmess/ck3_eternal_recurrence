#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <array>
#include <charconv>
#include <cstdint>
#include <limits>
#include <string>
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

bool CheckedAdd(std::int64_t left, std::int64_t right,
                std::int64_t &output) {
  if ((right > 0 &&
       left > std::numeric_limits<std::int64_t>::max() - right) ||
      (right < 0 &&
       left < std::numeric_limits<std::int64_t>::min() - right)) {
    return false;
  }
  output = left + right;
  return true;
}

bool ReadinessComplete(const game::WarEntryAssessmentReadinessV1 &value) {
  return value.actor_identity_ready && value.targets_declarable_ready &&
         value.effective_targets_ready && value.ai_context_ready &&
         value.native_output_ready && value.network_decomposition_ready &&
         value.same_frame_ready && value.ready;
}

bool ResultComplete(const game::WarEntryAssessmentsV1 &result) {
  if (!result.available || !ReadinessComplete(result.readiness) ||
      result.actor_character_id <= 0 ||
      result.requested_target_character_ids.empty() ||
      result.requested_target_character_ids.size() !=
          result.assessments.size() ||
      result.requested_target_character_ids.size() >
          static_cast<std::size_t>(kWarEntryAssessmentsV1MaximumTargets) ||
      !result.unavailable_stage.empty()) {
    return false;
  }
  for (std::size_t index = 0; index < result.assessments.size(); ++index) {
    const auto &row = result.assessments[index];
    if (result.requested_target_character_ids[index] <= 0 ||
        row.target_character_id !=
            result.requested_target_character_ids[index] ||
        row.effective_target_character_id <= 0 || row.distance_raw < 0 ||
        row.actor_power_base_raw < 0 || row.actor_power_total_raw < 0 ||
        row.actor_network_contribution_raw < 0 ||
        row.target_power_base_raw < 0 ||
        row.target_network_contribution_raw < 0 ||
        row.target_pre_adjustment_total_raw < 0 ||
        row.target_power_total_raw < 0 || row.actual_power_ratio_raw < 0) {
      return false;
    }
    std::int64_t actor_total = 0;
    std::int64_t target_pre = 0;
    std::int64_t target_total = 0;
    if (!CheckedAdd(row.actor_power_base_raw,
                    row.actor_network_contribution_raw, actor_total) ||
        actor_total != row.actor_power_total_raw ||
        !CheckedAdd(row.target_power_base_raw,
                    row.target_network_contribution_raw, target_pre) ||
        target_pre != row.target_pre_adjustment_total_raw ||
        !CheckedAdd(target_pre, row.target_adjustment_delta_raw,
                    target_total) ||
        target_total != row.target_power_total_raw) {
      return false;
    }
  }
  return true;
}

bool AppendIdArray(std::string &output,
                   const std::vector<std::int32_t> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendNumber(output, values[index])) {
      return false;
    }
  }
  output.push_back(']');
  return true;
}

bool AppendRow(std::string &output,
               const game::WarEntryAssessmentRowV1 &row) {
  output += "{\"target_character_id\":";
  if (!AppendNumber(output, row.target_character_id)) {
    return false;
  }
  output += ",\"effective_target_character_id\":";
  if (!AppendNumber(output, row.effective_target_character_id)) {
    return false;
  }
  output += ",\"distance_raw\":";
  if (!AppendNumber(output, row.distance_raw)) {
    return false;
  }
  output += ",\"actor_power_base_raw\":";
  if (!AppendNumber(output, row.actor_power_base_raw)) {
    return false;
  }
  output += ",\"actor_network_contribution_raw\":";
  if (!AppendNumber(output, row.actor_network_contribution_raw)) {
    return false;
  }
  output += ",\"actor_power_total_raw\":";
  if (!AppendNumber(output, row.actor_power_total_raw)) {
    return false;
  }
  output += ",\"target_power_base_raw\":";
  if (!AppendNumber(output, row.target_power_base_raw)) {
    return false;
  }
  output += ",\"target_network_contribution_raw\":";
  if (!AppendNumber(output, row.target_network_contribution_raw)) {
    return false;
  }
  output += ",\"target_pre_adjustment_total_raw\":";
  if (!AppendNumber(output, row.target_pre_adjustment_total_raw)) {
    return false;
  }
  output += ",\"target_adjustment_delta_raw\":";
  if (!AppendNumber(output, row.target_adjustment_delta_raw)) {
    return false;
  }
  output += ",\"target_power_total_raw\":";
  if (!AppendNumber(output, row.target_power_total_raw)) {
    return false;
  }
  output += ",\"actual_power_ratio_raw\":";
  if (!AppendNumber(output, row.actual_power_ratio_raw)) {
    return false;
  }
  output += ",\"target_ai_context_actor_entry_raw\":";
  if (!AppendNumber(output, row.target_ai_context_actor_entry_raw)) {
    return false;
  }
  output += ",\"actor_ai_context_target_entry_raw\":";
  if (!AppendNumber(output, row.actor_ai_context_target_entry_raw)) {
    return false;
  }
  output += ",\"native_flags_raw\":";
  if (!AppendNumber(output, static_cast<std::uint32_t>(row.native_flags_raw))) {
    return false;
  }
  output.push_back('}');
  return true;
}

} // namespace

std::string
SerializeWarEntryAssessmentsV1(const game::WarEntryAssessmentsV1 &result) {
  if (!ResultComplete(result)) {
    return {};
  }
  std::string output;
  output.reserve(1024 + result.assessments.size() * 512);
  output += "{\"schema_version\":1,\"status\":\"available\",";
  output += "\"snapshot_revision\":";
  if (!AppendNumber(output, result.snapshot_revision)) {
    return {};
  }
  output += ",\"date_raw\":";
  if (!AppendNumber(output, result.date_raw)) {
    return {};
  }
  output += ",\"actor_character_id\":";
  if (!AppendNumber(output, result.actor_character_id)) {
    return {};
  }
  output += ",\"requested_target_character_ids\":";
  if (!AppendIdArray(output, result.requested_target_character_ids)) {
    return {};
  }
  output += ",\"assessments\":[";
  for (std::size_t index = 0; index < result.assessments.size(); ++index) {
    if (index != 0) {
      output.push_back(',');
    }
    if (!AppendRow(output, result.assessments[index])) {
      return {};
    }
  }
  output += "],\"readiness\":{";
  output += "\"actor_identity_ready\":true,";
  output += "\"targets_declarable_ready\":true,";
  output += "\"effective_targets_ready\":true,";
  // `ai_context_ready` is the frozen schema-v1 spelling.  Its production
  // meaning is authoritative native actor State16 builder readiness.
  output += "\"ai_context_ready\":true,";
  output += "\"native_output_ready\":true,";
  output += "\"network_decomposition_ready\":true,";
  output += "\"same_frame_ready\":true,\"ready\":true},";
  output += "\"provenance\":{";
  output += "\"game_version\":\"1.19.0.6\",";
  output += "\"executable_sha256\":\"";
  output += kWarEntryAssessmentsV1ExecutableSha256;
  output += "\",\"assessment_rva\":\"0x1878A00\",";
  output += "\"network_collector_rva\":\"0x1879850\",";
  output +=
      "\"power_leaf\":\"CCharacter+0x1B8->+0x308\",";
  output += "\"fixed_point_scale\":100000}}";
  return output;
}

} // namespace xar::ck3_11906
