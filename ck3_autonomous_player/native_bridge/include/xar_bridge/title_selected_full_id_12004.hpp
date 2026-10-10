#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kTitleSelectedFullIdEntry12004 = 0x2C42820;

struct TitleSelectedFullIdAccess12004 {
  void *context = nullptr;
  bool (*read_memory)(void *, std::uintptr_t, void *, std::size_t) noexcept = nullptr;
  std::uintptr_t module_base = 0;
  bool exact_12004_bound = false;
};

enum class TitleSelectedFullIdBranch12004 : std::uint8_t {
  unobserved,
  flag_nonzero_character_link,
  flag_zero_title_reference,
};

// Only values read by the actual2C42820 path are copied. In particular, the
// fallback object's full ID is not queried when native code does not read it.
struct TitleSelectedFullIdSource12004 {
  std::uintptr_t original_title_identity = 0;
  std::optional<std::uint8_t> title_flag_130;
  TitleSelectedFullIdBranch12004 branch = TitleSelectedFullIdBranch12004::unobserved;
  std::optional<std::uint32_t> requested_full_id;
  std::optional<std::uintptr_t> selected_object_identity;
  std::optional<std::uint32_t> checked_selected_full_id;
  std::optional<bool> used_fallback;
  std::optional<std::uintptr_t> selected_link_identity;
  std::optional<std::uint32_t> output_full_id;
  bool source_complete = false;
};

// Copies the actual selected Title -> output32 loads without invoking CK3.
// False preserves out_full_id. FFFFFFFF is a successful raw source value;
// the caller2C42930 owns its substitution with originalTitle+128.
bool ReadTitleSelectedFullId12004(
    const TitleSelectedFullIdAccess12004 &access, std::uintptr_t title,
    std::uint32_t &out_full_id,
    TitleSelectedFullIdSource12004 *source = nullptr) noexcept;

// The context is a pointer to a live TitleSelectedFullIdAccess12004. This
// matches38d's readonly child callback without a shared type dependency.
bool ReadTitleSelectedFullIdAdapter12004(
    void *context, std::uintptr_t title, std::uint32_t &out_full_id) noexcept;

} // namespace xar::ck3_12004
