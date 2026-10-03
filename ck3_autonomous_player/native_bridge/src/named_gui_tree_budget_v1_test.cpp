#include "xar_bridge/frontend_gui_route_v1.hpp"
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
}
int main() {
  using namespace xar::ck3_11906;
  static_assert(kNamedGuiTreeInspectionMaximumFrameBytesV1 == xar::bridge::kMaximumFrameBytes);
  bool ok = Check(kNamedGuiTreeInspectionMaximumWidgetsV1 == 2048, "widget budget differs");
  ok &= ReadWideTree(513, false);
  ok &= ReadWideTree(2048, false);
  ok &= ReadWideTree(2049, true);
  ok &= Check(NamedGuiTreeInspectionFrameBytesFitV1(2U * 1024U * 1024U), "exact frame limit must fit");
  ok &= Check(!NamedGuiTreeInspectionFrameBytesFitV1(2U * 1024U * 1024U + 1U), "oversized tree frame admitted");
  ok &= Check(sizeof(NamedGuiTreeInspectionV1) < 256, "tree rows returned to mailbox stack");
  std::cout << "{\"row_bytes\":" << sizeof(NamedGuiWidgetInspectionV1)
            << ",\"tree_result_bytes\":" << sizeof(NamedGuiTreeInspectionV1)
            << ",\"frontend_context_bytes\":" << sizeof(FrontendGuiRouteMailboxContextV1)
            << ",\"ingame_ui_result_bytes\":" << sizeof(IngameUiResultV1)
            << ",\"heap_rows_max_bytes\":" << sizeof(NamedGuiWidgetInspectionV1) * 2048
            << ",\"maximum_widgets\":2048,\"frame_bytes\":2097152}" << '\n';
  return ok ? 0 : 1;
}
