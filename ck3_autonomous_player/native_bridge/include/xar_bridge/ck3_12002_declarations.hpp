#pragma once

#include "xar_bridge/ck3_12002_commands.hpp"

#include <vector>
#include <span>

namespace xar::ck3_12002 {

inline constexpr std::uintptr_t kDeclarationsCbDatabaseGetterRva = 0x8FC320;
inline constexpr std::uintptr_t kDeclarationsInteractionDatabaseGetterRva = 0x89DA60;
inline constexpr std::uintptr_t kDeclarationsEvaluateCbRva = 0x31F4540;
inline constexpr std::uintptr_t kDeclarationsScratchRva = 0x54E14B8;
inline constexpr std::uintptr_t kDeclarationsDestroyConfigurationRva = 0x111F190;
inline constexpr std::uintptr_t kDeclarationsConstructContextRva = 0x3076C90;
inline constexpr std::uintptr_t kDeclarationsRefreshContextRva = 0x3078A60;
inline constexpr std::uintptr_t kDeclarationsFinalizeContextRva = 0x3078C90;
inline constexpr std::uintptr_t kDeclarationsValidateContextRva = 0x307C040;
inline constexpr std::uintptr_t kDeclarationsDestroyContextRva = 0x30773A0;
inline constexpr std::uintptr_t kDeclarationsConstructSendRva = 0x2968170;
inline constexpr std::uintptr_t kDeclarationsCopyIntArrayRva = 0xC858C0;
inline constexpr std::uintptr_t kDeclarationsAppendIntArrayRva = 0x9E3790;
inline constexpr std::uintptr_t kDeclarationsWarVtableRva = 0x452FFC0;
inline constexpr std::uintptr_t kDeclarationsSendPrimaryVtableRva = 0x448BCE0;
inline constexpr std::uintptr_t kDeclarationsSendSecondaryVtableRva = 0x448BCB0;
inline constexpr std::size_t kDeclarationsInteractionOffset = 0xF60;
inline constexpr std::size_t kDeclarationsCbArrayOffset = 0x50;
inline constexpr std::size_t kDeclarationsCbCountOffset = 0x5C;
inline constexpr std::size_t kDeclarationsCbRuleOffset = 0x40;
inline constexpr std::size_t kDeclarationsCbDisabledOffset = 0x1F9;
inline constexpr std::size_t kDeclarationsCbFlagsOffset = 0x1548;
inline constexpr std::size_t kDeclarationsConfigurationSize = 0x98;
inline constexpr std::size_t kDeclarationsContextSize = 0x338;
inline constexpr std::size_t kDeclarationsSendSize = 0x368;
inline constexpr std::size_t kDeclarationsSpecialDataOffset = 0x330;
inline constexpr std::size_t kDeclarationsAdditionalRoleOffset = 0x2EC;
inline constexpr std::size_t kDeclarationsSendContextOffset = 0x20;
inline constexpr std::size_t kDeclarationsWarCbOffset = 0x08;
inline constexpr std::size_t kDeclarationsWarTitlesOffset = 0x10;
inline constexpr std::size_t kDeclarationsWarClaimantOffset = 0x28;

using DeclarationsDatabaseGetter = void *(*)();
using DeclarationsEvaluateCb = bool (*)(void *, void *, void *, void *, bool,
                                       bool, void *);
using DeclarationsDestroy = void (*)(void *);
// The final bool enables native role redirection. In 1.20 its implementation
// redirects six CharacterID roles, including the new context +0x2EC role.
using DeclarationsConstructContext = void *(*)(void *, void *, std::int32_t,
                                               std::int32_t, void *, bool);
using DeclarationsRefreshContext = void (*)(void *, bool);
using DeclarationsValidateContext = bool (*)(void *, void *);
using DeclarationsConstructSend = void *(*)(void *, const void *);
using DeclarationsCopyIntArray = void (*)(void *, const void *);
using DeclarationsAppendIntArray = void (*)(void *, std::int32_t,
                                            const std::int32_t *,
                                            const std::int32_t *);

enum class DeclarationsCandidateVariantV1 { full, cb_first, shadow };
enum class DeclarationsCandidateFactV1 { unknown, no, yes };
struct DeclarationsCandidateFactsV1 {
  DeclarationsCandidateFactV1 landed = DeclarationsCandidateFactV1::unknown;
  DeclarationsCandidateFactV1 independent = DeclarationsCandidateFactV1::unknown;
};
using DeclarationsCandidateFactsReaderV1 = bool (*)(
    std::uintptr_t, void *, DeclarationsCandidateFactsV1 &) noexcept;
using DeclarationsCandidateRealmReaderV1 = bool (*)(
    std::uintptr_t, void *, std::vector<void *> &) noexcept;
inline constexpr std::uint32_t kDeclarationsCandidateLandedV1 = 1;
inline constexpr std::uint32_t kDeclarationsCandidateIndependentV1 = 2;
// Entries must come from this loaded definition set's qualified source
// manifest, including override resolution. A same-named CB or EXE hash alone
// is not qualification. Missing/unknown rules and facts retain the wide set.
struct DeclarationsCandidateRuleV1 {
  std::string_view key;
  std::string_view definition_source_sha256;
  std::uint32_t necessary_conditions = 0;
};
struct DeclarationsCandidateOptionsV1 {
  DeclarationsCandidateVariantV1 variant = DeclarationsCandidateVariantV1::full;
  std::span<const DeclarationsCandidateRuleV1> qualified_rules;
  std::string_view qualified_source_manifest_sha256;
  // Optional launch-bound controlled file, read at each existing query entry.
  // Accepts only full/shadow-v1/cb-first-v1; unavailable/malformed means full.
  std::string_view runtime_policy_path;
};
struct DeclarationsCandidateCbDiagnosticV1 {
  std::int32_t ordinal = -1;
  std::string key;
  std::uint64_t full_targets = 0, candidates = 0, evaluations = 0;
  std::uint64_t baseline_evaluations = 0, candidate_rows = 0, baseline_rows = 0;
  std::uint64_t missing_tuples = 0, extra_tuples = 0;
  std::uint32_t necessary_conditions = 0;
  std::string definition_source_sha256;
  std::int32_t native_target_titles_mode = -1;
  bool native_realm_index_used = false;
  std::uint64_t projected_candidate_evaluations = 0;
};
struct DeclarationsCandidateDiagnosticV1 {
  bool source_qualified = false, baseline_compared = false;
  bool same_frame = false, tuple_sets_equal = false;
  std::string qualified_source_manifest_sha256;
  bool native_realm_index_complete = false;
  std::uint64_t native_realm_index_entries = 0;
  std::vector<DeclarationsCandidateCbDiagnosticV1> casus_belli;
};

struct DeclarationsBindings {
  bool enabled = false;
  CoreBindings core;
  CommandBindings commands;
  void *configuration_scratch = nullptr;
  DeclarationsDatabaseGetter get_cb_database = nullptr;
  DeclarationsDatabaseGetter get_interaction_database = nullptr;
  DeclarationsEvaluateCb evaluate_cb = nullptr;
  DeclarationsDestroy destroy_configuration = nullptr;
  DeclarationsConstructContext construct_context = nullptr;
  DeclarationsRefreshContext refresh_context = nullptr;
  DeclarationsDestroy finalize_context = nullptr;
  DeclarationsValidateContext validate_context = nullptr;
  DeclarationsDestroy destroy_context = nullptr;
  DeclarationsConstructSend construct_send = nullptr;
  DeclarationsCopyIntArray copy_int_array = nullptr;
  DeclarationsAppendIntArray append_int_array = nullptr;
  std::uintptr_t war_declaration_vtable = 0;
  std::uintptr_t send_primary_vtable = 0;
  std::uintptr_t send_secondary_vtable = 0;
  std::uintptr_t candidate_provider_image_base = 0;
  DeclarationsCandidateFactsReaderV1 read_candidate_facts = nullptr;
  DeclarationsCandidateRealmReaderV1 read_candidate_realm = nullptr;
  std::size_t candidate_target_titles_mode_offset = 0;
  DeclarationsCandidateOptionsV1 candidate_options;
};

DeclarationsBindings BindDeclarationsImage(std::uintptr_t image_base,
                                            std::string_view sha256) noexcept;

// The native evaluator owns a shared scratch array: run on the owning thread
// against a paused map, through the adapter's main-thread mailbox.
game::ReadDeclarableWarsResult ReadDeclarableWarsForTarget(
    const DeclarationsBindings &, std::int32_t target_character_id,
    std::vector<game::DeclarableWarSnapshot> &output) noexcept;
// Optional offline profiling: set XAR_CK3_DECLARATIONS_PROFILE_JSONL to an
// existing output directory's JSONL filename before launching CK3.
// Full enumeration semantics are unchanged; an unset/empty value disables
// timing, counter updates and file output. Failure to write is diagnostic only.
bool ReadDeclarableWars(const DeclarationsBindings &,
                       std::vector<game::DeclarableWarSnapshot> &) noexcept;
// Opt-in CB -> conservative target superset -> unchanged stock false,false
// evaluation/materialization. Shadow returns the original full result even
// on parity failure. Full remains the default and submit re-evaluates normally.
bool ReadDeclarableWarsWithCandidatesV1(
    const DeclarationsBindings &, const DeclarationsCandidateOptionsV1 &,
    std::vector<game::DeclarableWarSnapshot> &,
    DeclarationsCandidateDiagnosticV1 * = nullptr) noexcept;
game::DeclareWarResult SubmitDeclareWar(
    const DeclarationsBindings &, const game::DeclarableWarSnapshot &) noexcept;

} // namespace xar::ck3_12002
