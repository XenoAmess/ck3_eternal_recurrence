#pragma once

// Private traversal implementation shared only by the fixed war-window
// provider and its standalone fixture. No GUI expression or action is called.
#include <cstddef>
#include <cstdint>
#include <set>
#include <string_view>
#include <vector>

namespace xar::ck3_11906::detail {

inline constexpr std::size_t kWarDeclaredOwnerMaximumWidgetsV1 = 262'144;
inline constexpr std::size_t kWarDeclaredOwnerMaximumEdgesV1 = 1'048'576;

enum class WarDeclaredOwnerReadFailureV1 : std::uint8_t {
  none, reader_unavailable, invalid_budget, owner_root_missing,
  widget_runtime_unreadable, duplicate_named_window,
  child_vector_unreadable, child_count_unreadable, negative_child_count,
  child_count_exceeds_widget_budget, edge_budget_exhausted,
  child_vector_missing, child_address_overflow, child_slot_unreadable,
  child_slot_null, widget_budget_exhausted, duplicate_child,
  storage_or_callback_failure,
};

inline constexpr std::string_view WarDeclaredOwnerFailureNameV1(
    WarDeclaredOwnerReadFailureV1 value) noexcept {
  using F = WarDeclaredOwnerReadFailureV1;
  switch (value) {
  case F::none: return "none";
  case F::reader_unavailable: return "reader_unavailable";
  case F::invalid_budget: return "invalid_budget";
  case F::owner_root_missing: return "owner_root_missing";
  case F::widget_runtime_unreadable: return "widget_runtime_unreadable";
  case F::duplicate_named_window: return "duplicate_named_window";
  case F::child_vector_unreadable: return "child_vector_unreadable";
  case F::child_count_unreadable: return "child_count_unreadable";
  case F::negative_child_count: return "negative_child_count";
  case F::child_count_exceeds_widget_budget: return "child_count_exceeds_widget_budget";
  case F::edge_budget_exhausted: return "edge_budget_exhausted";
  case F::child_vector_missing: return "child_vector_missing";
  case F::child_address_overflow: return "child_address_overflow";
  case F::child_slot_unreadable: return "child_slot_unreadable";
  case F::child_slot_null: return "child_slot_null";
  case F::widget_budget_exhausted: return "widget_budget_exhausted";
  case F::duplicate_child: return "duplicate_child";
  case F::storage_or_callback_failure: return "storage_or_callback_failure";
  }
  return "unknown_read_failure";
}

struct WarDeclaredOwnerReadCallbacksV1 {
  const void *context = nullptr;
  WarDeclaredOwnerReadFailureV1 (*runtime)(
      const void *, std::uintptr_t, bool &, bool &) noexcept = nullptr;
  WarDeclaredOwnerReadFailureV1 (*children)(
      const void *, std::uintptr_t, std::uintptr_t &, std::int32_t &) noexcept = nullptr;
  WarDeclaredOwnerReadFailureV1 (*child)(
      const void *, std::uintptr_t, std::uint32_t, std::uintptr_t &) noexcept = nullptr;
};

struct WarDeclaredOwnerReadBudgetV1 {
  std::size_t widgets = kWarDeclaredOwnerMaximumWidgetsV1;
  std::size_t edges = kWarDeclaredOwnerMaximumEdgesV1;
};

struct WarDeclaredOwnerReadResultV1 {
  bool complete = false;
  std::uintptr_t target = 0;
  bool target_visible = false;
  WarDeclaredOwnerReadFailureV1 failure = WarDeclaredOwnerReadFailureV1::none;
  std::size_t at = 0, queued = 0, visited = 0, edges = 0, matches = 0;
  std::int32_t child_count = 0, child_index = -1;
};

// Budget may be reduced by a fixture, never enlarged beyond the fixed native
// maxima. Production supplies the defaults. A target is published only after
// every reachable widget/edge passes; an early match gives no partial credit.
inline bool ReadWarDeclaredOwnerTreeV1(
    std::uintptr_t root, const WarDeclaredOwnerReadCallbacksV1 &read,
    WarDeclaredOwnerReadResultV1 &out,
    WarDeclaredOwnerReadBudgetV1 budget = {}) noexcept {
  using F = WarDeclaredOwnerReadFailureV1;
  out = {};
  const auto fail = [&](F why) noexcept {
    out.failure = why;
    out.complete = false;
    out.target = 0;
    out.target_visible = false;
    return false;
  };
  if (!read.runtime || !read.children || !read.child)
    return fail(F::reader_unavailable);
  if (!budget.widgets || budget.widgets > kWarDeclaredOwnerMaximumWidgetsV1 ||
      !budget.edges || budget.edges > kWarDeclaredOwnerMaximumEdgesV1)
    return fail(F::invalid_budget);
  if (!root) return fail(F::owner_root_missing);
  try {
    // Both containers are heap-backed and hold at most budget.widgets items.
    // std::set gives bounded O(log N) membership, including collision-free
    // worst-case behavior; no whole-prefix std::find or unbounded hash growth.
    std::vector<std::uintptr_t> pending;
    pending.reserve(budget.widgets);
    std::set<std::uintptr_t> seen;
    pending.push_back(root);
    seen.insert(root);
    out.queued = 1;
    std::uintptr_t found = 0;
    bool found_visible = false;
    for (std::size_t at = 0; at < pending.size(); ++at) {
      out.at = at;
      out.child_count = 0;
      out.child_index = -1;
      bool target = false, visible = false;
      auto failure = read.runtime(read.context, pending[at], target, visible);
      if (failure != F::none) return fail(failure);
      ++out.visited;
      if (target) {
        if (++out.matches != 1) return fail(F::duplicate_named_window);
        found = pending[at];
        found_visible = visible;
      }
      std::uintptr_t children = 0;
      failure = read.children(read.context, pending[at], children, out.child_count);
      if (failure != F::none) return fail(failure);
      if (out.child_count < 0) return fail(F::negative_child_count);
      const auto count = static_cast<std::size_t>(out.child_count);
      if (count > budget.widgets) return fail(F::child_count_exceeds_widget_budget);
      if (count > budget.edges - out.edges) return fail(F::edge_budget_exhausted);
      if (count && !children) return fail(F::child_vector_missing);
      out.edges += count;
      for (std::int32_t index = 0; index < out.child_count; ++index) {
        out.child_index = index;
        std::uintptr_t child = 0;
        failure = read.child(read.context, children,
                             static_cast<std::uint32_t>(index), child);
        if (failure != F::none) return fail(failure);
        if (!child) return fail(F::child_slot_null);
        if (pending.size() == budget.widgets) return fail(F::widget_budget_exhausted);
        if (!seen.insert(child).second) return fail(F::duplicate_child);
        pending.push_back(child);
        out.queued = pending.size();
      }
    }
    out.complete = true;
    out.target = found;
    out.target_visible = found_visible;
    return true;
  } catch (...) {
    return fail(F::storage_or_callback_failure);
  }
}

} // namespace xar::ck3_11906::detail
