#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <optional>
#include <string>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::religion::holy_order {

struct HireCostContextBindings {
  void **title_registry_slot = nullptr;
  void **title_fallback_slot = nullptr;
  const std::int64_t *patron_hire_multiplier_raw = nullptr;
  const std::int64_t *patron_recall_multiplier_raw = nullptr;
};

struct HireCostContext {
  bool available = false;
  std::string unavailable_reason = "native_hire_cost_context_binding_unavailable";
  std::optional<std::uint32_t> order_title_id;
  bool order_title_resolved = false;
  // Effective holder includes the same native fallback used by26198E0.
  std::optional<std::uint32_t> order_title_holder_id;
  std::optional<bool> title_holder_is_player;
  std::optional<bool> patron_is_player;
  std::optional<bool> employed_by_other;
  std::optional<std::string> cost_branch;
  std::optional<std::int64_t> selected_patron_multiplier_raw;
};

namespace hire_cost_detail {
template <typename T>
inline bool Read(const void *object, std::size_t offset, T &value) noexcept {
  if (object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
inline bool Patron(void *(*fn)(void *), void *order, void *&result) noexcept {
  if (fn == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    result = fn(order);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
} // namespace hire_cost_detail

// A readonly source projection of26198E0 and the patron prefix of2619980.
// It does not calculate the final quote or alter final CanHire/CanAfford.
inline HireCostContext ReadHireCostContext12003(const HireCostContextBindings &b,
    void *order, void *player, void *(*native_patron)(void *)) {
  using hire_cost_detail::Read;
  HireCostContext out;
  if (b.title_registry_slot == nullptr || b.title_fallback_slot == nullptr) return out;
  out.unavailable_reason = "native_hire_cost_context_title_unavailable";
  std::uint32_t title_id = UINT32_MAX, actor_id = UINT32_MAX;
  if (!Read(order, 0x28, title_id) || !Read(player, 0x18, actor_id)) return out;
  out.order_title_id = title_id;
  void *registry = nullptr, *title = nullptr;
  if (!Read(b.title_registry_slot, 0, registry)) return out;
  if (registry != nullptr) {
    std::int32_t bound = -1;
    if (!Read(registry, 0x2C, bound) || bound < 0) return out;
    const auto index = title_id & 0x00FFFFFFU;
    if (index < static_cast<std::uint32_t>(bound)) {
      const void *entries = nullptr;
      if (!Read(registry, 0x20, entries) || entries == nullptr ||
          !Read(entries, static_cast<std::size_t>(index) * 0x10 + 8, title)) return out;
      if (title != nullptr) {
        std::uint32_t actual_id = UINT32_MAX;
        if (!Read(title, 0x10, actual_id)) return out;
        if (actual_id != title_id) title = nullptr;
      }
    }
  }
  out.order_title_resolved = title != nullptr;
  if (title == nullptr && !Read(b.title_fallback_slot, 0, title)) return out;
  std::uint32_t holder = UINT32_MAX;
  if (!Read(title, 0x128, holder)) return out;
  if (holder != UINT32_MAX) out.order_title_holder_id = holder;
  out.title_holder_is_player = holder == actor_id;
  if (*out.title_holder_is_player) {
    //2619935 zeros the ten-resource quote and returns before patron work.
    out.cost_branch = "title_holder_zero";
    out.available = true;
    out.unavailable_reason.clear();
    return out;
  }
  out.unavailable_reason = "native_hire_cost_context_patron_unavailable";
  void *patron = nullptr;
  if (!hire_cost_detail::Patron(native_patron, order, patron)) return out;
  out.patron_is_player = patron == player;
  if (!*out.patron_is_player) {
    out.cost_branch = "ordinary";
    out.available = true;
    out.unavailable_reason.clear();
    return out;
  }
  std::uint32_t employer = UINT32_MAX;
  out.unavailable_reason = "native_hire_cost_context_employer_unavailable";
  if (!Read(order, 0x80, employer)) return out;
  out.employed_by_other = employer != UINT32_MAX && employer != actor_id;
  out.cost_branch = *out.employed_by_other ? "patron_recall" : "patron_hire";
  const auto *multiplier = *out.employed_by_other ? b.patron_recall_multiplier_raw
                                                : b.patron_hire_multiplier_raw;
  out.unavailable_reason = "native_hire_cost_context_multiplier_unavailable";
  std::int64_t raw = 0;
  if (!Read(multiplier, 0, raw)) return out;
  out.selected_patron_multiplier_raw = raw;
  out.available = true;
  out.unavailable_reason.clear();
  return out;
}

} // namespace xar::ck3_12003::religion::holy_order
