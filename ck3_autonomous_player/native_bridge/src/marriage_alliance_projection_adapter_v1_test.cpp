#include "xar_bridge/marriage_alliance_projection_adapter_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace bridge = xar::bridge;

namespace {

constexpr std::uint32_t kPlayerId = 0x01000001U;
constexpr std::uint32_t kCandidateId = 0x02000002U;
constexpr std::uint32_t kOtherId = 0x03000003U;

template <typename Value, std::size_t Size>
void Write(std::array<std::byte, Size> &bytes, std::size_t offset,
           Value value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0x40> storage{};
  std::array<std::byte, 0x50> slots{};
  std::array<std::byte, 0x200> player{};
  std::array<std::byte, 0x200> candidate{};
  std::array<std::byte, 0x200> other{};
  std::array<std::byte, 0x70> marriage_info{};
  std::array<std::byte, bridge::kMarriageInfoAllianceRowStrideV1 * 2> rows{};
  std::uintptr_t storage_pointer = 0;
  std::uint32_t current_player_id = kPlayerId;

  Fixture() {
    storage_pointer = reinterpret_cast<std::uintptr_t>(storage.data());
    Write(storage, bridge::kMarriageCharacterStorageSlotsOffsetV1,
          reinterpret_cast<std::uintptr_t>(slots.data()));
    Write(storage, bridge::kMarriageCharacterStorageCapacityOffsetV1,
          std::int32_t{4});
    Write(slots, 1 * bridge::kMarriageCharacterStorageSlotStrideV1 +
                     bridge::kMarriageCharacterStorageSlotObjectOffsetV1,
          reinterpret_cast<std::uintptr_t>(player.data()));
    Write(slots, 2 * bridge::kMarriageCharacterStorageSlotStrideV1 +
                     bridge::kMarriageCharacterStorageSlotObjectOffsetV1,
          reinterpret_cast<std::uintptr_t>(candidate.data()));
    Write(slots, 3 * bridge::kMarriageCharacterStorageSlotStrideV1 +
                     bridge::kMarriageCharacterStorageSlotObjectOffsetV1,
          reinterpret_cast<std::uintptr_t>(other.data()));
    Write(player, bridge::kMarriageCharacterIdOffsetV1, kPlayerId);
    Write(candidate, bridge::kMarriageCharacterIdOffsetV1, kCandidateId);
    Write(other, bridge::kMarriageCharacterIdOffsetV1, kOtherId);
    Write(marriage_info, bridge::kMarriageInfoAllianceDataOffsetV1,
          reinterpret_cast<std::uintptr_t>(rows.data()));
    Write(marriage_info, bridge::kMarriageInfoAllianceCapacityOffsetV1,
          std::int32_t{2});
    Write(marriage_info, bridge::kMarriageInfoAllianceCountOffsetV1,
          std::int32_t{2});
    Write(marriage_info, bridge::kMarriageInfoAllianceAllocatorOffsetV1,
          std::uintptr_t{0x1234});
    Write(rows, 0, kOtherId);
    Write(rows, bridge::kMarriageInfoAllianceRowStrideV1, kCandidateId);
  }
};

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

void Initialize(Fixture &fixture,
                bridge::MarriageAllianceProjectionStateV1 &state) {
  auto &env = state.environment;
  env.module_base = 1;
  env.exact_build_admitted = true;
  env.admitted_executable_sha256 =
      bridge::kMarriageProposalNativeBinderExecutableSha256V1;
  env.offline_fixture = true;
  env.read_memory = &ReadMemory;
  env.character_storage_slot =
      reinterpret_cast<std::uintptr_t>(&fixture.storage_pointer);
  env.current_player_id_address =
      reinterpret_cast<std::uintptr_t>(&fixture.current_player_id);
}

void TestExactBindingAndProjectedPair() {
  const auto bound = bridge::BindMarriageAllianceProjectionEnvironmentV1(
      0x10000000U, true,
      bridge::kMarriageProposalNativeBinderExecutableSha256V1);
  assert(bound.character_storage_slot ==
         0x10000000U + bridge::kMarriageCharacterStorageSlotRvaV1);
  assert(bound.current_player_id_address ==
         0x10000000U + bridge::kMarriageInfoCurrentPlayerIdRvaV1);

  Fixture fixture{};
  bridge::MarriageAllianceProjectionStateV1 state{};
  Initialize(fixture, state);
  bool projected = false;
  assert(bridge::ReadMarriageAllianceProjectionPairExactV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.marriage_info.data()),
      kPlayerId, kCandidateId, projected));
  assert(projected);
  assert(bridge::ReadMarriageAllianceProjectionPairExactV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.marriage_info.data()),
      kCandidateId, kPlayerId, projected));
  assert(projected);
}

void TestScopeAndGenerationFailClosed() {
  Fixture fixture{};
  bridge::MarriageAllianceProjectionStateV1 state{};
  Initialize(fixture, state);
  bool projected = true;
  assert(!bridge::ReadMarriageAllianceProjectionPairExactV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.marriage_info.data()),
      kCandidateId, kOtherId, projected));
  assert(!projected);
  assert(bridge::ReadMarriageAllianceProjectionFailureV1(state) ==
         bridge::MarriageAllianceProjectionFailureV1::
             pair_not_current_player);

  Write(fixture.candidate, bridge::kMarriageCharacterIdOffsetV1,
        std::uint32_t{0x03000002U});
  assert(!bridge::ReadMarriageAllianceProjectionPairExactV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.marriage_info.data()),
      kPlayerId, kCandidateId, projected));
  assert(bridge::ReadMarriageAllianceProjectionFailureV1(state) ==
         bridge::MarriageAllianceProjectionFailureV1::
             row_identity_unavailable);
}

void TestHeaderAndShaFailClosed() {
  Fixture fixture{};
  bridge::MarriageAllianceProjectionStateV1 state{};
  Initialize(fixture, state);
  Write(fixture.marriage_info,
        bridge::kMarriageInfoAllianceCountOffsetV1, std::int32_t{3});
  bool projected = false;
  assert(!bridge::ReadMarriageAllianceProjectionPairExactV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.marriage_info.data()),
      kPlayerId, kCandidateId, projected));
  assert(bridge::ReadMarriageAllianceProjectionFailureV1(state) ==
         bridge::MarriageAllianceProjectionFailureV1::
             projection_header_invalid);

  Write(fixture.marriage_info,
        bridge::kMarriageInfoAllianceCountOffsetV1, std::int32_t{2});
  state.environment.admitted_executable_sha256 = "wrong";
  assert(!bridge::ReadMarriageAllianceProjectionPairExactV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.marriage_info.data()),
      kPlayerId, kCandidateId, projected));
  assert(bridge::ReadMarriageAllianceProjectionFailureV1(state) ==
         bridge::MarriageAllianceProjectionFailureV1::
             exact_build_not_admitted);
}

} // namespace

int main() {
  TestExactBindingAndProjectedPair();
  TestScopeAndGenerationFailClosed();
  TestHeaderAndShaFailClosed();
  std::cout << "marriage alliance projection adapter v1 tests passed\n";
  return 0;
}
