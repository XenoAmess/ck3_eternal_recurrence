#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <unordered_map>

using namespace xar::bridge;

namespace {

constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kStorage = 0x200000000;
constexpr std::uintptr_t kSlots = 0x210000000;
constexpr std::uintptr_t kPlayer = 0x220000000;
constexpr std::uintptr_t kPrisoner = 0x220001000;
constexpr std::uintptr_t kSecondPrisoner = 0x220002000;
constexpr std::uintptr_t kPrisonerExtension = 0x260000000;
constexpr std::uintptr_t kSecondPrisonerExtension = 0x260001000;
constexpr std::uintptr_t kPrisonerRelation = 0x270000000;
constexpr std::uintptr_t kSecondPrisonerRelation = 0x270001000;
constexpr std::uintptr_t kLand = 0x230000000;
constexpr std::uintptr_t kArray = 0x240000000;
constexpr std::uint32_t kPlayerId = 0x01000002;
constexpr std::uint32_t kPrisonerId = 0x02000003;
constexpr std::uint32_t kSecondPrisonerId = 0x03000004;

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> memory;
  PlayerPrisonerFrameV1 frame{};
  int frame_captures = 0;
  bool drift_frame = false;
  bool drift_array_on_second_read = false;
  int prisoner_array_reads = 0;

  template <typename T>
  void Put(std::uintptr_t address, T value) {
    const auto *bytes = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(value); ++index) {
      memory[address + index] = bytes[index];
    }
  }

  Fixture() {
    frame.public_revision = 11;
    frame.native_revision = 12;
    frame.proof_epoch = 13;
    frame.date_raw = 14;
    frame.paused = true;
    frame.map_ready = true;
    frame.played_character_id = static_cast<std::int32_t>(kPlayerId);
    frame.played_character_alive = true;
    frame.played_character_identity_round_trip = true;
    Put(kBase + kPlayerPrisonerCharacterStorageSlotRvaV1, kStorage);
    Put(kBase + kPlayerPrisonerCharacterFallbackSlotRvaV1,
        static_cast<std::uintptr_t>(0x250000000));
    Put(kStorage + 0x20, kSlots);
    Put(kStorage + 0x2C, std::int32_t{8});
    Put(kSlots + 2 * 0x10 + 0x08, kPlayer);
    Put(kSlots + 3 * 0x10 + 0x08, kPrisoner);
    Put(kSlots + 4 * 0x10 + 0x08, kSecondPrisoner);
    Put(kPlayer + 0x18, kPlayerId);
    Put(kPrisoner + 0x18, kPrisonerId);
    Put(kSecondPrisoner + 0x18, kSecondPrisonerId);
    Put(kPrisoner + 0x1A8, kPrisonerExtension);
    Put(kSecondPrisoner + 0x1A8, kSecondPrisonerExtension);
    Put(kPrisonerExtension + 0x288, kPrisonerRelation);
    Put(kSecondPrisonerExtension + 0x288, kSecondPrisonerRelation);
    Put(kPrisonerRelation, kPlayerId);
    Put(kSecondPrisonerRelation, kPlayerId);
    Put(kPlayer + 0x1B8, kLand);
    Put(kLand + 0xD8, kArray);
    Put(kLand + 0xD8 + 0x0C, std::int32_t{1});
    Put(kArray, kPrisonerId);
  }
};

bool Capture(void *context, PlayerPrisonerFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.frame;
  if (fixture.drift_frame && ++fixture.frame_captures == 2) {
    ++output.native_revision;
  }
  return true;
}

bool Read(void *context, std::uintptr_t address, void *output,
          std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (address == kArray && size == sizeof(kPrisonerId) &&
      fixture.drift_array_on_second_read &&
      ++fixture.prisoner_array_reads == 2) {
    const auto other = kSecondPrisonerId;
    std::memcpy(output, &other, sizeof(other));
    return true;
  }
  auto *bytes = static_cast<std::uint8_t *>(output);
  for (std::size_t index = 0; index < size; ++index) {
    const auto found = fixture.memory.find(address + index);
    if (found == fixture.memory.end()) return false;
    bytes[index] = found->second;
  }
  return true;
}

PlayerPrisonerCollectionAccessV1 Access(Fixture &fixture) {
  PlayerPrisonerCollectionAccessV1 access{};
  access.exact_build_admitted = true;
  access.admitted_executable_sha256 =
      kPlayerPrisonerManagementSnapshotV1ExecutableSha256;
  access.module_base = kBase;
  access.current_thread_id = 8;
  access.application_main_thread_id = 8;
  access.context = &fixture;
  access.capture_frame = Capture;
  access.read_memory = Read;
  return access;
}

bool Expect(bool condition, const char *case_name) {
  if (!condition) std::cerr << "FAIL " << case_name << '\n';
  return condition;
}

} // namespace

int main() {
  int passed = 0;
  {
    Fixture fixture;
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                            result) &&
                         result.available && result.collection_complete &&
                         result.total_count == 1 && result.returned_count == 1 &&
                         result.rows[0].source_ordinal == 0 &&
                         result.rows[0].full_character_id == kPrisonerId &&
                         result.rows[0].jailer_character_id == kPlayerId,
                     "full-id collection");
  }
  {
    Fixture fixture;
    fixture.Put(kLand + 0xD8 + 0x0C, std::int32_t{2});
    fixture.Put(kArray + sizeof(kPrisonerId), kSecondPrisonerId);
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                            result) &&
                         result.total_count == 2 &&
                         result.rows[0].full_character_id == kPrisonerId &&
                         result.rows[1].source_ordinal == 1 &&
                         result.rows[1].full_character_id ==
                             kSecondPrisonerId &&
                         result.rows[1].jailer_character_id == kPlayerId,
                     "complete source order");
  }
  {
    Fixture fixture;
    fixture.Put(kPrisonerRelation, kSecondPrisonerId);
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                             result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::
                                 custody_relation_invalid,
                     "reverse jailer relation");
  }
  {
    Fixture fixture;
    fixture.Put(kPlayer + 0x1B8, std::uintptr_t{0});
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                            result) &&
                         result.collection_complete && result.total_count == 0,
                     "empty fallback");
  }
  {
    Fixture fixture;
    fixture.Put(kPrisoner + 0x18, kPrisonerId + 0x01000000);
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                             result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::
                                 prisoner_identity_invalid,
                     "generation-bearing identity");
  }
  {
    Fixture fixture;
    fixture.Put(kLand + 0xD8 + 0x0C, std::int32_t{65});
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                             result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::
                                 collection_truncated,
                     "oversize is unavailable");
  }
  {
    Fixture fixture;
    fixture.frame.paused = false;
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                             result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::not_paused,
                     "paused frame required");
  }
  {
    Fixture fixture;
    auto access = Access(fixture);
    access.current_thread_id = 9;
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(access, result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::
                                 application_main_thread_required,
                     "main thread required");
  }
  {
    Fixture fixture;
    auto access = Access(fixture);
    access.admitted_executable_sha256 = "wrong";
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(access, result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::
                                 exact_build_mismatch,
                     "exact build required");
  }
  {
    Fixture fixture;
    fixture.drift_frame = true;
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                             result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::frame_drift,
                     "frame drift");
  }
  {
    Fixture fixture;
    fixture.drift_array_on_second_read = true;
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                             result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::sample_drift,
                     "second-sample drift rejected");
  }
  std::cout << "player_prisoner_collection_query_v1_private " << passed
            << "/11 GREEN\n";
  return passed == 11 ? 0 : 1;
}
