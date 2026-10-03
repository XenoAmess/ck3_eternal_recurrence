#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/ck3_12003_repentance_recipient_candidates.hpp"
#include "xar_bridge/religion_doctrine12002_intrinsic.hpp"
#include "xar_bridge/religion_doctrine12002_tenet.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::repentance_pam_route {

inline constexpr std::string_view kSchema = "ck3_12003_repentance_pam_route_v1";
inline constexpr const char *kEvaluator = "stock_exact_typed_inputs";
inline constexpr std::uintptr_t kFeatureRootSlotRva = 0x5CB87F8;
inline constexpr std::uintptr_t kFeatureEnumTableRva = 0x47334C0;
inline constexpr std::size_t kEffectiveFeatureBitsOffset = 0x2B0;
inline constexpr std::uint32_t kPamFeatureIndex = 43, kPamFeatureIdentifier = 0x4169;

struct Bindings {
  bool enabled = false;
  const std::uintptr_t *feature_root_slot = nullptr;
  const std::uint32_t *feature_enum_table = nullptr;
};

struct BoolObservation {
  bool available = false;
  const char *reason = "not_sampled";
  std::optional<bool> value;
};

// Parent copies these three independent sibling raw leaves only after reading
// them in this same owner frame. No prior external query or cached DTO is used.
struct RawRouteInputs {
  bool available = false;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<bool> pope_excom;
  std::optional<std::int32_t> highest_held_title_tier;
  std::optional<bool> any_held_title_has_clerical_region;
};

struct CandidateRoute {
  std::int32_t requested_recipient_character_id = -1;
  BoolObservation recipient_is_religious_authority;
  BoolObservation pam_ordinary_route_clause_passes;
};

struct Context {
  bool available = false;
  const char *reason = "bindings_unavailable";
  const char *evaluator = kEvaluator;
  bool compiled_named_trigger_invoked = false;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::uint32_t> current_rite_id, faith_id, faith_main_rite_id;
  std::optional<std::string> religion_key;
  BoolObservation faith_main_rite_spiritual_head_of_faith;
  const char *faith_central_sacraments_source = "faith_main_rite_effective_doctrines";
  BoolObservation has_pam_dlc;
  BoolObservation faith_qualifies_for_pam_clergy_route;
  BoolObservation religious_authority_exists;
  BoolObservation capital_clerical_holder_is_religious_authority;
  BoolObservation capital_clerical_holder_is_actor;
  BoolObservation petition_head_of_faith_repentance_requires_petition;
  BoolObservation need_hof_for_clergy_interaction;
  BoolObservation is_archbishop_or_higher;
  BoolObservation faith_has_central_sacraments;
  std::vector<CandidateRoute> candidates;
};

Bindings BindRepentancePamRouteImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;

// Fresh typed providers must share actual actor/date/epoch, Faith and main Rite.
// Native stock source formulas and scalar ?= semantics are frozen before this
// leaf. This evaluator is not a compiled named trigger invocation. Its route
// clause is one input to native final validity, never permission to submit a
// selected repentance petition or ordinary interaction.
bool ReadRepentancePamRoute12003(const Bindings &, void *actual_played_character,
    std::int32_t actor, std::int32_t date, std::uint64_t epoch,
    const ck3_12002::religion::Context &religion,
    const ck3_12002::religion::doctrine12002::TenetParameterContext &parameters,
    const ck3_12002::religion::doctrine12002::FaithMainRiteDoctrines &doctrines,
    const repentance_candidates::Context &current_candidates,
    const RawRouteInputs &raw, Context &output) noexcept;
std::string SerializeRepentancePamRoute12003(const Context &);

} // namespace xar::ck3_12003::religion::repentance_pam_route
