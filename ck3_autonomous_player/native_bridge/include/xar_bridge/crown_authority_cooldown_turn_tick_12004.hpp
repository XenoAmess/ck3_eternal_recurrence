#pragma once

#include "xar_bridge/ck3_12002_realm_law.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::crown_cooldown::turn_tick {

inline constexpr std::string_view kSource =
    "native_variable_manager_turn_tick_context";

// Private companion: no public Snapshot, cooldown Observation or law DTO layout
// changes. Values describe the current native branch inputs, not a tick ACK.
struct Observation {
  bool read_available = false;
  std::optional<std::uint64_t> manager_match_count{};
  std::optional<bool> manager_contains_context{};
  std::optional<bool> scalar_tail_allows_tick{};
  std::optional<bool> context_tick_eligible{};
  std::string_view unavailable_reason = "turn_tick_context_not_read";
};

struct Access {
  std::uintptr_t game_state_slot_address = 0;
  void *context = nullptr;
  ck3_12002::private_law::ReadRealmLawActiveMemory read_memory = nullptr;
};

// Original raw9 and this companion share exactly one native kind4 resolution.
bool ReadWithTurnTick(const crown_cooldown::Bindings &, std::int32_t character_id,
    std::int64_t frame_date_raw, crown_cooldown::Observation &cooldown,
    const Access &, Observation &turn_tick) noexcept;

} // namespace xar::ck3_12004::crown_cooldown::turn_tick

namespace xar::ck3_12002 {

struct RealmLawTurnTickQuery12004 {
  RealmLawReadbackQuery12002 query{};
  ck3_12004::crown_cooldown::turn_tick::Observation turn_tick{};
};

bool CaptureRealmLawReadbackWithTurnTick12004(
    const private_law::RealmLawActiveCollectionAccess &access,
    std::uintptr_t module_base, const RealmLawReadbackFrame12002 &frame,
    const private_law::RealmLawFinalTerms12002Operations &operations,
    RealmLawReadback12002 &output,
    ck3_12004::crown_cooldown::turn_tick::Observation &turn_tick,
    std::string_view actual_executable_sha256,
    const ck3_12004::crown_cooldown::Bindings *cooldown_bindings_override = nullptr) noexcept;

std::string SerializeRealmLawReadbackWithTurnTick12004(
    const RealmLawReadback12002 &readback,
    const ck3_12004::crown_cooldown::turn_tick::Observation &turn_tick);

bool ExecuteRealmLawPausedPrivateQueryWithTurnTick12004(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

} // namespace xar::ck3_12002
