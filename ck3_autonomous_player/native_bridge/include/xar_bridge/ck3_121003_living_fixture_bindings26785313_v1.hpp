#pragma once
#include "xar_bridge/ck3_121003_living_inventory26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Native-private observed references. These are never parsed from wire, nor
// selected by a caller. Actual fixture actor variables precede management UI.
inline constexpr std::array<const char*,6>kLivingArtifactReferenceKeys267V1{
 "xalw_fixture_target","xalw_fixture_material_common","xalw_fixture_material_masterwork",
 "xalw_fixture_material_famed","xalw_fixture_material_illustrious","xalw_selected_artifact"};
struct LivingFixtureBindings267V1{
 std::array<LivingArtifactReference267V1,6>refs;
 std::uintptr_t variable_owner=0,official_descriptor=0;
 std::array<std::uintptr_t,6>borrowed{};
 std::array<std::array<std::byte,16>,6>raw{};
 bool sampled_twice=false;
 friend bool operator==(const LivingFixtureBindings267V1&,const LivingFixtureBindings267V1&)=default;
};
bool ReadLivingFixtureBindings267V1(const ReadonlyBindings&,const LivingInventoryFrame267V1&,
 const LivingInventoryRequest267V1&,std::uint64_t,LivingFixtureBindings267V1&,bool&cleanup_known,std::string&)noexcept;
}
