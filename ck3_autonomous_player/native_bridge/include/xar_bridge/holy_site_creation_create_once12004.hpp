#pragma once
#include "xar_bridge/holy_site_creation12004.hpp"
#include <array>
#include <mutex>

namespace xar::ck3_12004::religion::holy_site_creation {
// Bridge-computed intent binding, never an engine-provided hash. Pointer
// identities enter only this hash and never cross the public transport.
std::string PreviewIdentitySha25612004(const Snapshot&, std::uintptr_t image_base,
    const void* selected_native_type, const void* gui_context) noexcept;
bool PreviewIdentityValid12004(std::string_view) noexcept;
std::string_view CreateOnceGuard12004(const Snapshot&, std::string_view expected,
    bool feature_enabled) noexcept;
enum class OnceClaim12004 { claimed, already_attempted, capacity_exhausted, invalid_scope, unavailable };
class CreateOnceLedger12004 {
 public:
  static constexpr std::size_t capacity = 64;
  OnceClaim12004 Claim(std::uintptr_t process_scope, std::uintptr_t owner_scope,
      std::uint64_t expected_revision, std::string_view preview) noexcept;
 private:
  struct Entry {
    std::uintptr_t process_scope=0, owner_scope=0;
    std::uint64_t revision=0;
    std::array<char,64> preview{};
    bool operator==(const Entry&) const = default;
  };
  std::mutex mutex_;
  std::array<Entry,capacity> entries_{};
  std::size_t size_=0;
};
}
