#include "xar_bridge/ck3_12002_family_outbound.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>

using namespace xar::ck3_12002;
using xar::bridge::MarriageOutboundPendingSnapshotV1;
using xar::bridge::MarriageOutboundPendingStateV1;
using xar::bridge::MarriageProposalResolutionIdentityV1;

namespace {
template <typename T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  assert(offset + sizeof(value) <= N);
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

bool alive = true;
const void *last_component = nullptr;
bool ComponentAlive(const void *component) {
  last_component = component;
  std::int32_t id = -1;
  std::memcpy(&id, static_cast<const std::byte *>(component) + 8, sizeof(id));
  return alive && id != -1;
}

struct Fixture {
  static constexpr std::uintptr_t base = 0x140000000ULL;
  static constexpr std::uintptr_t definition = 0x141234560ULL;
  static constexpr std::int32_t pending_id = 0x01000001;
  MarriageProposalResolutionIdentityV1 identity{
      definition, 0x11000011, 0x12000012, 0x13000013, 0x14000014, -1};
  std::array<std::byte, 0x5C8> pending{}, second{};
  std::array<std::byte, 8> special{};
  std::array<std::byte, 0x40> storage{}, slots{};
  std::array<std::byte, 0xF38> database{};
  void *storage_pointer = storage.data();
  void *database_pointer = database.data();
  FamilyOutboundBindings bindings = BindFamilyOutboundImage(base, kExecutableSha256);

  Fixture() {
    bindings.component_alive = ComponentAlive;
    bindings.pending_storage_slot = &storage_pointer;
    bindings.interaction_database_slot = &database_pointer;
    Put(special, 0, bindings.marriage_special_vtable);
    Put(database, kFamilyOutboundArrangeDefinitionOffset, definition);
    Put(storage, 0x20, static_cast<void *>(slots.data()));
    Put(storage, 0x2C, std::int32_t{4});
    Put(slots, 0x18, static_cast<void *>(pending.data()));
    Put(pending, 0, bindings.pending_vtable);
    Put(pending, kFamilyOutboundPendingIdentityOffset, pending_id);
    Put(pending, kFamilyOutboundPendingDefinitionOffset, definition);
    Put(pending, kFamilyOutboundPendingActorOffset, identity.actor_character_id);
    Put(pending, kFamilyOutboundPendingRecipientOffset, identity.recipient_character_id);
    Put(pending, kFamilyOutboundPendingSubjectOffset, identity.subject_character_id);
    Put(pending, kFamilyOutboundPendingCandidateOffset, identity.candidate_character_id);
    Put(pending, kFamilyOutboundPendingIntermediaryOffset, identity.intermediary_character_id);
    Put(pending, kFamilyOutboundPendingSpecialOffset, static_cast<void *>(special.data()));
    Put(pending, kFamilyOutboundPendingAgeOffset, std::int32_t{7});
    Put(pending, kFamilyOutboundPendingCutoffOffset, std::int32_t{14});
    Put(pending, kFamilyOutboundPendingRouteOffset, std::int32_t{0});
  }

  bool Read(MarriageOutboundPendingSnapshotV1 &result) const {
    return ReadMarriageOutboundPendingSnapshotV1(
        bindings, identity.actor_character_id, identity.recipient_character_id,
        identity.subject_character_id, identity.candidate_character_id, result);
  }
};

void AssertEmpty(const MarriageOutboundPendingSnapshotV1 &result,
                 MarriageOutboundPendingStateV1 state = MarriageOutboundPendingStateV1::absent) {
  assert(result.state == state && result.pending_id == -1);
  assert(result.age_days == -1 && result.ai_reply_cutoff_days == -1);
}
} // namespace

int main() {
  Fixture f;
  MarriageOutboundPendingSnapshotV1 result{};
  assert(f.Read(result)); // No resolution journal is created or installed.
  assert(result.state == MarriageOutboundPendingStateV1::active);
  assert(result.pending_id == Fixture::pending_id && result.age_days == 7);
  assert(result.ai_reply_cutoff_days == 14 && last_component == f.pending.data() + 8);

  Put(f.pending, kFamilyOutboundPendingRouteOffset, std::int32_t{2});
  Put(f.pending, kFamilyOutboundPendingAgeOffset, std::int32_t{0});
  Put(f.pending, kFamilyOutboundPendingCutoffOffset, std::int32_t{0});
  assert(f.Read(result));
  assert(result.state == MarriageOutboundPendingStateV1::active);
  assert(result.age_days == 0 && result.ai_reply_cutoff_days == 0);
  Put(f.pending, kFamilyOutboundPendingRouteOffset, std::int32_t{256});
  assert(f.Read(result)); // Reading one byte would incorrectly classify this as active.
  assert(result.state == MarriageOutboundPendingStateV1::ambiguous);
  assert(result.pending_id == Fixture::pending_id);
  Put(f.pending, kFamilyOutboundPendingRouteOffset, std::int32_t{0});

  const std::array<std::size_t, 5> role_offsets{
      kFamilyOutboundPendingActorOffset, kFamilyOutboundPendingRecipientOffset,
      kFamilyOutboundPendingSubjectOffset, kFamilyOutboundPendingCandidateOffset,
      kFamilyOutboundPendingIntermediaryOffset};
  for (const auto offset : role_offsets) {
    const auto saved = f.pending;
    Put(f.pending, offset, std::int32_t{0x22000022});
    assert(f.Read(result));
    AssertEmpty(result);
    f.pending = saved;
  }
  Put(f.pending, kFamilyOutboundPendingDefinitionOffset, Fixture::definition + 8);
  assert(f.Read(result));
  AssertEmpty(result);
  Put(f.pending, kFamilyOutboundPendingDefinitionOffset, Fixture::definition);
  Put(f.pending, 0, f.bindings.pending_vtable + 8);
  assert(f.Read(result));
  AssertEmpty(result);
  Put(f.pending, 0, f.bindings.pending_vtable);
  Put(f.pending, kFamilyOutboundPendingIdentityOffset, std::int32_t{0x01000002});
  assert(f.Read(result));
  AssertEmpty(result);
  Put(f.pending, kFamilyOutboundPendingIdentityOffset, Fixture::pending_id);
  alive = false;
  assert(f.Read(result));
  AssertEmpty(result);
  alive = true;

  Put(f.special, 0, f.bindings.marriage_special_vtable + 8);
  assert(!f.Read(result));
  AssertEmpty(result);
  Put(f.special, 0, f.bindings.marriage_special_vtable);
  Put(f.pending, kFamilyOutboundPendingSpecialOffset, static_cast<void *>(nullptr));
  assert(!f.Read(result));
  AssertEmpty(result);
  Put(f.pending, kFamilyOutboundPendingSpecialOffset, static_cast<void *>(f.special.data()));

  f.second = f.pending;
  Put(f.second, kFamilyOutboundPendingIdentityOffset, std::int32_t{0x02000002});
  Put(f.slots, 0x28, static_cast<void *>(f.second.data()));
  assert(f.Read(result));
  AssertEmpty(result, MarriageOutboundPendingStateV1::ambiguous);
  Put(f.slots, 0x28, static_cast<void *>(nullptr));
  Put(f.slots, 0x18, static_cast<void *>(nullptr));
  assert(f.Read(result));
  AssertEmpty(result); // Native absence has no terminal/refusal classification.
  Put(f.slots, 8, static_cast<void *>(f.pending.data()));
  Put(f.pending, kFamilyOutboundPendingIdentityOffset, std::int32_t{0});
  assert(f.Read(result));
  assert(result.state == MarriageOutboundPendingStateV1::active && result.pending_id == 0);

  assert(InspectFamilyOutboundPendingSlotsV1(f.bindings, nullptr, 0, f.identity, result));
  AssertEmpty(result);
  assert(!InspectFamilyOutboundPendingSlotsV1(f.bindings, nullptr, 4, f.identity, result));
  AssertEmpty(result);
  f.database_pointer = nullptr;
  assert(!f.Read(result));
  AssertEmpty(result);
  f.database_pointer = f.database.data();
  f.storage_pointer = nullptr;
  assert(!f.Read(result));
  AssertEmpty(result);
  f.storage_pointer = f.storage.data();
  Put(f.database, kFamilyOutboundArrangeDefinitionOffset, std::uintptr_t{0});
  assert(!f.Read(result));
  AssertEmpty(result);

  const auto bound = BindFamilyOutboundImage(Fixture::base, kExecutableSha256);
  assert(bound.enabled);
  assert(reinterpret_cast<std::uintptr_t>(bound.pending_storage_slot) ==
         Fixture::base + kFamilyOutboundPendingStorageSlotRva);
  assert(reinterpret_cast<std::uintptr_t>(bound.component_alive) ==
         Fixture::base + kFamilyOutboundComponentAliveRva);
  assert(bound.pending_vtable == Fixture::base + kFamilyOutboundPendingVtableRva);
  assert(bound.marriage_special_vtable == Fixture::base + kFamilyOutboundMarriageSpecialVtableRva);
  assert(!BindFamilyOutboundImage(0, kExecutableSha256).enabled);
  assert(!BindFamilyOutboundImage(Fixture::base, "old-build").enabled);
  std::cout << "PASS family outbound: cold global snapshot, full native identities, all roles, dword route, duplicate ambiguity and lawful absence\n";
}
