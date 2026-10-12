#pragma once

#include "xar_bridge/ck3_12002_family_obligations_alliance.hpp"

#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

struct PrewarOwnerAlly12004 {
  std::int32_t character_id = -1;
  bool forward_is_allied = false;
  bool reverse_is_allied = false;
  bool has_realm_data = false;

  bool operator==(const PrewarOwnerAlly12004 &) const = default;
};

struct PrewarOwnerAllies12004 {
  std::int32_t owner_character_id = -1;
  bool owner_verified = false;
  bool owner_alive = false;

  bool family_component_present = false;
  bool family_source_complete = false;
  // Raw spouse-vector rows, including absent (-1) entries, before deduplication.
  // -1 means the vector count has not been observed. Betrothed is separate.
  std::int32_t family_source_count = -1;
  std::int32_t family_source_visited_count = 0;
  bool family_betrothed_observed = false;
  std::int32_t family_betrothed_character_id = -1;

  bool relations_component_present = false;
  bool relations_source_complete = false;
  std::int32_t relations_source_count = -1;
  std::int32_t relations_source_visited_count = 0;

  std::vector<std::int32_t> source_character_ids;
  std::vector<std::int32_t> dead_source_character_ids;
  std::vector<std::int32_t> unresolved_source_character_ids;
  // Every resolved, living peer has a sample, including observed false values.
  // These samples let the owning aggregate compare both complete read rounds.
  std::vector<PrewarOwnerAlly12004> native_membership_samples;
  std::int32_t native_pair_predicate_sampled_count = 0;
  // Only peers with observed native IsAllied=true in both directions.
  std::vector<PrewarOwnerAlly12004> allies;
  bool collection_complete = false;
  std::string_view reason;

  bool operator==(const PrewarOwnerAllies12004 &) const = default;
};

// Owning paused application thread only. The caller must supply independently
// admitted actual4 BindFamilyObligationsAllianceImage bindings and its genuine
// played-character frame; owner is a separate full-generation CharacterID.
// This is one sample. The owning aggregate checks its mailbox ticket/frame and
// compares two whole DTOs before publishing a stable result.
// True means a verified living owner was sampled, including partial samples.
// Malformed source containers/unresolved references retain observed rows with
// collection_complete=false and a reason; they never become an empty result.
// Null native family/relations components are observed complete empty sources.
// False means the binding/frame/owner/capture could not be admitted. The DTO
// still retains observed identity/completeness diagnostics; do not read its
// default false fields as native predicate observations.
bool ReadPrewarOwnerAllies12004(
    const ck3_12002::family_obligations_alliance::Bindings &bindings,
    const ck3_12002::CoreSnapshotPrefix &frame,
    std::int32_t owner_character_id, PrewarOwnerAllies12004 &output,
    std::string_view *reason = nullptr) noexcept;

} // namespace xar::ck3_12004
