#include "xar_bridge/ck3_12002_family_outbound.hpp"

#include <cstring>

namespace xar::ck3_12002 {
namespace {
template <typename T>
T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

template <typename Callback>
bool ReadBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}

bool ValidIdentity(const bridge::MarriageProposalResolutionIdentityV1 &value)
    noexcept {
  const auto valid_id = [](std::int32_t id) { return id != -1 && id != 0; };
  return value.interaction_definition != 0 &&
      valid_id(value.actor_character_id) && valid_id(value.recipient_character_id) &&
      valid_id(value.subject_character_id) && valid_id(value.candidate_character_id) &&
      value.subject_character_id != value.candidate_character_id &&
      (value.intermediary_character_id == -1 || valid_id(value.intermediary_character_id));
}
} // namespace

FamilyOutboundBindings BindFamilyOutboundImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  FamilyOutboundBindings result{};
  if (base == 0 || sha != kExecutableSha256) return result;
  result.enabled = true;
  result.module_base = base;
  result.pending_storage_slot = reinterpret_cast<void **>(
      base + kFamilyOutboundPendingStorageSlotRva);
  result.interaction_database_slot = reinterpret_cast<void **>(
      base + kFamilyOutboundInteractionDatabaseSlotRva);
  result.component_alive = reinterpret_cast<bridge::MarriagePendingComponentAliveV1>(
      base + kFamilyOutboundComponentAliveRva);
  result.pending_vtable = base + kFamilyOutboundPendingVtableRva;
  result.marriage_special_vtable = base + kFamilyOutboundMarriageSpecialVtableRva;
  return result;
}

bool InspectFamilyOutboundPendingSlotsV1(
    const FamilyOutboundBindings &bindings, const void *slots,
    std::int32_t capacity,
    const bridge::MarriageProposalResolutionIdentityV1 &identity,
    bridge::MarriageOutboundPendingSnapshotV1 &output) noexcept {
  output = {};
  if (!bindings.enabled || bindings.component_alive == nullptr ||
      bindings.pending_vtable == 0 || bindings.marriage_special_vtable == 0 ||
      !ValidIdentity(identity) || capacity < 0 || capacity > 1'000'000 ||
      (capacity != 0 && slots == nullptr))
    return false;
  bridge::MarriageOutboundPendingSnapshotV1 result{};
  const bool readable = ReadBoundary([&]() noexcept {
    std::uint32_t matches = 0;
    for (std::int32_t index = 0; index < capacity; ++index) {
      const auto pending = Load<const std::byte *>(
          slots, static_cast<std::size_t>(index) * 0x10 + 8);
      if (pending == nullptr || Load<std::uintptr_t>(pending, 0) != bindings.pending_vtable)
        continue;
      const auto full_id = Load<std::int32_t>(pending, kFamilyOutboundPendingIdentityOffset);
      if (full_id == -1 ||
          (static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU) !=
              static_cast<std::uint32_t>(index) ||
          !bindings.component_alive(pending + 8))
        continue;
      if (Load<std::uintptr_t>(pending, kFamilyOutboundPendingDefinitionOffset) !=
          identity.interaction_definition)
        continue;
      const bridge::MarriageProposalResolutionIdentityV1 observed{
          identity.interaction_definition,
          Load<std::int32_t>(pending, kFamilyOutboundPendingActorOffset),
          Load<std::int32_t>(pending, kFamilyOutboundPendingRecipientOffset),
          Load<std::int32_t>(pending, kFamilyOutboundPendingSubjectOffset),
          Load<std::int32_t>(pending, kFamilyOutboundPendingCandidateOffset),
          Load<std::int32_t>(pending, kFamilyOutboundPendingIntermediaryOffset)};
      if (observed != identity) continue;
      const auto special = Load<const void *>(pending, kFamilyOutboundPendingSpecialOffset);
      if (special == nullptr ||
          Load<std::uintptr_t>(special, 0) != bindings.marriage_special_vtable)
        return false;
      if (++matches > 1) {
        result = {};
        result.state = bridge::MarriageOutboundPendingStateV1::ambiguous;
        return true;
      }
      // Native routing is a dword, unlike the small reply-status bytes.
      const auto route = Load<std::int32_t>(pending, kFamilyOutboundPendingRouteOffset);
      result.state = route == 0 || route == 2
          ? bridge::MarriageOutboundPendingStateV1::active
          : bridge::MarriageOutboundPendingStateV1::ambiguous;
      result.pending_id = full_id;
      result.age_days = Load<std::int32_t>(pending, kFamilyOutboundPendingAgeOffset);
      result.ai_reply_cutoff_days = Load<std::int32_t>(pending, kFamilyOutboundPendingCutoffOffset);
    }
    return true;
  });
  if (readable) output = result;
  return readable;
}

bool ReadMarriageOutboundPendingSnapshotV1(
    const FamilyOutboundBindings &bindings, std::int32_t actor,
    std::int32_t recipient, std::int32_t subject, std::int32_t candidate,
    bridge::MarriageOutboundPendingSnapshotV1 &output) noexcept {
  output = {};
  if (!bindings.enabled || bindings.pending_storage_slot == nullptr ||
      bindings.interaction_database_slot == nullptr)
    return false;
  return ReadBoundary([&]() noexcept {
    const auto database = *bindings.interaction_database_slot;
    const auto storage = *bindings.pending_storage_slot;
    if (database == nullptr || storage == nullptr) return false;
    const bridge::MarriageProposalResolutionIdentityV1 identity{
        Load<std::uintptr_t>(database, kFamilyOutboundArrangeDefinitionOffset),
        actor, recipient, subject, candidate, -1};
    return InspectFamilyOutboundPendingSlotsV1(
        bindings, Load<const void *>(storage, 0x20),
        Load<std::int32_t>(storage, 0x2C), identity, output);
  });
}

} // namespace xar::ck3_12002
