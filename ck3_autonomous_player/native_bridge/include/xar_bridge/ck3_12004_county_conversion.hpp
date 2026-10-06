#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_clergy_appointment.hpp"
#include "xar_bridge/ck3_12003_county_conversion.hpp"

namespace xar::ck3_12004::religion::county_conversion {

// Reuse software DTOs and callable signatures. No old image binder or reader
// is admitted by the actual .4 entry points.
namespace dto = ck3_12003::religion::county_conversion;
using NativeVector = dto::NativeVector;
using HashKey = dto::HashKey;
using LookupType = dto::LookupType;
using Shown = dto::Shown;
using Valid = dto::Valid;
using TargetValid = dto::TargetValid;
using ProduceTargets = dto::ProduceTargets;
using EvaluatedTaskMonthlyRate = dto::EvaluatedTaskMonthlyRate;
using CountyRiteGetter = dto::CountyRiteGetter;
using ObjectGetter = dto::ObjectGetter;
using IdentifierName = dto::IdentifierName;
using CountyOpinionGetter = dto::CountyOpinionGetter;
using ChangeCouncilTaskFinalValidator = dto::ChangeCouncilTaskFinalValidator;
using Failure = dto::Failure;
using Candidate = dto::Candidate;
using CountyValueInputs = dto::CountyValueInputs;
using ValueInputs = dto::ValueInputs;
using TaskDispatchCandidate = dto::TaskDispatchCandidate;
using TaskDispatch = dto::TaskDispatch;
using Observation = dto::Observation;
using AllocatorBindings = ck3_12002::CouncilCandidatesEnvironmentV1;

inline constexpr std::string_view kTaskKey = dto::kTaskKey;
inline constexpr std::int64_t kFixedPointScale = dto::kFixedPointScale;

struct Environment {
  bool exact_build_admitted = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::string_view executable_sha256{};
  std::uint32_t application_main_thread_id = 0;
  ck3_12004::religion::clergy::Bindings clergy{};
  AllocatorBindings allocator{};
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
  bool value_inputs_enabled = false;
  ObjectGetter character_rite = nullptr;
  ObjectGetter rite_faith = nullptr;
  ObjectGetter government = nullptr;
  ObjectGetter title_by_key = nullptr;
  IdentifierName identifier_name = nullptr;
  CountyOpinionGetter county_opinion = nullptr;
  void **government_fallback_slot = nullptr;
  bool task_dispatch_enabled = false;
  ChangeCouncilTaskFinalValidator final_task_validator = nullptr;
};

// Address calculation against the actual .4 ABI ledger only.
Environment BindCountyConversionImage12004(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

// Existing application-main paused transaction. Every core, character and
// clergy-seat read selects actual .4 native bindings; fields/failures retain
// the adopted county DTO, including independent value and dispatch inputs.
bool ReadCountyConversion12004(const Environment &, std::uint64_t capture_epoch,
    Observation &) noexcept;
bool ReadCountyConversionCommandMaterial12004(const Environment &,
    const Observation &, const void *&conversion_type,
    std::optional<std::uint16_t> &current_target_scope_tag) noexcept;

// Pure software serialization uses the existing schema and actual .4 identity.
std::string SerializeCountyConversion12004(const Observation &);
const char *CountyConversionFailureKey12004(Failure) noexcept;

} // namespace xar::ck3_12004::religion::county_conversion
