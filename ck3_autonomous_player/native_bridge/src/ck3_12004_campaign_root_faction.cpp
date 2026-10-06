#include "xar_bridge/ck3_12004_campaign_root_faction.hpp"

#include <algorithm>
#include <cstring>

namespace xar::ck3_12004 {
namespace {
using Access = ck3_12002::CampaignRootAccessV1;

template <typename T>
bool Read(const Access &access, const void *base, std::size_t offset,
          T &output) noexcept {
  if (!base) return false;
  const auto *address = static_cast<const std::byte *>(base) + offset;
  if (access.read_memory)
    return access.read_memory(access.context, address, &output, sizeof(T));
  std::memcpy(&output, address, sizeof(T));
  return true;
}

bool ReadDirectVassals(const CampaignRootFactionBindings12004 &bindings,
                      const Access &access, void *player,
                      std::vector<std::int32_t> &output) {
  void *storage = nullptr, *character_fallback = nullptr;
  void *title_storage = nullptr, *title_fallback = nullptr, *slots = nullptr;
  std::int32_t capacity = 0;
  if (!Read(access, bindings.core.character_storage_slot, 0, storage) ||
      !Read(access, bindings.character_fallback_slot, 0, character_fallback) ||
      !Read(access, bindings.title_storage_slot, 0, title_storage) ||
      !Read(access, bindings.title_fallback_slot, 0, title_fallback) ||
      !Read(access, storage, 0x20, slots) ||
      !Read(access, storage, 0x2C, capacity) || !slots ||
      capacity <= 0 || capacity > 4'194'304 || !title_storage) return false;
  output.clear();
  for (std::int32_t index = 0; index < capacity; ++index) {
    void *character = nullptr;
    if (!Read(access, slots, static_cast<std::size_t>(index) * 0x10 + 8,
              character)) return false;
    if (!character || character == character_fallback || character == player)
      continue;
    std::int32_t id = -1;
    void *death = nullptr;
    if (!Read(access, character, 0x18, id)) return false;
    if (id <= 0 || (static_cast<std::uint32_t>(id) & 0xFFFFFFU) !=
                       static_cast<std::uint32_t>(index)) continue;
    if (!Read(access, character, 0x1D0, death)) return false;
    if (death || bindings.immediate_liege(character) != player) continue;
    void *title = bindings.primary_title(character);
    if (!title || title == title_fallback) continue;
    std::int32_t title_id = -1, title_capacity = 0, roundtrip_id = -1;
    void *title_slots = nullptr, *roundtrip = nullptr;
    if (!Read(access, title, 0x10, title_id) || title_id == -1 ||
        !Read(access, title_storage, 0x20, title_slots) ||
        !Read(access, title_storage, 0x2C, title_capacity) || !title_slots ||
        title_capacity <= 0 || title_capacity > 4'194'304) return false;
    const auto title_index = static_cast<std::uint32_t>(title_id) & 0xFFFFFFU;
    if (title_index >= static_cast<std::uint32_t>(title_capacity) ||
        !Read(access, title_slots, static_cast<std::size_t>(title_index) * 0x10 + 8,
              roundtrip) || !roundtrip || roundtrip == title_fallback ||
        !Read(access, roundtrip, 0x10, roundtrip_id) ||
        roundtrip != title || roundtrip_id != title_id) return false;
    output.push_back(id);
  }
  std::sort(output.begin(), output.end());
  return std::adjacent_find(output.begin(), output.end()) == output.end();
}

bool Matches(const CoreSnapshotPrefix &core,
             const game::CampaignRootFrameV1 &frame) noexcept {
  return core.clock.paused && core.map_ready && core.has_played_character &&
      core.played_character_alive && core.clock.date_raw == frame.date_raw &&
      core.played_character_id == frame.played_character_id;
}
} // namespace

CampaignRootFactionBindings12004 BindCampaignRootFactionImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  CampaignRootFactionBindings12004 bindings{};
  bindings.core = ck3_12004::BindCoreImage(base, sha);
  if (!bindings.core.enabled) return bindings;
  bindings.character_fallback_slot = reinterpret_cast<void **>(base + 0x5C67570);
  bindings.title_storage_slot = reinterpret_cast<void **>(base + 0x5D1DAF8);
  bindings.title_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DAE0);
  bindings.immediate_liege = reinterpret_cast<
      ck3_12002::NativeCampaignRootCharacterResolverV1>(base + 0x28BFC50);
  bindings.primary_title = reinterpret_cast<
      ck3_12002::NativeCampaignRootCharacterResolverV1>(base + 0x289DA10);
  bindings.enabled = true;
  return bindings;
}

bool ReadCampaignRootFaction12004(
    const CampaignRootFactionBindings12004 &bindings, const Access &access,
    const ck3_12002::CampaignRootContextRequestV1 &request,
    game::CampaignRootContextV1 &output) noexcept {
  output = {};
  try {
    game::CampaignRootFrameV1 before{}, after{};
    CoreSnapshotPrefix native_before{}, native_after{};
    if (!bindings.enabled || !bindings.core.enabled ||
        !bindings.immediate_liege || !bindings.primary_title ||
        !access.is_main_thread || !access.is_main_thread(access.context) ||
        !access.capture_frame || request.expected_snapshot_revision == 0 ||
        !access.capture_frame(access.context, before) ||
        before.snapshot_revision != request.expected_snapshot_revision ||
        !before.paused || !before.map_ready || !before.has_played_character ||
        !before.played_character_alive || before.played_character_id <= 0 ||
        !ck3_12004::ReadCoreSnapshot(bindings.core, native_before) ||
        !Matches(native_before, before)) return false;
    void *player = ck3_12004::ResolveCoreCharacter(
        bindings.core, before.played_character_id);
    std::vector<std::int32_t> first, second;
    if (!player || !ReadDirectVassals(bindings, access, player, first) ||
        !ReadDirectVassals(bindings, access, player, second) || first != second ||
        !ck3_12004::ReadCoreSnapshot(bindings.core, native_after) ||
        !Matches(native_after, before) ||
        ck3_12004::ResolveCoreCharacter(bindings.core, before.played_character_id) != player ||
        !access.capture_frame(access.context, after) || before != after) return false;
    output.status = game::CampaignRootContextStatusV1::available;
    output.snapshot_revision = before.snapshot_revision;
    output.date_raw = before.date_raw;
    output.player_character_id = before.played_character_id;
    output.player_character_alive = true;
    output.direct_landed_vassal_character_ids = std::move(first);
    output.readiness.direct_landed_vassals_ready = true;
    return true;
  } catch (...) { output = {}; return false; }
}
} // namespace xar::ck3_12004
