#pragma once
#include "xar_bridge/ck3_1210_battle_candidate_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include <string>

namespace xar::ck3_1210 {
// A future main-mailbox producer captures these from CURRENT Core and the
// actual executor stamp. Expected/request fields must never populate this.
// This reserve is internal: the candidate leaf has no observed-frame field.
struct BattleCandidateActualSourceStampV1 {
  CoreSnapshotPrefix core{};
  ck3_11906::MainThreadExecutionStampV1 application_main{};
};
using BattleCandidateCaptureActualSourceV1 = bool (*)(void *,
    BattleCandidateActualSourceStampV1 &) noexcept;
struct BattleCandidateActualSourceAccessV1 {
  void *context = nullptr;
  BattleCandidateCaptureActualSourceV1 capture = nullptr;
};
struct BattleCandidateProducedLeafV1 {
  bool exact_source_admitted = false;
  BattleCandidateObservationV1 candidate{};
  // Missing means no observed Core/custody stamp producer was supplied.
  // Even a present value is no Full/Root/Action qualification or live proof.
  std::optional<BattleCandidateActualSourceStampV1> actual_source_stamp;
};
namespace battle_candidate_serializer_detail_v1 {
inline bool SameCore(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.speed == b.clock.speed &&
      a.clock.paused == b.clock.paused && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
inline bool SaneActualStamp(const BattleCandidateActualSourceStampV1 &value,
    std::int32_t actor) noexcept {
  const auto &core = value.core; const auto &stamp = value.application_main;
  // Sanity checks are not a current-thread/TLS ownership verifier. The actual
  // owning executor must perform that verification before invoking capture.
  return core.clock.paused && core.map_ready && core.has_played_character &&
      core.played_character_alive && core.played_character_id == actor &&
      core.local_player_id != -1 && stamp.paused &&
      stamp.date_raw == core.clock.date_raw && stamp.thread_id != 0 &&
      stamp.pump_epoch != 0 && stamp.game_state != 0 && stamp.jomini_state != 0 &&
      stamp.tls_initialized_flag_address != 0 && stamp.tls_initialized != 0 &&
      stamp.tls_context != 0 && stamp.tls_main_thread_marker != 0;
}
inline bool ValidCandidate(const BattleCandidateObservationV1 &value) noexcept {
  switch (value.status) {
  case BattleCandidateStatusV1::unavailable:
    return value.subject_public_cunit_id == -1 && value.source_native_carmy_id == -1 &&
        !value.candidate_combat_id;
  case BattleCandidateStatusV1::not_referenced:
    return value.subject_public_cunit_id != -1 && value.source_native_carmy_id != -1 &&
        !value.candidate_combat_id;
  case BattleCandidateStatusV1::identity_candidate:
    return value.subject_public_cunit_id != -1 && value.source_native_carmy_id != -1 &&
        value.candidate_combat_id && *value.candidate_combat_id != -1;
  }
  return false;
}
} // namespace battle_candidate_serializer_detail_v1

// Actual source path: invoke the exact1210 full-ID/tag/backlink memory reader.
// The optional reserve captures real before/after Core/executor values; its
// absence remains explicit. No route, native call, revision or deadline is
// minted. Original query deadlines remain the outer mailbox owner's concern.
inline bool ReadBattleCandidateProducedLeafV1(const BattleCandidateBindingsV1 &bindings,
    std::int32_t unit_id, std::int32_t actor_id, BattleCandidateProducedLeafV1 &output,
    BattleCandidateAccessV1 identity_access,
    BattleCandidateActualSourceAccessV1 source_access = {}) noexcept {
  output = {};
  if (!bindings.exact_build_admitted || unit_id == -1 || actor_id == -1 ||
      identity_access.copy == nullptr || identity_access.same_paused_frame == nullptr ||
      !identity_access.same_paused_frame(identity_access.context)) return false;
  BattleCandidateActualSourceStampV1 before{}, after{};
  if (source_access.capture != nullptr &&
      (!source_access.capture(source_access.context, before) ||
       !battle_candidate_serializer_detail_v1::SaneActualStamp(before, actor_id))) return false;
  BattleCandidateObservationV1 candidate{};
  if (!ReadBattleCandidateV1(bindings, unit_id, actor_id, candidate, identity_access)) return false;
  if (source_access.capture != nullptr) {
    if (!source_access.capture(source_access.context, after) ||
        !battle_candidate_serializer_detail_v1::SaneActualStamp(after, actor_id) ||
        !battle_candidate_serializer_detail_v1::SameCore(before.core, after.core) ||
        before.application_main != after.application_main ||
        !identity_access.same_paused_frame(identity_access.context)) return false;
    output.actual_source_stamp = after;
  }
  output.exact_source_admitted = true;
  output.candidate = candidate;
  return true;
}

// Pure formatter consumed by production and the NoGame RAM fixture alike.
// It emits the agreed strict union only. Exact source failure or malformed
// DTOs collapse to unavailable without IDs. No observed stamp is synthesized
// or serialized, and no legacy status/available/ready/action flag is emitted.
inline std::string SerializeBattleCandidateLeafV1(const BattleCandidateProducedLeafV1 &value) {
  constexpr auto unavailable = "{\"candidate_status\":\"unavailable\"}";
  const auto &candidate = value.candidate;
  if (!value.exact_source_admitted ||
      !battle_candidate_serializer_detail_v1::ValidCandidate(candidate) ||
      candidate.status == BattleCandidateStatusV1::unavailable) return unavailable;
  std::string out = "{\"candidate_status\":\"";
  out += candidate.status == BattleCandidateStatusV1::not_referenced ?
      "not_referenced" : "identity_candidate";
  out += "\",\"subject_public_cunit_id\":" + std::to_string(candidate.subject_public_cunit_id);
  out += ",\"source_native_carmy_id\":" + std::to_string(candidate.source_native_carmy_id);
  out += ",\"candidate_combat_id\":";
  out += candidate.candidate_combat_id ? std::to_string(*candidate.candidate_combat_id) : "null";
  out += '}';
  return out;
}
} // namespace xar::ck3_1210
