#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004::title_ui {
// Read-only candidate for exact 1.20.0.4. All addresses stay provider-private.
using ReadMemory = bool (*)(void *, const void *, void *, std::size_t) noexcept;
struct Bindings {
  bool enabled=false;
  std::uintptr_t image_base=0;
  ReadMemory read_memory=nullptr;
  void *read_context=nullptr;
};
struct Selection {
  const void *window=nullptr, *root=nullptr, *title=nullptr;
  std::uint32_t raw_title_id=0xFFFFFFFFU;
  bool subject_available=false;
  bool operator==(const Selection &) const = default;
};
Bindings BindImage12004(std::uintptr_t image_base, std::string_view executable_sha256,
    ReadMemory read_memory, void *read_context=nullptr) noexcept;
// A stable typed window can have no resolvable subject. Callers must check the
// explicit availability flag before consuming raw_title_id. Hidden != visible.
bool ReadSelection12004(const Bindings &, const void *handler,
    Selection &, std::string &unavailable_reason) noexcept;
} // namespace xar::ck3_12004::title_ui
