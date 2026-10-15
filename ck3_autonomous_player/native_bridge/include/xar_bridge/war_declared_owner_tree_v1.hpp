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

// A cache contains topology, never cached visibility/name/type or a trusted
// target pointer. A warm pass rereads every node and every edge from the current
// owner root. Equal edges inherit the original complete walk's uniqueness, so
// the per-node std::set allocation is unnecessary. A changed edge rebuilds the
// complete walk; an unreadable edge/runtime remains unknown without retry.
struct WarDeclaredOwnerCachedNodeV1 {
  std::uintptr_t node = 0, children = 0;
  std::uint32_t child_count = 0, first_child = 0;
};

struct WarDeclaredOwnerTreeCacheV1 {
  bool complete = false;
  std::vector<WarDeclaredOwnerCachedNodeV1> nodes;
  void invalidate() noexcept { complete = false; }
};

struct WarDeclaredOwnerTreeScopeCacheV1 {
  std::uintptr_t module = 0, owner = 0;
  std::uint64_t generation = 0;
  std::int64_t actor = -1;
  WarDeclaredOwnerTreeCacheV1 tree;
  WarDeclaredOwnerTreeCacheV1 &bind(std::uintptr_t next_module, std::uintptr_t next_owner,
                                   std::uint64_t next_generation, std::int64_t next_actor) noexcept {
    if (module != next_module || owner != next_owner || generation != next_generation || actor != next_actor) {
      tree.invalidate();
      tree.nodes.clear();
      module = next_module;
      owner = next_owner;
      generation = next_generation;
      actor = next_actor;
    }
    return tree;
  }
};

inline bool ReadWarDeclaredOwnerTreeCachedV1(
    std::uintptr_t root, const WarDeclaredOwnerReadCallbacksV1 &read,
    WarDeclaredOwnerTreeCacheV1 &cache, WarDeclaredOwnerReadResultV1 &out,
    WarDeclaredOwnerReadBudgetV1 budget = {}) noexcept {
  using F = WarDeclaredOwnerReadFailureV1;
  out = {};
  const auto fail = [&](F why) noexcept {
    cache.invalidate();
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

  if (cache.complete && !cache.nodes.empty() && cache.nodes.front().node == root &&
      cache.nodes.size() <= budget.widgets) {
    bool topology_matches = true;
    std::uintptr_t found = 0;
    bool found_visible = false;
    out.queued = cache.nodes.size();
    for (std::size_t at = 0; at < cache.nodes.size(); ++at) {
      out.at = at;
      out.child_index = -1;
      const auto &node = cache.nodes[at];
      bool target = false, visible = false;
      auto failure = read.runtime(read.context, node.node, target, visible);
      if (failure != F::none) return fail(failure);
      ++out.visited;
      if (target) {
        if (++out.matches != 1) return fail(F::duplicate_named_window);
        found = node.node;
        found_visible = visible;
      }
      std::uintptr_t children = 0;
      failure = read.children(read.context, node.node, children, out.child_count);
      if (failure != F::none) return fail(failure);
      if (out.child_count < 0) return fail(F::negative_child_count);
      const auto count = static_cast<std::size_t>(out.child_count);
      if (count > budget.widgets) return fail(F::child_count_exceeds_widget_budget);
      if (count > budget.edges - out.edges) return fail(F::edge_budget_exhausted);
      if (count && !children) return fail(F::child_vector_missing);
      if (children != node.children || count != node.child_count ||
          node.first_child != out.edges + 1 ||
          node.first_child > cache.nodes.size() ||
          count > cache.nodes.size() - node.first_child ||
          (count && node.first_child <= at)) {
        topology_matches = false;
        break;
      }
      out.edges += count;
      for (std::int32_t index = 0; index < out.child_count; ++index) {
        out.child_index = index;
        std::uintptr_t child = 0;
        failure = read.child(read.context, children, static_cast<std::uint32_t>(index), child);
        if (failure != F::none) return fail(failure);
        if (!child) return fail(F::child_slot_null);
        if (child != cache.nodes[node.first_child + static_cast<std::size_t>(index)].node) {
          topology_matches = false;
          break;
        }
      }
      if (!topology_matches) break;
    }
    if (topology_matches && out.edges + 1 == cache.nodes.size()) {
      out.complete = true;
      out.target = found;
      out.target_visible = found_visible;
      return true;
    }
  }

  // A miss can mean a legitimate rebuild of the GUI. Capture the BFS topology
  // during the original complete traversal, without an extra memory read.
  cache.invalidate();
  cache.nodes.clear();
  struct Capture {
    const WarDeclaredOwnerReadCallbacksV1 *read;
    WarDeclaredOwnerTreeCacheV1 *cache;
    std::size_t maximum, queued = 1;
  } capture{&read, &cache, budget.widgets};
  WarDeclaredOwnerReadCallbacksV1 recording{};
  recording.context = &capture;
  recording.runtime = [](const void *opaque, std::uintptr_t node,
                         bool &target, bool &visible) noexcept {
    const auto &c = *static_cast<const Capture *>(opaque);
    return c.read->runtime(c.read->context, node, target, visible);
  };
  recording.children = [](const void *opaque, std::uintptr_t node,
                          std::uintptr_t &address, std::int32_t &count) noexcept {
    auto &c = *const_cast<Capture *>(static_cast<const Capture *>(opaque));
    auto failure = c.read->children(c.read->context, node, address, count);
    if (failure != F::none) return failure;
    // The original walker diagnoses invalid counts/budgets. Do not allocate or
    // derive an index from those values before it can reject them.
    if (count < 0 || static_cast<std::size_t>(count) > c.maximum || c.queued > c.maximum)
      return F::none;
    try {
      auto &nodes = c.cache->nodes;
      if (nodes.size() == nodes.capacity()) {
        const auto next = nodes.capacity() ? nodes.capacity() * 2 : std::size_t{256};
        nodes.reserve(next < c.maximum ? next : c.maximum);
      }
      nodes.push_back({node, address, static_cast<std::uint32_t>(count),
                       static_cast<std::uint32_t>(c.queued)});
      c.queued += static_cast<std::size_t>(count);
      return F::none;
    } catch (...) { return F::storage_or_callback_failure; }
  };
  recording.child = [](const void *opaque, std::uintptr_t address,
                       std::uint32_t index, std::uintptr_t &value) noexcept {
    const auto &c = *static_cast<const Capture *>(opaque);
    return c.read->child(c.read->context, address, index, value);
  };
  if (!ReadWarDeclaredOwnerTreeV1(root, recording, out, budget)) return false;
  cache.complete = cache.nodes.size() == out.visited && capture.queued == out.queued;
  if (!cache.complete) return fail(F::storage_or_callback_failure);
  return true;
}

} // namespace xar::ck3_11906::detail
