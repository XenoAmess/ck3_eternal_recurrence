#include "xar_bridge/religion_reform12002_window.hpp"
#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T out{};
  std::memcpy(&out, static_cast<const std::byte *>(base) + offset, sizeof(out));
  return out;
}

bool ReadWindow(const DraftWindowBindings &bindings, DraftWindowView &output) {
  if (!bindings.enabled || !bindings.core.enabled ||
      bindings.core.jomini_state_slot == nullptr || !bindings.is_visible) {
    return false;
  }
  CoreSnapshotPrefix before{};
  if (!ReadCoreSnapshot(bindings.core, before) || !before.map_ready ||
      !before.has_played_character) {
    output.failure = DraftWindowFailure::core_unavailable; return false;
  }
  output.date_raw = before.clock.date_raw;
  output.played_character_id = static_cast<std::uint32_t>(before.played_character_id);
  if (!before.clock.paused) {
    output.failure = DraftWindowFailure::frame_not_paused; return false;
  }
  const auto *owner = *bindings.core.jomini_state_slot;
  const auto *idler = owner ? Load<const void *>(owner, 0x10) : nullptr;
  if (!idler || Load<std::uintptr_t>(idler, 0) != bindings.idler_vtable) {
    output.failure = DraftWindowFailure::idler_unavailable; return false;
  }
  const auto *handler = Load<const void *>(idler, kDraftHandlerFromIdlerOffset);
  if (!handler || Load<std::uintptr_t>(handler, 0) != bindings.handler_vtable) {
    output.failure = DraftWindowFailure::handler_unavailable; return false;
  }
  const auto *window = Load<const void *>(handler, kDraftWindowFromHandlerOffset);
  output.present = window != nullptr;
  if (window) {
    if (Load<std::uintptr_t>(window, 0) != bindings.window_vtable ||
        Load<std::uintptr_t>(window, 0x10) != bindings.window_secondary_vtable ||
        Load<const void *>(window, kDraftWindowOwnerOffset) != handler) {
      output.failure = DraftWindowFailure::window_layout_unavailable; return false;
    }
    output.visible = bindings.is_visible(window);
    if (output.visible) {
      if (Load<std::uint32_t>(window, kDraftWindowActorIdOffset) !=
          output.played_character_id) {
        output.failure = DraftWindowFailure::draft_subject_unavailable; return false;
      }
      const auto rite = Load<std::uint32_t>(window, kDraftWindowRiteIdOffset);
      if (rite == 0xFFFFFFFFU) {
        output.failure = DraftWindowFailure::draft_subject_unavailable; return false;
      }
      output.source_rite_id = rite;
      output.window = window;
    }
  }
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(bindings.core, after) ||
      after.clock.date_raw != before.clock.date_raw || !after.clock.paused ||
      !after.has_played_character ||
      after.played_character_id != before.played_character_id ||
      *bindings.core.jomini_state_slot != owner ||
      Load<const void *>(owner, 0x10) != idler ||
      Load<const void *>(idler, kDraftHandlerFromIdlerOffset) != handler ||
      Load<const void *>(handler, kDraftWindowFromHandlerOffset) != window) {
    output.window = nullptr; output.source_rite_id.reset();
    output.failure = DraftWindowFailure::state_changed; return false;
  }
  output.available = true; output.failure = DraftWindowFailure::none;
  return true;
}
} // namespace

DraftWindowBindings BindCurrentRiteCreationWindow12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  DraftWindowBindings b{};
  b.core = BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  b.enabled = true;
  b.idler_vtable = base + kDraftIdlerVtableRva;
  b.handler_vtable = base + kDraftHandlerVtableRva;
  b.window_vtable = base + kDraftWindowPrimaryVtableRva;
  b.window_secondary_vtable = base + kDraftWindowSecondaryVtableRva;
  b.is_visible = reinterpret_cast<DraftWindowVisible>(base + kDraftWindowVisibilityRva);
  return b;
}

bool ReadCurrentRiteCreationWindow12002(const DraftWindowBindings &bindings,
    std::uint64_t epoch, DraftWindowView &output) noexcept {
  output = {}; output.capture_epoch = epoch;
#if defined(_WIN32) && defined(_MSC_VER)
  __try { return ReadWindow(bindings, output); }
  __except (1) { output.window = nullptr; output.source_rite_id.reset();
    output.available = false; output.failure = DraftWindowFailure::window_layout_unavailable;
    return false; }
#else
  return ReadWindow(bindings, output);
#endif
}

const char *DraftWindowFailureKey(DraftWindowFailure f) noexcept {
  switch (f) {
  case DraftWindowFailure::none: return "none";
  case DraftWindowFailure::bindings_unavailable: return "bindings_unavailable";
  case DraftWindowFailure::core_unavailable: return "core_unavailable";
  case DraftWindowFailure::frame_not_paused: return "frame_not_paused";
  case DraftWindowFailure::idler_unavailable: return "idler_unavailable";
  case DraftWindowFailure::handler_unavailable: return "handler_unavailable";
  case DraftWindowFailure::window_layout_unavailable: return "window_layout_unavailable";
  case DraftWindowFailure::draft_subject_unavailable: return "draft_subject_unavailable";
  case DraftWindowFailure::state_changed: return "state_changed";
  }
  return "unknown";
}

std::string SerializeCurrentRiteCreationWindow12002(const DraftWindowView &v) {
  return std::string("{\"schema\":\"ck3_12002_current_rite_creation_window_v1\",\"available\":") +
    (v.available ? "true" : "false") + ",\"unavailable_reason\":\"" + DraftWindowFailureKey(v.failure) +
    "\",\"present\":" + (v.present ? "true" : "false") +
    ",\"visible\":" + (v.visible ? "true" : "false") +
    ",\"draft_observed\":" + (v.window ? "true" : "false") +
    ",\"played_character_id\":" + std::to_string(v.played_character_id) +
    ",\"source_rite_id\":" + (v.source_rite_id ? std::to_string(*v.source_rite_id) : "null") +
    ",\"date_raw\":" + std::to_string(v.date_raw) +
    ",\"capture_epoch\":" + std::to_string(v.capture_epoch) + "}";
}
} // namespace xar::ck3_12002::religion_reform
