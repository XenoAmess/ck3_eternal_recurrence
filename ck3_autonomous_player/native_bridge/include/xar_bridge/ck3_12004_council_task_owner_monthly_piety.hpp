#pragma once

#include "xar_bridge/ck3_12004_council_task_owner_tax.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004 {

// Actual4 named descriptor row105 at RVA480D998, label RVA48159F8:
// MOD_MONTHLY_PIETY. The borrowed runtime keyword must also match.
inline constexpr CouncilTaskTaxDescriptor12004 kCouncilMonthlyPietyDescriptor12004{97, 11117};

struct CouncilTaskOwnerMonthlyPietyBindings12004 {
  NativeCouncilTaskOwnerModifier12004 build = nullptr;
  NativeCouncilTaskModifierValue12004 value = nullptr;
  NativeCouncilTaskModifierDestroy12004 destroy = nullptr;
  NativeCouncilTaskKeywordName12004 keyword_name = nullptr;
};

using CouncilTaskMonthlyPietyReadMemory12004 =
    bool (*)(void *, const void *, void *, std::size_t) noexcept;

enum class CouncilTaskOwnerMonthlyPietyFailure12004 : std::uint8_t {
  none = 0,
  context_unavailable,
  native_bindings_unavailable,
  keyword_unavailable,
  keyword_mismatch,
  builder_unavailable,
  cleanup_unavailable,
  numeric_unavailable,
};

struct CouncilTaskOwnerMonthlyPietyObservation12004 {
  std::int32_t incumbent_character_id = -1;
  std::int32_t owner_character_id = -1;
  std::array<char, 64> observed_keyword_key{};
  std::optional<std::int64_t> raw;
  CouncilTaskOwnerMonthlyPietyFailure12004 unavailable_reason =
      CouncilTaskOwnerMonthlyPietyFailure12004::none;
};

// Reuses the exact4 current-owner evaluator/numeric/cleanup/keyword source
// already held for Council tax. No process lookup, scan or native call.
CouncilTaskOwnerMonthlyPietyBindings12004 BindCouncilTaskOwnerMonthlyPiety12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// The caller supplies the actual TaskType and its original32-byte Task+40
// scopes in the existing paused query. This evaluates only its owner component,
// not total player piety, an alternative task, or effective frozen application.
CouncilTaskOwnerMonthlyPietyObservation12004 ReadCouncilTaskOwnerMonthlyPiety12004(
    const CouncilTaskOwnerMonthlyPietyBindings12004 &bindings,
    const void *task_type, const void *original_scopes,
    CouncilTaskMonthlyPietyReadMemory12004 read_memory = nullptr,
    void *read_context = nullptr) noexcept;

// Matches existing CampaignRootNativeEnvironmentV1::task_owner_monthly_piety.
// Install only through the exact4-admitted root environment binder. The root
// owns current task identity, frozen provenance, recapture, and serialization.
bool ReadCampaignRootTaskOwnerMonthlyPiety12004(
    std::uintptr_t module_base, void *task_type, const void *original_scopes,
    std::int64_t &raw) noexcept;

} // namespace xar::ck3_12004
