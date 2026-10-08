#pragma once

#include "xar_bridge/council_current_task_domain_tax_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {
struct CouncilCandidatesAccessV1;

inline constexpr std::uintptr_t kCouncilTaskOwnerModifierRva12004 = 0x31ABDF0;
inline constexpr std::uintptr_t kCouncilTaskModifierValueRva12004 = 0x23036E0;
inline constexpr std::uintptr_t kCouncilTaskModifierDestroyRva12004 = 0x9F24F0;
inline constexpr std::uintptr_t kCouncilTaskKeywordNameRva12004 = 0x3F4F8E0;
inline constexpr std::size_t kCouncilTaskModifierSize12004 = 0x1C0;
inline constexpr std::int64_t kCouncilTaskModifierScale12004 = 100000;

struct CouncilTaskTaxDescriptor12004 {
  std::uint16_t modifier_id = 0xFFFF;
  std::uint32_t keyword_id = 0;
};

using NativeCouncilTaskOwnerModifier12004 =
    void *(*)(const void *, void *, const void *);
using NativeCouncilTaskModifierValue12004 =
    std::int64_t *(*)(const void *, std::int64_t *, std::uint16_t);
using NativeCouncilTaskModifierDestroy12004 = void (*)(void *);
using NativeCouncilTaskKeywordName12004 = const std::string *(*)(std::int32_t);

struct CouncilTaskOwnerTaxBindings12004 {
  CouncilTaskTaxDescriptor12004 descriptor;
  NativeCouncilTaskOwnerModifier12004 build = nullptr;
  NativeCouncilTaskModifierValue12004 value = nullptr;
  NativeCouncilTaskModifierDestroy12004 destroy = nullptr;
  NativeCouncilTaskKeywordName12004 keyword_name = nullptr;
};

// Descriptor is supplied only by the separately captured named actual4 row.
// No tax ID or keyword token is inferred from ordinal or old resource IDs.
CouncilTaskOwnerTaxBindings12004 BindCouncilTaskOwnerTax12004(
    std::uintptr_t module_base, std::string_view executable_sha256,
    CouncilTaskTaxDescriptor12004 descriptor) noexcept;

game::CouncilCurrentTaskDomainTaxV1 ReadCouncilTaskOwnerTax12004(
    const CouncilTaskOwnerTaxBindings12004 &bindings,
    const CouncilCandidatesAccessV1 &access, const void *current_task,
    std::int32_t active_task_id, std::int32_t owner_character_id,
    std::int32_t incumbent_character_id);

} // namespace xar::ck3_12004
