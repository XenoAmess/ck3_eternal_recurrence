#pragma once

#include "xar_bridge/ck3_12004_guardian_factory_lookup.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
struct ZhongguoScoreboardNativeEnvironmentV1;
}

namespace xar::ck3_12004 {

struct GuardianFactoryVirtualSlotMetadata12004V1 {
  bool available{};
  std::uintptr_t address{};
  std::optional<std::uintptr_t> rva;
};

struct GuardianFactoryRttiMetadata12004V1 {
  bool col_pointer_available{};
  std::uintptr_t col_address{};
  bool col_fields_available{};
  std::array<std::uint32_t, 6> col_fields{};
  std::optional<std::uintptr_t> type_descriptor_address;
  bool type_name_available{};
  std::string type_name;
  bool type_name_truncated{};
  std::string_view unavailable_reason{"factory_not_found"};
};

struct GuardianFactoryTypedMetadata12004V1 {
  ExistingGuardianFactoryMetadata12004V1 lookup;
  // Raw factory+0x18 creation input; an observed zero remains available.
  std::optional<std::uint64_t> factory_create_input_18_qword;
  // Source-discovery slots only: no Create/Evaluate role is assigned.
  std::array<GuardianFactoryVirtualSlotMetadata12004V1, 4> virtual_slots{};
  GuardianFactoryRttiMetadata12004V1 rtti;
};

struct GuardianFactoryDiscoveryMetadata12004V1 {
  std::uintptr_t module_base{};
  std::uintptr_t image_size{};
  std::array<GuardianFactoryTypedMetadata12004V1, 2> factories{};
};

// Reuses the existing in-process Read implementation. No UI handler, window,
// player click, name interner, factory construction or evaluator is invoked.
GuardianFactoryReadEnvironment12004V1
BindGuardianFactoryDiscoveryEnvironment12004V1(
    const xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment)
    noexcept;

// Reads the fixed two lookup records, raw factory+0x18 QWORDs, four virtual
// slots each, COL/TD fields and a bounded decorated type name. Availability is independent
// per record/slot/type; this metadata is not guardian pair membership.
GuardianFactoryDiscoveryMetadata12004V1
ReadGuardianFactoryDiscoveryMetadata12004V1(
    const GuardianFactoryReadEnvironment12004V1 &environment,
    std::uintptr_t image_size) noexcept;

} // namespace xar::ck3_12004
