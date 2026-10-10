#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

using ConceptionSecondaryContext12004ReadMemory =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

struct ConceptionSecondaryContext12004Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  ConceptionSecondaryContext12004ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

struct ConceptionSecondaryContext12004Step {
  // Known native fallback is distinct from a failed observer copy.
  std::string_view status = "not_read";
  std::optional<std::uint32_t> requested_full_id;
  std::uintptr_t resolved_object = 0;
};

struct ConceptionSecondaryContext12004Read {
  std::string_view source = "native_conception_secondary_context";
  std::string_view status = "unavailable";
  std::string_view unavailable_reason =
      "native_conception_secondary_context_binding_unavailable";
  std::array<ConceptionSecondaryContext12004Step, 3> resolution;
  std::optional<std::int32_t> context_7d8_raw_i32;
  std::optional<bool> selects_alternate_relation_path;
};

ConceptionSecondaryContext12004Bindings BindConceptionSecondaryContext12004(
    std::string_view build_version, std::string_view executable_sha256,
    std::uintptr_t image_base,
    ConceptionSecondaryContext12004ReadMemory read_memory,
    void *read_context = nullptr) noexcept;

// The caller owns the same-frame current household Character and full ID.
// Reads the three qualified lookups and signed field; never calls the provider.
ConceptionSecondaryContext12004Read
ReadConceptionSecondaryContextForCharacter12004(
    const ConceptionSecondaryContext12004Bindings &bindings,
    std::uintptr_t character, std::uint32_t expected_full_id) noexcept;

// Native relation route: first true skips the second predicate entirely.
// Unknown first stays unknown even if the second input is known true.
std::optional<bool> SelectConceptionSecondaryRelationPath12004(
    std::optional<bool> first, std::optional<bool> second) noexcept;

} // namespace xar::ck3_12004
