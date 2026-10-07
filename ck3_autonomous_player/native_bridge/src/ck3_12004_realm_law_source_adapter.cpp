#include "xar_bridge/ck3_12004_realm_law_source_adapter.hpp"
#include "xar_bridge/ck3_12004_realm_law_enact_command_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12004 {
namespace {
using Source = RealmLawCrownSource12004;
namespace old_law = ck3_12002::private_law;
using namespace bridge;
using Presence = RealmLawGovernancePresenceV1;
using TermsStatus = old_law::RealmLawFinalTerms12002Status;
constexpr std::array<std::string_view, 10> kCurrencies{
    "gold", "prestige", "piety", "renown", "influence", "herd",
    "treasury", "treasury_or_gold", "merit", "barter_goods"};

template <typename T>
bool Read(Source &source, std::uintptr_t address, T &out) noexcept {
  return address != 0 && source.read_memory != nullptr &&
      source.read_memory(source.callback_context, address, &out, sizeof(out));
}

std::uintptr_t Resolve(Source &source, std::int32_t id,
                       std::uintptr_t storage_rva,
                       std::uintptr_t fallback_rva,
                       std::size_t identity_offset) noexcept {
  if (id == -1) return 0;
  std::uintptr_t storage = 0, fallback = 0, slots = 0, object = 0;
  std::int32_t capacity = 0, observed_id = -1;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (!Read(source, source.module_base + storage_rva, storage) ||
      !Read(source, source.module_base + fallback_rva, fallback) ||
      !Read(source, storage + 0x20, slots) ||
      !Read(source, storage + 0x2C, capacity) || capacity <= 0 ||
      index >= static_cast<std::uint32_t>(capacity) ||
      !Read(source, slots + static_cast<std::uintptr_t>(index) * 0x10 + 8, object) ||
      object == 0 || object == fallback ||
      !Read(source, object + identity_offset, observed_id) || observed_id != id)
    return 0;
  return object;
}

bool Proof(void *opaque, RealmLawNativeRuntimeProofV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  if (source.read_runtime_proof == nullptr ||
      !source.read_runtime_proof(source.callback_context, out)) return false;
  source.connection_generation = out.connection_generation;
  return true;
}

bool Frame(void *opaque, RealmLawGovernanceFrameV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  return source.capture_frame != nullptr &&
      source.capture_frame(source.callback_context, out);
}

bool Player(void *opaque, std::int32_t id,
            RealmLawGovernanceSourcePlayerLeaseV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  out = {};
  const auto actor = Resolve(source, id, kCharacterStorageSlotRva,
                            kCrownCharacterFallbackSlotRva12004, 0x18);
  if (actor == 0) { source.failure = "player_identity_unavailable"; return false; }
  out.identity_round_trip = true;
  out.native_address = actor;
  out.character_id = id;
  return true;
}

struct CandidateObserver {
  Source *source = nullptr;
  std::uintptr_t actor = 0;
  std::int32_t actor_id = -1;
};

bool ObserveCandidate(void *opaque, std::size_t group, std::size_t index,
                      std::uintptr_t law,
                      const old_law::RealmLawCandidateCollectionRow11906 &)
    noexcept {
  auto &observer = *static_cast<CandidateObserver *>(opaque);
  auto &source = *observer.source;
  if (group >= source.readback.final.size() ||
      index >= source.readback.final[group].size()) return false;
  auto &result = source.readback.final[group][index];
  result = private_law::ReadRealmLawFinalTerms12004(
      {reinterpret_cast<const void *>(law),
       reinterpret_cast<const void *>(observer.actor),
       static_cast<std::uint32_t>(observer.actor_id)}, source.final_operations);
  if (!result.terms.cost_available || result.terms.status == TermsStatus::unavailable)
    return false;
  if (group == 0) {
    source.crown_components[index] = old_law::ReadRealmLawComponents12002(
        reinterpret_cast<const void *>(law),
        reinterpret_cast<const void *>(observer.actor), source.component_operations);
    std::array<std::byte, 0xC40> copied_definition{};
    if (!source.crown_components[index].complete ||
        !Read(source, law, copied_definition) ||
        !old_law::ReadRealmLawSuccessionShape12002(
            copied_definition.data(), source.crown_succession_shapes[index])) return false;
    source.crown_law_addresses[index] = law;
    std::uintptr_t law_group = 0;
    if (!Read(source, law + private_law::kLawOwningGroupOffset12004, law_group) ||
        law_group == 0 || (source.crown_group_address != 0 &&
                           source.crown_group_address != law_group)) return false;
    source.crown_group_address = law_group;
  }
  return true;
}

bool Refresh(Source &source,
             const RealmLawGovernanceSourcePlayerLeaseV1 &player) noexcept {
  RealmLawGovernanceFrameV1 frame{};
  if (source.admitted_executable_sha256 !=
          kExecutableSha256 ||
      !Frame(&source, frame) || !frame.paused || !frame.map_ready ||
      frame.played_character_id != player.character_id ||
      !frame.played_character_alive || !frame.played_character_identity_round_trip)
    return false;
  source.readback = {};
  source.crown_law_addresses = {};
  source.crown_group_address = 0;
  source.readback.frame = {frame.public_revision, frame.date_raw, player.character_id};
  old_law::RealmLawActiveCollectionAccess access{
      source.admitted_executable_sha256, player.native_address,
      source.callback_context, source.read_memory};
  CandidateObserver observer{&source, player.native_address, player.character_id};
  source.readback.available = private_law::ReadRealmLawCandidateCollectionWithObserver12004(
      access, source.module_base, &observer, ObserveCandidate, source.readback.collection);
  if (!source.readback.available) source.failure = "law_native_readback_unavailable";
  return source.readback.available;
}

bool Container(void *opaque, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
               RealmLawGovernanceSourceContainerLeaseV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  std::uintptr_t law_context = 0;
  out = {};
  if (!Read(source, player.native_address + private_law::kCharacterLawContextOffset12004,
            law_context) || law_context == 0 || !Refresh(source, player)) return false;
  out.identity_round_trip = true;
  out.native_address = law_context;
  out.identity = law_context;
  out.generation = source.connection_generation;
  out.owner_character_id = player.character_id;
  out.group_count = 1;
  return true;
}

bool Group(void *opaque, const RealmLawGovernanceSourcePlayerLeaseV1 &,
           const RealmLawGovernanceSourceContainerLeaseV1 &,
           std::size_t index, RealmLawGovernanceSourceGroupLeaseV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  out = {};
  if (index != 0 || !source.readback.available || source.crown_group_address == 0)
    return false;
  const auto &group = source.readback.collection.groups[0];
  if (!group.active_found) return false;
  out.engine_final_permission_only = true;
  out.identity_round_trip = true;
  out.native_address = source.crown_group_address;
  out.identity = source.crown_group_address;
  out.generation = source.connection_generation;
  if (!AssignRealmLawGovernanceKeyV1(
          {group.key.bytes.data(), group.key.size}, out.group_key) ||
      !AssignRealmLawGovernanceKeyV1(
          {group.active_law_key.bytes.data(), group.active_law_key.size},
          out.active_law_key)) return false;
  out.candidate_count = group.candidate_count;
  return true;
}

bool Candidate(void *opaque, const RealmLawGovernanceSourcePlayerLeaseV1 &,
               const RealmLawGovernanceSourceContainerLeaseV1 &,
               const RealmLawGovernanceSourceGroupLeaseV1 &, std::size_t index,
               RealmLawGovernanceCandidateV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  out = {};
  const auto &group = source.readback.collection.groups[0];
  if (index >= group.candidate_count) return false;
  const auto &row = group.candidates[index];
  const auto &terms = source.readback.final[0][index];
  if (!AssignRealmLawGovernanceKeyV1({row.key.bytes.data(), row.key.size}, out.law_key))
    return false;
  out.engine_final_only = true;
  out.can_have = source.crown_components[index].can_have;
  out.can_pass = source.crown_components[index].can_pass;
  out.is_active = row.active;
  out.evaluation_complete = true;
  out.can_enact = terms.terms.status == TermsStatus::can_enact;
  if (out.can_enact) out.blocked_reason.presence = Presence::absent;
  else {
    const auto reason = terms.native_reason_available && !terms.native_reason.empty()
        ? std::string_view(terms.native_reason)
        : out.is_active ? std::string_view("already_active")
                        : std::string_view("native_final_denied");
    if (!AssignRealmLawGovernanceReasonV1(reason, out.blocked_reason)) return false;
  }
  out.costs_complete = terms.terms.cost_available;
  for (std::size_t slot = 0; slot < kCurrencies.size(); ++slot) {
    const auto amount = terms.terms.cost_raw[slot];
    if (amount == 0) continue;  // Observed native zero, never a missing balance.
    if (amount < 0 || out.cost_count >= out.costs.size()) {
      source.failure = "crown_cost_vector_not_representable"; return false;
    }
    auto &cost = out.costs[out.cost_count++];
    if (!AssignRealmLawGovernanceKeyV1(kCurrencies[slot], cost.currency_key)) return false;
    cost.amount_raw = amount;
  }
  out.succession = source.crown_succession_shapes[index];
  return RealmLawGovernanceKeyViewV1(out.law_key).starts_with("crown_authority_");
}

bool InvokePrimary(Source &source, std::uintptr_t actor,
                   std::uintptr_t &out) noexcept {
  if (source.primary_title == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    out = reinterpret_cast<std::uintptr_t>(
        source.primary_title(reinterpret_cast<void *>(actor)));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool Successors(Source &source, std::uintptr_t title,
                RealmLawGovernanceHeldTitleSuccessionV1 &out) noexcept {
  std::uintptr_t data = 0;
  std::int32_t capacity = -1, count = -1;
  if (!Read(source, title + kCrownSuccessorDataOffset12004, data) ||
      !Read(source, title + kCrownSuccessorCapacityOffset12004, capacity) ||
      !Read(source, title + kCrownSuccessorCountOffset12004, count) ||
      count < 0 || capacity < count ||
      count > static_cast<std::int32_t>(out.successor_character_ids.size()))
    return false;
  out.successor_count = static_cast<std::uint32_t>(count);
  for (std::int32_t i = 0; i < count; ++i) {
    auto &id = out.successor_character_ids[static_cast<std::size_t>(i)];
    if (!Read(source, data + static_cast<std::uintptr_t>(i) * 4, id) ||
        Resolve(source, id, kCharacterStorageSlotRva,
                kCrownCharacterFallbackSlotRva12004, 0x18) == 0) return false;
  }
  return true;
}

bool Titles(void *opaque, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
            RealmLawGovernanceTitleBaselineV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  out = {};
  std::uintptr_t land = 0, data = 0, primary = 0;
  std::int32_t count = -1, capacity = -1, primary_id = -1;
  if (!Read(source, player.native_address + kCrownCharacterLandOffset12004, land) ||
      !Read(source, land + kCrownHeldTitleDataOffset12004, data) ||
      !Read(source, land + kCrownHeldTitleCapacityOffset12004, capacity) ||
      !Read(source, land + kCrownHeldTitleCountOffset12004, count) ||
      count < 0 || capacity < count ||
      count > static_cast<std::int32_t>(out.held_titles.size()) ||
      !InvokePrimary(source, player.native_address, primary)) return false;
  std::uintptr_t title_fallback = 0;
  if (!Read(source, source.module_base + kCrownTitleFallbackSlotRva12004,
            title_fallback)) return false;
  if (count == 0 && (primary == 0 || primary == title_fallback)) {
    out.primary_title_presence = Presence::absent;
    out.primary_title_id = -1;
    return true;
  }
  if (!Read(source, primary + kCrownTitleIdentityOffset12004, primary_id)) return false;
  out.primary_title_presence = Presence::present;
  out.primary_title_id = primary_id;
  out.held_title_count = static_cast<std::uint32_t>(count);
  for (std::int32_t i = 0; i < count; ++i) {
    auto &title = out.held_titles[static_cast<std::size_t>(i)];
    if (!Read(source, data + static_cast<std::uintptr_t>(i) * 4, title.title_id)) return false;
    const auto address = Resolve(source, title.title_id,
        kCrownTitleStorageSlotRva12004, kCrownTitleFallbackSlotRva12004,
        kCrownTitleIdentityOffset12004);
    std::int32_t holder = -1;
    if (address == 0 || !Read(source, address + kCrownTitleHolderOffset12004, holder) ||
        holder != player.character_id || !Successors(source, address, title)) return false;
    title.primary = title.title_id == primary_id;
    if (title.primary) {
      out.primary_title_successor_count = title.successor_count;
      out.primary_title_successor_character_ids = title.successor_character_ids;
    }
  }
  return true;
}

bool Resources(void *opaque, const RealmLawGovernanceSnapshotV1 &snapshot,
               RealmLawNativeResourceSampleV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  out = {};
  RealmLawGovernanceSourcePlayerLeaseV1 player{};
  if (!Player(&source, snapshot.played_character_id, player)) return false;
  std::uintptr_t extension = 0;
  if (!Read(source, player.native_address + kCrownActorResourceExtensionOffset12004,
            extension)) return false;
  // Actual affordability switch table 0x310ED8C ordinals 0,1,2,4,8;
  // RESOURCE14 joins the named Influence/Merit branches to their field blocks.
  // Preserve legal null-extension zero and the existing unavailable currencies.
  for (std::size_t i = 0; i < kCrownResourceCurrencySlots12004.size(); ++i) {
    auto &balance = out.resources[out.resource_count++];
    if (!AssignRealmLawGovernanceKeyV1(
            kCurrencies[kCrownResourceCurrencySlots12004[i]], balance.currency_key))
      return false;
    if (extension != 0 && !Read(source,
            extension + kCrownResourceBalanceOffsets12004[i], balance.amount_raw))
      return false;
  }
  out.complete = true;
  out.public_revision = snapshot.public_revision;
  out.native_revision = snapshot.native_revision;
  out.proof_epoch = snapshot.proof_epoch;
  out.connection_generation = source.connection_generation;
  out.date_raw = snapshot.date_raw;
  out.player_character_id = snapshot.played_character_id;
  return true;
}

RealmLawNativeSubmitDispositionV1 Submit(
    void *opaque, const RealmLawEnactSubmissionV1 &submission) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  RealmLawNativeEnactTargetLeaseV1 first{}, second{};
  if (!ResolveRealmLawCrownTarget12004(&source, submission, first) ||
      !ResolveRealmLawCrownTarget12004(&source, submission, second) || first != second)
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  const auto result = private_law::SubmitAddLawCommand12004V1(source.command_access, submission, second);
  if (result.failure != old_law::AddLawCommandFailureV1::none)
    source.failure = old_law::AddLawCommandFailureNameV1(result.failure);
  return result.disposition;
}
} // namespace

ck3_12002::private_law::RealmLawComponentBindings12002
BindRealmLawComponentsImage12004(
    std::uintptr_t module, std::string_view executable_sha256) noexcept {
  ck3_12002::private_law::RealmLawComponentBindings12002 output{};
  if (module == 0 || executable_sha256 != kExecutableSha256) return output;
  output.enabled = true;
  output.construct_actor_scope = reinterpret_cast<decltype(output.construct_actor_scope)>(
      module + kCrownActorScopeRva12004);
  output.evaluate_trigger = reinterpret_cast<decltype(output.evaluate_trigger)>(
      module + kCrownCompiledTriggerRva12004);
  output.destroy_scope_tail = reinterpret_cast<decltype(output.destroy_scope_tail)>(
      module + kCrownScopeTailDestroyRva12004);
  output.destroy_scope_rows = reinterpret_cast<decltype(output.destroy_scope_rows)>(
      module + kCrownScopeRowsDestroyRva12004);
  return output;
}

RealmLawNativeBinderOperationsV1 MakeRealmLawCrownSourceOperations12004() noexcept {
  return {Proof, Frame, Player, Container, Group, Candidate, Titles, Resources, Submit};
}

bool ResolveRealmLawCrownTarget12004(
    void *opaque, const RealmLawEnactSubmissionV1 &submission,
    RealmLawNativeEnactTargetLeaseV1 &out) noexcept {
  auto &source = *static_cast<Source *>(opaque);
  out = {};
  if (RealmLawGovernanceKeyViewV1(submission.group_key) != "crown_authority") return false;
  RealmLawGovernanceSourcePlayerLeaseV1 player{};
  RealmLawGovernanceFrameV1 frame{};
  if (!Frame(&source, frame) || frame.public_revision != submission.public_revision ||
      frame.native_revision != submission.native_revision || frame.proof_epoch != submission.proof_epoch ||
      !Player(&source, submission.player_character_id, player) || !Refresh(source, player)) return false;
  const auto &group = source.readback.collection.groups[0];
  for (std::size_t i = 0; i < group.candidate_count; ++i) {
    const auto &row = group.candidates[i];
    const std::string_view key{row.key.bytes.data(), row.key.size};
    if (key != RealmLawGovernanceKeyViewV1(submission.requested_law_key)) continue;
    if (row.active || source.readback.final[0][i].terms.status != TermsStatus::can_enact) return false;
    out.actor_identity_round_trip = true;
    out.actor_address = player.native_address;
    out.actor_character_id = player.character_id;
    out.group_identity_round_trip = true;
    out.group_identity = source.crown_group_address;
    out.group_generation = source.connection_generation;
    out.group_key = submission.group_key;
    out.law_identity_round_trip = true;
    out.law_address = source.crown_law_addresses[i];
    out.law_identity = out.law_address;
    out.law_generation = source.connection_generation;
    out.law_key = submission.requested_law_key;
    out.connection_generation = source.connection_generation;
    out.proof_epoch = submission.proof_epoch;
    return true;
  }
  return false;
}

bool BindRealmLawCrownSource12004(
    Source &source, std::string_view signature_manifest_sha256,
    RealmLawNativeBinderStateV1 &state, bool offline_fixture) noexcept {
  if (source.admitted_executable_sha256 != kExecutableSha256 ||
      source.module_base == 0 || source.read_memory == nullptr ||
      source.read_runtime_proof == nullptr || source.capture_frame == nullptr) return false;
  if (source.primary_title == nullptr) source.primary_title =
      reinterpret_cast<ck3_12002::NativeCampaignRootCharacterResolverV1>(
          source.module_base + kCrownPrimaryTitleRva12004);
  if (!source.component_operations.enabled) source.component_operations =
      BindRealmLawComponentsImage12004(
          source.module_base, source.admitted_executable_sha256);
  RealmLawNativeBinderEnvironmentV1 environment{};
  environment.expected_executable_sha256 = source.admitted_executable_sha256;
  environment.binding_enabled = true;
  environment.offline_fixture = offline_fixture;
  environment.module_base = source.module_base;
  environment.admitted_executable_sha256 = source.admitted_executable_sha256;
  environment.expected_signature_manifest_sha256 = signature_manifest_sha256;
  environment.native_context = &source;
  environment.operations = MakeRealmLawCrownSourceOperations12004();
  return BindRealmLawNativeV1(environment, state);
}
} // namespace xar::ck3_12004
