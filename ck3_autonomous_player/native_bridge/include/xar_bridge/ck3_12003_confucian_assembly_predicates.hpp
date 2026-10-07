#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_phase_character.hpp"
#include "xar_bridge/religion_rite_governance12002_organization_members.hpp"

#include <optional>
#include <string>
#include <vector>

// This additive observation does not run a script trigger, issue a command,
// change a vote, or select a candidate. All fields come from the paused native
// Faith graph; the application-main query mailbox is the sole live caller.
namespace xar::ck3_12003::confucian_assembly {

using ObjectGetter = void *(*)(void *);
using ContainerGetter = const void *(*)(void *);
using BoolGetter = bool (*)(void *);
using EffectiveSkillGetter = std::int32_t (*)(void *, std::int32_t);
using Collector = ck3_12002::religion::organization::members::Collector;
using CoreSnapshotReader = bool (*)(const ck3_12002::CoreBindings &,
                                   ck3_12002::CoreSnapshotPrefix &) noexcept;
using CoreCharacterResolver = void *(*)(const ck3_12002::CoreBindings &,
                                       std::int32_t) noexcept;

enum class NativeBuild { crozier_12003, crozier_12004 };
std::string_view GameVersion(NativeBuild) noexcept;
std::string_view ExecutableSha256(NativeBuild) noexcept;
std::string_view BackendId(NativeBuild) noexcept;

struct Bindings {
  bool enabled = false;
  NativeBuild native_build = NativeBuild::crozier_12003;
  ck3_12002::CoreBindings core{};
  CoreSnapshotReader read_core_snapshot = &ck3_12002::ReadCoreSnapshot;
  CoreCharacterResolver resolve_core_character = &ck3_12002::ResolveCoreCharacter;
  ck3_12002::phase_character::Bindings traits{};
  void **rite_storage_slot = nullptr;
  void **title_storage_slot = nullptr;
  ObjectGetter character_rite = nullptr;
  ObjectGetter rite_faith = nullptr;
  ObjectGetter faith_religion = nullptr;
  ContainerGetter faith_rites = nullptr;
  Collector faith_characters = nullptr;
  Collector rite_counties = nullptr;
  EffectiveSkillGetter effective_skill = nullptr;
  const std::int32_t *adult_threshold_zero = nullptr;
  const std::int32_t *adult_threshold_one = nullptr;
  // A null getter means that this predicate has no qualified current-build
  // binding. The result remains UNKNOWN; custody presence is not substituted.
  BoolGetter is_imprisoned = nullptr;
};

struct CharacterPredicate {
  std::uint32_t character_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<bool> alive;
  std::optional<bool> adult;
  std::optional<bool> imprisoned;
  std::optional<bool> incapable;
  std::optional<bool> is_ai;
  std::optional<std::int32_t> effective_learning;
  std::optional<std::int16_t> adult_measure_raw;
  std::optional<std::uint8_t> adult_selector_raw;
  std::optional<std::int32_t> adult_threshold_raw;
  bool complete = false;
  std::string unavailable_reason;
  bool operator==(const CharacterPredicate &) const = default;
};

struct RiteCounties {
  std::uint32_t rite_id = 0xFFFFFFFFU;
  std::vector<std::uint32_t> county_title_ids;
  bool complete = false;
  std::string unavailable_reason;
  bool operator==(const RiteCounties &) const = default;
};

struct Snapshot {
  NativeBuild native_build = NativeBuild::crozier_12003;
  bool available = false;
  bool predicates_complete = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::uint32_t> played_rite_id;
  std::optional<std::uint32_t> religion_id;
  std::optional<std::int32_t> alive_source_pool_count;
  std::optional<std::int32_t> religion_county_source_pool_count;
  std::vector<std::uint32_t> complete_native_faith_member_ids;
  std::vector<std::uint32_t> complete_native_faith_rite_ids;
  std::vector<CharacterPredicate> members;
  std::vector<RiteCounties> rites;
};

// Exact 1.20.0.3 identity only. The historical .2 leaf DTOs retain their gates;
// this binder installs the independently qualified .3 addresses directly.
Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;

bool ReadCurrentFaithPredicates(const Bindings &, std::uint64_t capture_epoch,
                               Snapshot &) noexcept;
std::string Serialize(const Snapshot &);

} // namespace xar::ck3_12003::confucian_assembly
