#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"
#include "xar_bridge/player_prisoner_collection_private_transport_v1.hpp"

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
constexpr std::uintptr_t kHouseStorage = 0x280000000;
constexpr std::uintptr_t kHouseSlots = 0x281000000;
constexpr std::uintptr_t kHouse = 0x282000000;
constexpr std::uintptr_t kDynastyStorage = 0x290000000;
constexpr std::uintptr_t kDynastySlots = 0x291000000;
constexpr std::uintptr_t kDynasty = 0x292000000;
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
    Put(kPlayer + 0x150, std::int32_t{-1});
    Put(kPrisoner + 0x150, std::int32_t{-1});
    Put(kSecondPrisoner + 0x150, std::int32_t{-1});
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

int child_relation_calls = 0;
bool IsChildOf(void *child, void *parent) {
  ++child_relation_calls;
  return child == reinterpret_cast<void *>(kPrisoner) &&
         parent == reinterpret_cast<void *>(kPlayer);
}

PlayerPrisonerCollectionAccessV1 Access(Fixture &fixture) {
  PlayerPrisonerCollectionAccessV1 access{};
  access.exact_build_admitted = true;
  access.read_lineage = true;
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
    for (std::size_t offset = 0; offset < sizeof(std::int32_t); ++offset) {
      fixture.memory.erase(kPlayer + 0x150 + offset);
      fixture.memory.erase(kPrisoner + 0x150 + offset);
    }
    auto access = Access(fixture);
    access.read_lineage = false;
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(ReadPlayerPrisonerCollectionV1Private(access, result) &&
                         result.available && result.played_house_id == -1 &&
                         result.rows[0].house_id == -1,
                     "legacy collection does not require lineage");
  }
  {
    Fixture fixture;
    fixture.Put(kBase + 0x570C408, kHouseStorage);
    fixture.Put(kBase + 0x570C400, std::uintptr_t{0x283000000});
    fixture.Put(kHouseStorage + 0x20, kHouseSlots);
    fixture.Put(kHouseStorage + 0x2C, std::int32_t{8});
    fixture.Put(kHouseSlots + 3 * 0x10 + 0x08, kHouse);
    fixture.Put(kHouse + 0x10, std::int32_t{3});
    fixture.Put(kHouse + 0x2C, std::int32_t{4});
    fixture.Put(kBase + 0x570C748, kDynastyStorage);
    fixture.Put(kBase + 0x570C700, std::uintptr_t{0x293000000});
    fixture.Put(kDynastyStorage + 0x20, kDynastySlots);
    fixture.Put(kDynastyStorage + 0x2C, std::int32_t{8});
    fixture.Put(kDynastySlots + 4 * 0x10 + 0x08, kDynasty);
    fixture.Put(kDynasty + 0x10, std::int32_t{4});
    fixture.Put(kPlayer + 0x150, std::int32_t{3});
    fixture.Put(kPrisoner + 0x150, std::int32_t{3});
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                            result) &&
                         result.played_house_id == 3 &&
                         result.played_dynasty_id == 4 &&
                         result.rows[0].house_id == 3 &&
                         result.rows[0].dynasty_id == 4,
                     "same-house dynasty identities");
    fixture.Put(kHouse + 0x10, std::int32_t{0x01000003});
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(Access(fixture),
                                                             result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::
                                 lineage_unavailable,
                     "stale house generation unavailable");
  }
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
    fixture.Put(kLand + 0xD8 + 0x0C, std::int32_t{2});
    fixture.Put(kArray + sizeof(kPrisonerId), kSecondPrisonerId);
    auto access = Access(fixture);
    access.read_child_relation = true;
    access.is_child_of = IsChildOf;
    child_relation_calls = 0;
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(ReadPlayerPrisonerCollectionV1Private(access, result) &&
                         result.rows[0].child_of_played_character &&
                         !result.rows[1].child_of_played_character &&
                         child_relation_calls == 4,
                     "same-frame full-id child relation for both rows");
  }
  {
    Fixture fixture;
    auto access = Access(fixture);
    access.read_child_relation = true;
    PlayerPrisonerCollectionSnapshotV1 result{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1Private(access, result) &&
                         result.failure ==
                             PlayerPrisonerCollectionFailureV1::
                                 child_relation_unavailable,
                     "missing child relation callback is unavailable");
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
  {
    using Wait = xar::ck3_11906::MainThreadQueryWaitResultV1;
    using xar::ck3_11906::PlayerPrisonerCollectionFailureDetailV1;
    passed += Expect(
        PlayerPrisonerCollectionFailureDetailV1(
            Wait::timeout_cancelled_before_execution, false, false,
            false, false) ==
            "prisoner collection main-thread query timed out before execution",
        "queued timeout remains distinct");
    passed += Expect(
        PlayerPrisonerCollectionFailureDetailV1(
            Wait::executor_failed, false, false, false, false) ==
            "prisoner collection main-thread executor failed",
        "executor failure remains distinct");
    passed += Expect(
        PlayerPrisonerCollectionFailureDetailV1(
            Wait::completed, false, false, false, false) ==
            "prisoner collection executor did not mark completion",
        "missing executor completion remains distinct");
    passed += Expect(
        PlayerPrisonerCollectionFailureDetailV1(
            Wait::completed, true, true, false, false) ==
            "prisoner collection main-thread frame changed",
        "main-thread frame drift remains distinct");
    passed += Expect(
        PlayerPrisonerCollectionFailureDetailV1(
            Wait::completed, true, false, false, false) ==
            "prisoner collection completion snapshot was unreadable",
        "completion read failure remains distinct");
    passed += Expect(
        PlayerPrisonerCollectionFailureDetailV1(
            Wait::completed, true, false, true, false) ==
            "prisoner collection completion snapshot changed",
        "completion frame drift remains distinct");
    passed += Expect(
        PlayerPrisonerCollectionFailureDetailV1(
            Wait::completed, true, false, true, true) ==
            "prisoner collection result serialization failed",
        "serialization failure remains distinct");
  }
  std::cout << "player_prisoner_collection_query_v1_private " << passed
            << "/23 GREEN\n";
  return passed == 23 ? 0 : 1;
}
