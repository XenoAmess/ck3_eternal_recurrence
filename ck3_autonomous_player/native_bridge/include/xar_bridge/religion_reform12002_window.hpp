#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include <optional>
#include <string>

namespace xar::ck3_12002::religion_reform {

inline constexpr std::uintptr_t kDraftIdlerVtableRva = 0x44BC408;
inline constexpr std::uintptr_t kDraftHandlerVtableRva = 0x44BA890;
inline constexpr std::uintptr_t kDraftWindowPrimaryVtableRva = 0x4565C30;
inline constexpr std::uintptr_t kDraftWindowSecondaryVtableRva = 0x4565C08;
inline constexpr std::uintptr_t kDraftWindowVisibilityRva = 0x21603A0;
inline constexpr std::size_t kDraftHandlerFromIdlerOffset = 0x88;
inline constexpr std::size_t kDraftWindowFromHandlerOffset = 0x278;
inline constexpr std::size_t kDraftWindowOwnerOffset = 0xA0;
inline constexpr std::size_t kDraftWindowRiteIdOffset = 0xC8;
inline constexpr std::size_t kDraftWindowActorIdOffset = 0xCC;

using DraftWindowVisible = bool (*)(const void *);
struct DraftWindowBindings {
  bool enabled = false;
  CoreBindings core{};
  std::uintptr_t idler_vtable = 0;
  std::uintptr_t handler_vtable = 0;
  std::uintptr_t window_vtable = 0;
  std::uintptr_t window_secondary_vtable = 0;
  DraftWindowVisible is_visible = nullptr;
};

enum class DraftWindowFailure {
  none, bindings_unavailable, core_unavailable, frame_not_paused,
  idler_unavailable, handler_unavailable, window_layout_unavailable,
  draft_subject_unavailable, state_changed,
};

// The pointer is an internal, owning-thread-only handoff to the cost/choice/gate
// readers. It is never included in serialized observations or accepted as input.
struct DraftWindowView {
  bool available = false;
  bool present = false;
  bool visible = false;
  DraftWindowFailure failure = DraftWindowFailure::bindings_unavailable;
  const void *window = nullptr;
  std::uint32_t played_character_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> source_rite_id;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
};

DraftWindowBindings BindCurrentRiteCreationWindow12002(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
bool ReadCurrentRiteCreationWindow12002(const DraftWindowBindings &bindings,
    std::uint64_t capture_epoch, DraftWindowView &output) noexcept;
std::string SerializeCurrentRiteCreationWindow12002(const DraftWindowView &view);
const char *DraftWindowFailureKey(DraftWindowFailure failure) noexcept;

} // namespace xar::ck3_12002::religion_reform
