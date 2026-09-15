#include "player_held_construction_model_enumerator_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kModelSingletonSlotRva = 0x57BFBA8;
constexpr std::size_t kGameStateGameDataOffset = 0xA0;
constexpr std::size_t kJominiPlayersOffset = 0x18;
constexpr std::size_t kPlayersLocalPlayerIdOffset = 0x1F0;
constexpr std::size_t kGameDataPlayerManagerOffset = 0x1D4F0;
constexpr std::size_t kPlayerManagerEntriesOffset = 0x58;
constexpr std::size_t kPlayerManagerCountOffset = 0x64;
constexpr std::size_t kPlayerEntryCharacterIdOffset = 0xB0;
constexpr std::size_t kPlayerEntryPlayerIdOffset = 0xD8;
constexpr std::size_t kCharacterIdentityOffset = 0x18;
constexpr std::size_t kCharacterDeathMarkerOffset = 0x1C8;
constexpr std::size_t kCharacterLandStateOffset = 0x1B8;
constexpr std::size_t kHeldTitleIdsOffset = 0x1E0;
constexpr std::size_t kVectorCountOffset = 0x0C;
constexpr std::size_t kStorageSlotsOffset = 0x20;
constexpr std::size_t kStorageCapacityOffset = 0x2C;
constexpr std::size_t kStorageStride = 0x10;
constexpr std::size_t kStorageObjectOffset = 0x08;
constexpr std::size_t kTitleIdentityOffset = 0x10;
constexpr std::size_t kTitleTemplateOffset = 0x160;
constexpr std::size_t kTitleTierOffset = 0x5C;
constexpr std::size_t kTitleHolderCharacterIdOffset = 0x258;
constexpr std::size_t kBaronyProvinceOffset = 0x460;
constexpr std::size_t kProvinceIdentityOffset = 0x10;
constexpr std::size_t kGameDataProvinceArrayOffset = 0x140;
constexpr std::size_t kGameDataProvinceCountOffset = 0x14C;
constexpr std::size_t kModelCatalogOffset = 0x628;
constexpr std::size_t kModelDefinitionVectorOffset = 0x60;
constexpr std::int32_t kMaxPlayerEntries = 1'024;
constexpr std::int32_t kMaxComponentSlots = 4'194'304;
constexpr std::int32_t kMaxHeldTitles = 4'096;
constexpr std::int32_t kMaxProvinces = 1'000'000;
constexpr std::int32_t kMaxDefinitions = 16'384;

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &output) noexcept {
  if (base == 0 || offset >
                       std::numeric_limits<std::uintptr_t>::max() - base) {
    return false;
  }
  output = base + offset;
  return true;
}

template <typename T>
bool Read(const CampaignRootAccessV1 &access, std::uintptr_t base,
          std::size_t offset, T &output) noexcept {
  std::uintptr_t address = 0;
  return Add(base, offset, address) &&
         access.read_memory(access.context,
                            reinterpret_cast<const void *>(address),
                            &output, sizeof(output));
}

bool ReadSlot(const CampaignRootAccessV1 &access, std::uintptr_t module,
              std::uintptr_t rva, std::uintptr_t &output) noexcept {
  return Read(access, module, rva, output);
}

bool ResolveComponent(const CampaignRootAccessV1 &access,
                      std::uintptr_t module, std::uintptr_t storage_rva,
                      std::uintptr_t fallback_rva, std::int32_t full_id,
                      std::size_t identity_offset,
                      std::uintptr_t &output) noexcept {
  output = 0;
  if (full_id <= 0) {
    return false;
  }
  std::uintptr_t storage = 0;
  std::uintptr_t fallback = 0;
  std::uintptr_t slots = 0;
  std::int32_t capacity = 0;
  if (!ReadSlot(access, module, storage_rva, storage) ||
      !ReadSlot(access, module, fallback_rva, fallback) || storage == 0 ||
      !Read(access, storage, kStorageSlotsOffset, slots) ||
      !Read(access, storage, kStorageCapacityOffset, capacity) || slots == 0 ||
      capacity <= 0 || capacity > kMaxComponentSlots) {
    return false;
  }
  const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) {
    return false;
  }
  std::int32_t observed_id = -1;
  return Read(access, slots,
              static_cast<std::size_t>(index) * kStorageStride +
                  kStorageObjectOffset,
              output) &&
         output != 0 && output != fallback &&
         Read(access, output, identity_offset, observed_id) &&
         observed_id == full_id;
}

bool ReadPlayer(const CampaignRootAccessV1 &access, std::uintptr_t module,
                const game::CampaignRootFrameV1 &frame,
                std::uintptr_t &game_data,
                std::uintptr_t &character) noexcept {
  std::uintptr_t game_state = 0;
  std::uintptr_t jomini_state = 0;
  std::uintptr_t players = 0;
  std::uintptr_t entries = 0;
  std::int32_t local_player_id = -1;
  std::int32_t count = 0;
  if (!ReadSlot(access, module, kCampaignRootGameStateSlotRva, game_state) ||
      !ReadSlot(access, module, kCampaignRootJominiStateSlotRva,
                jomini_state) ||
      game_state == 0 || jomini_state == 0 ||
      !Read(access, game_state, kGameStateGameDataOffset, game_data) ||
      game_data == 0 ||
      !Read(access, jomini_state, kJominiPlayersOffset, players) ||
      players == 0 ||
      !Read(access, players, kPlayersLocalPlayerIdOffset, local_player_id) ||
      local_player_id < 0 ||
      !Read(access, game_data,
            kGameDataPlayerManagerOffset + kPlayerManagerEntriesOffset,
            entries) ||
      !Read(access, game_data,
            kGameDataPlayerManagerOffset + kPlayerManagerCountOffset, count) ||
      entries == 0 || count <= 0 || count > kMaxPlayerEntries) {
    return false;
  }
  std::int32_t matches = 0;
  std::int32_t character_id = -1;
  for (std::int32_t index = 0; index < count; ++index) {
    std::uintptr_t entry = 0;
    std::int32_t player_id = -1;
    if (!Read(access, entries, static_cast<std::size_t>(index) * 8,
              entry)) {
      return false;
    }
    if (entry == 0) {
      continue;
    }
    if (!Read(access, entry, kPlayerEntryPlayerIdOffset, player_id)) {
      return false;
    }
    if (player_id != local_player_id) {
      continue;
    }
    if (!Read(access, entry, kPlayerEntryCharacterIdOffset, character_id) ||
        character_id <= 0) {
      return false;
    }
    ++matches;
  }
  if (matches != 1 || character_id != frame.played_character_id ||
      !ResolveComponent(access, module, kCampaignRootCharacterStorageSlotRva,
                        kCampaignRootCharacterFallbackSlotRva, character_id,
                        kCharacterIdentityOffset, character)) {
    return false;
  }
  std::uintptr_t death_marker = 0;
  return Read(access, character, kCharacterDeathMarkerOffset, death_marker) &&
         death_marker == 0;
}

bool ReadHeldBaronies(const CampaignRootAccessV1 &access,
                      std::uintptr_t module, std::uintptr_t game_data,
                      std::uintptr_t character, std::int32_t player_id,
                      std::vector<PlayerHeldHoldingSourceV1> &output,
                      PlayerHeldConstructionModelFailureV1 &failure) {
  failure = PlayerHeldConstructionModelFailureV1::held_title_source;
  std::uintptr_t land_state = 0;
  std::uintptr_t title_ids = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  if (!Read(access, character, kCharacterLandStateOffset, land_state) ||
      land_state == 0 || !Read(access, land_state, kHeldTitleIdsOffset,
                              title_ids) ||
      !Read(access, land_state, kHeldTitleIdsOffset + 0x08, capacity) ||
      !Read(access, land_state,
            kHeldTitleIdsOffset + kVectorCountOffset, count) ||
      capacity < 0 || count < 0 || count > capacity ||
      count > kMaxHeldTitles || (count > 0 && title_ids == 0)) {
    return false;
  }
  std::uintptr_t provinces = 0;
  std::int32_t province_count = 0;
  if (!Read(access, game_data, kGameDataProvinceArrayOffset, provinces) ||
      !Read(access, game_data, kGameDataProvinceCountOffset,
            province_count) ||
      provinces == 0 || province_count <= 0 ||
      province_count > kMaxProvinces) {
    failure =
        PlayerHeldConstructionModelFailureV1::holding_province_identity;
    return false;
  }
  std::vector<std::int32_t> seen_title_ids;
  seen_title_ids.reserve(static_cast<std::size_t>(count));
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    std::int32_t title_id = -1;
    std::uintptr_t title = 0;
    std::uintptr_t title_template = 0;
    std::int32_t holder_id = -1;
    std::int32_t tier = 0;
    if (!Read(access, title_ids,
              static_cast<std::size_t>(index) * sizeof(title_id),
              title_id) || title_id <= 0 ||
        std::find(seen_title_ids.begin(), seen_title_ids.end(), title_id) !=
            seen_title_ids.end() ||
        !ResolveComponent(access, module,
                          kCampaignRootLandedTitleStorageSlotRva,
                          kCampaignRootLandedTitleFallbackSlotRva, title_id,
                          kTitleIdentityOffset, title) ||
        !Read(access, title, kTitleHolderCharacterIdOffset, holder_id) ||
        holder_id != player_id ||
        !Read(access, title, kTitleTemplateOffset, title_template) ||
        title_template == 0 ||
        !Read(access, title_template, kTitleTierOffset, tier) ||
        tier < 1 || tier > 5) {
      return false;
    }
    seen_title_ids.push_back(title_id);
    if (tier != 1) {
      continue;
    }
    failure =
        PlayerHeldConstructionModelFailureV1::holding_province_identity;
    std::uintptr_t province = 0;
    std::uintptr_t indexed = 0;
    std::int32_t province_id = -1;
    if (!Read(access, title, kBaronyProvinceOffset, province) ||
        province == 0 ||
        !Read(access, province, kProvinceIdentityOffset, province_id) ||
        province_id <= 0 || province_id >= province_count ||
        !Read(access, provinces,
              static_cast<std::size_t>(province_id) * sizeof(indexed),
              indexed) || indexed != province) {
      return false;
    }
    output.push_back({title_id, province_id});
    failure = PlayerHeldConstructionModelFailureV1::held_title_source;
  }
  std::sort(output.begin(), output.end(),
            [](const auto &left, const auto &right) {
              return left.barony_title_id < right.barony_title_id;
            });
  failure = PlayerHeldConstructionModelFailureV1::none;
  return true;
}

bool ReadDefinitionSource(const CampaignRootAccessV1 &access,
                          std::uintptr_t module,
                          std::vector<std::uintptr_t> &output) {
  std::uintptr_t singleton = 0;
  std::uintptr_t catalog = 0;
  std::uintptr_t definitions = 0;
  std::int32_t count = 0;
  if (!ReadSlot(access, module, kModelSingletonSlotRva, singleton) ||
      singleton == 0 ||
      !Read(access, singleton, kModelCatalogOffset, catalog) ||
      catalog == 0 ||
      !Read(access, catalog, kModelDefinitionVectorOffset,
            definitions) ||
      !Read(access, catalog,
            kModelDefinitionVectorOffset + kVectorCountOffset, count) ||
      count < 0 || count > kMaxDefinitions ||
      (count > 0 && definitions == 0)) {
    return false;
  }
  output.reserve(static_cast<std::size_t>(count));
  for (std::int32_t index = 0; index < count; ++index) {
    std::uintptr_t definition = 0;
    if (!Read(access, definitions,
              static_cast<std::size_t>(index) * sizeof(definition),
              definition) || definition == 0) {
      return false;
    }
    output.push_back(definition);
  }
  return true;
}

PlayerHeldConstructionModelResultV1 Failed(
    PlayerHeldConstructionModelFailureV1 failure) noexcept {
  PlayerHeldConstructionModelResultV1 result{};
  result.failure = failure;
  return result;
}

} // namespace

PlayerHeldConstructionModelResultV1
ReadPlayerHeldConstructionModelSourcesV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    const CampaignRootAccessV1 &access,
    const PlayerHeldConstructionModelRequestV1 &request) noexcept {
  if (module_base == 0 || !exact_build_admitted) {
    return Failed(PlayerHeldConstructionModelFailureV1::exact_build);
  }
  if (access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context)) {
    return Failed(PlayerHeldConstructionModelFailureV1::application_main);
  }
  if (access.capture_frame == nullptr || access.read_memory == nullptr) {
    return Failed(PlayerHeldConstructionModelFailureV1::paused_frame);
  }
  game::CampaignRootFrameV1 before{};
  if (!access.capture_frame(access.context, before) ||
      before.snapshot_revision != request.expected_snapshot_revision ||
      !before.paused || !before.map_ready ||
      !before.has_played_character || !before.played_character_alive ||
      before.played_character_id <= 0) {
    return Failed(PlayerHeldConstructionModelFailureV1::paused_frame);
  }
  try {
    PlayerHeldConstructionModelResultV1 result{};
    std::uintptr_t game_data = 0;
    std::uintptr_t player_character = 0;
    if (!ReadPlayer(access, module_base, before, game_data,
                    player_character)) {
      return Failed(PlayerHeldConstructionModelFailureV1::player_identity);
    }
    if (!ReadHeldBaronies(access, module_base, game_data, player_character,
                           before.played_character_id,
                           result.directly_held_barony_provinces,
                           result.failure)) {
      return Failed(result.failure);
    }
    if (!ReadDefinitionSource(access, module_base,
                              result.borrowed_definition_addresses)) {
      return Failed(PlayerHeldConstructionModelFailureV1::definition_source);
    }
    game::CampaignRootFrameV1 after{};
    if (!access.capture_frame(access.context, after) || after != before) {
      return Failed(PlayerHeldConstructionModelFailureV1::frame_changed);
    }
    result.status = PlayerHeldConstructionModelStatusV1::sources_available;
    result.snapshot_revision = before.snapshot_revision;
    result.date_raw = before.date_raw;
    result.player_character_id = before.played_character_id;
    return result;
  } catch (...) {
    return Failed(PlayerHeldConstructionModelFailureV1::held_title_source);
  }
}

} // namespace xar::ck3_11906
