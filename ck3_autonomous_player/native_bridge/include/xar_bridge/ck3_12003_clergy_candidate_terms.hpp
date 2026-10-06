#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_council_candidates.hpp"
#include "xar_bridge/ck3_12002_council_gates.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12003::religion::clergy_candidate_terms {

struct Environment {
  bool enabled = false;
  std::string_view executable_sha256{};
  ck3_12002::CouncilCandidatesEnvironmentV1 candidates{};
  ck3_12002::CouncilCandidatesAccessV1 access{};
  ck3_12002::CouncilGatesEnvironment12002 gates{};
};

struct Request {
  // Actual public/native binding from the caller's existing owning envelope.
  // The capture callback supplies the same source frame; no value is guessed.
  ck3_12002::CouncilCandidatesRequestV1 frame{};
  std::int32_t candidate_character_id = -1;
};

enum class Failure {
  none,
  bindings_unavailable,
  invalid_request,
  candidate_collection_unavailable,
  frame_unavailable,
  candidate_unavailable,
  native_predicate_unavailable,
  state_changed,
};

struct Observation {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t owner_character_id = -1;
  std::int32_t candidate_character_id = -1;
  std::optional<std::int32_t> active_task_id;
  std::optional<std::int32_t> incumbent_character_id;
  bool candidate_collection_available = false;
  std::optional<std::uint32_t> candidate_count;
  std::optional<std::uint32_t> candidate_match_count;
  std::optional<bool> candidate_in_native_collection;
  std::optional<std::uint32_t> native_collection_ordinal;
  std::optional<std::int32_t> candidate_learning;
  bool final_predicates_available = false;
  std::optional<bool> candidate_already_councillor;
  std::optional<bool> candidate_is_guest;
  std::optional<bool> pending_character_interaction;
  std::optional<bool> native_can_confirm_replacement;
};

// Address calculation only. The .3 identity is public; reviewed ABI provider
// binders remain strict .2 and are reused internally by the Crozier adapter.
Environment BindClergyCandidateTermsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Read-only same-frame collection and explicit-candidate terms. Calls no
// appointment, recruitment, swap, task-selection or mutation helper.
bool ReadClergyCandidateTerms12003(const Environment &environment,
    const Request &request, std::uint64_t capture_epoch,
    Observation &output) noexcept;
std::string SerializeClergyCandidateTerms12003(const Observation &value);
const char *ClergyCandidateTermsFailureKey12003(Failure failure) noexcept;

} // namespace xar::ck3_12003::religion::clergy_candidate_terms
