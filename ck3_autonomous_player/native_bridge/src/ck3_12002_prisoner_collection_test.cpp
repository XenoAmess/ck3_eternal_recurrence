#include "xar_bridge/ck3_12002_prisoner.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/ck3_12002_family_subject_abi.hpp"

#include <cstddef>
#include <cstdint>
#include <iostream>
#include <unordered_map>

namespace {
using namespace xar::bridge;
using namespace xar::ck3_12002;

constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kStorage = 0x200000000;
constexpr std::uintptr_t kSlots = 0x210000000;
constexpr std::uintptr_t kPlayer = 0x220000000;
constexpr std::uintptr_t kPrisoner = 0x220001000;
constexpr std::uintptr_t kSecondPrisoner = 0x220002000;
constexpr std::uintptr_t kExtension = 0x260000000;
constexpr std::uintptr_t kSecondExtension = 0x260001000;
constexpr std::uintptr_t kRelation = 0x270000000;
constexpr std::uintptr_t kSecondRelation = 0x270001000;
constexpr std::uintptr_t kLand = 0x230000000;
constexpr std::uintptr_t kArray = 0x240000000;
constexpr std::uintptr_t kHouseStorage = 0x280000000;
constexpr std::uintptr_t kHouseSlots = 0x281000000;
constexpr std::uintptr_t kHouse = 0x282000000;
constexpr std::uintptr_t kSecondHouse = 0x282001000;
constexpr std::uintptr_t kDynastyStorage = 0x290000000;
constexpr std::uintptr_t kDynastySlots = 0x291000000;
constexpr std::uintptr_t kDynasty = 0x292000000;
constexpr std::uintptr_t kTitleStorage = 0x2A0000000;
constexpr std::uintptr_t kTitleSlots = 0x2A1000000;
constexpr std::uintptr_t kTitle = 0x2A2000000;
constexpr std::uintptr_t kTitleTemplate = 0x2A3000000;
constexpr std::uintptr_t kFamily = 0x2B0000000;
constexpr std::uintptr_t kSecondFamily = 0x2B0001000;
constexpr std::uint32_t kPlayerId = 0x01000002;
constexpr std::uint32_t kPrisonerId = 0x02000003;
constexpr std::uint32_t kSecondPrisonerId = 0x03000004;
constexpr std::int32_t kHouseId = 0x01000001;
constexpr std::int32_t kSecondHouseId = 0x02000003;
constexpr std::int32_t kDynastyId = 0x02000002;
constexpr std::int32_t kTitleId = 0x04000005;

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> memory;
  PlayerPrisonerFrameV1 frame{};

  template <typename T> void Put(std::uintptr_t address, T value) {
    const auto *bytes = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(value); ++index)
      memory[address + index] = bytes[index];
  }

  void Collection(std::int32_t count) {
    Put(kLand + 0xD8, kArray);
    Put(kLand + 0xE4, count);
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
    Put(kBase + kCharacterStorageSlotRva, kStorage);
    Put(kBase + 0x5C67570, std::uintptr_t{0x250000000});
    Put(kStorage + 0x20, kSlots);
    Put(kStorage + 0x2C, std::int32_t{8});
    Put(kSlots + 2 * 0x10 + 0x08, kPlayer);
    Put(kSlots + 3 * 0x10 + 0x08, kPrisoner);
    Put(kSlots + 4 * 0x10 + 0x08, kSecondPrisoner);
    Put(kPlayer + 0x18, kPlayerId);
    Put(kPrisoner + 0x18, kPrisonerId);
    Put(kSecondPrisoner + 0x18, kSecondPrisonerId);
    Put(kPlayer + 0x158, kHouseId);
    Put(kPrisoner + 0x158, kHouseId);
    Put(kSecondPrisoner + 0x158, kSecondHouseId);
    Put(kPrisoner + 0x1B0, kExtension);
    Put(kSecondPrisoner + 0x1B0, kSecondExtension);
    Put(kExtension + 0x288, kRelation);
    Put(kSecondExtension + 0x288, kSecondRelation);
    Put(kRelation, kPlayerId);
    Put(kSecondRelation, kPlayerId);
    Put(kPlayer + 0x1C0, kLand);
    Put(kLand + 0x350, std::int64_t{4'000'000});
    Collection(2);
    Put(kArray, kPrisonerId);
    Put(kArray + 4, kSecondPrisonerId);

    Put(kBase + kFamilySubjectHouseStorageSlotRva, kHouseStorage);
    Put(kBase + kFamilySubjectHouseFallbackSlotRva, std::uintptr_t{0x283000000});
    Put(kHouseStorage + 0x20, kHouseSlots);
    Put(kHouseStorage + 0x2C, std::int32_t{8});
    Put(kHouseSlots + 1 * 0x10 + 0x08, kHouse);
    Put(kHouseSlots + 3 * 0x10 + 0x08, kSecondHouse);
    Put(kHouse + 0x10, kHouseId);
    Put(kHouse + 0x2C, kDynastyId);
    Put(kSecondHouse + 0x10, kSecondHouseId);
    Put(kSecondHouse + 0x2C, std::int32_t{-1});
    Put(kBase + kFamilySubjectDynastyStorageSlotRva, kDynastyStorage);
    Put(kBase + kFamilySubjectDynastyFallbackSlotRva, std::uintptr_t{0x293000000});
    Put(kDynastyStorage + 0x20, kDynastySlots);
    Put(kDynastyStorage + 0x2C, std::int32_t{8});
    Put(kDynastySlots + 2 * 0x10 + 0x08, kDynasty);
    Put(kDynasty + 0x10, kDynastyId);

    Put(kBase + kCampaignRootLandedTitleStorageSlotRva, kTitleStorage);
    Put(kBase + kCampaignRootLandedTitleFallbackSlotRva, std::uintptr_t{0x2A4000000});
    Put(kTitleStorage + 0x20, kTitleSlots);
    Put(kTitleStorage + 0x2C, std::int32_t{8});
    Put(kTitleSlots + 5 * 0x10 + 0x08, kTitle);
    Put(kTitle + 0x10, kTitleId);
    Put(kTitle + 0x48, kTitleTemplate);
    Put(kTitleTemplate + 0x64, std::int32_t{3});
    Put(kPrisoner + 0x1A8, kFamily);
    Put(kSecondPrisoner + 0x1A8, kSecondFamily);
    Put(kFamily, kPlayerId);
    Put(kFamily + 4, std::int32_t{-1});
    Put(kSecondFamily, kPlayerId + 0x01000000);
    Put(kSecondFamily + 4, std::int32_t{-1});
  }
};

bool Capture(void *context, PlayerPrisonerFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}

bool Read(void *context, std::uintptr_t address, void *output,
          std::size_t size) noexcept {
  const auto &memory = static_cast<Fixture *>(context)->memory;
  auto *bytes = static_cast<std::uint8_t *>(output);
  for (std::size_t index = 0; index < size; ++index) {
    const auto found = memory.find(address + index);
    if (found == memory.end()) return false;
    bytes[index] = found->second;
  }
  return true;
}

void *GetPrimaryTitle(void *character) {
  return character == reinterpret_cast<void *>(kPrisoner)
             ? reinterpret_cast<void *>(kTitle) : nullptr;
}

PlayerPrisonerCollectionAccessV1 Access(Fixture &fixture) {
  PlayerPrisonerCollectionAccessV1 access{};
  access.exact_build_admitted = true;
  access.admitted_executable_sha256 = kExecutableSha256;
  access.read_lineage = true;
  access.read_child_relation = true;
  access.read_title_tier = true;
  access.read_dread = true;
  access.module_base = kBase;
  access.current_thread_id = 8;
  access.application_main_thread_id = 8;
  access.context = &fixture;
  access.capture_frame = Capture;
  access.read_memory = Read;
  access.get_primary_title = GetPrimaryTitle;
  return access;
}

bool Expect(bool condition, const char *name) {
  if (!condition) std::cerr << "FAIL " << name << '\n';
  return condition;
}
} // namespace

int main() {
  int passed = 0;
  {
    Fixture fixture;
    PlayerPrisonerCollectionSnapshotV1 output{};
    passed += Expect(ReadPlayerPrisonerCollectionV1(Access(fixture), output) &&
        output.available && output.collection_complete && output.total_count == 2 &&
        output.returned_count == 2 && output.rows[0].source_ordinal == 0 &&
        output.rows[0].full_character_id == kPrisonerId &&
        output.rows[1].source_ordinal == 1 &&
        output.rows[1].full_character_id == kSecondPrisonerId &&
        output.rows[0].jailer_character_id == kPlayerId &&
        output.rows[1].jailer_character_id == kPlayerId,
        "new collection and custody full IDs");
    passed += Expect(output.played_house_id == kHouseId &&
        output.played_dynasty_id == kDynastyId && output.rows[0].house_id == kHouseId &&
        output.rows[0].dynasty_id == kDynastyId && output.rows[1].house_id == kSecondHouseId &&
        output.rows[1].dynasty_id == -1,
        "generation-bearing lineage and legal dynasty-none");
    passed += Expect(output.rows[0].child_of_played_character &&
        !output.rows[1].child_of_played_character,
        "inline native child relation compares full parent ID");
    passed += Expect(output.rows[0].primary_title_tier_raw == 3 &&
        output.rows[1].primary_title_tier_raw == -1 && output.played_dread_raw == 4'000'000,
        "new title template tier and dread layouts");
    fixture.Put(kSecondPrisoner + 0x1A8, std::uintptr_t{0});
    passed += Expect(ReadPlayerPrisonerCollectionV1(Access(fixture), output) &&
        !output.rows[1].child_of_played_character,
        "native null family is legal false");
  }
  {
    Fixture fixture;
    fixture.Put(kPlayer + 0x1C0, std::uintptr_t{0});
    PlayerPrisonerCollectionSnapshotV1 output{};
    passed += Expect(ReadPlayerPrisonerCollectionV1(Access(fixture), output) &&
        output.collection_complete && output.total_count == 0 &&
        output.returned_count == 0 && output.played_dread_raw == 0,
        "native empty land-state fallback and zero dread");
  }
  {
    Fixture fixture;
    fixture.Put(kRelation, kSecondPrisonerId);
    PlayerPrisonerCollectionSnapshotV1 output{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1(Access(fixture), output) &&
        output.failure == PlayerPrisonerCollectionFailureV1::custody_relation_invalid,
        "collection row with other jailer is unavailable");
  }
  {
    Fixture fixture;
    auto access = Access(fixture);
    access.admitted_executable_sha256 = kPlayerPrisonerManagementSnapshotV1ExecutableSha256;
    PlayerPrisonerCollectionSnapshotV1 output{};
    passed += Expect(!ReadPlayerPrisonerCollectionV1(access, output) &&
        output.failure == PlayerPrisonerCollectionFailureV1::exact_build_mismatch,
        "old executable does not admit new layout");
  }
  std::cout << "ck3_12002_prisoner_collection " << passed << "/8 GREEN\n";
  return passed == 8 ? 0 : 1;
}
