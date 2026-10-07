#include "xar_bridge/ck3_12004_confucian_assembly_bindings.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_phase_character.hpp"

#include <iostream>

namespace legacy = xar::ck3_12003::confucian_assembly;
namespace actual = xar::ck3_12004::confucian_assembly;
namespace {
int checks = 0;
bool Check(bool value, const char *message) {
  ++checks;
  if (!value) std::cerr << "FAIL " << message << '\n';
  return value;
}
template <typename T> bool At(T value, std::uintptr_t base, std::uintptr_t rva) {
  return reinterpret_cast<std::uintptr_t>(value) == base + rva;
}
} // namespace

int main() {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto b = actual::BindImage(base, xar::ck3_12004::kExecutableSha256);
  if (!Check(b.enabled && b.native_build == legacy::NativeBuild::crozier_12004,
             "actual4 independent exact admission") ||
      !Check(!actual::BindImage(0, xar::ck3_12004::kExecutableSha256).enabled &&
             !actual::BindImage(base, xar::ck3_12003::kExecutableSha256).enabled &&
             !legacy::BindImage(base, xar::ck3_12004::kExecutableSha256).enabled,
             "zero image and cross-build admission rejected") ||
      !Check(b.read_core_snapshot == &xar::ck3_12004::ReadCoreSnapshot &&
             b.resolve_core_character == &xar::ck3_12004::ResolveCoreCharacter &&
             At(b.core.get_local_player, base, 0x383E290),
             "actual4 core callbacks and local-player entry") ||
      !Check(At(b.traits.character_has_trait, base, 0x28BB1D0) &&
             At(b.traits.is_human_player_character, base, 0x2BAA6F0),
             "actual4 trait and human callbacks") ||
      !Check(At(b.character_rite, base, 0x28D2F70) &&
             At(b.rite_faith, base, 0x24FC540) &&
             At(b.faith_religion, base, 0x2443D20) &&
             At(b.rite_storage_slot, base, 0x5D1E2F8),
             "actual4 full native Faith graph bindings") ||
      !Check(At(b.faith_characters, base, 0x1C610C0) &&
             At(b.rite_counties, base, 0x1D2B6D0) &&
             At(b.title_storage_slot, base, 0x5D1DAF8),
             "actual4 complete native collectors and Title storage") ||
      !Check(At(b.faith_rites, base, 0xB801B0) &&
             At(b.effective_skill, base, 0x28B1690) &&
             At(b.is_imprisoned, base, 0x28C2080) &&
             At(b.adult_threshold_zero, base, 0x5C6A15C) &&
             At(b.adult_threshold_one, base, 0x5C69D10),
             "actual4 bounded getters and independently proved age slots")) return 1;
  legacy::Snapshot unavailable;
  if (!Check(!legacy::ReadCurrentFaithPredicates(
                 actual::BindImage(0, xar::ck3_12004::kExecutableSha256), 12004, unavailable) &&
             unavailable.native_build == legacy::NativeBuild::crozier_12004 &&
             unavailable.capture_epoch == 12004,
             "failed actual4 binding preserves actual identity and UNKNOWN") ||
      !Check(legacy::Serialize(unavailable).find("\"game_version\":\"1.20.0.4\"") != std::string::npos &&
             legacy::Serialize(unavailable).find(xar::ck3_12004::kExecutableSha256) != std::string::npos &&
             legacy::Serialize(unavailable).find("\"members\":null") != std::string::npos,
             "actual4 serializer identity and unavailable members") ||
      !Check(legacy::Serialize({}).find("\"game_version\":\"1.20.0.3\"") != std::string::npos &&
             legacy::BackendId(legacy::NativeBuild::crozier_12003) ==
                 "ck3-1.20.0.3-native-confucian-assembly-predicates-v1" &&
             legacy::BackendId(legacy::NativeBuild::crozier_12004) ==
                 "ck3-1.20.0.4-native-confucian-assembly-predicates-v1",
             "historical default tuple and independent actual4 backend")) return 2;
  std::cout << "PASS checks=" << checks << " binding_fixture=true unavailable_reader_path=true actual_serializer=true live=false\n";
  return 0;
}
