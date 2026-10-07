#include "xar_bridge/ck3_12004_confucian_assembly_bindings.hpp"

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_family_abi.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"
#include "xar_bridge/ck3_12004_religion_adopted_observers.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

namespace xar::ck3_12004::confucian_assembly {
namespace {
// Actual .4 complete Faith-Rites5B leaf: existing religion addon operand ledger.
constexpr std::uintptr_t kFaithRitesRva = 0xB801B0;
// Actual .4 complete indexed getter90B: adopted Army/Council operand ledgers.
constexpr std::uintptr_t kEffectiveSkillRva = 0x28B1690;
// Actual GUI callback28CF390+12 E8 resolves28C2080. Its complete28B leaf
// retains Character+1B0/extension+288 and both returns; no jailer resolution.
// Source receipt: r20-native-adapter-review-sourceonly-20261007-001/assembly/
// imprisoned-leaf-002/REPORT.json. No runtime qualification is claimed here.
constexpr std::uintptr_t kIsImprisonedRva = 0x28C2080;
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  b.native_build = ck3_12003::confucian_assembly::NativeBuild::crozier_12004;
  if (base == 0 || sha != ck3_12004::kExecutableSha256) return b;
  const auto members = religion::adopted::BindOrganizationMembersImage12004(base, sha);
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.read_core_snapshot = &ck3_12004::ReadCoreSnapshot;
  b.resolve_core_character = &ck3_12004::ResolveCoreCharacter;
  b.traits = phase_character::BindImage(base, sha);
  b.rite_storage_slot = reinterpret_cast<void **>(base + religion::profile::kRiteStorageSlotRva);
  b.title_storage_slot = members.title_storage_slot;
  b.character_rite = members.character_rite;
  b.rite_faith = members.rite_faith;
  b.faith_religion = members.faith_religion;
  b.faith_rites = reinterpret_cast<decltype(b.faith_rites)>(base + kFaithRitesRva);
  b.faith_characters = members.faith_characters;
  b.rite_counties = members.rite_counties;
  b.effective_skill = reinterpret_cast<decltype(b.effective_skill)>(base + kEffectiveSkillRva);
  b.adult_threshold_zero = reinterpret_cast<const std::int32_t *>(base + kFamilyAdultThresholdZeroRva);
  b.adult_threshold_one = reinterpret_cast<const std::int32_t *>(base + kFamilyAdultThresholdOneRva);
  b.is_imprisoned = reinterpret_cast<decltype(b.is_imprisoned)>(base + kIsImprisonedRva);
  b.enabled = b.core.enabled && b.traits.enabled && members.enabled;
  return b;
}

} // namespace xar::ck3_12004::confucian_assembly
