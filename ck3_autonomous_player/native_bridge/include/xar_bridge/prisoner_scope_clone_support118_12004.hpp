#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"
#include "xar_bridge/prisoner_support_predicate_3727580_readonly_12004.hpp"
#include <array>
#include <cstring>
#include <span>
#include <type_traits>

#define XAR_HAS_PRISONER_SCOPE_CLONE_SUPPORT118_12004 1

namespace xar::ck3_12004 {
inline constexpr std::size_t kPrisonerScopeCloneSupport118Bytes12004 = 0x50;

struct PrisonerScopeCloneSupport118Source12004 {
  PrisonerQuoteSourceFrame12004 frame{};
  std::optional<std::uintptr_t> original_source_support_identity;
  std::optional<std::uintptr_t> source_vector10_data, source_vector30_data;
  std::optional<std::int32_t> source_vector10_count, source_vector30_count;
  std::optional<std::uint32_t> source_scalar28_raw_u32;
  std::array<std::uint8_t, kPrisonerScopeCloneSupport118Bytes12004> raw{}, defined{};
  // These identities remain original input provenance. An empty ordered input
  // list is qualified only by an actual read count0, never by array defaults.
  std::optional<std::vector<std::uintptr_t>> ordered_source_vector10_elements;
  std::optional<std::vector<std::uintptr_t>> ordered_source_vector30_elements;
  std::optional<std::uint8_t> final_predicate_al_raw_u8;
  std::optional<std::uintptr_t> physical_cloned_support_identity;
  bool returned_fields_source_ready = false;
  bool native_copy_called = false;
  std::string unavailable_reason;
};

namespace prisoner_scope_clone_support118_detail {
template<class T> inline void Number(
    std::array<std::uint8_t, kPrisonerScopeCloneSupport118Bytes12004> &raw,
    std::array<std::uint8_t, kPrisonerScopeCloneSupport118Bytes12004> &defined,
    std::size_t offset, T value) noexcept {
  static_assert(std::is_integral_v<T>);
  std::memcpy(raw.data() + offset, &value, sizeof(value));
  for (std::size_t i = offset; i < offset + sizeof(value); ++i) defined[i] = 1;
}
inline bool RequiredDefined(
    const std::array<std::uint8_t, kPrisonerScopeCloneSupport118Bytes12004> &defined) noexcept {
  for (std::size_t i = 0; i < 0x2C; ++i) if (defined[i] != 1) return false;
  for (std::size_t i = 0x30; i < 0x4F; ++i) if (defined[i] != 1) return false;
  return true;
}
} // namespace prisoner_scope_clone_support118_detail

// Source-defined fresh destination member of actual373ACF0, reached through
// 373ADBD ->3727180. This reads the caller's original scope once in its current
// quote frame. It does not call a copy, allocator, destructor or registration.
// Both source counts0 close the returned fields through17/48/40/20 contracts.
// Nonempty and negative source paths retain their explicit postcopy frontier.
inline PrisonerScopeCloneSupport118Source12004 ReadPrisonerScopeCloneSupport11812004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame) {
  using namespace prisoner_scope_clone_support118_detail;
  PrisonerScopeCloneSupport118Source12004 out; out.frame = frame;
  constexpr auto max_address = (std::numeric_limits<std::uintptr_t>::max)();
  if (!PrisonerQuoteSourceFrameReady12004(frame) ||
      frame.interaction_context_identity > max_address - 8 ||
      frame.original_scope_identity != frame.interaction_context_identity + 8 ||
      frame.original_scope_identity > max_address - 0x118 ||
      frame.module_base > max_address - 0x54DE278) {
    out.unavailable_reason = "support_original_scope_or_current_frame_unavailable"; return out;
  }
  const auto source = frame.original_scope_identity + 0x118;
  out.original_source_support_identity = source;
  out.source_vector10_data = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, source, 0x10);
  out.source_vector10_count = ReadPrisonerQuoteSource12004<std::int32_t>(access, source, 0x1C);
  out.source_scalar28_raw_u32 = ReadPrisonerQuoteSource12004<std::uint32_t>(access, source, 0x28);
  out.source_vector30_data = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, source, 0x30);
  out.source_vector30_count = ReadPrisonerQuoteSource12004<std::int32_t>(access, source, 0x3C);
  if (!out.source_vector10_data || !out.source_vector10_count || !out.source_scalar28_raw_u32 ||
      !out.source_vector30_data || !out.source_vector30_count) {
    out.unavailable_reason = "support_original_copy_fields_read_unavailable"; return out;
  }
  if (*out.source_vector10_count < 0 || *out.source_vector30_count < 0) {
    out.unavailable_reason = "support_negative_source_count_path_unclosed"; return out;
  }
  if (*out.source_vector10_count != 0 || *out.source_vector30_count != 0) {
    out.unavailable_reason = "support_nonempty_copy_poststate_unavailable"; return out;
  }

  // Local proposed shape becomes a returned shape only after the exact final
  // predicate and20's equality/noqueue branch. Unwritten padding stays unknown.
  std::array<std::uint8_t, kPrisonerScopeCloneSupport118Bytes12004> raw{}, defined{};
  Number(raw, defined, 0x00, static_cast<std::uint64_t>(frame.module_base + 0x448D1F8));
  Number(raw, defined, 0x08, static_cast<std::uint64_t>(frame.module_base + 0x448D268));
  Number(raw, defined, 0x10, std::uint64_t{0});
  Number(raw, defined, 0x18, std::uint32_t{0});
  Number(raw, defined, 0x1C, std::int32_t{0});
  Number(raw, defined, 0x20, static_cast<std::uint64_t>(frame.module_base + 0x54DE278));
  Number(raw, defined, 0x28, *out.source_scalar28_raw_u32);
  Number(raw, defined, 0x30, std::uint64_t{0});
  Number(raw, defined, 0x38, std::uint32_t{0});
  Number(raw, defined, 0x3C, std::int32_t{0});
  Number(raw, defined, 0x40, static_cast<std::uint64_t>(frame.module_base + 0x54DE270));
  Number(raw, defined, 0x48, std::int32_t{-1});
  Number(raw, defined, 0x4C, std::uint16_t{0});
  Number(raw, defined, 0x4E, std::uint8_t{0});
  const auto predicate = ProjectPrisonerSupportPredicate3727580FreshEmpty12004(
      std::span<const std::uint8_t>(raw), std::span<const std::uint8_t>(defined));
  out.final_predicate_al_raw_u8 = predicate.al_raw_u8;
  if (!predicate.al_raw_u8 || *predicate.al_raw_u8 != 0 || !RequiredDefined(defined)) {
    out.unavailable_reason = "support_final_predicate_or_defined_fields_unavailable"; return out;
  }
  // SETNE(-1,-1)=0 equals actual AL0:3727EC0 returns without queue or field writes.
  out.raw = raw; out.defined = defined;
  out.ordered_source_vector10_elements.emplace();
  out.ordered_source_vector30_elements.emplace();
  out.returned_fields_source_ready = true;
  return out;
}
} // namespace xar::ck3_12004
