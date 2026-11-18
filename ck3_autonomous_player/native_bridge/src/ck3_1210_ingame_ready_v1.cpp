#include "xar_bridge/ck3_1210_ingame_ready_v1.hpp"
#include <array>
#include <cstring>
#include <limits>
#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_1210 {
namespace {
bool Copy(const void *source, void *destination, std::size_t size) noexcept {
  if (!source || !destination || size == 0) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  if (size - 1 > (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
#if defined(_MSC_VER)
  __try { std::memcpy(destination, source, size); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(destination, source, size); return true;
#endif
}
template <class T> bool Load(const void *object, std::size_t offset, T &value) noexcept {
  if (!object) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(object);
  if (offset > (std::numeric_limits<std::uintptr_t>::max)() - address) return false;
  return Copy(reinterpret_cast<const void *>(address + offset), &value, sizeof(value));
}
template <std::size_t N> bool Bytes(std::uintptr_t base, std::uintptr_t rva,
    const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t, N> actual{};
  return Copy(reinterpret_cast<const void *>(base + rva), actual.data(), actual.size()) && actual == expected;
}
bool Pointer(std::uintptr_t base, std::uintptr_t slot, std::uintptr_t target) noexcept {
  std::uintptr_t actual = 0;
  return Load(reinterpret_cast<const void *>(base + slot), 0, actual) && actual == base + target;
}
bool SameIdentity(const IngameReadyGraphV1 &a, const IngameReadyGraphV1 &b) noexcept {
  return a.root == b.root && a.application == b.application && a.gfx == b.gfx && a.handler == b.handler;
}
bool Fail(IngameReadyWitnessV1 &witness, IngameReadyObservationV1 &out,
    std::string_view reason) noexcept {
  witness = {}; out = {}; out.unavailable_reason = reason; return false;
}
bool Graph(const IngameReadyBindingsV1 &b, IngameReadyGraphV1 &g,
    std::string_view &reason) noexcept {
  g = {};
  reason = "full_snapshot_ingame_root_unpublished";
  if (!Load(b.core.jomini_state_slot, 0, g.root) || !g.root) return false;
  std::uintptr_t type = 0;
  reason = "full_snapshot_ingame_root_type_mismatch";
  if (!Load(g.root, 0, type) || type != b.root_vtable) return false;
  reason = "full_snapshot_ingame_application_unavailable";
  if (!Load(g.root, 0x18, g.application) || !g.application) return false;
  reason = "full_snapshot_ingame_application_type_mismatch";
  if (!Load(g.application, 0, type) || type != b.application_vtable) return false;
  void *current = nullptr, *pending = nullptr;
  std::uint8_t transition = 0;
  reason = "full_snapshot_ingame_transition_unreadable";
  if (!Load(g.application, 0x28, current) || !Load(g.application, 0x78, pending) ||
      !Load(g.application, 0x30, transition)) return false;
  reason = "full_snapshot_ingame_transition_pending";
  if (pending || transition != 0) return false;
  reason = "full_snapshot_ingame_current_root_mismatch";
  if (current != g.root) return false;
  reason = "full_snapshot_ingame_gfx_unpublished";
  if (!Load(g.root, 0x10, g.gfx) || !g.gfx) return false;
  reason = "full_snapshot_ingame_gfx_type_mismatch";
  if (!Load(g.gfx, 0, type) || type != b.gfx_vtable) return false;
  void *root_backref = nullptr, *application_backref = nullptr;
  reason = "full_snapshot_ingame_gfx_backref_mismatch";
  if (!Load(g.gfx, 0x20, root_backref) || root_backref != g.root ||
      !Load(g.gfx, 0x90, application_backref) || application_backref != g.application) return false;
  reason = "full_snapshot_ingame_handler_unpublished";
  if (!Load(g.gfx, 0x88, g.handler) || !g.handler) return false;
  reason = "full_snapshot_ingame_handler_type_mismatch";
  if (!Load(g.handler, 0, type) || type != b.handler_vtable) return false;
  reason = "full_snapshot_ingame_handler_backref_mismatch";
  if (!Load(g.handler, 0x40, root_backref) || root_backref != g.root) return false;
  reason = "full_snapshot_ingame_completed_epoch_unreadable";
  if (!Load(g.application, kIngameCompletedFrameEpochOffsetV1, g.completed_frame_epoch)) return false;
  reason = {}; return true;
}
} // namespace

IngameReadyBindingsV1 BindIngameReadyImageV1(std::uintptr_t base, std::string_view sha) noexcept {
  IngameReadyBindingsV1 b{};
  if (!base || sha != kExecutableSha256 ||
      base > (std::numeric_limits<std::uintptr_t>::max)() - kJominiStateSlotRva - sizeof(void *)) return b;
  b.core = BindCoreImage(base, sha);
  // Mapped-image checks cover exact type dispatch and the publication/completion
  // instructions used by this guard; successful binding invokes no game code.
  constexpr std::array<std::uint8_t, 7> handler_publish{0x48,0x89,0xBB,0x88,0x00,0x00,0x00};
  constexpr std::array<std::uint8_t, 7> global_publish{0x48,0x89,0x0D,0x20,0xDD,0xC2,0x05};
  constexpr std::array<std::uint8_t, 21> current_then_enter{
      0x49,0x89,0x7E,0x28,0x41,0xC6,0x46,0x30,0x00,0x48,0x8B,0x07,0x48,0x8B,0xCF,
      0xFF,0x90,0x80,0x00,0x00,0x00};
  constexpr std::array<std::uint8_t, 7> completed_epoch{0x49,0xFF,0x86,0x80,0x01,0x00,0x00};
  const bool pins = Pointer(base, kIngameRootVtableRvaV1 + 0x80, 0xC85AD0) &&
      Pointer(base, kIngameGfxVtableRvaV1 + 8, 0xB235C0) &&
      Pointer(base, kIngameGfxVtableRvaV1 + 0x28, 0xB266E0) &&
      Pointer(base, kIngameHandlerVtableRvaV1 + 8, 0xAEAC50) &&
      Pointer(base, kIngameApplicationVtableRvaV1 + 0x50, 0x26692F0) &&
      Bytes(base, 0xB23613, handler_publish) && Bytes(base, 0xC85AD9, global_publish) &&
      Bytes(base, 0x3F5A628, current_then_enter) && Bytes(base, 0x3F5A65D, completed_epoch);
  if (!b.core.enabled || !pins) return {};
  b.root_vtable = base + kIngameRootVtableRvaV1;
  b.application_vtable = base + kIngameApplicationVtableRvaV1;
  b.gfx_vtable = base + kIngameGfxVtableRvaV1;
  b.handler_vtable = base + kIngameHandlerVtableRvaV1;
  b.exact_build_admitted = true; return b;
}

bool ObserveIngameReadyV1(const IngameReadyBindingsV1 &b, IngameReadyWitnessV1 &w,
    IngameReadyObservationV1 &out) noexcept {
  out = {};
  if (!b.exact_build_admitted || !b.core.enabled || !b.core.jomini_state_slot ||
      !b.root_vtable || !b.application_vtable || !b.gfx_vtable || !b.handler_vtable)
    return Fail(w, out, "full_snapshot_ingame_binding_unavailable");
  IngameReadyGraphV1 first{}, second{}; std::string_view reason;
  if (!Graph(b, first, reason) || !Graph(b, second, reason)) return Fail(w, out, reason);
  if (first != second) return Fail(w, out, "full_snapshot_ingame_graph_changed");
  out.graph = second;
  if (!w.observed || !SameIdentity(w.last, second)) {
    w = {true, false, second};
    out.unavailable_reason = "full_snapshot_ingame_first_completed_frame_required"; return false;
  }
  // Counter reset or uint64 wrap never borrows an older ready witness. Relearn
  // from the newly observed value; a later real frame may qualify it normally.
  if (second.completed_frame_epoch < w.last.completed_frame_epoch) {
    w = {true, false, second};
    out.unavailable_reason = "full_snapshot_ingame_completed_epoch_restarted"; return false;
  }
  if (!w.ready && second.completed_frame_epoch == w.last.completed_frame_epoch) {
    out.unavailable_reason = "full_snapshot_ingame_completed_frame_not_advanced"; return false;
  }
  w.ready = true; w.last = second;
  out.ready = true; out.unavailable_reason = {}; return true;
}

bool ConfirmIngameReadyV1(const IngameReadyBindingsV1 &b, IngameReadyWitnessV1 &w,
    const IngameReadyGraphV1 &expected, std::string_view &reason) noexcept {
  IngameReadyObservationV1 current{};
  if (!ObserveIngameReadyV1(b, w, current)) { reason = current.unavailable_reason; return false; }
  if (current.graph != expected) { reason = "full_snapshot_ingame_completed_frame_changed"; return false; }
  reason = {}; return true;
}
} // namespace xar::ck3_1210
