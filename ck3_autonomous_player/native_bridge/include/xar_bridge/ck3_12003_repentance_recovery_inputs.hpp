#pragma once

#include "xar_bridge/ck3_12002_religion_conversion_gates.hpp"
#include <optional>
#include <string>

namespace xar::ck3_12003::religion::repentance_recovery_inputs {
using ExistingAtomLookup = xar::ck3_12002::religion::conversion_gates::ExistingAtomLookup;
using NativeStringView = xar::ck3_12002::religion::conversion_gates::NativeStringView;
using ObjectGetter = void* (*)(void*);
using HighestHeldTier = std::int32_t (*)(void*);
using ModifierDatabase = void* (*)();
using StableKeyHash = std::uint32_t (*)(void*, const char*, std::uint32_t);
using ModifierLookup = void* (*)(void*, std::int32_t);
struct Bindings {
  bool enabled = false;
  ExistingAtomLookup existing_atom = nullptr;
  void* atom_pool = nullptr;
  ObjectGetter character_flag_collection = nullptr;
  HighestHeldTier highest_held_tier = nullptr;
  void** title_storage_slot = nullptr;
  ModifierDatabase modifier_database = nullptr;
  StableKeyHash stable_key_hash = nullptr;
  ModifierLookup modifier_lookup = nullptr;
  void** modifier_fallback_slot = nullptr;
};
struct BoolObservation {
  bool available = false;
  const char* reason = "bindings_unavailable";
  std::optional<bool> value;
};
struct NumberObservation {
  bool available = false;
  const char* reason = "bindings_unavailable";
  std::optional<std::int32_t> value;
};
struct ModifierObservation {
  bool available = false;
  const char* reason = "bindings_unavailable";
  std::optional<bool> present;
  std::optional<std::int32_t> expiry_date_raw;
  std::optional<std::int64_t> remaining_calendar_days;
};
struct Context {
  bool available = false;
  std::int32_t played_character_id = -1;
  std::int32_t date_raw = 0;
  std::uint64_t capture_epoch = 0;
  BoolObservation pope_excom;
  ModifierObservation recent_excommunication;
  ModifierObservation promised_pilgrimage_to_clergy;
  NumberObservation highest_held_title_tier;
  BoolObservation any_held_title_has_clerical_region;
};
Bindings BindPlayerRepentanceRecoveryInputsImage12003(std::uintptr_t, std::string_view) noexcept;
// Called inside the existing application-main paused owner. The parent supplies
// the already resolved played actor and the same date/epoch stamp.
bool ReadPlayerRepentanceRecoveryInputs12003(const Bindings&, void* actor,
    std::int32_t expected_actor_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Context&) noexcept;
std::string SerializePlayerRepentanceRecoveryInputs12003(const Context&);
} // namespace xar::ck3_12003::religion::repentance_recovery_inputs
