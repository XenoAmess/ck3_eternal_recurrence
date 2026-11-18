#pragma once

#include "xar_bridge/ck3_1210.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kActiveWarsRegistryRvaV1 = 0x6A666D0;
inline constexpr std::uintptr_t kActiveWarsRegistryVtableRvaV1 = 0x4E9C188;
inline constexpr std::uintptr_t kActiveWarsManagerVtableRvaV1 = 0x4E9C2C0;
inline constexpr std::uintptr_t kActiveWarsWarVtableRvaV1 = 0x4E51D80;
inline constexpr std::size_t kActiveWarsManagerOffsetV1 = 0x3F2D8;
inline constexpr std::uintptr_t kActiveWarsScoreRvaV1 = 0x29E8DE0;
inline constexpr std::int32_t kActiveWarsStorageLimitV1 = 1'048'576;
inline constexpr std::int32_t kActiveWarsSideLimitV1 = 65'536;
inline constexpr std::size_t kActiveWarsParticipantBudgetV1 = 1'048'576;
inline constexpr std::size_t kActiveWarsOwnedLimitV1 = 4'096;
inline constexpr std::array<std::uint8_t,32> kActiveWarsScoreEntry32V1{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x20,0x57,
    0x48,0x83,0xEC,0x40,0x48,0x8B,0xF2,0x48,0x8B,0xE9,0x4C,0x8B,0xCA,0x45,0x33,0xC0};

using ActiveWarsNativeScoreGetterV1 = std::int32_t (*)(const void *war, void *tooltip);
struct ActiveWarsBindingsV1 {
  bool exact_build_admitted = false;
  // Only the outer paused application-main owner may opt in. Identity reads
  // do not depend on score permission or on any Unit registry being empty.
  bool integration_native_calls_permitted = false;
  CoreBindings core{};
  void **war_registry_slot = nullptr;
  std::uintptr_t war_registry_vtable = 0;
  std::uintptr_t war_manager_vtable = 0;
  std::uintptr_t war_vtable = 0;
  ActiveWarsNativeScoreGetterV1 get_attacker_war_score = nullptr;
};
using ActiveWarsCopyV1 = bool (*)(void *context, const void *source,
    void *destination, std::size_t size) noexcept;
struct ActiveWarsReadAccessV1 {
  void *context = nullptr;
  ActiveWarsCopyV1 copy = nullptr;
};
enum class ActiveWarPlayerSideV1 { attacker, defender };

// A scoped identity result, deliberately not game::ActiveWarSnapshot.
struct ActiveWarIdentityRowV1 {
  std::int32_t war_id = -1;
  std::int32_t actual_player_character_id = -1;
  ActiveWarPlayerSideV1 player_side = ActiveWarPlayerSideV1::attacker;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::int32_t primary_opponent_character_id = -1;
  bool player_is_primary_war_leader = false;
  // Exact native order, including any duplicate records, retained as read.
  std::vector<std::int32_t> attacker_participant_ids;
  std::vector<std::int32_t> defender_participant_ids;
  std::optional<std::int32_t> native_attacker_score_raw;
  std::optional<std::int32_t> player_relative_war_score;
  std::string_view score_unavailable_reason = "active_wars_score_not_read";
  // No empty objective/army arrays are manufactured for unobserved domains.
  bool targeted_titles_observed = false;
  bool objectives_observed = false;
  bool allied_armies_observed = false;
  bool enemy_armies_observed = false;
};
struct ActiveWarsObservationV1 {
  bool available = false;
  bool same_frame_ready = false;
  bool identity_complete = false;
  bool score_complete = false;
  bool partial = true;
  bool full_snapshot_available = false;
  bool complete_active_wars_qualified = false;
  CoreSnapshotPrefix frame{};
  std::optional<std::vector<ActiveWarIdentityRowV1>> active_wars;
  std::int32_t war_slots_scanned = 0;
  std::size_t active_war_rows = 0;
  std::size_t ended_war_rows = 0;
  std::size_t participant_records = 0;
  // Preserved on unavailable output, including guard/call result failures.
  std::size_t native_score_calls_attempted = 0;
  std::string_view unavailable_reason = "active_wars_not_read";
};

ActiveWarsBindingsV1 BindActiveWarsImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Two complete War-only identity scans and three matching Core reads; score
// calls additionally bracket exact War/side/root identity with fresh Core.
// Successful identity with unavailable score is an honest partial result.
bool ReadActiveWarsV1(const ActiveWarsBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, ActiveWarsObservationV1 &output,
    ActiveWarsReadAccessV1 access = {}) noexcept;
} // namespace xar::ck3_1210
