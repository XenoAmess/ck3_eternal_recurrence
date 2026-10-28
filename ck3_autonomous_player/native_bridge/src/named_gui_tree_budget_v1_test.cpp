#include "xar_bridge/frontend_gui_route_v1.hpp"
#include "xar_bridge/named_gui_widget_resolution_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
bool Check(bool actual, const char *message) {
  if (!actual) std::cerr << message << '\n';
  return actual;
}
bool ReadWideTree(std::size_t count, bool truncated) {
  using namespace xar::ck3_11906;
  std::vector<std::array<std::uint8_t, 0x200>> nodes(count);
  std::vector<void *> children;
  children.reserve(count - 1);
  for (std::size_t i = 0; i < count; ++i) {
    const std::uintptr_t vtable = 0x100008;
    std::memcpy(nodes[i].data(), &vtable, sizeof(vtable));
    // Empty MSVC string, inline capacity15. No borrowed allocation or call.
    const std::uint64_t capacity = 15;
    std::memcpy(nodes[i].data() + kZhongguoWidgetNameOffset + 24,
                &capacity, sizeof(capacity));
    if (i != 0) children.push_back(nodes[i].data());
  }
  auto *child_data = children.data();
  const auto child_count = static_cast<std::int32_t>(children.size());
  std::memcpy(nodes[0].data() + kZhongguoWidgetChildrenOffset,
              &child_data, sizeof(child_data));
  std::memcpy(nodes[0].data() + kZhongguoWidgetChildCountOffset,
              &child_count, sizeof(child_count));
  ZhongguoScoreboardAccessV1 access{};
  NamedGuiTreeInspectionV1 result{};
  const bool read = InspectNamedGuiSubtreeV1(access, 0x100000,
      nodes[0].data(), "frontend_bookmarks", result);
  const auto wanted = count > kNamedGuiTreeInspectionMaximumWidgetsV1
      ? kNamedGuiTreeInspectionMaximumWidgetsV1 : count;
  return Check(read, "actual bounded traversal failed") &&
      Check(result.widget_count == wanted && result.widgets.size() == wanted,
            "native rows/count exceeded or lost their exact boundary") &&
      Check(result.truncated == truncated, "native truncation boundary changed");
}

// Exercise the actual native singleton-chain and named resolver. This fixture
// does not enable the production resolver's offline function-override bypass.
struct LookupTree {
  using Node = std::array<std::uint8_t, 0x200>;
  std::vector<Node> nodes;
  std::vector<std::vector<void *>> children;
  std::array<std::array<std::uint8_t, 0x400>, 5> chain{};
  void *singleton = nullptr;
  const void *blocked_read = nullptr;
  std::size_t reads = 0;

  template <std::size_t Size, typename Value>
  static void Put(std::array<std::uint8_t, Size> &buffer, std::size_t offset,
                  const Value &value) {
    std::memcpy(buffer.data() + offset, &value, sizeof(value));
  }
  explicit LookupTree(std::size_t count) : nodes(count), children(count) {
    using namespace xar::ck3_11906;
    singleton = chain[0].data();
    Put(chain[0], kZhongguoGuiChainFirstOffset, chain[1].data());
    Put(chain[1], kZhongguoGuiChainSecondOffset, chain[2].data());
    Put(chain[2], kZhongguoGuiContextOffset, chain[3].data());
    Put(chain[3], kZhongguoGuiOwnerOffset, chain[4].data());
    Put(chain[4], kZhongguoGuiOwnerRootWidgetOffset, nodes[0].data());
    for (std::size_t i = 0; i < count; ++i) {
      SetName(i, "");
      if (i != 0) children[(i - 1) / 32].push_back(nodes[i].data());
    }
    Finalize();
  }
  void SetName(std::size_t index, std::string_view name) {
    using namespace xar::ck3_11906;
    // Every test name fits in the native MSVC inline-string representation.
    std::memset(nodes[index].data() + kZhongguoWidgetNameOffset, 0, 32);
    std::memcpy(nodes[index].data() + kZhongguoWidgetNameOffset,
                name.data(), name.size());
    Put(nodes[index], kZhongguoWidgetNameOffset + 16,
        static_cast<std::uint64_t>(name.size()));
    Put(nodes[index], kZhongguoWidgetNameOffset + 24, std::uint64_t{15});
  }
  void Finalize() {
    using namespace xar::ck3_11906;
    for (std::size_t i = 0; i < nodes.size(); ++i) {
      Put(nodes[i], kZhongguoWidgetChildrenOffset, children[i].data());
      Put(nodes[i], kZhongguoWidgetChildCountOffset,
          static_cast<std::int32_t>(children[i].size()));
    }
  }
  static void *__fastcall NoTopLevel(void *, const std::string *) {
    return nullptr;
  }
  static bool Read(void *opaque, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &tree = *static_cast<LookupTree *>(opaque);
    ++tree.reads;
    if (address == tree.blocked_read) return false;
    std::memcpy(output, address, size);
    return true;
  }
  bool Resolve(std::string_view name,
               xar::ck3_11906::NamedGuiWidgetResolutionV1 expected,
               void *target = nullptr) {
    using namespace xar::ck3_11906;
    ZhongguoScoreboardNativeEnvironmentV1 environment{};
    environment.gui_global_slot = &singleton;
    environment.find_top_level_widget = NoTopLevel;
    ZhongguoScoreboardAccessV1 access{};
    access.context = this;
    access.read_memory = Read;
    void *root = reinterpret_cast<void *>(1);
    void *widget = reinterpret_cast<void *>(1);
    NamedGuiWidgetResolutionV1 status = NamedGuiWidgetResolutionV1::invalid_request;
    const bool valid = ResolveNamedGuiWidgetWithResolutionV1(environment, access,
        name, name, root, widget, status);
    return Check(status == expected, "named lookup lost its typed failure") &&
        Check(valid == (expected == NamedGuiWidgetResolutionV1::resolved ||
                        expected == NamedGuiWidgetResolutionV1::missing ||
                        expected == NamedGuiWidgetResolutionV1::budget_exhausted),
              "named lookup bool/failure contract changed") &&
        Check(root == target && widget == target, "named lookup returned a false identity") &&
        Check([&] {
          void *legacy_root = nullptr, *legacy_widget = nullptr;
          const bool legacy = ResolveNamedGuiWidgetV1(environment, access, name,
              name, legacy_root, legacy_widget);
          return legacy == valid && legacy_root == root && legacy_widget == widget;
        }(), "original named resolver ABI wrapper differs");
  }
};

bool ReadNamedLookup() {
  using namespace xar::ck3_11906;
  bool ok = true;
  {
    LookupTree tree(5000);
    tree.SetName(4999, "lookup_target");
    LookupTree::Put(tree.nodes[4999], kZhongguoWidgetHiddenFlagsOffset,
                    std::uint8_t{0x18});
    ok &= tree.Resolve("lookup_target", NamedGuiWidgetResolutionV1::resolved,
                       tree.nodes[4999].data());
    ok &= tree.Resolve("absent", NamedGuiWidgetResolutionV1::missing);
    tree.blocked_read = tree.nodes[7].data() + kZhongguoWidgetNameOffset;
    ok &= tree.Resolve("absent", NamedGuiWidgetResolutionV1::read_failed);
    tree.blocked_read = nullptr;
    LookupTree::Put(tree.nodes[7], kZhongguoWidgetChildCountOffset, std::int32_t{4097});
    ok &= tree.Resolve("absent", NamedGuiWidgetResolutionV1::read_failed);
  }
  {
    LookupTree tree(2);
    tree.children[0].assign(4096, tree.nodes[1].data());
    tree.children[1].assign(4096, tree.nodes[0].data());
    tree.Finalize();
    ok &= tree.Resolve("absent", NamedGuiWidgetResolutionV1::missing);
    ok &= Check(tree.reads < 17000, "cycle or duplicate edges multiplied node traversal");
  }
  {
    LookupTree tree(66);
    for (std::size_t i = 0; i < tree.nodes.size(); ++i) {
      tree.children[i].clear();
      if (i + 1 < tree.nodes.size()) tree.children[i].push_back(tree.nodes[i + 1].data());
    }
    tree.Finalize();
    tree.SetName(64, "depth_limit");
    tree.SetName(65, "beyond_depth");
    ok &= tree.Resolve("depth_limit", NamedGuiWidgetResolutionV1::resolved,
                       tree.nodes[64].data());
    ok &= tree.Resolve("beyond_depth", NamedGuiWidgetResolutionV1::budget_exhausted);
  }
  {
    LookupTree tree(257);
    tree.children[0].clear();
    for (std::size_t i = 1; i < tree.nodes.size(); ++i) {
      tree.children[0].push_back(tree.nodes[i].data());
      tree.children[i].assign(4096, tree.nodes[0].data());
    }
    tree.Finalize();
    ok &= tree.Resolve("absent", NamedGuiWidgetResolutionV1::budget_exhausted);
    ok &= Check(tree.reads < 530000, "duplicate-edge work escaped its linear budget");
    tree.SetName(256, "queued_target");
    ok &= tree.Resolve("queued_target", NamedGuiWidgetResolutionV1::resolved,
                       tree.nodes[256].data());
  }
  {
    LookupTree tree(kNamedGuiLookupMaximumWidgetsV1);
    ok &= tree.Resolve("absent", NamedGuiWidgetResolutionV1::missing);
  }
  {
    LookupTree tree(kNamedGuiLookupMaximumWidgetsV1 + 1);
    tree.SetName(kNamedGuiLookupMaximumWidgetsV1 - 1, "queued_target");
    tree.SetName(kNamedGuiLookupMaximumWidgetsV1, "beyond_budget");
    ok &= tree.Resolve("queued_target", NamedGuiWidgetResolutionV1::resolved,
                       tree.nodes[kNamedGuiLookupMaximumWidgetsV1 - 1].data());
    ok &= tree.Resolve("beyond_budget", NamedGuiWidgetResolutionV1::budget_exhausted);
  }
  return ok;
}
}
int main() {
  using namespace xar::ck3_11906;
  static_assert(kNamedGuiTreeInspectionMaximumFrameBytesV1 == xar::bridge::kMaximumFrameBytes);
  bool ok = Check(kNamedGuiTreeInspectionMaximumWidgetsV1 == 2048, "widget budget differs");
  ok &= ReadWideTree(513, false);
  ok &= ReadWideTree(2048, false);
  ok &= ReadWideTree(2049, true);
  ok &= ReadNamedLookup();
  ok &= Check(NamedGuiTreeInspectionFrameBytesFitV1(xar::bridge::kMaximumFrameBytes), "exact frame limit must fit");
  ok &= Check(!NamedGuiTreeInspectionFrameBytesFitV1(xar::bridge::kMaximumFrameBytes + 1U), "oversized tree frame admitted");
  ok &= Check(sizeof(NamedGuiTreeInspectionV1) < 256, "tree rows returned to mailbox stack");
  std::cout << "{\"row_bytes\":" << sizeof(NamedGuiWidgetInspectionV1)
            << ",\"tree_result_bytes\":" << sizeof(NamedGuiTreeInspectionV1)
            << ",\"frontend_context_bytes\":" << sizeof(FrontendGuiRouteMailboxContextV1)
            << ",\"ingame_ui_result_bytes\":" << sizeof(IngameUiResultV1)
            << ",\"heap_rows_max_bytes\":" << sizeof(NamedGuiWidgetInspectionV1) * 2048
            << ",\"maximum_widgets\":2048,\"frame_bytes\":"
            << xar::bridge::kMaximumFrameBytes << "}" << '\n';
  return ok ? 0 : 1;
}
