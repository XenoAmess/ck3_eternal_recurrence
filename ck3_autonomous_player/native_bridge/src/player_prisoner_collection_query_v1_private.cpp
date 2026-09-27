#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"

#include <algorithm>
#include <limits>

namespace xar::bridge {
namespace {

using Failure = PlayerPrisonerCollectionFailureV1;
using Snapshot = PlayerPrisonerCollectionSnapshotV1;

static_assert(sizeof(void *) == 8, "CK3 prisoner collection ABI is x64-only");

constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageSlotStride = 0x10;
constexpr std::size_t kStorageSlotObjectOffset = 0x08;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterExtensionOffset = 0x1A8;
constexpr std::size_t kCharacterLandStateOffset = 0x1B8;
constexpr std::size_t kCharacterHouseIdOffset = 0x150;
constexpr std::size_t kHouseDynastyIdOffset = 0x2C;
constexpr std::size_t kLineageIdentityOffset = 0x10;
constexpr std::uintptr_t kHouseStorageSlotRva = 0x570C408;
constexpr std::uintptr_t kHouseFallbackSlotRva = 0x570C400;
constexpr std::uintptr_t kDynastyStorageSlotRva = 0x570C748;
constexpr std::uintptr_t kDynastyFallbackSlotRva = 0x570C700;
constexpr std::size_t kExtensionPrisonRelationOffset = 0x288;
constexpr std::size_t kPrisonRelationJailerIdOffset = 0;
constexpr std::size_t kLandStatePrisonersOffset = 0xD8;
constexpr std::size_t kCollectionDataOffset = 0;
constexpr std::size_t kCollectionCountOffset = 0x0C;
constexpr std::uint32_t kIdentitySlotMask = 0x00FFFFFFU;
constexpr std::int32_t kMaximumCharacterSlots = 1 << 20;

struct SourceSample {
  std::uintptr_t player_address = 0;
  std::int32_t player_house_id = -1;
  std::int32_t player_dynasty_id = -1;
  std::uintptr_t collector_address = 0;
  std::uintptr_t data_address = 0;
  std::uint32_t count = 0;
  std::array<PlayerPrisonerCollectionRowV1, kPlayerPrisonerMaximumRowsV1>
      rows{};
};

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &address) noexcept {
  if (base == 0 ||
      offset > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    return false;
  }
  address = base + offset;
  return true;
}

template <typename T>
bool Read(const PlayerPrisonerCollectionAccessV1 &access,
          std::uintptr_t base, std::size_t offset, T &value) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) &&
         access.read_memory(access.context, address, &value, sizeof(value));
}

bool ResolveCharacter(const PlayerPrisonerCollectionAccessV1 &access,
                      std::uintptr_t storage, std::uintptr_t fallback,
                      std::uint32_t full_id,
                      std::uintptr_t &character) noexcept {
  character = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (full_id == 0 || !Read(access, storage, kStorageSlotsOffset, slots) ||
      slots == 0 ||
      !Read(access, storage, kStorageCapacityOffset, capacity) ||
      capacity <= 0 || capacity > kMaximumCharacterSlots) {
    return false;
  }
  const auto slot = full_id & kIdentitySlotMask;
  if (slot >= static_cast<std::uint32_t>(capacity) ||
      !Read(access, slots,
            static_cast<std::size_t>(slot) * kStorageSlotStride +
                kStorageSlotObjectOffset,
            character) ||
      character == 0 || character == fallback) {
    character = 0;
    return false;
  }
  std::uint32_t observed_id = 0;
  if (!Read(access, character, kCharacterIdentityOffset, observed_id) ||
      observed_id != full_id) {
    character = 0;
    return false;
  }
  return true;
}

bool ResolveLineageComponent(const PlayerPrisonerCollectionAccessV1 &access,
                             std::uintptr_t storage_slot_rva,
                             std::uintptr_t fallback_slot_rva,
                             std::int32_t full_id,
                             std::uintptr_t &component) noexcept {
  component = 0;
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (full_id < 0 ||
      !Read(access, access.module_base, storage_slot_rva, storage) ||
      !Read(access, access.module_base, fallback_slot_rva, fallback) ||
      storage == 0 ||
      !Read(access, storage, kStorageSlotsOffset, slots) || slots == 0 ||
      !Read(access, storage, kStorageCapacityOffset, capacity) ||
      capacity <= 0 || capacity > kMaximumCharacterSlots) {
    return false;
  }
  const auto slot = static_cast<std::uint32_t>(full_id) & kIdentitySlotMask;
  if (slot >= static_cast<std::uint32_t>(capacity) ||
      !Read(access, slots,
            static_cast<std::size_t>(slot) * kStorageSlotStride +
                kStorageSlotObjectOffset,
            component) || component == 0 || component == fallback) {
    component = 0;
    return false;
  }
  std::int32_t observed_id = -1;
  if (!Read(access, component, kLineageIdentityOffset, observed_id) ||
      observed_id != full_id) {
    component = 0;
    return false;
  }
  return true;
}

bool ReadLineage(const PlayerPrisonerCollectionAccessV1 &access,
                 std::uintptr_t character, std::int32_t &house_id,
                 std::int32_t &dynasty_id) noexcept {
  house_id = -1;
  dynasty_id = -1;
  if (!Read(access, character, kCharacterHouseIdOffset, house_id) ||
      house_id < -1) return false;
  if (house_id == -1) return true;
  std::uintptr_t house = 0;
  if (!ResolveLineageComponent(access, kHouseStorageSlotRva,
                               kHouseFallbackSlotRva, house_id, house) ||
      !Read(access, house, kHouseDynastyIdOffset, dynasty_id) ||
      dynasty_id < -1) {
    return false;
  }
  if (dynasty_id == -1) return true;
  std::uintptr_t dynasty = 0;
  return ResolveLineageComponent(access, kDynastyStorageSlotRva,
                                 kDynastyFallbackSlotRva, dynasty_id,
                                 dynasty);
}

Failure ReadSample(const PlayerPrisonerCollectionAccessV1 &access,
                   std::uint32_t player_id, SourceSample &sample) noexcept {
  sample = {};
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  if (!Read(access, access.module_base,
            kPlayerPrisonerCharacterStorageSlotRvaV1, storage) ||
      !Read(access, access.module_base,
            kPlayerPrisonerCharacterFallbackSlotRvaV1, fallback) ||
      storage == 0) {
    return Failure::memory_unavailable;
  }
  if (!ResolveCharacter(access, storage, fallback, player_id,
                        sample.player_address)) {
    return Failure::player_unavailable;
  }
  if (access.read_lineage &&
      !ReadLineage(access, sample.player_address, sample.player_house_id,
                   sample.player_dynasty_id)) {
    return Failure::lineage_unavailable;
  }
  std::uintptr_t land_state = 0;
  if (!Read(access, sample.player_address, kCharacterLandStateOffset,
            land_state)) {
    return Failure::memory_unavailable;
  }
  if (land_state == 0) {
    // Exact getter 0x2614F30 returns its process-global empty container.
    // No borrowed pointer from that fallback crosses this query boundary.
    return Failure::none;
  }
  if (!Add(land_state, kLandStatePrisonersOffset,
           sample.collector_address)) {
    return Failure::collection_invalid;
  }
  std::int32_t signed_count = 0;
  if (!Read(access, sample.collector_address, kCollectionDataOffset,
            sample.data_address) ||
      !Read(access, sample.collector_address, kCollectionCountOffset,
            signed_count)) {
    return Failure::memory_unavailable;
  }
  if (signed_count < 0) return Failure::collection_invalid;
  sample.count = static_cast<std::uint32_t>(signed_count);
  if (sample.count > kPlayerPrisonerMaximumRowsV1) {
    return Failure::collection_truncated;
  }
  if (sample.count != 0 && sample.data_address == 0) {
    return Failure::collection_invalid;
  }
  for (std::uint32_t index = 0; index < sample.count; ++index) {
    std::uint32_t full_id = 0;
    if (!Read(access, sample.data_address,
              static_cast<std::size_t>(index) * sizeof(full_id), full_id)) {
      return Failure::memory_unavailable;
    }
    std::uintptr_t prisoner_address = 0;
    if (full_id == player_id ||
        !ResolveCharacter(access, storage, fallback, full_id,
                          prisoner_address)) {
      return Failure::prisoner_identity_invalid;
    }
    std::uintptr_t extension = 0;
    std::uintptr_t prison_relation = 0;
    std::uint32_t jailer_id = 0;
    if (!Read(access, prisoner_address, kCharacterExtensionOffset, extension) ||
        extension == 0 ||
        !Read(access, extension, kExtensionPrisonRelationOffset,
              prison_relation) ||
        prison_relation == 0 ||
        !Read(access, prison_relation, kPrisonRelationJailerIdOffset,
              jailer_id) ||
        jailer_id != player_id) {
      return Failure::custody_relation_invalid;
    }
    std::int32_t house_id = -1;
    std::int32_t dynasty_id = -1;
    if (access.read_lineage &&
        !ReadLineage(access, prisoner_address, house_id, dynasty_id)) {
      return Failure::lineage_unavailable;
    }
    bool child_of_played_character = false;
    if (access.read_child_relation) {
      if (access.is_child_of == nullptr) return Failure::child_relation_unavailable;
      child_of_played_character = access.is_child_of(
          reinterpret_cast<void *>(prisoner_address),
          reinterpret_cast<void *>(sample.player_address));
    }
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (sample.rows[prior].full_character_id == full_id) {
        return Failure::collection_invalid;
      }
    }
    sample.rows[index] = {index, full_id, jailer_id, house_id, dynasty_id,
                          child_of_played_character};
  }
  return Failure::none;
}

void Fail(Snapshot &output, Failure failure) noexcept {
  output = {};
  output.failure = failure;
}

} // namespace

bool ReadPlayerPrisonerCollectionV1Private(
    const PlayerPrisonerCollectionAccessV1 &access,
    PlayerPrisonerCollectionSnapshotV1 &output) noexcept {
  Fail(output, Failure::callbacks_unavailable);
  if (!access.exact_build_admitted ||
      access.admitted_executable_sha256 !=
          kPlayerPrisonerManagementSnapshotV1ExecutableSha256 ||
      access.module_base == 0) {
    Fail(output, Failure::exact_build_mismatch);
    return false;
  }
  if (access.capture_frame == nullptr || access.read_memory == nullptr) {
    return false;
  }
  if (access.read_child_relation && access.is_child_of == nullptr) {
    Fail(output, Failure::child_relation_unavailable);
    return false;
  }
  if (access.current_thread_id == 0 ||
      access.current_thread_id != access.application_main_thread_id) {
    Fail(output, Failure::application_main_thread_required);
    return false;
  }
  PlayerPrisonerFrameV1 before{};
  if (!access.capture_frame(access.context, before)) {
    Fail(output, Failure::frame_unavailable);
    return false;
  }
  if (!before.paused) {
    Fail(output, Failure::not_paused);
    return false;
  }
  if (!before.map_ready || !before.played_character_alive ||
      !before.played_character_identity_round_trip ||
      before.played_character_id <= 0 || before.public_revision == 0 ||
      before.native_revision == 0 || before.proof_epoch == 0) {
    Fail(output, Failure::player_unavailable);
    return false;
  }
  SourceSample first{};
  auto failure = ReadSample(access,
                            static_cast<std::uint32_t>(before.played_character_id),
                            first);
  if (failure != Failure::none) {
    Fail(output, failure);
    return false;
  }
  SourceSample second{};
  failure = ReadSample(access,
                       static_cast<std::uint32_t>(before.played_character_id),
                       second);
  if (failure != Failure::none) {
    Fail(output, failure);
    return false;
  }
  if (first.player_address != second.player_address ||
      first.player_house_id != second.player_house_id ||
      first.player_dynasty_id != second.player_dynasty_id ||
      first.collector_address != second.collector_address ||
      first.data_address != second.data_address || first.count != second.count ||
      !std::equal(first.rows.begin(), first.rows.begin() + first.count,
                  second.rows.begin())) {
    Fail(output, Failure::sample_drift);
    return false;
  }
  PlayerPrisonerFrameV1 after{};
  if (!access.capture_frame(access.context, after)) {
    Fail(output, Failure::frame_unavailable);
    return false;
  }
  if (before != after) {
    Fail(output, Failure::frame_drift);
    return false;
  }
  output = {};
  output.available = true;
  output.failure = Failure::none;
  output.frame = before;
  output.played_house_id = first.player_house_id;
  output.played_dynasty_id = first.player_dynasty_id;
  output.total_count = first.count;
  output.returned_count = first.count;
  output.collection_complete = true;
  output.rows = first.rows;
  return true;
}

std::string_view PlayerPrisonerCollectionFailureNameV1(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::callbacks_unavailable: return "callbacks_unavailable";
  case Failure::application_main_thread_required:
    return "application_main_thread_required";
  case Failure::frame_unavailable: return "frame_unavailable";
  case Failure::not_paused: return "not_paused";
  case Failure::player_unavailable: return "player_unavailable";
  case Failure::memory_unavailable: return "memory_unavailable";
  case Failure::collection_invalid: return "collection_invalid";
  case Failure::collection_truncated: return "collection_truncated";
  case Failure::prisoner_identity_invalid: return "prisoner_identity_invalid";
  case Failure::custody_relation_invalid: return "custody_relation_invalid";
  case Failure::lineage_unavailable: return "lineage_unavailable";
  case Failure::child_relation_unavailable:
    return "child_relation_unavailable";
  case Failure::sample_drift: return "sample_drift";
  case Failure::frame_drift: return "frame_drift";
  }
  return "unknown";
}

} // namespace xar::bridge
