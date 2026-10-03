#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_council_candidates.hpp"
#include "xar_bridge/religion_rite_governance12002_clergy.hpp"

#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12003::religion::county_conversion {

inline constexpr std::string_view kTaskKey = "task_conversion";
inline constexpr std::int64_t kFixedPointScale = 100'000;
inline constexpr std::uintptr_t kMonthlyRateRva = 0x31ADC60;
inline constexpr std::uintptr_t kCountyRiteRva = 0x24D6350;

using NativeVector = ck3_12002::CouncilCandidatesNativeVectorV1;
using HashKey = std::int32_t (*)(void *, const char *, std::uint32_t);
using LookupType = const void *(*)(const void *, std::int32_t);
using Shown = bool (*)(const void *, const void *);
using Valid = bool (*)(const void *, const void *, void *);
using TargetValid = bool (*)(const void *, const void *, const void *, void *);
using ProduceTargets = void (*)(const void *, const void *, bool, NativeVector *, bool);
using EvaluatedTaskMonthlyRate = std::int64_t *(*)(
    const void *, std::int64_t *, const void *, void *, bool);
using CountyRiteGetter = const void *(*)(const void *);

struct Environment {
  bool exact_build_admitted = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  std::uint32_t application_main_thread_id = 0;
  ck3_12002::religion::clergy::Bindings clergy{};
  ck3_12002::CouncilCandidatesEnvironmentV1 allocator{};
  void **game_state_slot = nullptr;
  void **title_storage_slot = nullptr;
  void **title_fallback_slot = nullptr;
  void **task_type_database_slot = nullptr;
  void **task_type_fallback_slot = nullptr;
  HashKey hash_key = nullptr;
  LookupType lookup_type = nullptr;
  Shown shown = nullptr;
  Valid valid = nullptr;
  TargetValid target_valid = nullptr;
  ProduceTargets produce_targets = nullptr;
  EvaluatedTaskMonthlyRate monthly_rate = nullptr;
  CountyRiteGetter county_rite = nullptr;
};

enum class Failure {
  none,
  bindings_unavailable,
  owner_thread_required,
  frame_unavailable,
  not_paused,
  player_unavailable,
  clergy_seat_unavailable,
  task_type_unavailable,
  current_task_unavailable,
  candidate_collection_unavailable,
  county_identity_unavailable,
  county_rite_unavailable,
  native_evaluation_unavailable,
  state_changed,
  reader_exception,
};

struct Candidate {
  std::uint32_t native_collection_ordinal = 0;
  std::int32_t province_id = -1;
  std::int32_t county_title_id = -1;
  std::int32_t holder_character_id = -1;
  std::optional<std::uint32_t> county_rite_id;
  bool directly_held_by_player = false;
  bool native_target_valid = false;
  std::optional<std::int64_t> native_monthly_rate_raw;
};

struct Observation {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t owner_character_id = -1;
  std::optional<std::uint32_t> owner_rite_id;
  bool position_present = false;
  std::optional<std::int32_t> incumbent_character_id;
  std::optional<std::uint32_t> incumbent_rite_id;
  std::optional<std::int32_t> active_task_id;
  std::string current_task_key;
  std::optional<std::int32_t> current_task_type;
  std::optional<std::int32_t> current_progress_kind;
  std::optional<bool> current_task_frozen;
  std::optional<std::int64_t> current_percentage_progress_raw;
  std::optional<std::int64_t> current_conversion_monthly_rate_raw;
  std::optional<std::int32_t> current_target_province_id;
  std::optional<std::int32_t> current_target_county_title_id;
  std::optional<std::uint32_t> current_target_county_rite_id;
  std::optional<bool> native_task_shown;
  std::optional<bool> native_task_valid;
  bool candidate_collection_evaluated = false;
  bool candidate_collection_complete = false;
  std::vector<Candidate> candidates;
};

Environment BindCountyConversionImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Read-only, existing application-main paused owner. Temporary scopes contain
// real owner/incumbent IDs and each native Province target; no task is allocated
// or reassigned. The numeric core is called with a null GUI breakdown.
bool ReadCountyConversion12003(const Environment &environment,
    std::uint64_t capture_epoch, Observation &output) noexcept;
std::string SerializeCountyConversion12003(const Observation &value);
const char *CountyConversionFailureKey(Failure value) noexcept;

} // namespace xar::ck3_12003::religion::county_conversion
