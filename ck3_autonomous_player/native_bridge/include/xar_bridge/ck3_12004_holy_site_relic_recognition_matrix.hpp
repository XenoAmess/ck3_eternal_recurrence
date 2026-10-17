#pragma once
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004::religion::holy_site_relic {
struct Bindings;
struct Snapshot;
struct MatrixFaith {
  std::uint32_t faith_id = 0xFFFFFFFFU;
  bool source_associated = false, source_player = false, source_county_holder = false;
  bool object_resolved = false;
  std::string unavailable_reason;
};
struct MatrixArtifact {
  std::uint32_t artifact_id = 0xFFFFFFFFU;
  std::vector<std::uint32_t> slot_indices, candidate_indices;
  bool source_action_request = false, object_resolved = false;
  std::string unavailable_reason;
};
struct MatrixCell {
  std::uint32_t artifact_id = 0xFFFFFFFFU, faith_id = 0xFFFFFFFFU;
  bool available = false;
  std::optional<bool> value;
  std::string unavailable_reason = "recognition_not_read";
};
struct RecognitionMatrix {
  bool available = false, complete = false, source_arrays_stable = false;
  std::uint32_t holy_site_id = 0xFFFFFFFFU;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  bool associated_available = false, slots_available = false, window_candidates_available = false;
  std::vector<std::uint32_t> associated_faith_ids, window_candidate_artifact_ids;
  std::vector<std::optional<std::uint32_t>> slot_artifact_ids;
  std::optional<std::uint32_t> player_faith_id, county_holder_faith_id, requested_action_artifact_id;
  std::vector<MatrixFaith> faiths;
  std::vector<MatrixArtifact> artifacts;
  std::vector<MatrixCell> cells;
  std::uint32_t native_getter_calls = 0;
  static constexpr std::uint32_t max_native_getter_calls = 256;
  static constexpr std::uint32_t max_faiths = 64, max_slots = 64, max_candidates = 64, max_artifacts = 64;
  std::string unavailable_reason = "recognition_matrix_not_read";
};
// Only the existing paused religion owner. Original recognition evaluations are
// sequential and may allocate/use TLS; unproved deeper script RNG effects remain
// unknown. No command/cache refresh and no claim of per-faith Active or benefits.
bool ReadHolySiteRelicRecognitionMatrix12004(const Bindings &, const void *jomini_owner,
    const ck3_12002::religion::Context &, std::uint32_t holy_site_id,
    std::optional<std::uint32_t> requested_action_artifact_id,
    const Snapshot *expected_context, RecognitionMatrix &) noexcept;
std::string SerializeHolySiteRelicRecognitionMatrix12004(const RecognitionMatrix &);
}
