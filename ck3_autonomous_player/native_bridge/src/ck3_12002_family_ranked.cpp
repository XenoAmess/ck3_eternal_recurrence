#include "xar_bridge/ck3_12002_family_ranked.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_family_ranked_abi.hpp"

#include <algorithm>
#include <cstring>
#include <limits>

namespace xar::ck3_12002 {
namespace {
using Failure = bridge::MarriageMatchmakingObserverFailureV1;
using SourceFailure = bridge::MarriageMatchmakingSourceAdapterFailureV1;
template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}
template <typename T> void Store(void *base, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(T));
}
struct Header { void *data = nullptr; std::int32_t capacity = 0, count = 0; void *owner = nullptr; };
struct CandidateStorage { Header header; std::array<std::byte, 0x410> owner{}; };
struct ScoredStorage { Header header; std::array<std::byte, 0x210> owner{}; };
static_assert(sizeof(Header) == 0x18);
static_assert(sizeof(CandidateStorage) == 0x428);
static_assert(sizeof(ScoredStorage) == 0x228);
struct Containers {
  const FamilyRankedBindings &bindings;
  CandidateStorage &candidate;
  ScoredStorage &scored;
  bool candidate_initialized = false, scored_initialized = false;
  ~Containers() {
    if (scored_initialized) {
      if (HeaderValidForDestruction()) {
        for (std::int32_t index = 0; index < scored.header.count; ++index)
          bindings.destroy_scored_row(static_cast<std::byte *>(scored.header.data) +
              static_cast<std::size_t>(index) * 0x10, 0);
      }
      scored.header.count = 0;
      bindings.release_native_buffer(scored.owner.data(), scored.header.data, 8);
      scored.header.data = nullptr; scored.header.capacity = 0;
    }
    if (candidate_initialized) {
      candidate.header.count = 0;
      bindings.release_native_buffer(candidate.owner.data(), candidate.header.data, 8);
    }
  }
  bool HeaderValidForDestruction() const noexcept {
    return scored.header.count >= 0 && scored.header.count <= scored.header.capacity &&
        scored.header.count <= 4096 && (scored.header.count == 0 || scored.header.data != nullptr);
  }
};
bool HeaderValid(const Header &header) noexcept {
  return header.owner != nullptr && header.capacity >= 0 && header.count >= 0 &&
      header.count <= header.capacity && header.count <= 4096 &&
      (header.count == 0 || header.data != nullptr);
}
bool InitializeCandidates(Containers &c) noexcept {
  const auto &b = c.bindings;
  c.candidate.header.owner = c.candidate.owner.data();
  Store(c.candidate.owner.data(), 0, b.candidate_owner_vtable);
  Store(c.candidate.owner.data(), 0x408, b.candidate_backing_allocator);
  b.release_native_buffer(c.candidate.owner.data(), nullptr, 8);
  b.initialize_candidate_buffer(c.candidate.owner.data(), &c.candidate.header.data,
      &c.candidate.header.capacity);
  c.candidate_initialized = true;
  return c.candidate.header.data == c.candidate.owner.data() + 8 &&
      c.candidate.header.capacity == 0x80 && c.candidate.header.count == 0;
}
bool InitializeScored(Containers &c) noexcept {
  const auto &b = c.bindings;
  if (b.initialize_scored_container(&c.scored.header) != &c.scored.header) return false;
  c.scored_initialized = true;
  return c.scored.header.owner == c.scored.owner.data() &&
      c.scored.header.data == c.scored.owner.data() + 8 &&
      c.scored.header.capacity == 0x20 && c.scored.header.count == 0 &&
      Load<std::uintptr_t>(c.scored.owner.data(), 0) == b.scored_owner_vtable &&
      Load<std::uintptr_t>(c.scored.owner.data(), 0x208) == b.scored_backing_allocator;
}
bool BindingsComplete(const FamilyRankedBindings &b) noexcept {
  return b.enabled && b.family.enabled && b.read_native_tier != nullptr &&
      b.native_cap_table_slot != nullptr && b.enumerate_candidates != nullptr &&
      b.score_candidates != nullptr && b.sort_scored_candidates != nullptr &&
      b.destroy_scored_row != nullptr && b.initialize_scored_container != nullptr &&
      b.release_native_buffer != nullptr && b.initialize_candidate_buffer != nullptr &&
      b.candidate_owner_vtable != 0 && b.scored_owner_vtable != 0 &&
      b.scored_row_vtable != 0 && b.candidate_backing_allocator != 0 &&
      b.scored_backing_allocator != 0;
}
void *Alive(const FamilyRankedBindings &b, std::uint32_t id) noexcept {
  auto *character = ResolveCoreCharacter(b.family.context.core, static_cast<std::int32_t>(id));
  return character != nullptr && Load<void *>(character, kCharacterDeathDataOffset) == nullptr ?
      character : nullptr;
}
SourceFailure Strategy(void *subject, void *&strategy) noexcept {
  strategy = nullptr;
  const auto *living = Load<const std::byte *>(subject, kFamilyRankedCharacterLivingOffset);
  if (living == nullptr) return SourceFailure::strategy_unavailable;
  strategy = Load<void *>(living, kFamilyRankedLivingStrategyOffset);
  if (strategy == nullptr || Load<void *>(strategy, kFamilyRankedStrategyReadyOwnerOffset) == nullptr)
    return SourceFailure::strategy_unavailable;
  if (Load<void *>(strategy, kFamilyRankedStrategySourceCharacterOffset) != subject)
    return SourceFailure::strategy_identity_mismatch;
  return SourceFailure::none;
}
bool Parameters(const FamilyRankedBindings &b, void *subject,
    std::array<std::byte, 0x20> &out) noexcept {
  out = {};
  const auto *slot = b.family.context.interaction_database_slot;
  if (slot == nullptr || *slot == nullptr) return false;
  auto *interaction = Load<void *>(*slot, kMarriageArrangeMarriageInteractionOffset);
  if (interaction == nullptr) return false;
  Store(out.data(), 0, interaction); Store(out.data(), 8, subject); Store(out.data(), 0x10, subject);
  const auto *living = Load<const std::byte *>(subject, kFamilyRankedCharacterLivingOffset);
  bool younger_than_thirty = false;
  if (living != nullptr) {
    const auto *age = Load<const std::byte *>(living, kFamilyRankedLivingAgeDataOffset);
    if (age == nullptr) return false;
    younger_than_thirty = Load<std::int8_t>(age, kFamilyRankedAgeValueOffset) < 30;
  }
  Store(out.data(), 0x18, younger_than_thirty); Store(out.data(), 0x1C, std::int32_t{1});
  return true;
}
SourceFailure ReadRanked(const FamilyRankedBindings &b, std::uint32_t subject_id,
    std::uint32_t limit, bridge::MarriageMatchmakingNativeSampleV1 &sample,
    FamilyRankedDiagnosticsV1 &diagnostics) noexcept {
  auto *subject = Alive(b, subject_id);
  if (subject == nullptr) return SourceFailure::character_identity_unavailable;
  void *strategy = nullptr;
  auto failure = Strategy(subject, strategy);
  if (failure != SourceFailure::none) return failure;
  const auto tier = b.read_native_tier(subject);
  const auto *table = *b.native_cap_table_slot;
  if (table == nullptr) return SourceFailure::ranked_invocation_failed;
  // The signed tier indexes the exact native cap table, including its sentinel
  // entry. The producer receives this cap, not our returned-row limit.
  diagnostics.native_cap = (std::max)(std::int32_t{0}, table[tier]);
  std::array<std::byte, 0x20> parameters{};
  if (!Parameters(b, subject, parameters)) return SourceFailure::interaction_unavailable;
  alignas(16) CandidateStorage candidate_storage{};
  alignas(16) ScoredStorage scored_storage{};
  Containers containers{b, candidate_storage, scored_storage};
  if (!InitializeCandidates(containers)) return SourceFailure::ranked_container_invalid;
  b.enumerate_candidates(strategy, 0, true, diagnostics.native_cap, &containers.candidate.header);
  if (!HeaderValid(containers.candidate.header)) return SourceFailure::ranked_container_invalid;
  diagnostics.native_pool_count = containers.candidate.header.count;
  if (!InitializeScored(containers)) return SourceFailure::ranked_container_invalid;
  b.score_candidates(strategy, parameters.data(), &containers.candidate.header, &containers.scored.header);
  if (!HeaderValid(containers.scored.header)) return SourceFailure::ranked_container_invalid;
  alignas(8) std::array<std::byte, kFamilyRankedSortScratchSize> sort_scratch{};
  b.sort_scored_candidates(&containers.scored.header, sort_scratch.data());
  if (!HeaderValid(containers.scored.header)) return SourceFailure::ranked_container_invalid;
  diagnostics.native_scored_count = containers.scored.header.count;
  sample.candidate_count = (std::min)(limit, static_cast<std::uint32_t>(containers.scored.header.count));
  for (std::uint32_t index = 0; index < sample.candidate_count; ++index) {
    const auto *row = static_cast<const std::byte *>(containers.scored.header.data) + index * 0x10;
    if (Load<std::uintptr_t>(row, 0) != b.scored_row_vtable) return SourceFailure::ranked_container_invalid;
    auto &candidate = sample.candidates[index];
    candidate.candidate_character_id = Load<std::uint32_t>(row, 8);
    candidate.native_candidate_score = Load<std::int32_t>(row, 0xC);
    if (candidate.candidate_character_id == 0 || candidate.candidate_character_id == subject_id ||
        Alive(b, candidate.candidate_character_id) == nullptr)
      return SourceFailure::ranked_candidate_identity_unavailable;
    for (std::uint32_t prior = 0; prior < index; ++prior)
      if (sample.candidates[prior].candidate_character_id == candidate.candidate_character_id)
        return SourceFailure::ranked_container_invalid;
  }
  void *strategy_after = nullptr;
  if (Alive(b, subject_id) != subject || Strategy(subject, strategy_after) != SourceFailure::none ||
      strategy_after != strategy) return SourceFailure::post_evaluation_identity_drift;
  return SourceFailure::none;
}
bool ValidRoles(const bridge::MarriageMatchmakingPairRolesV1 &r,
    std::uint32_t subject, std::uint32_t candidate) noexcept {
  return r.actor_character_id == subject && r.secondary_actor_character_id == subject &&
      r.secondary_recipient_character_id == candidate && r.recipient_character_id != 0 &&
      r.recipient_character_id != subject && candidate != subject;
}
SourceFailure Evaluate(const FamilyRankedBindings &b, std::uint32_t subject_id,
    std::uint32_t candidate_id, bridge::MarriageMatchmakingPairEvaluationV1 &out) noexcept {
  out = {};
  auto *subject = Alive(b, subject_id), *candidate = Alive(b, candidate_id);
  if (subject == nullptr || candidate == nullptr) return SourceFailure::character_identity_unavailable;
  FamilyPairContextV1 context{};
  if (!PrepareFamilyPairContextV1(b.family, static_cast<std::int32_t>(subject_id),
      static_cast<std::int32_t>(subject_id), static_cast<std::int32_t>(candidate_id), context))
    return SourceFailure::context_construction_failed;
  struct ContextLease {
    const FamilyBindings &bindings; FamilyPairContextV1 &context;
    ~ContextLease() { DestroyFamilyPairContextV1(bindings, context); }
  } lease{b.family, context};
  FamilyPairTermsV1 terms{};
  if (!ReadFamilyPairTermsV1(b.family, static_cast<std::int32_t>(subject_id),
      static_cast<std::int32_t>(candidate_id), context, terms)) return SourceFailure::context_roles_invalid;
  const auto &r = terms.roles;
  out.roles = {static_cast<std::uint32_t>(r.actor_character_id),
      static_cast<std::uint32_t>(r.recipient_character_id),
      static_cast<std::uint32_t>(r.secondary_actor_character_id),
      static_cast<std::uint32_t>(r.secondary_recipient_character_id),
      static_cast<std::uint32_t>(r.intermediary_character_id)};
  if (!ValidRoles(out.roles, subject_id, candidate_id) || Alive(b, out.roles.recipient_character_id) == nullptr ||
      (r.intermediary_character_id != -1 && Alive(b, out.roles.intermediary_character_id) == nullptr))
    return SourceFailure::context_roles_invalid;
  if (terms.recipient_ai_accept_raw < (std::numeric_limits<std::int32_t>::min)() ||
      terms.recipient_ai_accept_raw > (std::numeric_limits<std::int32_t>::max)())
    return SourceFailure::acceptance_score_overflow;
  out.complete_can_send = terms.complete_can_send;
  out.complete_can_send_status_raw = terms.complete_can_send ? 1 : 0;
  out.recipient_ai_accept_raw = static_cast<std::int32_t>(terms.recipient_ai_accept_raw);
  out.recipient_answer_status_raw = terms.recipient_answer_status_raw;
  out.recipient_answer_allows_send = terms.recipient_answer_status_raw != 2;
  out.predicted_outcome = terms.adult.predicted_outcome;
  if (Alive(b, subject_id) != subject || Alive(b, candidate_id) != candidate)
    return SourceFailure::post_evaluation_identity_drift;
  return SourceFailure::none;
}
std::string_view SnapshotId(const bridge::MarriageMatchmakingFrameV1 &frame) noexcept {
  const auto end = std::find(frame.snapshot_id.begin(), frame.snapshot_id.end(), '\0');
  return {frame.snapshot_id.data(), static_cast<std::size_t>(end - frame.snapshot_id.begin())};
}
Failure ValidateFrame(const bridge::MarriageMatchmakingFrameV1 &f,
    const bridge::MarriageMatchmakingObserverRequestV1 &r) noexcept {
  if (SnapshotId(f) != r.expected_snapshot_id) return Failure::snapshot_identity_mismatch;
  if (f.public_revision != r.expected_public_revision || f.native_revision != r.expected_native_revision)
    return Failure::revision_drift;
  if (f.date_raw != r.expected_date_raw) return Failure::date_drift;
  if (!f.paused) return Failure::not_paused;
  if (!f.map_ready || !f.has_played_character || !f.played_character_alive ||
      !f.played_character_identity_round_trip || f.played_character_id != r.subject_character_id)
    return Failure::player_unavailable;
  return Failure::none;
}
} // namespace

FamilyRankedBindings BindFamilyRankedImage(std::uintptr_t base, std::string_view sha) noexcept {
  FamilyRankedBindings b{};
  b.family = BindFamilyImage(base, sha);
  if (!b.family.enabled) return b;
  b.enabled = true;
  b.read_native_tier = reinterpret_cast<FamilyRankedReadTier>(base + kFamilyRankedNativeTierRva);
  b.native_cap_table_slot = reinterpret_cast<const std::int32_t *const *>(base + kFamilyRankedNativeCapTableSlotRva);
  b.enumerate_candidates = reinterpret_cast<FamilyRankedEnumerate>(base + kFamilyRankedEnumeratorRva);
  b.score_candidates = reinterpret_cast<FamilyRankedScore>(base + kFamilyRankedScoreFilterRva);
  b.sort_scored_candidates = reinterpret_cast<FamilyRankedSortScored>(base + kFamilyRankedSortScoredRva);
  b.destroy_scored_row = reinterpret_cast<FamilyRankedDestroyScoredRow>(base + kFamilyRankedDestroyScoredRowRva);
  b.initialize_scored_container = reinterpret_cast<FamilyRankedInitializeScored>(base + kFamilyRankedInitializeScoredRva);
  b.release_native_buffer = reinterpret_cast<FamilyRankedReleaseBuffer>(base + kFamilyRankedReleaseBufferRva);
  b.initialize_candidate_buffer = reinterpret_cast<FamilyRankedInitializeCandidates>(base + kFamilyRankedInitializeCandidatesRva);
  b.candidate_owner_vtable = base + kFamilyRankedCandidateOwnerVtableRva;
  b.scored_owner_vtable = base + kFamilyRankedScoredOwnerVtableRva;
  b.scored_row_vtable = base + kFamilyRankedScoredRowVtableRva;
  b.candidate_backing_allocator = base + kFamilyRankedCandidateBackingAllocatorRva;
  b.scored_backing_allocator = base + kFamilyRankedScoredBackingAllocatorRva;
  return b;
}

bool ReadMarriageMatchmakingObservationV1(const FamilyRankedBindings &b,
    const FamilyRankedAccessV1 &access, const bridge::MarriageMatchmakingObserverRequestV1 &request,
    bridge::MarriageMatchmakingObservationV1 &out, FamilyRankedDiagnosticsV1 *diag) noexcept {
  out = {};
  FamilyRankedDiagnosticsV1 diagnostics{};
  auto fail = [&](Failure failure) {
    out = {}; out.unavailable_reason = failure;
    if (diag != nullptr) *diag = diagnostics;
    return false;
  };
  if (request.expected_snapshot_id.empty() || request.expected_snapshot_id.size() >= 48 ||
      request.expected_public_revision == 0 || request.expected_native_revision == 0 ||
      request.expected_date_raw <= 0 || request.subject_character_id == 0 ||
      request.matchmaker_character_id != request.subject_character_id || request.limit == 0 ||
      request.limit > 8 || request.candidate_character_id == request.subject_character_id ||
      access.capture_frame == nullptr || access.is_main_thread == nullptr) return fail(Failure::invalid_request);
  if (!b.enabled || !b.family.enabled) return fail(Failure::exact_build_not_admitted);
  if (!BindingsComplete(b)) return fail(Failure::native_entry_points_unavailable);
  if (!access.is_main_thread(access.context)) return fail(Failure::application_main_thread_required);
  bridge::MarriageMatchmakingFrameV1 before{}, after{};
  if (!access.capture_frame(access.context, before)) return fail(Failure::frame_capture_failed);
  auto failure = ValidateFrame(before, request);
  if (failure != Failure::none) return fail(failure);
  CoreSnapshotPrefix core{};
  if (!ReadCoreSnapshot(b.family.context.core, core) || !core.clock.paused || !core.map_ready ||
      !core.has_played_character || !core.played_character_alive ||
      static_cast<std::uint32_t>(core.played_character_id) != request.subject_character_id ||
      core.clock.date_raw != request.expected_date_raw) return fail(Failure::player_unavailable);
  std::array<bridge::MarriageMatchmakingNativeSampleV1, 2> samples{};
  for (auto &sample : samples) {
    sample.subject_character_id = request.subject_character_id;
    sample.matchmaker_character_id = request.matchmaker_character_id;
    diagnostics.source_failure = ReadRanked(b, request.subject_character_id, request.limit, sample, diagnostics);
    if (diagnostics.source_failure == SourceFailure::strategy_unavailable) return fail(Failure::ranked_source_unavailable);
    if (diagnostics.source_failure != SourceFailure::none) return fail(Failure::native_ranked_source_failed);
    for (std::uint32_t index = 0; index < sample.candidate_count; ++index) {
      diagnostics.source_failure = Evaluate(b, request.subject_character_id,
          sample.candidates[index].candidate_character_id, sample.evaluations[index]);
      if (diagnostics.source_failure != SourceFailure::none) return fail(Failure::pair_evaluation_failed);
    }
  }
  if (samples[0] != samples[1]) return fail(Failure::native_sample_drift);
  if (!access.capture_frame(access.context, after)) return fail(Failure::frame_capture_failed);
  if (SnapshotId(before) != SnapshotId(after)) return fail(Failure::snapshot_identity_mismatch);
  if (before.date_raw != after.date_raw) return fail(Failure::date_drift);
  if (before != after) return fail(Failure::revision_drift);
  CoreSnapshotPrefix core_after{};
  if (!ReadCoreSnapshot(b.family.context.core, core_after) || !core_after.clock.paused ||
      core_after.clock.date_raw != core.clock.date_raw ||
      core_after.played_character_id != core.played_character_id || !core_after.played_character_alive)
    return fail(Failure::revision_drift);
  out.status = bridge::MarriageMatchmakingObserverStatusV1::available;
  out.snapshot_id = before.snapshot_id; out.public_revision = before.public_revision;
  out.native_revision = before.native_revision; out.proof_epoch = before.proof_epoch; out.date_raw = before.date_raw;
  out.subject_character_id = request.subject_character_id; out.matchmaker_character_id = request.matchmaker_character_id;
  for (std::uint32_t index = 0; index < samples[0].candidate_count; ++index) {
    const auto &row = samples[0].candidates[index];
    if (request.candidate_character_id != 0 && row.candidate_character_id != request.candidate_character_id) continue;
    auto &candidate = out.candidates[out.candidate_count++];
    candidate.rank = index + 1; candidate.subject_character_id = request.subject_character_id;
    candidate.matchmaker_character_id = request.matchmaker_character_id;
    candidate.candidate_character_id = row.candidate_character_id;
    candidate.native_candidate_score = row.native_candidate_score; candidate.evaluation = samples[0].evaluations[index];
  }
  out.readiness = {true, true, true, true, true, true, true, true};
  if (diag != nullptr) *diag = diagnostics;
  return true;
}
} // namespace xar::ck3_12002
#endif
