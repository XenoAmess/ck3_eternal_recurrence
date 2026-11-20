#pragma once
#include "xar_bridge/ck3_1210_core_control_v1.hpp"
#include <cstddef>
#include <cstdint>
namespace xar::ck3_1210 {
// Read-only algorithm seam. Passing this verifier is not owner or call authority.
struct SaveImageRead111 {
  void *context = nullptr;
  bool (*copy)(void *, std::uintptr_t, void *, std::size_t) noexcept = nullptr;
};
bool VerifySaveImage111(std::uintptr_t base, SaveImageRead111 access = {}) noexcept;
bool SaveMailboxOwner111(const CoreControlContextV1 &,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
// This production entry binds the actual application module, Core targets,
// command targets, current warm MainTLS and currently executing ticket itself.
bool SaveAdmission111(const CoreControlContextV1 &,
    const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
} // namespace xar::ck3_1210
