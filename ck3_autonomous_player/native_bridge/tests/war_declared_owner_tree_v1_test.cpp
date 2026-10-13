#include "xar_bridge/war_declared_owner_tree_v1.hpp"
#include <cstdint>
#include <iostream>
#include <limits>
#include <vector>

namespace {
using namespace xar::ck3_11906::detail;
using Failure = WarDeclaredOwnerReadFailureV1;

struct Node {
  bool target = false, visible = false, readable = true;
  bool header_readable = true, slot_readable = true;
  std::vector<std::uintptr_t> children;
};
struct Graph {
  std::vector<Node> nodes;
  mutable std::size_t runtime_reads = 0, header_reads = 0, child_reads = 0;
  explicit Graph(std::size_t count) : nodes(count) {}
  static Failure Runtime(const void *opaque, std::uintptr_t id,
                         bool &target, bool &visible) noexcept {
    const auto &graph = *static_cast<const Graph *>(opaque);
    ++graph.runtime_reads;
    if (!id || id > graph.nodes.size() || !graph.nodes[id-1].readable)
      return Failure::widget_runtime_unreadable;
    target = graph.nodes[id-1].target;
    visible = graph.nodes[id-1].visible;
    return Failure::none;
  }
  static Failure Children(const void *opaque, std::uintptr_t id,
                          std::uintptr_t &list, std::int32_t &count) noexcept {
    const auto &graph = *static_cast<const Graph *>(opaque);
    ++graph.header_reads;
    if (!id || id > graph.nodes.size() || !graph.nodes[id-1].header_readable)
      return Failure::child_count_unreadable;
    const auto &children = graph.nodes[id-1].children;
    if (children.size() > static_cast<std::size_t>((std::numeric_limits<std::int32_t>::max)()))
      return Failure::child_count_unreadable;
    list = children.empty() ? 0 : id;
    count = static_cast<std::int32_t>(children.size());
    return Failure::none;
  }
  static Failure Child(const void *opaque, std::uintptr_t list,
                       std::uint32_t index, std::uintptr_t &child) noexcept {
    const auto &graph = *static_cast<const Graph *>(opaque);
    ++graph.child_reads;
    if (!list || list > graph.nodes.size() || !graph.nodes[list-1].slot_readable ||
        index >= graph.nodes[list-1].children.size())
      return Failure::child_slot_unreadable;
    child = graph.nodes[list-1].children[index];
    return Failure::none;
  }
  WarDeclaredOwnerReadCallbacksV1 Read() const noexcept {
    return {this, &Runtime, &Children, &Child};
  }
};

Graph Wide(std::size_t count, bool target) {
  Graph graph(count);
  graph.nodes[0].children.reserve(count - 1);
  for (std::size_t index = 1; index < count; ++index)
    graph.nodes[0].children.push_back(index + 1);
  // An early target must not terminate traversal or hide a later failure.
  graph.nodes[0].target = target;
  graph.nodes[0].visible = target;
  return graph;
}

bool Check(bool value, const char *scene) {
  if (!value) std::cerr << scene << '\n';
  return value;
}
bool Unknown(const WarDeclaredOwnerReadResultV1 &out, Failure expected) {
  return !out.complete && out.target == 0 && !out.target_visible && out.failure == expected;
}
}

int main() {
  static_assert(kWarDeclaredOwnerMaximumWidgetsV1 == 16384);
  static_assert(kWarDeclaredOwnerMaximumEdgesV1 == 65536);
  bool ok = true;
  std::size_t scenes = 0;
  {
    auto graph = Wide(4097, true);
    WarDeclaredOwnerReadResultV1 out;
    const bool read = ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out);
    ok &= Check(read && out.complete && out.target == 1 && out.target_visible &&
                out.matches == 1 && out.visited == 4097 && graph.runtime_reads == 4097 &&
                graph.header_reads == 4097 && graph.child_reads == 4096,
                "more_than2048_early_target_requires_complete_read");
    ++scenes;
  }
  {
    auto graph = Wide(4097, false);
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) && out.complete &&
                !out.target && !out.matches && graph.runtime_reads == 4097,
                "more_than2048_complete_absence");
    ++scenes;
  }
  {
    auto graph = Wide(16384, true);
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) && out.complete &&
                out.visited == 16384 && graph.runtime_reads == 16384,
                "exact_widget_budget_can_complete");
    ++scenes;
  }
  {
    auto graph = Wide(16385, true);
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) &&
                Unknown(out, Failure::widget_budget_exhausted) && out.queued == 16384,
                "widget_budget_exhaustion_never_publishes_early_target");
    ++scenes;
  }
  {
    auto graph = Wide(4097, true);
    graph.nodes.back().readable = false;
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) &&
                Unknown(out, Failure::widget_runtime_unreadable) && graph.runtime_reads == 4097,
                "late_unreadable_widget_keeps_found_target_unknown");
    ++scenes;
  }
  {
    auto graph = Wide(2, true);
    graph.nodes[0].children.push_back(2);
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) && Unknown(out, Failure::duplicate_child),
                "duplicate_child_remains_unknown");
    ++scenes;
  }
  {
    Graph graph(1);
    graph.nodes[0].children.push_back(1);
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) && Unknown(out, Failure::duplicate_child),
                "cycle_remains_unknown");
    ++scenes;
  }
  {
    Graph graph(1);
    graph.nodes[0].target = graph.nodes[0].visible = true;
    graph.nodes[0].children.push_back(0);
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) && Unknown(out, Failure::child_slot_null),
                "null_child_remains_unknown");
    ++scenes;
  }
  {
    auto graph = Wide(2, true);
    graph.nodes[0].slot_readable = false;
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) && Unknown(out, Failure::child_slot_unreadable),
                "unreadable_slot_remains_unknown");
    ++scenes;
  }
  {
    auto graph = Wide(2, true);
    graph.nodes[1].target = true;
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) && Unknown(out, Failure::duplicate_named_window),
                "multiple_distinct_targets_remain_unknown");
    ++scenes;
  }
  {
    auto graph = Wide(10, true);
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out, {64, 8}) &&
                Unknown(out, Failure::edge_budget_exhausted) && graph.child_reads == 0,
                "edge_budget_exhaustion_remains_unknown_before_child_read");
    ++scenes;
  }
  {
    auto graph = Wide(2, true);
    graph.nodes[1].header_readable = false;
    WarDeclaredOwnerReadResultV1 out;
    ok &= Check(!ReadWarDeclaredOwnerTreeV1(1, graph.Read(), out) && Unknown(out, Failure::child_count_unreadable),
                "unreadable_header_remains_unknown");
    ++scenes;
  }
  std::cout << "{\"status\":\"" << (ok ? "GREEN" : "RED")
            << "\",\"scenes\":" << scenes
            << ",\"max_widgets\":16384,\"max_edges\":65536,\"new_fixture\":true}\n";
  return ok ? 0 : 1;
}
