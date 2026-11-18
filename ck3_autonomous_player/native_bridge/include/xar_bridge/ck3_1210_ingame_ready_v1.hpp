#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <cstdint>
#include <string_view>

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kIngameRootVtableRvaV1 = 0x4B45FB8;
inline constexpr std::uintptr_t kIngameApplicationVtableRvaV1 = 0x4AFA620;
inline constexpr std::uintptr_t kIngameGfxVtableRvaV1 = 0x4B24758;
inline constexpr std::uintptr_t kIngameHandlerVtableRvaV1 = 0x4B22568;
inline constexpr std::size_t kIngameCompletedFrameEpochOffsetV1 = 0x180;

struct IngameReadyBindingsV1 {
  bool exact_build_admitted = false;
  CoreBindings core{};
  std::uintptr_t root_vtable = 0;
  std::uintptr_t application_vtable = 0;
  std::uintptr_t gfx_vtable = 0;
  std::uintptr_t handler_vtable = 0;
};
struct IngameReadyGraphV1 {
  void *root = nullptr;
  void *application = nullptr;
  void *gfx = nullptr;
  void *handler = nullptr;
  std::uint64_t completed_frame_epoch = 0;
  friend bool operator==(const IngameReadyGraphV1 &, const IngameReadyGraphV1 &) = default;
};
// Owned by one adapter/owner session, never copied with Full bindings. A new
// adapter starts empty; no process-global readiness or wall-clock threshold.
struct IngameReadyWitnessV1 {
  bool observed = false;
  bool ready = false;
  IngameReadyGraphV1 last{};
};
struct IngameReadyObservationV1 {
  bool ready = false;
  IngameReadyGraphV1 graph{};
  std::string_view unavailable_reason = "full_snapshot_ingame_not_observed";
};

// Exact PE proof: R0007-ui-lifecycle-static02/LIFECYCLE_STATIC.actual.json,
// SHA256 16db19b39a3153f2e66cd4309fdaf07236a7ae9a315f946500a80b41d2efd4f5.
// Completion proof: R0007-ingame-completed-epoch-static01,
// SHA256 0835bdcca1d65837f8b4eb22e50ce64d3a6ac16573b480cd1f66d35df4bfe99d.
// app current/pending/transition and the global root publish BEFORE Enter
// returns. app+180 increments at3F5A65D only AFTER Enter/+60/+70 return.
IngameReadyBindingsV1 BindIngameReadyImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Raw copies only: no game getter, selector, lock, tick or queued action. The
// owning Full path supplies its existing application-main/TLS custody first.
// First exact graph records an epoch and remains unavailable. A later complete
// application frame on that same graph proves Enter has returned. Any missing
// object, graph/transition mismatch or epoch rollback invalidates the witness.
bool ObserveIngameReadyV1(const IngameReadyBindingsV1 &bindings,
    IngameReadyWitnessV1 &witness, IngameReadyObservationV1 &output) noexcept;
// Full's two passes must stay on the identical graph AND completed-frame epoch.
bool ConfirmIngameReadyV1(const IngameReadyBindingsV1 &bindings,
    IngameReadyWitnessV1 &witness, const IngameReadyGraphV1 &expected,
    std::string_view &unavailable_reason) noexcept;
} // namespace xar::ck3_1210
