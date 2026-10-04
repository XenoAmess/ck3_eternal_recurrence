#pragma once

#include "xar_bridge/game_contract.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

using game::Snapshot;
using game::RaiseTroopsResult;
using game::MoveArmyResult;
using game::HaltArmyResult;
using game::PreviewMoveArmyResult;
using game::PreviewMoveArmyStatus;
using game::DisbandArmyResult;
using game::SplitArmyHalfResult;
using game::MergeArmiesResult;
using game::StartAssaultResult;
using game::StopAssaultResult;

struct CommandBindings;

// These callbacks read the caller's own game image on its owning thread.
// Offline fixtures substitute ordinary caller-owned byte arrays.
struct MilitaryWorldAccess {
  void *context = nullptr;
  bool (*read_snapshot)(void *, Snapshot &) noexcept = nullptr;
  void *(*resolve_character)(void *, std::int32_t) noexcept = nullptr;
  void *(*resolve_unit)(void *, std::int32_t) noexcept = nullptr;
  void *(*resolve_province)(void *, std::int32_t) noexcept = nullptr;
  void *(*resolve_siege)(void *, std::int32_t) noexcept = nullptr;
};

struct MilitaryBindings {
  bool enabled = false;
  void *submit_context = nullptr;
  bool (*submit_copy)(void *, void *, std::uint32_t) noexcept = nullptr;
  std::uintptr_t raise_primary = 0, raise_secondary = 0;
  std::uintptr_t move_primary = 0, move_secondary = 0;
  std::uintptr_t halt_primary = 0, halt_secondary = 0;
  std::uintptr_t disband_primary = 0, disband_secondary = 0;
  std::uintptr_t split_primary = 0, split_secondary = 0;
  std::uintptr_t merge_primary = 0, merge_secondary = 0;
  std::uintptr_t start_primary = 0, start_secondary = 0;
  std::uintptr_t stop_primary = 0, stop_secondary = 0;
  void *(*get_character_capital)(void *) = nullptr;
  void *(*resolve_raise_province)(void *, void *, std::int32_t,
                                 std::int32_t) = nullptr;
  void *(*construct_raise)(void *, std::int32_t, const void *) = nullptr;
  bool (*validate_raise)(void *, void *) = nullptr;
  void *(*destroy_raise)(void *, std::int32_t) = nullptr;
  std::int32_t (*move_mode)(void *, void *, std::int32_t) = nullptr;
  bool (*character_command_allowed)(void *, std::int32_t) = nullptr;
  bool (*army_move_allowed)(void *, std::int32_t) = nullptr;
  bool (*move_allowed)(std::int32_t, void *, std::int32_t) = nullptr;
  void *(*construct_move_path)(void *) = nullptr;
  void *(*destroy_move)(void *, std::int32_t) = nullptr;
  void *(*construct_halt)(void *, std::int32_t, const void *) = nullptr;
  bool (*validate_halt)(void *, void *) = nullptr;
  void *(*destroy_halt)(void *, std::int32_t) = nullptr;
  std::int64_t *(*read_move_progress)(void *, std::int64_t *) = nullptr;
  void *(*read_route_first)(void *) = nullptr;
  void *(*read_route_last)(void *) = nullptr;
  const std::int64_t *move_progress_cutoff = nullptr;
  void *(*construct_path_context)(void *, void *) = nullptr;
  bool (*build_route)(void *, void *, void *, std::int32_t, void *) = nullptr;
  bool (*validate_disband)(std::int32_t, std::int32_t, void *) = nullptr;
  bool (*validate_split)(std::int32_t, std::int32_t, std::int32_t,
                         void *) = nullptr;
  void *(*destroy_split)(void *, std::int32_t) = nullptr;
  void *(*create_merge)() = nullptr;
  void (*append_int_range)(void *, std::int32_t, const std::int32_t *,
                           const std::int32_t *) = nullptr;
  bool (*validate_merge)(void *, void *) = nullptr;
  void *(*destroy_merge)(void *, std::int32_t) = nullptr;
  bool (*validate_start)(std::int32_t, std::int32_t, std::int32_t,
                         void *) = nullptr;
  bool (*validate_stop)(std::int32_t, std::int32_t, std::int32_t,
                        void *) = nullptr;
  void *(*destroy_assault)(void *, std::int32_t) = nullptr;
};

// Binds addresses only. The CommandBindings argument must outlive the result.
MilitaryBindings BindMilitaryImage(std::uintptr_t image_base,
                                    std::string_view executable_sha256,
                                    const CommandBindings &commands) noexcept;

void *ResolveMilitaryDefaultRaiseProvince(const MilitaryBindings &,
                                          void *character) noexcept;

// 1.20 inlines the old origin selector. Reproduce its native branch choices
// through the three preserved native getters; no obsolete callable is reused.
void *ResolveMilitaryMoveOrigin(const MilitaryBindings &, void *unit,
                                void *target, bool mode_is_one) noexcept;

RaiseTroopsResult SubmitRaiseTroopsDefault(const MilitaryBindings &,
                                          const MilitaryWorldAccess &) noexcept;
MoveArmyResult SubmitMoveArmy(const MilitaryBindings &,
                              const MilitaryWorldAccess &,
                              std::int32_t unit_id,
                              std::int32_t province_id) noexcept;
HaltArmyResult SubmitHaltArmy(const MilitaryBindings &,
                              const MilitaryWorldAccess &,
                              std::int32_t unit_id) noexcept;
PreviewMoveArmyResult PreviewMoveArmy(const MilitaryBindings &,
                                      const MilitaryWorldAccess &,
                                      std::int32_t unit_id,
                                      std::int32_t province_id) noexcept;
DisbandArmyResult SubmitDisbandArmy(const MilitaryBindings &,
                                    const MilitaryWorldAccess &,
                                    std::int32_t unit_id) noexcept;
SplitArmyHalfResult SubmitSplitArmyHalf(const MilitaryBindings &,
                                        const MilitaryWorldAccess &,
                                        std::int32_t unit_id) noexcept;
MergeArmiesResult SubmitMergeArmies(const MilitaryBindings &,
                                    const MilitaryWorldAccess &,
                                    std::int32_t destination_unit_id,
                                    std::int32_t source_unit_id) noexcept;
StartAssaultResult SubmitStartAssault(const MilitaryBindings &,
                                      const MilitaryWorldAccess &,
                                      std::int32_t siege_id) noexcept;
StopAssaultResult SubmitStopAssault(const MilitaryBindings &,
                                    const MilitaryWorldAccess &,
                                    std::int32_t siege_id) noexcept;

// Payload declarations are exposed for deterministic offline native fixtures.
struct MilitaryCommandHeader {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 3> padding{};
  std::array<std::uint32_t, 3> metadata{};
  std::uintptr_t secondary_vtable = 0;
};
struct MoveUnitCommand {
  MilitaryCommandHeader header;
  std::int32_t kind = 1, unit_id = -1, province_id = -1, mode = 0;
  std::int32_t route_kind = 2, direct_target = 1;
  std::array<std::byte, 0x130> path{};
};
struct DisbandUnitCommand {
  MilitaryCommandHeader header;
  std::int32_t kind = 1, internal_army_id = -1;
};
struct SplitHalfUnitCommand {
  MilitaryCommandHeader header;
  std::int32_t kind = 1, character_id = -1, internal_army_id = -1;
  std::array<std::byte, 4> padding{};
};
struct NativeMilitaryIntArray {
  std::int32_t *data = nullptr;
  std::int32_t capacity = 0, count = 0;
  void *allocator = nullptr;
};
struct HaltUnitCommand {
  MilitaryCommandHeader header;
  std::int32_t kind = 1;
  std::array<std::byte, 4> padding{};
  NativeMilitaryIntArray unit_ids;
};
struct MergeUnitCommand {
  MilitaryCommandHeader header;
  std::int32_t kind = 0, destination_unit_id = -1;
  NativeMilitaryIntArray source_unit_ids;
};
struct AssaultSiegeCommand {
  MilitaryCommandHeader header;
  std::int32_t kind = 1, character_id = -1, siege_id = -1;
  std::array<std::byte, 4> padding{};
};
static_assert(sizeof(MilitaryCommandHeader) == 0x20);
static_assert(offsetof(MilitaryCommandHeader, secondary_vtable) == 0x18);
static_assert(sizeof(MoveUnitCommand) == 0x168);
static_assert(offsetof(MoveUnitCommand, path) == 0x38);
static_assert(sizeof(DisbandUnitCommand) == 0x28);
static_assert(sizeof(SplitHalfUnitCommand) == 0x30);
static_assert(offsetof(SplitHalfUnitCommand, character_id) == 0x24);
static_assert(offsetof(SplitHalfUnitCommand, internal_army_id) == 0x28);
static_assert(sizeof(HaltUnitCommand) == 0x40);
static_assert(offsetof(HaltUnitCommand, unit_ids) == 0x28);
static_assert(sizeof(MergeUnitCommand) == 0x40);
static_assert(offsetof(MergeUnitCommand, source_unit_ids) == 0x28);
static_assert(sizeof(AssaultSiegeCommand) == 0x30);
static_assert(offsetof(AssaultSiegeCommand, siege_id) == 0x28);

} // namespace xar::ck3_12002
