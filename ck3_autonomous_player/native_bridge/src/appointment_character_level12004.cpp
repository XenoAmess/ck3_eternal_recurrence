#include "xar_bridge/appointment_character_level12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/appointment_window_snapshot_v1.hpp"
#include <algorithm>
#include <array>
#include <limits>

namespace xar::ck3_12004 {
namespace {
using Access = ck3_11906::AppointmentWindowAccessV1;
constexpr std::string_view kExe =
    xar::ck3_12004::kExecutableSha256;
// Actual4 28BE1D0 leaf, selected by320F4B6 and320EE0D type0 branches.
constexpr std::uintptr_t kThresholdData = 0x5458818;
constexpr std::uintptr_t kThresholdCount = 0x5458824;
// Actual4 320D38C→320D393, indexed by Title.template+64 tier.
constexpr std::uintptr_t kType0TierFloorData = 0x5461660;

template<class T> bool Read(const Access &a, std::uintptr_t p, T &v) noexcept {
  return p != 0 && a.read && a.read(a.context, p, &v, sizeof(v));
}
bool ResolveCharacter(const Access &a, std::uint32_t id,
                      std::uintptr_t &object) noexcept {
  if (id == std::numeric_limits<std::uint32_t>::max()) return false;
  std::uintptr_t storage = 0, slots = 0;
  std::uint32_t capacity = 0, full_id = 0;
  const auto index = id & 0x00FFFFFFU;
  return Read(a, a.module_base + 0x5C67568, storage) && storage &&
      Read(a, storage + 0x20, slots) && slots &&
      Read(a, storage + 0x2C, capacity) && index < capacity &&
      Read(a, slots + std::uintptr_t(index) * 0x10 + 8, object) && object &&
      Read(a, object + 0x18, full_id) && full_id == id;
}
struct Sample {
  std::uintptr_t character = 0, extension = 0, threshold_data = 0;
  std::uintptr_t title_template = 0, floor_data = 0;
  std::uint32_t title_id = 0, character_id = 0;
  std::uint8_t ordinal = 0, allowed_tier_ordinal = 0;
  std::int32_t candidate_tier = 0;
  std::array<std::uintptr_t, 7> candidate_tier_pointers{};
  std::uint32_t candidate_title_count = 0, candidate_title_id = 0;
  std::int32_t count = 0, cap = -1, tier = 0, floor = 0, level = 0;
  std::int64_t accumulated = 0;
  std::array<std::int64_t, 256> thresholds{};
  friend bool operator==(const Sample &, const Sample &) = default;
};
// Actual4 28AC690..28AC71C is a call-free, read-only tier getter.
// Guarded decoding preserves its cached-tier and first-full-title paths.
// Unlike its sentinel-title fallback, unresolved/stale title IDs stay unknown.
bool CaptureCandidateTier(const Access &a, Sample &s) noexcept {
  auto &p = s.candidate_tier_pointers;
  if (!Read(a, s.character + 0x1C0, p[0])) return false;
  if (p[0]) {
    if (!Read(a, p[0] + 0x1D4, s.candidate_tier)) return false;
    if (s.candidate_tier != 7)
      return s.candidate_tier >= 0 && s.candidate_tier <= 6;
    if (!Read(a, p[0] + 0x1EC, s.candidate_title_count) ||
        !s.candidate_title_count || !Read(a, p[0] + 0x1E0, p[1])) return false;
  } else {
    if (!Read(a, s.character + 0x1D0, p[0])) return false;
    if (!p[0]) { s.candidate_tier = 0; return true; }
    if (!Read(a, p[0] + 0x74, s.candidate_title_count) ||
        !s.candidate_title_count || !Read(a, p[0] + 0x68, p[1])) return false;
  }
  if (!p[1] || !Read(a, p[1], s.candidate_title_id) ||
      s.candidate_title_id == std::numeric_limits<std::uint32_t>::max()) return false;
  std::uint32_t capacity = 0, full_id = 0;
  const auto index = s.candidate_title_id & 0x00FFFFFFU;
  if (!Read(a, a.module_base + 0x5D1DAF8, p[2]) || !p[2] ||
      !Read(a, p[2] + 0x20, p[3]) || !p[3] ||
      !Read(a, p[2] + 0x2C, capacity) || index >= capacity ||
      !Read(a, p[3] + std::uintptr_t(index) * 0x10 + 8, p[4]) || !p[4] ||
      !Read(a, p[4] + 0x10, full_id) || full_id != s.candidate_title_id ||
      !Read(a, p[4] + 0x48, p[5]) || !p[5] ||
      !Read(a, p[5] + 0x64, s.candidate_tier)) return false;
  return s.candidate_tier >= 0 && s.candidate_tier <= 6;
}
bool Capture(const Access &a, std::uintptr_t rule, std::uintptr_t title,
             std::uint32_t title_id, std::uint32_t character_id,
             Sample &s) noexcept {
  if (!ResolveCharacter(a, character_id, s.character) ||
      !Read(a, s.character + 0x18, s.character_id) ||
      !Read(a, title + 0x10, s.title_id) || s.title_id != title_id ||
      !Read(a, rule + 0x148, s.ordinal) || s.ordinal != 0 ||
      !Read(a, rule + 0x149, s.allowed_tier_ordinal) ||
      !CaptureCandidateTier(a, s) ||
      !Read(a, title + 0x48, s.title_template) || !s.title_template ||
      !Read(a, s.title_template + 0x64, s.tier) || s.tier < 0 || s.tier > 6 ||
      !Read(a, a.module_base + kType0TierFloorData, s.floor_data) || !s.floor_data ||
      !Read(a, s.floor_data + std::uintptr_t(s.tier) * 4, s.floor) ||
      !Read(a, s.character + 0x1B0, s.extension)) return false;
  // The actual leaf returns0 when its extension load yields null.
  if (!s.extension) return true;
  if (!Read(a, s.extension + 0x178, s.accumulated) ||
      !Read(a, s.extension + 0x180, s.cap) ||
      !Read(a, a.module_base + kThresholdCount, s.count) || s.count > 256 ||
      !Read(a, a.module_base + kThresholdData, s.threshold_data) ||
      (s.count > 0 && !s.threshold_data)) return false;
  for (std::int32_t i = 0; i < s.count; ++i) {
    if (!Read(a, s.threshold_data + std::uintptr_t(i) * 8,
              s.thresholds[static_cast<std::size_t>(i)])) return false;
  }
  while (s.level < s.count && s.accumulated >=
         s.thresholds[static_cast<std::size_t>(s.level)]) ++s.level;
  if (s.cap >= 0) s.level = (std::min)(s.level, s.cap);
  return true;
}
}

bool ReadAppointmentCharacterLevel12004(
    const Access &a, std::string_view admitted_sha,
    std::uintptr_t rule, std::uintptr_t title,
    std::uint32_t title_id, std::uint32_t character_id,
    AppointmentCharacterLevel12004 &out) noexcept {
  out = {};
  out.character_id = character_id;
  out.title_id = title_id;
  if (admitted_sha != kExe || !a.module_base || !rule || !title || !a.read) {
    out.unavailable_reason = "exact4_current_rule_lease_required";
    return false;
  }
  std::uint8_t ordinal = 0, ordinal_later = 0;
  if (!Read(a, rule + 0x148, ordinal) ||
      !Read(a, rule + 0x148, ordinal_later) || ordinal != ordinal_later) {
    out.unavailable_reason = "appointment_level_source_ordinal_unverified";
    return false;
  }
  out.native_level_source_ordinal_available = true;
  out.native_level_source_ordinal = ordinal;
  if (ordinal != 0) {
    out.unavailable_reason = "appointment_level_source_ordinal_not_supported";
    return false;
  }
  Sample first{}, second{};
  if (!Capture(a, rule, title, title_id, character_id, first) ||
      !Capture(a, rule, title, title_id, character_id, second)) {
    out.unavailable_reason = "native_type0_level_fields_unavailable";
    return false;
  }
  if (first != second) {
    out.unavailable_reason = "native_type0_level_fields_changed";
    return false;
  }
  out.available = true;
  out.unavailable_reason = {};
  out.character_id = character_id;
  out.title_id = title_id;
  out.native_level_source_ordinal = first.ordinal;
  out.resource_extension_present = first.extension != 0;
  out.accumulated_raw = first.accumulated;
  out.level_cap_raw = first.cap;
  out.native_level = first.level;
  out.title_tier = first.tier;
  out.required_native_level = first.floor;
  out.meets_native_level_floor = first.level >= first.floor;
  out.current_rule_allowed_candidate_tier_ordinal = first.allowed_tier_ordinal;
  out.candidate_tier = first.candidate_tier;
  return true;
}
}
