#pragma once
#include "xar_bridge/character_skill_effect12004.hpp"
#include <cstdint>

namespace xar::bridge::character_skill_effect12004 {
// Owned invocation backing, constructed by the real paused global mailbox.
// No external memory or native-function override surface exists here.
struct NativeContext {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  std::uint32_t owner_thread_id = 0;
  Frame expected{};
  std::uint32_t requested_character_id = 0xFFFFFFFFU;
  void *snapshot_context = nullptr;
  ReadFrame snapshot_frame = nullptr;
  const char *failure = "native_context_not_bound";
  std::uint32_t level_calls = 0, breakdown_calls = 0, string_destroy_calls = 0;
};
// The exact native factory verifies code bytes before returning enabled=true.
// Lifetime: returned Environment borrows context until this owner query ends.
Environment BindNative(NativeContext &) noexcept;
bool NativeSourceStillBound(NativeContext &) noexcept;
} // namespace xar::bridge::character_skill_effect12004
