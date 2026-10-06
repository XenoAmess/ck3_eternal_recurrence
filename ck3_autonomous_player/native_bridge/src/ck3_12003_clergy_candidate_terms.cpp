#include "xar_bridge/ck3_12003_clergy_candidate_terms.hpp"

#include <algorithm>
#include <array>
#include <sstream>

namespace xar::ck3_12003::religion::clergy_candidate_terms {
namespace {
namespace c = ck3_12002;

template <std::size_t N>
std::string_view Fixed(const std::array<char, N> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return end == value.end() ? std::string_view{} :
      std::string_view{value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool Failed(Observation &out, Failure failure) noexcept {
  out.available = false;
  out.failure = failure;
  out.final_predicates_available = false;
  out.candidate_already_councillor.reset();
  out.candidate_is_guest.reset();
  out.pending_character_interaction.reset();
  out.native_can_confirm_replacement.reset();
  return false;
}

bool SameRequest(const c::CouncilCandidatesFrameV1 &frame,
                 const c::CouncilCandidatesRequestV1 &request) noexcept {
  return frame.paused && frame.map_ready && frame.has_played_character &&
      frame.played_character_alive && frame.played_character_identity_round_trip &&
      frame.active_task_identity_round_trip &&
      Fixed(frame.snapshot_id) == request.expected_snapshot_id &&
      frame.public_revision == request.expected_public_revision &&
      frame.native_revision == request.expected_native_revision &&
      frame.date_raw == request.expected_date_raw &&
      frame.played_character_id == request.expected_owner_character_id &&
      Fixed(frame.position_key) == c::kCouncilCandidatesChaplainPosition12002;
}

bool Incumbent(const Environment &e, const c::CouncilCandidatesFrameV1 &frame,
               std::int32_t &id, const void *&pointer) noexcept {
  pointer = nullptr;
  if (!c::ReadCouncilMemory12002(e.access,
      reinterpret_cast<const void *>(frame.active_task +
          c::kCouncilCandidatesTaskIncumbentOffset12002), &id, sizeof(id))) return false;
  return id == -1 || c::ResolveCouncilCharacter12002(e.candidates, e.access, id, pointer);
}

template <typename T>
void Optional(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
} // namespace

Environment BindClergyCandidateTermsImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  Environment e{};
  if (!base || sha != kExecutableSha256) return e;
  e.enabled = true;
  e.executable_sha256 = kExecutableSha256;
  e.candidates = c::BindCouncilCandidates12002(base, c::kExecutableSha256);
  e.gates = c::BindCouncilGates12002(base, c::kExecutableSha256);
  return e;
}

bool ReadClergyCandidateTerms12003(const Environment &e, const Request &request,
    std::uint64_t epoch, Observation &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  out.public_revision = request.frame.expected_public_revision;
  out.native_revision = request.frame.expected_native_revision;
  out.date_raw = request.frame.expected_date_raw;
  out.owner_character_id = request.frame.expected_owner_character_id;
  out.candidate_character_id = request.candidate_character_id;
  if (!e.enabled || e.executable_sha256 != kExecutableSha256)
    return Failed(out, Failure::bindings_unavailable);
  if (epoch == 0 || request.candidate_character_id <= 0 ||
      request.frame.position_key != c::kCouncilCandidatesChaplainPosition12002)
    return Failed(out, Failure::invalid_request);

  game::CouncilCompositionCandidatesPublicV1 collection{};
  if (c::ReadCouncilCandidates12002(e.candidates, e.access, request.frame, collection) !=
      ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1::available)
    return Failed(out, Failure::candidate_collection_unavailable);
  out.candidate_collection_available = true;
  out.candidate_count = collection.candidate_count;
  std::uint32_t matches = 0;
  for (std::uint32_t i = 0; i < collection.candidate_count; ++i) {
    const auto &row = collection.candidates[i];
    if (row.character_id != request.candidate_character_id) continue;
    ++matches;
    out.native_collection_ordinal = row.native_collection_ordinal;
    out.candidate_learning = row.main_skill.value;
  }
  out.candidate_match_count = matches;
  out.candidate_in_native_collection = matches == 1;

  c::CouncilCandidatesFrameV1 before{};
  if (!c::CaptureCouncilCandidatesFrame12002(e.candidates, e.access, before,
      c::kCouncilCandidatesChaplainPosition12002) || !SameRequest(before, request.frame) ||
      before.active_task_id <= 0)
    return Failed(out, Failure::frame_unavailable);
  std::int32_t incumbent_id = -1;
  const void *incumbent = nullptr;
  if (!Incumbent(e, before, incumbent_id, incumbent) ||
      incumbent_id != collection.incumbent_character_id)
    return Failed(out, Failure::state_changed);
  out.active_task_id = before.active_task_id;
  if (incumbent_id != -1) out.incumbent_character_id = incumbent_id;

  // The native collection excludes the current incumbent. A known absent row
  // remains an available membership observation; no imaginary route is tested.
  if (matches == 0) {
    out.native_collection_ordinal.reset();
    out.candidate_learning.reset();
  } else {
    if (matches != 1) return Failed(out, Failure::candidate_collection_unavailable);
    const void *candidate = nullptr;
    if (!c::ResolveCouncilCharacter12002(e.candidates, e.access,
        request.candidate_character_id, candidate))
      return Failed(out, Failure::candidate_unavailable);
    game::CouncilAssignCouncillorFrameV1 frame{};
    frame.available = true;
    frame.paused = before.paused;
    frame.map_ready = before.map_ready;
    frame.snapshot_id.assign(Fixed(before.snapshot_id));
    frame.public_revision = before.public_revision;
    frame.native_revision = before.native_revision;
    frame.date_raw = before.date_raw;
    frame.owner_character_id = before.played_character_id;
    frame.owner_identity_round_trip = before.played_character_identity_round_trip;
    frame.position_key.assign(c::kCouncilCandidatesChaplainPosition12002);
    frame.active_task_id = before.active_task_id;
    frame.active_task_identity_round_trip = before.active_task_identity_round_trip;
    frame.has_incumbent = incumbent_id != -1;
    frame.incumbent_character_id = incumbent_id;
    frame.incumbent_identity_round_trip = frame.has_incumbent && incumbent != nullptr;
    game::CouncilAssignCouncillorFinalLegalityV1 gates{};
    gates.owner_character_id = frame.owner_character_id;
    gates.active_task_id = frame.active_task_id;
    gates.position_key = frame.position_key;
    gates.candidate_character_id = request.candidate_character_id;
    gates.candidate_match_count = matches;
    gates.candidate_identity_round_trip = true;
    if (!c::EvaluateCouncilCandidateObservationGates12002(e.gates, frame,
        request.candidate_character_id, const_cast<void *>(candidate), gates) ||
        !gates.available)
      return Failed(out, Failure::native_predicate_unavailable);
    const void *candidate_after = nullptr;
    if (!c::ResolveCouncilCharacter12002(e.candidates, e.access,
        request.candidate_character_id, candidate_after) || candidate != candidate_after)
      return Failed(out, Failure::state_changed);
    out.final_predicates_available = true;
    out.candidate_already_councillor = gates.candidate_already_councillor;
    out.candidate_is_guest = gates.candidate_is_guest;
    out.pending_character_interaction = gates.pending_character_interaction;
    if (gates.incumbent_fireability_evaluated)
      out.native_can_confirm_replacement = gates.incumbent_can_be_fired;
  }

  c::CouncilCandidatesFrameV1 after{};
  std::int32_t incumbent_after_id = -1;
  const void *incumbent_after = nullptr;
  if (!c::CaptureCouncilCandidatesFrame12002(e.candidates, e.access, after,
      c::kCouncilCandidatesChaplainPosition12002) || after != before ||
      !Incumbent(e, after, incumbent_after_id, incumbent_after) ||
      incumbent_after_id != incumbent_id || incumbent_after != incumbent)
    return Failed(out, Failure::state_changed);
  out.available = true;
  out.failure = Failure::none;
  return true;
}

const char *ClergyCandidateTermsFailureKey12003(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::invalid_request: return "invalid_request";
  case Failure::candidate_collection_unavailable: return "candidate_collection_unavailable";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::candidate_unavailable: return "candidate_unavailable";
  case Failure::native_predicate_unavailable: return "native_predicate_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "unknown";
}

std::string SerializeClergyCandidateTerms12003(const Observation &v) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":\"xar.ck3.clergy-candidate-terms/v1\","
      "\"schema_version\":1,\"exact_build\":{\"game_version\":\"1.20.0.3\","
      "\"executable_sha256\":\"" << kExecutableSha256 << "\"},\"available\":"
      << v.available << ",\"failure\":\"" << ClergyCandidateTermsFailureKey12003(v.failure)
      << "\",\"capture_epoch\":" << v.capture_epoch << ",\"public_revision\":"
      << v.public_revision << ",\"native_revision\":" << v.native_revision
      << ",\"date_raw\":" << v.date_raw << ",\"owner_character_id\":"
      << v.owner_character_id << ",\"candidate_character_id\":" << v.candidate_character_id
      << ",\"position_key\":\"councillor_court_chaplain\",\"active_task_id\":";
  Optional(out, v.active_task_id);
  out << ",\"incumbent_character_id\":"; Optional(out, v.incumbent_character_id);
  out << ",\"candidate_collection_available\":" << v.candidate_collection_available
      << ",\"candidate_count\":"; Optional(out, v.candidate_count);
  out << ",\"candidate_match_count\":"; Optional(out, v.candidate_match_count);
  out << ",\"candidate_in_native_collection\":"; Optional(out, v.candidate_in_native_collection);
  out << ",\"native_collection_ordinal\":"; Optional(out, v.native_collection_ordinal);
  out << ",\"candidate_learning\":"; Optional(out, v.candidate_learning);
  out << ",\"final_predicates_available\":" << v.final_predicates_available
      << ",\"candidate_already_councillor\":"; Optional(out, v.candidate_already_councillor);
  out << ",\"candidate_is_guest\":"; Optional(out, v.candidate_is_guest);
  out << ",\"pending_character_interaction\":"; Optional(out, v.pending_character_interaction);
  out << ",\"native_can_confirm_replacement\":"; Optional(out, v.native_can_confirm_replacement);
  out << ",\"action_eligibility_complete\":false}";
  return out.str();
}

} // namespace xar::ck3_12003::religion::clergy_candidate_terms
