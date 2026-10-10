#include "xar_bridge/army_pre_date_prefix_stage_12004.hpp"

#include <limits>

namespace xar::ck3_12004::army_pre_date_prefix_stage {
namespace {
bool MatchesBuild(std::string_view actual) {
  if (actual.size() != kExecutableSha256.size()) return false;
  for (std::size_t index = 0; index < actual.size(); ++index) {
    char byte = actual[index];
    if (byte >= 'A' && byte <= 'F') byte = static_cast<char>(byte - 'A' + 'a');
    if (byte != kExecutableSha256[index]) return false;
  }
  return true;
}
} // namespace

CurrentHeaderFrame ObserveCurrentHeader(std::string_view executable_sha256,
    std::uintptr_t actual_primary, ReadBytes read_bytes, void *context) {
  CurrentHeaderFrame out{};
  out.executable_sha256 = executable_sha256;
  out.primary_identity = actual_primary;
  if (!MatchesBuild(executable_sha256)) {
    out.unavailable_reason = "pre_date_prefix_actual4_build_mismatch";
    return out;
  }
  if (!actual_primary || !read_bytes || actual_primary >
      std::numeric_limits<std::uintptr_t>::max() - kSourceCountOffset) {
    out.unavailable_reason = "pre_date_prefix_primary_reader_unavailable";
    return out;
  }
  std::int32_t raw_count{};
  if (!read_bytes(context, actual_primary + kSourceCountOffset,
                  &raw_count, sizeof(raw_count))) {
    out.unavailable_reason = "pre_date_prefix_primary_d4_unavailable";
    return out;
  }
  out.source_count_d4 = raw_count;
  return out;
}

ConditionalProjection ProjectCurrentHeader(const CurrentHeaderFrame &frame) {
  ConditionalProjection out{};
  if (!MatchesBuild(frame.executable_sha256)) {
    out.unavailable_reason = "pre_date_prefix_actual4_build_mismatch";
    return out;
  }
  if (!frame.primary_identity || !frame.source_count_d4) {
    out.unavailable_reason = frame.unavailable_reason.empty()
        ? "pre_date_prefix_primary_d4_unavailable" : frame.unavailable_reason;
    return out;
  }
  out.source_count_ready = true;
  if (*frame.source_count_d4 <= 0) {
    // 2A9A34A -> 2A9A35A -> 2A9A563..56C: no game stores or calls.
    out.verdict = Verdict::no_work;
    out.complete_no_work_arm = true;
    out.primary_state_preserved_by_prefix = true;
  } else {
    out.verdict = Verdict::positive_occurrence_inputs_required;
    out.unavailable_reason = "pre_date_prefix_positive_stage_inputs_required";
  }
  return out;
}

} // namespace xar::ck3_12004::army_pre_date_prefix_stage
