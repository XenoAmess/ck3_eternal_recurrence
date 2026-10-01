#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <span>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 {

inline constexpr std::size_t kWorldWarManagerOffset = 0x2EBE0;
inline constexpr std::size_t kWorldWarIdOffset = 0x08;
inline constexpr std::size_t kWorldWarAttackersOffset = 0x20;
inline constexpr std::size_t kWorldWarDefendersOffset = 0x80;
inline constexpr std::size_t kWorldWarCasusBelliOffset = 0x100;
inline constexpr std::size_t kWorldWarStartDateOffset = 0xE0;
inline constexpr std::size_t kWorldWarTargetTitleIdsOffset = 0x270;
inline constexpr std::size_t kWorldWarPrimaryAttackerOffset = 0x288;
inline constexpr std::size_t kWorldWarPrimaryDefenderOffset = 0x28C;
inline constexpr std::size_t kWorldWarClaimantOffset = 0x290;
// The native field is one byte. Reading a pointer here also reads unrelated
// fields at +0x359..+0x35F and incorrectly excludes otherwise active wars.
inline constexpr std::size_t kWorldWarEndedOffset = 0x358;
inline constexpr std::uintptr_t kWorldContainsParticipantRva = 0x2494B60;
inline constexpr std::uintptr_t kWorldGetWarScoreRva = 0x249AC40;
inline constexpr std::uintptr_t kWorldCharacterCapitalRva = 0x28B1CD0;
inline constexpr std::uintptr_t kWorldRaiseProvinceSelectorRva = 0x24A51B0;

using ContainsWarParticipant12002 = bool (*)(const void *, std::int32_t);
using GetWarScore12002 = std::int32_t (*)(const void *, void *);
using WorldCharacterCapitalGetter12002 = void *(*)(void *);
using WorldRaiseProvinceSelector12002 =
    void *(*)(void *, void *, std::int32_t, std::int32_t);

struct WorldBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  ContainsWarParticipant12002 contains_war_participant = nullptr;
  GetWarScore12002 get_war_score = nullptr;
  void **character_storage_slot = nullptr;
  WorldCharacterCapitalGetter12002 get_character_capital = nullptr;
  WorldRaiseProvinceSelector12002 resolve_raise_province = nullptr;
};

enum class WorldReadResult { unavailable, available, partial };

WorldBindings BindWorldImage(std::uintptr_t image_base,
                             std::string_view executable_sha256) noexcept;
// Each resolver checks the complete generation-bearing ID, not only its
// low 24-bit storage index. It resolves active wars only.
void *ResolveWar(const WorldBindings &bindings, std::int32_t war_id) noexcept;
bool ReadWarParticipantIds(const void *side,
                           std::vector<std::int32_t> &output) noexcept;
bool ReadWarTargetTitleIds(const void *war,
                           std::vector<std::int32_t> &output) noexcept;

// Reads the actual manager/storage/participant graph and the native score.
// all_armies is the version-bound CUnit projection used by both army and
// war snapshots. Objective Province enrichment is a separate reader.
WorldReadResult ReadActiveWars(
    const WorldBindings &bindings, std::int32_t played_character_id,
    std::span<const game::ArmySnapshot> all_armies,
    std::vector<game::ActiveWarSnapshot> &output) noexcept;

struct ArmyBindings;
struct ProvinceBindings;
// Whole-world projection includes armies, wars and objective Province state;
// it is static-ready until a new-build paused snapshot is captured in-game.
WorldReadResult ReadWorldSnapshot(
    const WorldBindings &bindings, const ArmyBindings &armies,
    const ProvinceBindings &provinces, const CoreSnapshotPrefix &prefix,
    game::Snapshot &output) noexcept;

} // namespace xar::ck3_12002
