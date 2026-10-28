#pragma once

#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

namespace xar::ck3_11906 {

enum class NamedGuiWidgetResolutionV1 : std::uint8_t {
  resolved,
  missing,
  budget_exhausted,
  read_failed,
  invalid_request,
  resource_unavailable,
};

// Lookup is independent of the 2048-row diagnostic export limit. Its queue
// and identity set live on the heap; neither may exceed this node budget.
inline constexpr std::size_t kNamedGuiLookupMaximumWidgetsV1 = 65'536;
// Repeated/cyclic edges cannot turn a bounded node census into quadratic work
// on CK3's main thread. Already queued identities remain searchable at the cap.
inline constexpr std::size_t kNamedGuiLookupMaximumEdgesV1 =
    kNamedGuiLookupMaximumWidgetsV1 * 4;

// Native-only diagnostic extension. The original resolver keeps its exact
// signature for all existing semantic adapters and frozen object consumers.
bool ResolveNamedGuiWidgetWithResolutionV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, std::string_view root_name,
    std::string_view descendant_name, void *&root, void *&widget,
    NamedGuiWidgetResolutionV1 &resolution) noexcept;

} // namespace xar::ck3_11906
