#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_1210 {
inline constexpr char kCurrentEventSnapshotSchemaV1[] = "ck3_1210_current_event_basic_snapshot_v1";
inline constexpr std::uintptr_t kCurrentEventSelectorRvaV1 = 0x2EBF120;
inline constexpr std::uintptr_t kCurrentEventCharacterSlotRvaV1 = 0x5D50448;
inline constexpr std::uintptr_t kCurrentEventDefinitionVtableRvaV1 = 0x4E52FA8;
inline constexpr std::size_t kCurrentEventManagerOffsetV1 = 0x44BC0;
inline constexpr std::size_t kCurrentEventQueuePointerOffsetV1 = 0x1F18;
inline constexpr std::size_t kCurrentEventQueueCountOffsetV1 = 0x1F24;
inline constexpr std::size_t kCurrentEventDefinitionOffsetV1 = 0x1B8;
inline constexpr std::size_t kCurrentEventCharacterOffsetV1 = 0x1C0;
inline constexpr std::size_t kCurrentEventInstanceOffsetV1 = 0x1C4;
inline constexpr std::size_t kCurrentEventAuthoredPointerOffsetV1 = 0x138;
inline constexpr std::size_t kCurrentEventAuthoredCapacityOffsetV1 = 0x140;
inline constexpr std::size_t kCurrentEventAuthoredCountOffsetV1 = 0x144;
// Adapter availability/work bounds, not engine maxima or clickable-option limits.
inline constexpr std::size_t kCurrentEventMaxQueuedV1 = 512;
inline constexpr std::size_t kCurrentEventMaxAuthoredV1 = 512;
inline constexpr std::array<std::uint8_t, 32> kCurrentEventSelectorEntry32V1 = {
  0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xEC,0x30,0x48,
  0x8D,0x05,0xEE,0x44,0x9F,0x03,0x48,0x89,0x44,0x24,0x20,0xB8,0x02,0x00,0x00,0x00};
using CurrentEventSelectorV1 = void *(*)(void *event_manager);
struct CurrentEventSnapshotBindingsV1 {
  bool exact_build_admitted = false;
  CoreBindings core{};
  CurrentEventSelectorV1 get_current_event = nullptr;
  // Actual selector operand2EBF1B7. Setter26D2510/1D copies Character+18;
  // DFF365/6C/6F resets it from NullCharacter68A8630. This is a full CharacterID,
  // NOT Core.local_player_id. SPlayerEventData+1C0 uses the same CharacterID.
  std::int32_t *selector_character_id_slot = nullptr;
  std::uintptr_t definition_vtable = 0;
};
struct CurrentEventSnapshotObservationV1 {
  std::string_view schema = kCurrentEventSnapshotSchemaV1;
  bool available = false;
  bool found = false;
  bool same_frame_ready = false;
  bool partial = true;
  bool full_snapshot_available = false;
  bool option_count_is_authored_total = true;
  bool option_eligibility_observed = false;
  CoreSnapshotPrefix frame{};
  std::int32_t active_event_instance_id = -1;
  std::int32_t active_event_option_count = 0;
  std::string_view unavailable_reason = "current_event_not_read";
};
// Evidence: Root agent-event-abi READONLY-CURRENT-EVENT-1210-CANDIDATE01.json
// SHA256 48cb4e474b68d20a213c6d42a311f7a3fd33c84c8c45c13fe20538c6b085b2cd;
// READONLY-CURRENT-EVENT-1210-PREFIX-AND-OPTIONS02.json SHA256
// 90826aa4ce338351ecba066879bbabbbf2eec971dd1e27cffb75ebc09550c9f6.
// Address-only binder; owning integration admits mapped-image
// pins plus actual paused application-main/TLS custody. No GUI/action interfaces.
CurrentEventSnapshotBindingsV1 BindCurrentEventSnapshotImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Two real selectors bracketed by complete Core/root/owner checks. Null is empty
// only after both selectors and all checks agree. Authored total grants no UI,
// shown, valid, executable or event-window capability and no full Snapshot.
bool ReadCurrentEventSnapshotV1(const CurrentEventSnapshotBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected, CurrentEventSnapshotObservationV1 &output) noexcept;
} // namespace xar::ck3_1210
