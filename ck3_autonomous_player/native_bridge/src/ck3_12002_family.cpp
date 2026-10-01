#include "xar_bridge/ck3_12002_family.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_family_abi.hpp"

#include <algorithm>
#include <cstring>
#include <utility>

namespace xar::ck3_12002 {
namespace {
using Failure = ck3_11906::CurrentFirstHeirRelationshipFailureV1;
using Relationship = ck3_11906::MarriageHeirRelationshipV1;
using Partner = ck3_11906::CurrentFirstHeirPartnerRelationshipV1;

template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}
struct alignas(8) ContextStorage { std::array<std::byte, 0x338> bytes{}; };
struct alignas(8) CommandStorage { std::array<std::byte, 0x368> bytes{}; };
struct DestroyContext {
  const ContextBindings &bindings;
  void *context;
  ~DestroyContext() { bindings.destroy(context); }
};

bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.paused == b.clock.paused &&
      a.clock.speed == b.clock.speed && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id &&
      a.played_character_alive == b.played_character_alive;
}
bool Frame(const FamilyBindings &b, CoreSnapshotPrefix &out) noexcept {
  return b.enabled && ReadCoreSnapshot(b.context.core, out) && out.clock.paused &&
      out.map_ready && out.has_played_character && out.played_character_alive;
}
bool Alive(const FamilyBindings &b, std::int32_t id, void *&character) noexcept {
  character = ResolveCoreCharacter(b.context.core, id);
  return id > 0 && character != nullptr &&
      Load<void *>(character, kCharacterDeathDataOffset) == nullptr;
}
bool ReadRaw(const FamilyBindings &b, std::int32_t id, Relationship &out) noexcept {
  out = {};
  void *character = nullptr;
  if (!Alive(b, id, character)) return false;
  const auto *family = Load<const std::byte *>(character, kMarriageCharacterFamilyDataOffset);
  if (family == nullptr) return true;
  const auto betrothed = Load<std::int32_t>(family, 0x10);
  const auto primary = Load<std::int32_t>(family, 0x14);
  const auto *ids = Load<const std::int32_t *>(family, 0x20);
  const auto capacity = Load<std::int32_t>(family, 0x28);
  const auto count = Load<std::int32_t>(family, 0x2C);
  if (count < 0 || capacity < count || count > 1'000'000 ||
      (count > 0 && ids == nullptr)) return false;
  const auto scalar = [&](std::int32_t raw, std::int32_t &value) {
    if (raw == -1 || raw == 0) { value = -1; return true; }
    void *peer = nullptr;
    if (!Alive(b, raw, peer)) return false;
    value = raw;
    return true;
  };
  if (!scalar(betrothed, out.betrothed_character_id) ||
      !scalar(primary, out.primary_spouse_character_id)) return false;
  for (std::int32_t index = 0; index < count; ++index) {
    void *peer = nullptr;
    if (!Alive(b, ids[index], peer)) return false;
    out.spouse_character_ids.push_back(ids[index]);
  }
  return true;
}
Failure ReadRelation(const FamilyBindings &b, std::int32_t id,
                     Relationship &out, std::vector<Partner> &partners) noexcept {
  void *heir = nullptr;
  if (!Alive(b, id, heir)) return Failure::heir_unavailable;
  if (!ReadRaw(b, id, out)) return Failure::relationship_unavailable;
  std::vector<std::int32_t> ids = out.spouse_character_ids;
  for (const auto value : {out.primary_spouse_character_id, out.betrothed_character_id})
    if (value > 0 && std::find(ids.begin(), ids.end(), value) == ids.end())
      ids.push_back(value);
  for (const auto value : ids) {
    Partner peer{};
    peer.character_id = value;
    if (!ReadRaw(b, value, peer.relationship)) return Failure::partner_unavailable;
    partners.push_back(std::move(peer));
  }
  return ck3_11906::ValidateCurrentFirstHeirBilateralRelationshipV1(id, out, partners)
      ? Failure::none : Failure::bilateral_inconsistent;
}
void *Definition(const FamilyBindings &b) noexcept {
  const auto *slot = b.context.interaction_database_slot;
  return slot != nullptr && *slot != nullptr ?
      Load<void *>(*slot, kMarriageArrangeMarriageInteractionOffset) : nullptr;
}
bool ContextRoles(const void *context, std::int32_t actor, std::int32_t subject,
                  std::int32_t candidate, game::ArrangeMarriageValidationSample &roles) noexcept {
  roles.actor_character_id = Load<std::int32_t>(context, 0x2D8);
  roles.recipient_character_id = Load<std::int32_t>(context, 0x2DC);
  roles.secondary_actor_character_id = Load<std::int32_t>(context, 0x2E0);
  roles.secondary_recipient_character_id = Load<std::int32_t>(context, 0x2E4);
  roles.intermediary_character_id = Load<std::int32_t>(context, 0x2E8);
  return roles.actor_character_id == actor && roles.secondary_actor_character_id == subject &&
      roles.secondary_recipient_character_id == candidate;
}
bool Prepare(const FamilyBindings &b, std::int32_t actor, std::int32_t subject,
             std::int32_t candidate, void *output,
             game::ArrangeMarriageValidationSample &roles) noexcept {
  const auto &context = b.context;
  void *definition = Definition(b);
  if (definition == nullptr || context.redirect_roles == nullptr ||
      context.construct_all_roles == nullptr || context.refresh == nullptr ||
      context.finalize == nullptr || context.validate == nullptr || context.destroy == nullptr)
    return false;
  std::int32_t recipient = candidate, secondary_actor = subject,
      secondary_recipient = candidate, intermediary = -1, added_role = -1;
  const auto played_actor = actor;
  context.redirect_roles(definition, &actor, &recipient, &secondary_actor,
      &secondary_recipient, &intermediary, &added_role);
  // Keep the actual played matchmaker, independently observed heir and fixed
  // partner. Redirected recipient / intermediary follow the native permission tree.
  if (actor != played_actor || secondary_actor != subject || secondary_recipient != candidate)
    return false;
  roles.actor_character_id = actor;
  roles.recipient_character_id = recipient;
  roles.secondary_actor_character_id = secondary_actor;
  roles.secondary_recipient_character_id = secondary_recipient;
  roles.intermediary_character_id = intermediary;
  if (context.construct_all_roles(output, definition, actor, recipient,
      secondary_actor, secondary_recipient, intermediary, nullptr) != output) return false;
  context.refresh(output, true);
  context.finalize(output);
  return true;
}
bool ReadAdult(const FamilyBindings &b, void *subject, void *candidate,
               bridge::MarriageNativeOutcomeDetailsV1 &out) noexcept {
  if (b.adult_threshold_zero == nullptr || b.adult_threshold_one == nullptr) return false;
  const auto selector_a = Load<std::uint8_t>(subject, kFamilyCharacterAdultSelectorOffset);
  const auto selector_b = Load<std::uint8_t>(candidate, kFamilyCharacterAdultSelectorOffset);
  if (selector_a > 1 || selector_b > 1) return false;
  out.subject_adult_measure_raw = Load<std::int16_t>(subject, kFamilyCharacterAdultMeasureOffset);
  out.candidate_adult_measure_raw = Load<std::int16_t>(candidate, kFamilyCharacterAdultMeasureOffset);
  out.subject_adult_threshold_raw = selector_a == 0 ? *b.adult_threshold_zero : *b.adult_threshold_one;
  out.candidate_adult_threshold_raw = selector_b == 0 ? *b.adult_threshold_zero : *b.adult_threshold_one;
  out.subject_is_adult = out.subject_adult_measure_raw >= out.subject_adult_threshold_raw;
  out.candidate_is_adult = out.candidate_adult_measure_raw >= out.candidate_adult_threshold_raw;
  return true;
}
bool ReadOutcome(const FamilyBindings &b, void *subject, void *candidate,
                 const void *context, bridge::MarriageNativeOutcomeDetailsV1 &out,
                 bool &matrilineal) noexcept {
  if (!ReadAdult(b, subject, candidate, out) || b.read_boolean_option == nullptr ||
      b.grand_wedding_option == nullptr || b.matrilineal_option == nullptr) return false;
  out.grand_wedding_option_selected = b.read_boolean_option(context, *b.grand_wedding_option);
  out.predicted_outcome = out.subject_is_adult && out.candidate_is_adult &&
      !out.grand_wedding_option_selected ? bridge::MarriagePredictedOutcomeV1::marriage :
      bridge::MarriagePredictedOutcomeV1::betrothal;
  const auto selector_a = Load<std::uint8_t>(subject, kFamilyCharacterAdultSelectorOffset);
  const auto selector_b = Load<std::uint8_t>(candidate, kFamilyCharacterAdultSelectorOffset);
  matrilineal = selector_a == selector_b ? selector_a != 0 :
      b.read_boolean_option(context, *b.matrilineal_option);
  return true;
}
bool ContainsSpouse(const Relationship &relation, std::int32_t peer) noexcept {
  return relation.primary_spouse_character_id == peer ||
      std::find(relation.spouse_character_ids.begin(), relation.spouse_character_ids.end(), peer)
          != relation.spouse_character_ids.end();
}
} // namespace

FamilyBindings BindFamilyImage(std::uintptr_t base, std::string_view sha) noexcept {
  FamilyBindings b{};
  b.context = BindContextImage(base, sha);
  b.values = family_value::BindImage(base, sha);
  if (!b.context.enabled) return b;
  b.enabled = true;
  b.evaluate_answer = reinterpret_cast<FamilyEvaluateAnswer>(base + kFamilyEvaluateAnswerRva);
  b.read_boolean_option = reinterpret_cast<FamilyReadBooleanOption>(base + kFamilyReadBooleanOptionRva);
  b.set_boolean_option = reinterpret_cast<FamilySetBooleanOption>(base + 0x30788E0);
  b.adult_threshold_zero = reinterpret_cast<const std::int32_t *>(base + kFamilyAdultThresholdZeroRva);
  b.adult_threshold_one = reinterpret_cast<const std::int32_t *>(base + kFamilyAdultThresholdOneRva);
  b.grand_wedding_option = reinterpret_cast<const std::uint32_t *>(base + kFamilyGrandWeddingOptionRva);
  b.matrilineal_option = reinterpret_cast<const std::uint32_t *>(base + kFamilyMatrilinealOptionRva);
  return b;
}

bool PrepareFamilyPairContextV1(const FamilyBindings &b, std::int32_t actor,
    std::int32_t subject, std::int32_t candidate, FamilyPairContextV1 &out) noexcept {
  out = {};
  out.initialized = b.enabled && Prepare(b, actor, subject, candidate,
      out.bytes.data(), out.roles);
  if (!out.initialized) return false;
  if (!ContextRoles(out.bytes.data(), actor, subject, candidate, out.roles)) {
    DestroyFamilyPairContextV1(b, out); return false;
  }
  return true;
}
void DestroyFamilyPairContextV1(const FamilyBindings &b, FamilyPairContextV1 &context) noexcept {
  if (context.initialized && b.context.destroy != nullptr) b.context.destroy(context.bytes.data());
  context.initialized = false;
}
bool ReadFamilyPairTermsV1(const FamilyBindings &b, std::int32_t subject_id,
    std::int32_t candidate_id, const FamilyPairContextV1 &storage, FamilyPairTermsV1 &out) noexcept {
  out = {};
  void *subject = nullptr, *candidate = nullptr;
  CoreSnapshotPrefix frame{};
  if (!storage.initialized || !Frame(b, frame) || !Alive(b, subject_id, subject) ||
      !Alive(b, candidate_id, candidate) || b.context.validate == nullptr ||
      b.context.recipient_answer_score == nullptr || b.evaluate_answer == nullptr ||
      b.context.evaluate_cost == nullptr) return false;
  auto *context = const_cast<std::byte *>(storage.bytes.data());
  if (!ContextRoles(context, frame.played_character_id, subject_id, candidate_id, out.roles) ||
      ResolveCoreCharacter(b.context.core, out.roles.recipient_character_id) == nullptr ||
      (out.roles.intermediary_character_id != -1 &&
       ResolveCoreCharacter(b.context.core, out.roles.intermediary_character_id) == nullptr)) return false;
  out.complete_can_send = b.context.validate(context, nullptr);
  out.final_legality_sampled = true;
  if (b.context.recipient_answer_score(context, &out.recipient_ai_accept_raw) != &out.recipient_ai_accept_raw)
    return false;
  out.recipient_answer_status_raw = b.evaluate_answer(context, 1, 1, nullptr, nullptr);
  if (out.recipient_answer_status_raw > 2) return false;
  void *def = Definition(b);
  if (def == nullptr) return false;
  b.context.evaluate_cost(static_cast<const std::byte *>(def) + 0x40,
      context + 8, out.generic_cost_raw.data());
  return ReadOutcome(b, subject, candidate, context, out.adult,
      out.effective_matrilineal_if_accepted);
}

game::ReadArrangeMarriageFamilyCandidatesResultV1 ReadArrangeMarriageFamilyCandidatesV1(
    const FamilyBindings &b, std::int32_t subject_id,
    std::vector<game::ArrangeMarriageFamilyCandidateV1> &output,
    game::ArrangeMarriageQueryDiagnostics &diagnostics) noexcept {
  using Result = game::ReadArrangeMarriageFamilyCandidatesResultV1;
  output.clear(); diagnostics = {};
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(b, before)) return Result::unavailable;
  void *subject = nullptr;
  if (subject_id == before.played_character_id || !Alive(b, subject_id, subject)) return Result::subject_not_found;
  void *store = b.context.core.character_storage_slot == nullptr ? nullptr : *b.context.core.character_storage_slot;
  if (store == nullptr) return Result::unavailable;
  family_value::CharacterValue played_value{}, subject_value{};
  if (!family_value::ReadCharacterValue(b.values, before.played_character_id, played_value, false) ||
      !family_value::ReadCharacterValue(b.values, subject_id, subject_value, false)) return Result::unavailable;
  void *slots = Load<void *>(store, 0x20);
  const auto count = Load<std::int32_t>(store, 0x2C);
  diagnostics.storage_capacity = count;
  if (slots == nullptr || count <= 0 || count > 1'000'000) return Result::unavailable;
  std::vector<game::ArrangeMarriageFamilyCandidateV1> candidates;
  for (std::int32_t index = 0; index < count; ++index) {
    ++diagnostics.slots_scanned;
    void *candidate = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
    if (candidate == nullptr) { ++diagnostics.empty_slots; continue; }
    const auto candidate_id = Load<std::int32_t>(candidate, 0x18);
    if (candidate_id == before.played_character_id || candidate_id == subject_id) {
      ++diagnostics.self_candidates; continue;
    }
    if (Load<void *>(candidate, kCharacterDeathDataOffset) != nullptr) { ++diagnostics.dead_candidates; continue; }
    if ((static_cast<std::uint32_t>(candidate_id) & 0xFFFFFFU) != static_cast<std::uint32_t>(index) ||
        ResolveCoreCharacter(b.context.core, candidate_id) != candidate) {
      ++diagnostics.generation_mismatch_candidates; continue;
    }
    ++diagnostics.live_candidates;
    FamilyPairContextV1 context{};
    if (!PrepareFamilyPairContextV1(b, before.played_character_id, subject_id, candidate_id, context)) {
      ++diagnostics.context_construct_failures; return Result::unavailable;
    }
    ++diagnostics.contexts_constructed;
    if (!b.context.validate(context.bytes.data(), nullptr)) {
      DestroyFamilyPairContextV1(b, context);
      ++diagnostics.native_validate_false;
      continue;
    }
    FamilyPairTermsV1 terms{};
    const bool available = ReadFamilyPairTermsV1(b, subject_id, candidate_id, context, terms);
    DestroyFamilyPairContextV1(b, context);
    if (!available) return Result::unavailable;
    if (!terms.complete_can_send) { ++diagnostics.native_validate_false; continue; }
    ++diagnostics.native_validate_true;
    game::ArrangeMarriageFamilyCandidateV1 row{};
    row.played_character_id = before.played_character_id;
    row.subject_character_id = subject_id; row.candidate_character_id = candidate_id;
    row.recipient_matchmaker_character_id = terms.roles.recipient_character_id;
    row.intermediary_character_id = terms.roles.intermediary_character_id;
    row.recipient_ai_accept_raw = terms.recipient_ai_accept_raw;
    row.recipient_answer_status_raw = terms.recipient_answer_status_raw;
    row.complete_can_send = true; row.recipient_answer_allows_send = terms.recipient_answer_status_raw <= 1;
    row.heir_adult_measure_raw = terms.adult.subject_adult_measure_raw;
    row.candidate_adult_measure_raw = terms.adult.candidate_adult_measure_raw;
    family_value::CharacterValue candidate_value{};
    if (!family_value::ReadCharacterValue(b.values, candidate_id, candidate_value, false)) return Result::unavailable;
    row.played_dynasty_id = played_value.lineage.dynasty_id;
    row.heir_dynasty_id = subject_value.lineage.dynasty_id;
    row.candidate_dynasty_id = candidate_value.lineage.dynasty_id;
    void *actor = ResolveCoreCharacter(b.context.core, before.played_character_id);
    void *recipient = ResolveCoreCharacter(b.context.core, terms.roles.recipient_character_id);
    row.realm_backed_actor_recipient = actor != nullptr && recipient != nullptr &&
        Load<void *>(actor, 0x1C0) != nullptr && Load<void *>(recipient, 0x1C0) != nullptr;
    candidates.push_back(std::move(row));
  }
  if (!Frame(b, after) || !SameFrame(before, after)) return Result::unavailable;
  output = std::move(candidates);
  return Result::available;
}

bridge::MarriageProposalNativeSubmitResultV1 SubmitFamilyMarriageProposalV1(
    const FamilyBindings &b, const bridge::MarriageProposalSubmissionV1 &submission) noexcept {
  using Result = bridge::MarriageProposalNativeSubmitResultV1;
  CoreSnapshotPrefix before{}, checked{};
  const auto actor = static_cast<std::int32_t>(submission.roles.actor_character_id);
  const auto subject_id = static_cast<std::int32_t>(submission.subject_character_id);
  const auto candidate_id = static_cast<std::int32_t>(submission.candidate_character_id);
  if (!Frame(b, before) || actor != before.played_character_id || subject_id <= 0 || candidate_id <= 0 ||
      actor == subject_id || candidate_id == actor || candidate_id == subject_id ||
      !submission.rankless_observed_heir || submission.fulfill_existing_betrothal ||
      b.context.construct_send_command == nullptr || !b.context.commands.enabled) return Result::unavailable;
  bridge::MarriageProposalBilateralRelationshipV1 bilateral{};
  if (!ReadFamilyBilateralRelationshipV1(b, subject_id, candidate_id, bilateral) ||
      bilateral.subject_has_candidate_as_spouse || bilateral.candidate_has_subject_as_spouse ||
      bilateral.subject_has_candidate_as_betrothed || bilateral.candidate_has_subject_as_betrothed)
    return Result::rejected;
  FamilyPairContextV1 storage{};
  if (!PrepareFamilyPairContextV1(b, actor, subject_id, candidate_id, storage)) return Result::unavailable;
  DestroyContext destroy{b.context, storage.bytes.data()};
  void *context = storage.bytes.data();
  if (submission.request_matrilineal_option) {
    if (b.set_boolean_option == nullptr || b.matrilineal_option == nullptr) return Result::unavailable;
    b.set_boolean_option(context, *b.matrilineal_option, true);
    b.context.refresh(context, true); b.context.finalize(context);
  }
  FamilyPairTermsV1 terms{};
  const auto intermediary = submission.roles.intermediary_character_id == 0 ? -1 :
      static_cast<std::int32_t>(submission.roles.intermediary_character_id);
  if (!ReadFamilyPairTermsV1(b, subject_id, candidate_id, storage, terms) || !terms.complete_can_send ||
      terms.recipient_answer_status_raw > 1 || terms.recipient_ai_accept_raw != submission.recipient_ai_accept_raw ||
      terms.recipient_answer_status_raw != submission.recipient_answer_status_raw ||
      terms.roles.recipient_character_id != static_cast<std::int32_t>(submission.roles.recipient_character_id) ||
      terms.roles.intermediary_character_id != intermediary ||
      (submission.predicted_outcome != bridge::MarriagePredictedOutcomeV1::unavailable &&
       terms.adult.predicted_outcome != submission.predicted_outcome) ||
      (submission.request_matrilineal_option && !b.read_boolean_option(context, *b.matrilineal_option)) ||
      (submission.require_matrilineal_option_off && b.read_boolean_option(context, *b.matrilineal_option)) ||
      !Frame(b, checked) || !SameFrame(before, checked)) return Result::rejected;
  CommandStorage command{};
  void *native_command = command.bytes.data();
  const bool constructed = b.context.construct_send_command(native_command, context) == native_command;
  const bool identity = constructed && Load<std::uintptr_t>(native_command, 0) == b.context.send_primary_vtable &&
      Load<std::uintptr_t>(native_command, 0x18) == b.context.send_secondary_vtable;
  const void *copy = static_cast<const std::byte *>(native_command) + 0x20;
  game::ArrangeMarriageValidationSample roles{};
  bool copied_lineality = false;
  bridge::MarriageNativeOutcomeDetailsV1 copied_outcome{};
  void *subject = ResolveCoreCharacter(b.context.core, subject_id);
  void *candidate = ResolveCoreCharacter(b.context.core, candidate_id);
  const bool valid = identity && ContextRoles(copy, actor, subject_id, candidate_id, roles) &&
      roles.recipient_character_id == terms.roles.recipient_character_id && roles.intermediary_character_id == intermediary &&
      ReadOutcome(b, subject, candidate, copy, copied_outcome, copied_lineality) &&
      copied_outcome == terms.adult && copied_lineality == terms.effective_matrilineal_if_accepted &&
      b.read_boolean_option(copy, *b.matrilineal_option) == b.read_boolean_option(context, *b.matrilineal_option);
  const auto queued = valid ? SubmitCommandCopy(b.context.commands, native_command, 0x0E) : CommandSubmitResult::unavailable;
  if (constructed || Load<void *>(native_command, 0x20) != nullptr)
    b.context.destroy(static_cast<std::byte *>(native_command) + 0x20);
  return queued == CommandSubmitResult::submitted ? Result::submitted :
      queued == CommandSubmitResult::rejected ? Result::rejected : Result::unavailable;
}

ck3_11906::MarriageCandidateAlliancePrivateReadV1 ReadMarriageCandidateAlliancePrivateV1(
    const FamilyBindings &b, const game::ArrangeMarriageFamilyCandidateV1 &observed,
    const FamilyProjectionBindings &projection, bool request_matrilineal, bool read_fertility) noexcept {
  using RichFailure = ck3_11906::MarriageCandidateAlliancePrivateFailureV1;
  ck3_11906::MarriageCandidateAlliancePrivateReadV1 out{};
  out.requested_matrilineal_option = request_matrilineal;
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(b, before) || before.played_character_id != observed.played_character_id ||
      observed.subject_character_id == before.played_character_id ||
      observed.candidate_character_id == observed.subject_character_id ||
      observed.candidate_character_id == before.played_character_id) return out;
  family_value::CharacterValue played{}, subject{}, candidate{};
  if (!family_value::ReadCharacterValue(b.values, observed.played_character_id, played, false) ||
      !family_value::ReadCharacterValue(b.values, observed.subject_character_id, subject, read_fertility) ||
      !family_value::ReadCharacterValue(b.values, observed.candidate_character_id, candidate, read_fertility)) {
    out.failure = RichFailure::lineage_unavailable; return out;
  }
  if (!ReadRaw(b, observed.subject_character_id, out.heir_relationship) ||
      !ReadRaw(b, observed.candidate_character_id, out.candidate_relationship)) {
    out.failure = RichFailure::heir_relationship_unavailable; return out;
  }
  out.played_lineage = {played.lineage.house_id, played.lineage.dynasty_id};
  out.heir_lineage = {subject.lineage.house_id, subject.lineage.dynasty_id};
  out.candidate_lineage = {candidate.lineage.house_id, candidate.lineage.dynasty_id};
  out.heir_sex_selector_raw = subject.sex_selector_raw;
  out.candidate_sex_selector_raw = candidate.sex_selector_raw;
  const auto fertility = [](const family_value::FertilityRead &v) {
    return bridge::MarriageCharacterFertilityReadV1{v.available, v.extension_present,
        v.native_gate_evaluated, v.native_gate_allows, v.effective_raw};
  };
  out.heir_fertility = fertility(subject.fertility);
  out.candidate_fertility = fertility(candidate.fertility);
  FamilyPairContextV1 context{};
  if (!PrepareFamilyPairContextV1(b, observed.played_character_id,
      observed.subject_character_id, observed.candidate_character_id, context)) return out;
  DestroyContext destroy{b.context, context.bytes.data()};
  if (context.roles.recipient_character_id != observed.recipient_matchmaker_character_id ||
      context.roles.intermediary_character_id != observed.intermediary_character_id) {
    out.failure = RichFailure::role_changed; return out;
  }
  if (request_matrilineal) {
    out.selected_option_readback = SelectFamilyMatrilinealOptionV1(projection, context.bytes.data());
    if (!out.selected_option_readback) { out.failure = RichFailure::selected_option_unavailable; return out; }
    b.context.refresh(context.bytes.data(), true); b.context.finalize(context.bytes.data());
  }
  FamilyPairTermsV1 terms{};
  if (!ReadFamilyPairTermsV1(b, observed.subject_character_id, observed.candidate_character_id, context, terms))
    return out;
  out.final_legality_sampled = terms.final_legality_sampled;
  out.complete_can_send = terms.complete_can_send;
  out.recipient_acceptance_ready = true;
  out.recipient_ai_accept_raw = terms.recipient_ai_accept_raw;
  out.recipient_answer_status_raw = terms.recipient_answer_status_raw;
  out.generic_cost_raw = terms.generic_cost_raw;
  if (!terms.complete_can_send || terms.recipient_answer_status_raw > 1 ||
      (request_matrilineal ? terms.recipient_ai_accept_raw <= 0 :
       terms.recipient_ai_accept_raw != observed.recipient_ai_accept_raw ||
       terms.recipient_answer_status_raw != observed.recipient_answer_status_raw)) {
    out.failure = RichFailure::final_legality_changed; return out;
  }
  out.predicted_outcome = terms.adult.predicted_outcome;
  out.heir_is_adult = terms.adult.subject_is_adult;
  out.candidate_is_adult = terms.adult.candidate_is_adult;
  out.heir_adult_measure_raw = terms.adult.subject_adult_measure_raw;
  out.candidate_adult_measure_raw = terms.adult.candidate_adult_measure_raw;
  out.heir_adult_threshold_raw = terms.adult.subject_adult_threshold_raw;
  out.candidate_adult_threshold_raw = terms.adult.candidate_adult_threshold_raw;
  out.grand_wedding_option_selected = terms.adult.grand_wedding_option_selected;
  out.effective_matrilineal_if_accepted = terms.effective_matrilineal_if_accepted;
  out.projection_failure = ReadFamilyAllianceProjectionV1(projection, context.bytes.data(),
      static_cast<std::uint32_t>(observed.played_character_id),
      static_cast<std::uint32_t>(observed.recipient_matchmaker_character_id),
      static_cast<std::uint32_t>(observed.subject_character_id),
      static_cast<std::uint32_t>(observed.candidate_character_id), out.projection);
  if (out.projection_failure != bridge::MarriageCandidateAllianceProjectionFailureV1::none) {
    out.failure = RichFailure::projection_unavailable; return out;
  }
  family_value::CharacterValue played_after{}, subject_after{}, candidate_after{};
  Relationship subject_relation{}, candidate_relation{};
  if (!Frame(b, after) || !SameFrame(before, after) ||
      !family_value::ReadCharacterValue(b.values, observed.played_character_id, played_after, false) ||
      !family_value::ReadCharacterValue(b.values, observed.subject_character_id, subject_after, read_fertility) ||
      !family_value::ReadCharacterValue(b.values, observed.candidate_character_id, candidate_after, read_fertility) ||
      played_after != played || subject_after != subject || candidate_after != candidate ||
      !ReadRaw(b, observed.subject_character_id, subject_relation) || subject_relation != out.heir_relationship ||
      !ReadRaw(b, observed.candidate_character_id, candidate_relation) || candidate_relation != out.candidate_relationship) {
    out.failure = RichFailure::frame_changed; out.projection = {}; return out;
  }
  out.failure = RichFailure::none;
  return out;
}

CurrentFirstHeirRelationshipReadV1 ReadCurrentFirstHeirRelationshipV1(
    const FamilyBindings &b, std::int32_t heir) noexcept {
  CurrentFirstHeirRelationshipReadV1 out{};
  out.heir_character_id = heir;
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(b, before)) { out.failure = Failure::frame_changed; return out; }
  Relationship first{}, second{};
  std::vector<Partner> first_peers, second_peers;
  out.failure = ReadRelation(b, heir, first, first_peers);
  if (out.failure != Failure::none) return out;
  out.failure = ReadRelation(b, heir, second, second_peers);
  if (out.failure != Failure::none) return out;
  if (!Frame(b, after) || !SameFrame(before, after) || first != second || first_peers != second_peers) {
    out.failure = Failure::frame_changed; return out;
  }
  out.relationship = std::move(second);
  return out;
}

CurrentFirstHeirBetrothalActionabilityReadV1 ReadCurrentFirstHeirBetrothalActionabilityV1(
    const FamilyBindings &b, const CurrentFirstHeirRelationshipReadV1 &relation) noexcept {
  CurrentFirstHeirBetrothalActionabilityReadV1 out{};
  CoreSnapshotPrefix before{}, after{};
  if (relation.failure != Failure::none || !Frame(b, before)) return out;
  out.actor_character_id = before.played_character_id;
  out.heir_character_id = relation.heir_character_id;
  out.partner_character_id = relation.relationship.betrothed_character_id;
  if (out.partner_character_id <= 0) { out.unavailable_reason = "current_heir_has_no_betrothal"; return out; }
  out.has_betrothal = true;
  void *subject = nullptr, *candidate = nullptr;
  if (!Alive(b, out.heir_character_id, subject) || !Alive(b, out.partner_character_id, candidate)) {
    out.unavailable_reason = "current_betrothal_identity_unavailable"; return out;
  }
  out.adult_readback_available = ReadAdult(b, subject, candidate, out.adult);
  ContextStorage storage{};
  game::ArrangeMarriageValidationSample roles{};
  if (!Prepare(b, before.played_character_id, out.heir_character_id, out.partner_character_id, storage.bytes.data(), roles)) {
    out.unavailable_reason = "current_betrothal_context_unavailable"; return out;
  }
  void *context = storage.bytes.data();
  DestroyContext destroy{b.context, context};
  if (!ContextRoles(context, before.played_character_id, out.heir_character_id, out.partner_character_id, roles) ||
      ResolveCoreCharacter(b.context.core, roles.recipient_character_id) == nullptr ||
      (roles.intermediary_character_id != -1 && ResolveCoreCharacter(b.context.core, roles.intermediary_character_id) == nullptr)) {
    out.unavailable_reason = "current_betrothal_final_roles_changed"; return out;
  }
  out.recipient_character_id = roles.recipient_character_id;
  out.intermediary_character_id = roles.intermediary_character_id;
  out.complete_can_send = b.context.validate(context, nullptr);
  out.final_legality_sampled = true;
  const bool score_ready = b.context.recipient_answer_score != nullptr &&
      b.context.recipient_answer_score(context, &out.recipient_ai_accept_raw) == &out.recipient_ai_accept_raw;
  out.recipient_answer_status_raw = score_ready && b.evaluate_answer != nullptr ?
      b.evaluate_answer(context, 1, 1, nullptr, nullptr) : 3;
  out.recipient_acceptance_ready = score_ready && out.recipient_answer_status_raw <= 2;
  if (b.context.evaluate_cost != nullptr) {
    b.context.evaluate_cost(static_cast<const std::byte *>(Definition(b)) + 0x40,
        static_cast<const std::byte *>(context) + 8, out.generic_cost_raw.data());
    out.generic_costs_available = true;
  }
  bridge::MarriageNativeOutcomeDetailsV1 finalized{};
  out.outcome_available = ReadOutcome(b, subject, candidate, context, finalized, out.effective_matrilineal_if_accepted);
  if (out.outcome_available) {
    if (out.adult_readback_available && (finalized.subject_adult_measure_raw != out.adult.subject_adult_measure_raw ||
        finalized.candidate_adult_measure_raw != out.adult.candidate_adult_measure_raw ||
        finalized.subject_adult_threshold_raw != out.adult.subject_adult_threshold_raw ||
        finalized.candidate_adult_threshold_raw != out.adult.candidate_adult_threshold_raw)) {
      out = {}; out.unavailable_reason = "current_betrothal_adult_input_changed"; return out;
    }
    out.adult = finalized;
    out.adult_readback_available = true;
    out.lineality_available = true;
  }
  const auto checked = ReadCurrentFirstHeirRelationshipV1(b, relation.heir_character_id);
  if (!Frame(b, after) || !SameFrame(before, after) || checked.failure != Failure::none ||
      checked.relationship != relation.relationship || ResolveCoreCharacter(b.context.core, out.heir_character_id) != subject ||
      ResolveCoreCharacter(b.context.core, out.partner_character_id) != candidate) {
    out = {}; out.unavailable_reason = "current_betrothal_frame_changed"; return out;
  }
  out.unavailable_reason = !out.adult_readback_available ? "current_betrothal_adulthood_unavailable" :
      !out.recipient_acceptance_ready ? "current_betrothal_recipient_answer_unavailable" :
      !out.generic_costs_available ? "current_betrothal_cost_unavailable" :
      !out.outcome_available ? "current_betrothal_outcome_unavailable" : std::string_view{};
  return out;
}

bool ReadFamilyBilateralRelationshipV1(const FamilyBindings &b, std::int32_t subject,
    std::int32_t candidate, bridge::MarriageProposalBilateralRelationshipV1 &out) noexcept {
  out = {};
  CoreSnapshotPrefix before{}, after{};
  Relationship first{}, second{}, first_repeat{}, second_repeat{};
  if (subject == candidate || !Frame(b, before) || !ReadRaw(b, subject, first) ||
      !ReadRaw(b, candidate, second) || !ReadRaw(b, subject, first_repeat) ||
      !ReadRaw(b, candidate, second_repeat) || first != first_repeat || second != second_repeat ||
      !Frame(b, after) || !SameFrame(before, after)) return false;
  out.subject_character_id = static_cast<std::uint32_t>(subject);
  out.candidate_character_id = static_cast<std::uint32_t>(candidate);
  out.subject_identity_round_trip = out.candidate_identity_round_trip = true;
  out.subject_alive = out.candidate_alive = true;
  out.subject_has_candidate_as_spouse = ContainsSpouse(first, candidate);
  out.candidate_has_subject_as_spouse = ContainsSpouse(second, subject);
  out.subject_has_candidate_as_betrothed = first.betrothed_character_id == candidate;
  out.candidate_has_subject_as_betrothed = second.betrothed_character_id == subject;
  return true;
}

bool ReadFamilyAlliancePairV1(const FamilyBindings &b, const FamilyProjectionBindings &projection,
    std::int32_t first_id, std::int32_t second_id, bool &first_has_second, bool &second_has_first) noexcept {
  first_has_second = second_has_first = false;
  CoreSnapshotPrefix before{}, after{};
  void *first = nullptr, *second = nullptr;
  if (!projection.exact_build_admitted || projection.admitted_executable_sha256 != kExecutableSha256 ||
      projection.is_allied == nullptr || first_id == second_id || !Frame(b, before) ||
      !Alive(b, first_id, first) || !Alive(b, second_id, second)) return false;
  const bool forward = projection.is_allied(first, second);
  const bool reverse = projection.is_allied(second, first);
  if (projection.is_allied(first, second) != forward || projection.is_allied(second, first) != reverse ||
      !Frame(b, after) || !SameFrame(before, after) ||
      ResolveCoreCharacter(b.context.core, first_id) != first ||
      ResolveCoreCharacter(b.context.core, second_id) != second) return false;
  first_has_second = forward; second_has_first = reverse;
  return true;
}

bridge::MarriageProposalNativeSubmitResultV1 SubmitCurrentFirstHeirBetrothalFulfillmentV1(
    const FamilyBindings &b, std::int32_t actor, std::int32_t heir,
    const CurrentFirstHeirBetrothalActionabilityReadV1 &observed, std::uint64_t revision,
    bridge::ObservedHeirMarriagePendingV1 &pending) noexcept {
  using Result = bridge::MarriageProposalNativeSubmitResultV1;
  pending = {};
  CoreSnapshotPrefix before{}, checked{};
  if (!Frame(b, before) || actor != before.played_character_id || b.context.construct_send_command == nullptr ||
      !b.context.commands.enabled || b.context.send_primary_vtable == 0 || b.context.send_secondary_vtable == 0)
    return Result::unavailable;
  const auto relation = ReadCurrentFirstHeirRelationshipV1(b, heir);
  const auto fresh = ReadCurrentFirstHeirBetrothalActionabilityV1(b, relation);
  bridge::MarriageProposalBilateralRelationshipV1 bilateral{};
  bridge::MarriageProposalSubmissionV1 submission{};
  bridge::ObservedHeirMarriagePendingV1 proposed{};
  if (!ReadFamilyBilateralRelationshipV1(b, heir, observed.partner_character_id, bilateral) ||
      !bridge::PrepareCurrentFirstHeirBetrothalFulfillmentSubmissionV1(actor, heir, observed, fresh,
          bilateral, revision, submission, proposed)) return Result::rejected;
  ContextStorage storage{};
  game::ArrangeMarriageValidationSample roles{};
  if (!Prepare(b, actor, heir, observed.partner_character_id, storage.bytes.data(), roles)) return Result::unavailable;
  void *context = storage.bytes.data();
  DestroyContext destroy{b.context, context};
  void *subject = ResolveCoreCharacter(b.context.core, heir);
  void *candidate = ResolveCoreCharacter(b.context.core, observed.partner_character_id);
  bridge::MarriageNativeOutcomeDetailsV1 outcome{};
  bool lineality = false;
  if (!ContextRoles(context, actor, heir, observed.partner_character_id, roles) ||
      roles.recipient_character_id != observed.recipient_character_id ||
      roles.intermediary_character_id != observed.intermediary_character_id || !b.context.validate(context, nullptr) ||
      !ReadOutcome(b, subject, candidate, context, outcome, lineality) || outcome != observed.adult ||
      lineality != observed.effective_matrilineal_if_accepted || !Frame(b, checked) || !SameFrame(before, checked))
    return Result::rejected;
  CommandStorage command{};
  void *native_command = command.bytes.data();
  const bool constructed = b.context.construct_send_command(native_command, context) == native_command;
  const bool identity = constructed && Load<std::uintptr_t>(native_command, 0) == b.context.send_primary_vtable &&
      Load<std::uintptr_t>(native_command, 0x18) == b.context.send_secondary_vtable;
  bool copied_lineality = false;
  bridge::MarriageNativeOutcomeDetailsV1 copied_outcome{};
  game::ArrangeMarriageValidationSample copied_roles{};
  const void *copy = static_cast<const std::byte *>(native_command) + 0x20;
  const bool copied = identity && ContextRoles(copy, actor, heir, observed.partner_character_id, copied_roles) &&
      copied_roles.recipient_character_id == roles.recipient_character_id &&
      copied_roles.intermediary_character_id == roles.intermediary_character_id &&
      ReadOutcome(b, subject, candidate, copy, copied_outcome, copied_lineality) && copied_outcome == outcome &&
      copied_lineality == lineality;
  const auto queued = copied ? SubmitCommandCopy(b.context.commands, native_command, 0x0E) : CommandSubmitResult::unavailable;
  if (constructed || Load<void *>(native_command, 0x20) != nullptr)
    b.context.destroy(static_cast<std::byte *>(native_command) + 0x20);
  if (queued == CommandSubmitResult::submitted) { pending = proposed; return Result::submitted; }
  return queued == CommandSubmitResult::rejected ? Result::rejected : Result::unavailable;
}

} // namespace xar::ck3_12002
#endif
