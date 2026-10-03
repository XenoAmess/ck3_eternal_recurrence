#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12003 {
inline constexpr std::uintptr_t kMercenaryTitleProvinceRvaV1 = 0x230F900;
inline constexpr std::uintptr_t kMercenaryHireRaiseSelectorRvaV1 = 0x24A6AB0;

struct MercenaryPositionBindingsV1 {
  // Exact .3 native leaves. Neither submits nor mutates a company/army.
  const void *(*get_title_province)(const void *) = nullptr;
  std::int32_t (*select_hire_raise_province)(const void *) = nullptr;
};
struct MercenaryPositionWorldV1 {
  void *context = nullptr;
  bool (*read_memory)(void *, const void *, void *, std::size_t) = nullptr;
  const void *(*resolve_title)(void *, std::int32_t) = nullptr;
  const void *(*resolve_province)(void *, std::int32_t) = nullptr;
};
struct MercenaryPositionObservationV1 {
  std::optional<std::int32_t> company_home_title_id;
  std::optional<std::int32_t> company_home_province_id;
  bool company_home_ready = false;
  std::string_view company_home_failure = "not_read";
  std::string_view company_home_source = "native_company_title_location";
  std::optional<std::int32_t> hire_auto_raise_province_id;
  std::optional<std::int32_t> actor_active_war_count;
  std::optional<bool> hire_auto_raise_attempted_in_active_war;
  bool hire_auto_raise_position_ready = false;
  std::string_view hire_auto_raise_position_failure = "not_read";
  std::string_view hire_auto_raise_position_source =
      "native_hire_auto_raise_selector";
};

// Owner thread; current paused actor/company already resolved by caller.
// The selector's output predicts the current normal Hire auto-raise location,
// not an army allocation or guaranteed spawn. No command is constructed/sent.
bool ReadMercenaryPositionV1(const MercenaryPositionBindingsV1 &,
    const MercenaryPositionWorldV1 &, const void *actor, const void *company,
    MercenaryPositionObservationV1 &) noexcept;
} // namespace xar::ck3_12003
