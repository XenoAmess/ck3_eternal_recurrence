#pragma once

#include "xar_bridge/ck3_12002_religion_conversion_gates.hpp"

namespace xar::ck3_12002::religion_conversion::outcome::state {

inline constexpr char kRecentConversionFlag[] = "faith_conversion_recently_converted";
inline constexpr char kConversionMemoryFlag[] = "conversion_memory_recently_created";
inline constexpr char kNarrativeRecentConvertFlag[] = "recent_convert";
inline constexpr std::size_t kFlagExpiryCounterOffset = 0x0C;
inline constexpr std::size_t kFlagCurrentCounterOffset = 0x28;
inline constexpr std::size_t kBaselineFulfillmentOffset = 0x300;

using NativeStringView = religion::conversion_gates::NativeStringView;
using KnowledgeGetter = religion::conversion_gates::KnowledgeGetter;
using ExistingAtomLookup = religion::conversion_gates::ExistingAtomLookup;

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  void **rite_storage_slot = nullptr;
  KnowledgeGetter rite_knowledge = nullptr;
  ExistingAtomLookup existing_atom = nullptr;
  void *atom_pool = nullptr;
  religion::ObjectGetter character_flag_collection = nullptr;
  religion::FixedPointGetter character_spiritual_fulfillment = nullptr;
};

enum class Failure {
  none, bindings_unavailable, played_character_unavailable, frame_not_paused,
  target_rite_unavailable, knowledge_unavailable, fulfillment_unavailable,
  flag_pool_unavailable, flag_collection_unavailable, state_changed,
};

struct FlagObservation {
  std::optional<bool> key_registered;
  std::optional<bool> present;
  std::optional<bool> timed;
  // Native FlagSet uses its own update counter, not the game's calendar date.
  // A present permanent flag preserves the native <= -1 expiry sentinel.
  std::optional<std::int32_t> expiry_counter_raw;
  std::optional<std::int32_t> current_counter_raw;
  std::optional<std::int64_t> remaining_updates;
  bool operator==(const FlagObservation &) const = default;
};

struct Context {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = religion::kAbsentReference;
  std::uint32_t requested_target_rite_id = religion::kAbsentReference;
  std::optional<std::uint32_t> target_rite_id;
  std::optional<std::int64_t> knowledge_level_raw;
  std::optional<std::int64_t> spiritual_fulfillment_raw;
  std::optional<std::int64_t> baseline_spiritual_fulfillment_raw;
  FlagObservation faith_conversion_recently_converted;
  FlagObservation conversion_memory_recently_created;
  FlagObservation recent_convert;
};

Bindings BindConversionOutcomeStateImage12002(std::uintptr_t module_base,
                                             std::string_view executable_sha256) noexcept;
bool ReadPlayedConversionOutcomeState12002(const Bindings &, std::uint32_t target_rite_id,
                                           std::uint64_t capture_epoch, Context &) noexcept;
std::string SerializePlayedConversionOutcomeState12002(const Context &);
const char *ConversionOutcomeStateFailureKey(Failure) noexcept;

} // namespace xar::ck3_12002::religion_conversion::outcome::state
