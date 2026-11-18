#pragma once
#include "xar_bridge/ck3_1210_current_event_snapshot_v1.hpp"
#include "xar_bridge/ck3_1210_commands.hpp"
#include <array>

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kEventOptionsIdlerVtableRvaV1 = 0x4B24758;
inline constexpr std::uintptr_t kEventOptionsWindowVtableRvaV1 = 0x4C5D430;
inline constexpr std::uintptr_t kSelectEventPrimaryVtableRvaV1 = 0x4E93728;
inline constexpr std::uintptr_t kSelectEventSecondaryVtableRvaV1 = 0x4E936F0;
inline constexpr std::uintptr_t kEventOptionCanSelectRvaV1 = 0x1B6C810;
inline constexpr std::size_t kEventOptionsMaxWindowsV1 = 32;
inline constexpr std::size_t kEventOptionsMaxShownV1 = kCurrentEventMaxAuthoredV1;
struct EventOptionsBindingsV1 {
  CurrentEventSnapshotBindingsV1 current{};
  bool source_abi_pins_verified = false;
  std::uintptr_t idler_vtable = 0, window_vtable = 0;
  std::uintptr_t select_primary_vtable = 0, select_secondary_vtable = 0;
  bool (*can_select)(const void *materialized_item) = nullptr;
};
struct EventOptionRowV1 {
  std::int32_t native_option_index = -1;
  bool enabled = false;
  bool operator==(const EventOptionRowV1 &) const = default;
};
struct EventOptionsObservationV1 {
  bool available = false;
  CoreSnapshotPrefix frame{};
  std::int32_t event_instance_id = -1;
  std::size_t count = 0;
  std::array<EventOptionRowV1, kEventOptionsMaxShownV1> rows{};
  std::string_view unavailable_reason = "event_options_not_read";
};
struct alignas(8) SelectEventCommandV1 {
  std::uintptr_t primary_vtable = 0;
  std::array<std::byte, 16> metadata{};
  std::uintptr_t secondary_vtable = 0;
  std::int32_t event_instance_id = -1, native_option_index = -1;
};
static_assert(sizeof(SelectEventCommandV1) == 0x28);
static_assert(offsetof(SelectEventCommandV1, event_instance_id) == 0x20);
static_assert(offsetof(SelectEventCommandV1, native_option_index) == 0x24);
EventOptionsBindingsV1 BindEventOptionsImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Requires paused application-main custody from the owning caller. Copies only
// materialized GUI rows; authored options alone never authorize a selection.
bool ReadEventOptionsV1(const EventOptionsBindingsV1 &, const CoreSnapshotPrefix &,
    std::int32_t expected_event_instance_id, EventOptionsObservationV1 &) noexcept;
SelectEventCommandV1 MakeSelectEventCommandV1(const EventOptionsBindingsV1 &,
    std::int32_t event_instance_id, std::int32_t native_option_index) noexcept;
} // namespace xar::ck3_1210
