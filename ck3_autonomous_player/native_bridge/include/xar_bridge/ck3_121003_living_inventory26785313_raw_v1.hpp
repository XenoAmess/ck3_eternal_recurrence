#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_121003::build26785313 {
// Isolated SOURCE candidate, not a registered capability or wire family.
// Frame is produced only by a future independent current Owner/Read callback.
// No caller artifact/owner/slot/key/coordinate can supply these pointers.
struct LivingInventoryFrame267V1 {
 ck3_1210::CoreSnapshotPrefix core{};
 std::uintptr_t game=0,jomini=0,character_storage=0,data=0,players=0,player=0,actor=0;
 std::uint64_t connection_generation=0;
 bool facts_verified=false;
};
struct LivingInventoryRequest267V1 {
 ck3_1210::CoreSnapshotPrefix expected{};
 std::uint64_t deadline_unix_ms=0;
};
enum class LivingNumericState267V1 { absent, present_empty, other_kind, numeric };
struct LivingNumeric267V1 {
 LivingNumericState267V1 state=LivingNumericState267V1::absent;
 std::uint16_t scope_kind=0;
 std::optional<std::int64_t> raw;
 friend bool operator==(const LivingNumeric267V1&,const LivingNumeric267V1&)=default;
};
inline constexpr std::array<const char*,4> kLivingNumericKeys267V1{
 "xalw_level","xalw_xp_in_level","xalw_pending_xp","xalw_growth_sequence"};
inline constexpr std::int64_t kLivingNumericDenominator267V1=100000;
struct LivingArtifact267V1 {
 std::uint32_t full_id=0xFFFFFFFFU,owner_full_id=0xFFFFFFFFU;
 std::string type_key;
 std::int32_t rarity_raw=0; // DATA: runtime canonical rarity names remain unbound.
 bool equipped=false; // Derived from every validated physical slot, not an ACK.
 std::array<LivingNumeric267V1,4> numeric;
 friend bool operator==(const LivingArtifact267V1&,const LivingArtifact267V1&)=default;
};
struct LivingInventorySlot267V1 {
 std::string key;
 std::optional<std::uint32_t> artifact_full_id;
 friend bool operator==(const LivingInventorySlot267V1&,const LivingInventorySlot267V1&)=default;
};
enum class LivingReferenceState267V1{absent,present_empty,wrong_kind,artifact};
struct LivingArtifactReference267V1{
 LivingReferenceState267V1 state=LivingReferenceState267V1::absent;
 std::uint16_t scope_kind=0;
 std::optional<std::uint32_t>full_id;
 friend bool operator==(const LivingArtifactReference267V1&,const LivingArtifactReference267V1&)=default;
};
inline constexpr std::array<const char*,6>kLivingReferenceRoles267V1{
 "fixture_target","fixture_material_common","fixture_material_masterwork",
 "fixture_material_famed","fixture_material_illustrious","selected_artifact"};
struct LivingInventorySource267V1 {
 std::uint32_t actor_full_id=0xFFFFFFFFU;
 std::vector<LivingArtifact267V1> artifacts; // Complete physical order, no filtering.
 std::vector<LivingInventorySlot267V1> slots;
 std::array<LivingArtifactReference267V1,6>fixed_references; // Observed DATA, never caller selectors or permissions.
 std::optional<std::size_t> weapon_slot; // Index is observed DATA, never a request selector.
 bool complete_inventory=false,sampled_twice=false;
 friend bool operator==(const LivingInventorySource267V1&,const LivingInventorySource267V1&)=default;
};
struct LivingInventoryRaw267V1 {
 LivingInventorySource267V1 source;
 bool entered=false,cleanup_known=true;
};
// Deliberately UNBOUND. A future integrator must implement a verifier from the
// exact static spans/RTTI and read-only descriptor+30 proof, not return true.
// No caller function pointer is accepted through any public request.
bool VerifyLivingInventoryImage267V1(std::uintptr_t image) noexcept;
bool ReadLivingInventoryRaw267V1(const ReadonlyBindings&,const LivingInventoryFrame267V1&,
 const LivingInventoryRequest267V1&,std::uint64_t original_monotonic_deadline_ms,
 LivingInventoryRaw267V1&,std::string&) noexcept;
}
