#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_phase_definitions.hpp"
#include "xar_bridge/player_epidemic_recovery_v1.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002::epidemic_recovery {

// Only presence is published. The native time value has no asserted unit.
struct CountyModifierResult {
  std::uint64_t native_time = 0;
  std::uint8_t present = 0;
  std::array<std::uint8_t, 7> padding{};
};
static_assert(sizeof(CountyModifierResult) == 0x10);

using ModifierDatabase = void *(*)();
using StableKeyHash = std::uint32_t (*)(void *, const char *, std::uint32_t);
using ModifierLookup = void *(*)(void *, std::int32_t);
using CountyModifierGetter = CountyModifierResult *(*)(
    CountyModifierResult *, void *, void *);

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  PhaseDefinitionBindings identifiers{};
  void **landed_title_store_slot = nullptr;
  void **modifier_fallback_slot = nullptr;
  ModifierDatabase modifier_database = nullptr;
  StableKeyHash stable_key_hash = nullptr;
  ModifierLookup modifier_lookup = nullptr;
  CountyModifierGetter county_modifier_getter = nullptr;
};

// Pure address calculation; no process discovery. Actual addresses are frozen
// by event12002_recovery_*_abi evidence for the exact executable.
Bindings BindImage(std::uintptr_t base, std::string_view executable_sha256) noexcept;

// Existing v1 wire semantics: title 0 lists the player's saved recovery
// targets; a positive title queries that frozen county after list clearing.
ck3_11906::PlayerEpidemicRecoveryV1 ReadEpidemicRecovery12002(
    const Bindings &bindings, std::uint64_t revision, std::int32_t date_raw,
    std::int32_t played_character_id, std::int32_t requested_title_id) noexcept;

} // namespace xar::ck3_12002::epidemic_recovery
