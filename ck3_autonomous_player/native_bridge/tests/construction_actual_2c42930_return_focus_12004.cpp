#include "construction_actual_2c42930_return_focus_12004.hpp"

#include "xar_bridge/construction_actual_2c42930_return_12004.hpp"

#include <cstring>
#include <map>
#include <vector>

namespace xar::ck3_12004::focus {
namespace {

using namespace construction_owner_mode3;
constexpr std::uintptr_t kModule = 0x10000000;
constexpr std::uintptr_t kTitle = 0x20000000;
constexpr std::uintptr_t kRegistry = 0x30000000;
constexpr std::uintptr_t kTable = 0x40000000;
constexpr std::uintptr_t kCandidate = 0x50000000;
constexpr std::uintptr_t kFallback = 0x60000000;
constexpr std::uint32_t kId = 0xF1000002u;
const char *g_failure = nullptr;
std::uint32_t g_cases = 0;

struct Scene {
  std::map<std::uintptr_t, std::vector<unsigned char>> fields;
  std::vector<std::uintptr_t> reads;
  std::uint32_t child_out = kId;
  bool child_available = true;
  std::uint32_t child_calls = 0;
  std::uintptr_t child_title = 0;

  template <typename T>
  void Put(std::uintptr_t address, T value) {
    std::vector<unsigned char> bytes(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
    fields[address] = bytes;
  }

  void Match(std::uint32_t id = kId) {
    child_out = id;
    Put(kModule + 0x5C67568, kRegistry);
    Put(kRegistry + 0x2C, (id & 0x00FFFFFFu) + 1u);
    Put(kRegistry + 0x20, kTable);
    Put(kTable + static_cast<std::uintptr_t>(id & 0x00FFFFFFu) * 16 + 8,
        kCandidate);
    Put(kCandidate + 0x18, id);
    // Title+128, fallback global and candidate magic are deliberately absent.
  }

  bool ReadSeen(std::uintptr_t address) const noexcept {
    for (const auto read : reads) if (read == address) return true;
    return false;
  }

  static bool Read(void *context, const void *source, void *destination,
                   std::size_t size) {
    auto &scene = *static_cast<Scene *>(context);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    scene.reads.push_back(address);
    const auto found = scene.fields.find(address);
    if (found == scene.fields.end() || found->second.size() != size)
      return false;
    std::memcpy(destination, found->second.data(), size);
    return true;
  }

  static bool Child(void *context, std::uintptr_t title,
                    std::uint32_t &out) noexcept {
    auto &scene = *static_cast<Scene *>(context);
    ++scene.child_calls;
    scene.child_title = title;
    if (!scene.child_available) return false;
    out = scene.child_out;
    return true;
  }

  RawTitleReturnAccessV1 Access() noexcept {
    return {this, Read, kModule, true, this, Child};
  }
};

bool Check(const char *label, bool passed) noexcept {
  ++g_cases;
  if (!passed) g_failure = label;
  return passed;
}

bool IsMatched(const ActualTitleReturnV1 &result, std::uint32_t id) noexcept {
  return result.observed && result.failure == ActualTitleReturnFailureV1::none &&
      result.route == ActualTitleReturnRouteV1::character_registry &&
      result.returned_pointer == kCandidate &&
      result.requested_full_id_observed && result.requested_full_id_u32 == id &&
      result.candidate_full_id_observed && result.candidate_full_id_u32 == id &&
      !result.used_character_fallback;
}

bool IsFallback(const ActualTitleReturnV1 &result,
                ActualTitleReturnFallbackV1 branch,
                std::uintptr_t pointer = kFallback) noexcept {
  return result.observed && result.failure == ActualTitleReturnFailureV1::none &&
      result.route == ActualTitleReturnRouteV1::character_fallback &&
      result.fallback == branch && result.used_character_fallback &&
      result.returned_pointer == pointer;
}

} // namespace

bool RunActual2C42930ReturnFocus12004() noexcept {
  g_failure = nullptr;
  g_cases = 0;
  {
    Scene s;
    s.Match();
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("high_generation_exact_match_lazy_fields",
               IsMatched(r, kId) && s.child_calls == 1 &&
               s.child_title == kTitle &&
               !s.ReadSeen(kTitle + 0x128) &&
               !s.ReadSeen(kModule + 0x5C67570))) return false;
  }
  {
    Scene s;
    s.Match(0);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("zero_raw_id_has_no_extra_gate", IsMatched(r, 0))) return false;
  }
  {
    Scene s;
    s.Match();
    s.child_out = 0xFFFFFFFFu;
    s.Put(kTitle + 0x128, kId);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("child_sentinel_substitutes_title128_only",
               IsMatched(r, kId) && r.used_title_128_fallback &&
               r.child_out_observed && r.child_out_full_id_u32 == 0xFFFFFFFFu &&
               s.ReadSeen(kTitle + 0x128))) return false;
  }
  {
    Scene s;
    s.Match(0xFFFFFFFFu);
    s.Put(kTitle + 0x128, 0xFFFFFFFFu);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("title128_all_ones_remains_raw_registry_id",
               IsMatched(r, 0xFFFFFFFFu) &&
               r.registry_index_u32 == 0x00FFFFFFu)) return false;
  }
  {
    Scene s;
    s.Put(kModule + 0x5C67568, std::uintptr_t{0});
    s.Put(kModule + 0x5C67570, std::uintptr_t{0});
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("registry_null_returns_observed_null_fallback",
               IsFallback(r, ActualTitleReturnFallbackV1::registry_null, 0) &&
               !r.registry_count_observed && !s.ReadSeen(kTitle + 0x128)))
      return false;
  }
  {
    Scene s;
    s.Put(kModule + 0x5C67568, kRegistry);
    s.Put(kRegistry + 0x2C, std::uint32_t{2});
    s.Put(kModule + 0x5C67570, kFallback);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("unsigned_count_boundary_skips_table",
               IsFallback(r, ActualTitleReturnFallbackV1::index_out_of_range) &&
               !s.ReadSeen(kRegistry + 0x20))) return false;
  }
  {
    Scene s;
    s.Match();
    s.Put(kTable + 2 * 16 + 8, std::uintptr_t{0});
    s.Put(kModule + 0x5C67570, kFallback);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("candidate_null_fallback_without_identity_read",
               IsFallback(r, ActualTitleReturnFallbackV1::candidate_null) &&
               !r.candidate_full_id_observed &&
               !s.ReadSeen(kCandidate + 0x18))) return false;
  }
  {
    Scene s;
    s.Match();
    s.Put(kCandidate + 0x18, std::uint32_t{0xE1000002u});
    s.Put(kModule + 0x5C67570, kFallback);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("same_low24_generation_mismatch_falls_back",
               IsFallback(r, ActualTitleReturnFallbackV1::generation_mismatch) &&
               r.candidate_full_id_observed &&
               r.candidate_full_id_u32 != r.requested_full_id_u32)) return false;
  }
  {
    Scene s;
    s.Put(kModule + 0x5C67568, kRegistry);
    s.Put(kModule + 0x5C67570, kFallback);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("missing_count_is_unknown_without_fallback_read",
               !r.observed && r.failure == ActualTitleReturnFailureV1::registry_count &&
               !r.registry_count_observed && !r.used_character_fallback &&
               !s.ReadSeen(kModule + 0x5C67570))) return false;
  }
  {
    Scene s;
    s.Match();
    s.Put(kRegistry + 0x20, std::uintptr_t{0});
    s.Put(kModule + 0x5C67570, kFallback);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("table_null_is_not_a_native_fallback_branch",
               !r.observed && r.failure == ActualTitleReturnFailureV1::registry_candidate &&
               r.registry_table_observed && !r.registry_candidate_observed &&
               !s.ReadSeen(kModule + 0x5C67570))) return false;
  }
  {
    Scene s;
    s.Match();
    s.fields.erase(kCandidate + 0x18);
    s.Put(kModule + 0x5C67570, kFallback);
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("unreadable_generation_is_unknown_without_fallback",
               !r.observed && r.failure == ActualTitleReturnFailureV1::candidate_identity &&
               !r.candidate_full_id_observed &&
               !s.ReadSeen(kModule + 0x5C67570))) return false;
  }
  {
    Scene s;
    s.Put(kModule + 0x5C67568, std::uintptr_t{0});
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("missing_fallback_pointer_is_unknown",
               !r.observed && r.failure == ActualTitleReturnFailureV1::fallback_global &&
               r.fallback == ActualTitleReturnFallbackV1::registry_null &&
               r.used_character_fallback &&
               r.route == ActualTitleReturnRouteV1::unavailable)) return false;
  }
  {
    Scene s;
    s.child_available = false;
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("missing_child_out_is_not_a_sentinel",
               !r.observed && r.failure == ActualTitleReturnFailureV1::child_out &&
               !r.child_out_observed && !r.used_title_128_fallback &&
               s.child_calls == 1 && s.reads.empty())) return false;
  }
  {
    Scene s;
    auto access = s.Access();
    access.exact_12004_bound = false;
    const auto r = ReadActual2C42930ReturnV1(access, kTitle);
    if (!Check("unbound_build_does_not_consume_inputs",
               !r.observed && r.failure == ActualTitleReturnFailureV1::exact_build &&
               s.child_calls == 0 && s.reads.empty())) return false;
  }
  {
    Scene s;
    s.child_out = 0xFFFFFFFFu;
    const auto r = ReadActual2C42930ReturnV1(s.Access(), kTitle);
    if (!Check("unreadable_title128_stays_unknown",
               !r.observed && r.failure == ActualTitleReturnFailureV1::title_128 &&
               r.child_out_observed && r.used_title_128_fallback &&
               !r.requested_full_id_observed &&
               !s.ReadSeen(kModule + 0x5C67568))) return false;
  }
  return g_cases == 15 && g_failure == nullptr;
}

const char *GetActual2C42930ReturnFocusFailure12004() noexcept {
  return g_failure;
}

std::uint32_t GetActual2C42930ReturnFocusCases12004() noexcept {
  return g_cases;
}

} // namespace xar::ck3_12004::focus
