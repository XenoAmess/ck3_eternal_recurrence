#pragma once

#include "xar_bridge/combat_phase_event_trace_ring_v1.hpp"

#include <array>
#include <atomic>
#include <cstdint>
#include <string>

namespace xar::ck3_11906 {

// Private exact-build observer. It never advances CK3 and is armed only by the
// existing recoverable-checkpoint / paused application-main trace transaction.
inline constexpr std::size_t kCombatScopedChainMaxRecordsV1 = 256;
inline constexpr std::size_t kCombatScopedChainMaxTraitsV1 = 128;
inline constexpr std::size_t kCombatScopedChainMaxEntriesV1 = 2048;
inline constexpr std::size_t kCombatScopedChainMaxTraitDefinitionsV1 = 8192;
inline constexpr std::size_t kCombatScopedChainMaxTraitTracksV1 = 256;
inline constexpr std::size_t kCombatScopedChainMaxEffectChildrenV1 = 256;
struct CombatScopedStableKeyV1 {
  std::uint32_t size = 0;
  std::array<char, 128> bytes{};
  friend bool operator==(const CombatScopedStableKeyV1 &,const CombatScopedStableKeyV1 &)=default;
};
struct CombatScopedTraitDefinitionV1 {
  std::int32_t trait_id = -1;
  CombatScopedStableKeyV1 key{};
  // Exact native getter 260F674 / prefix accumulator 260EB86: definition+294.
  // This is a signed number of flat XP entries, not a symbolic track ID.
  std::int32_t track_count = -1;
};

enum class CombatScopedChainBoundaryV1 : std::uint32_t {
  arm_paused = 0,
  phase_before = 1,
  phase_after = 2,
  effect_enter = 3,
  effect_return = 4,
  selector_enter = 5,
  selector_return = 6,
  death_request_enter = 7,
  death_request_return = 8,
  death_enqueue_enter = 9,
  death_enqueue_return = 10,
  death_commit_enter = 11,
  death_commit_return = 12,
  casualty_enter = 13,
  casualty_return = 14,
  next_paused = 15,
  filter_enter = 16,
  materializer_enter = 17,
  materializer_return = 18,
  predicate_enter = 19,
  predicate_return = 20,
  filter_return = 21,
  list_write_enter = 22,
  list_write_return = 23,
};

enum CombatScopedChainFailureV1 : std::uint32_t {
  scoped_chain_failure_none = 0,
  scoped_chain_failure_binding = 1U << 0,
  scoped_chain_failure_identity = 1U << 1,
  scoped_chain_failure_container = 1U << 2,
  scoped_chain_failure_capacity = 1U << 3,
  scoped_chain_failure_memory = 1U << 4,
  scoped_chain_failure_thread_or_date = 1U << 5,
  scoped_chain_failure_detour = 1U << 6,
  scoped_chain_failure_correlation = 1U << 7,
};

struct CombatScopedCharacterV1 {
  std::int32_t character_id = -1;
  std::int32_t observed_character_id = -1;
  bool identity_matches = false;
  std::int32_t martial = 0;
  std::int32_t learning = 0;
  std::int32_t prowess = 0;
  bool prestige_read = false;
  std::int64_t prestige_currency_raw = 0;
  std::int64_t prestige_experience_raw = 0;
  std::uintptr_t regiment_link = 0;
  std::int32_t current_regiment_id = -1;
  bool current_regiment_identity_matches = false;
  bool current_regiment_back_reference_matches = false;
  bool death_marker_present = false;
  bool death_details_read = false;
  std::int64_t death_date_raw = 0;
  std::uintptr_t death_reason = 0;
  CombatScopedStableKeyV1 death_reason_key{};
  std::int32_t death_killer_character_id = -1;
  std::int32_t death_artifact_id = -1;
  // No trait ABI is inferred from a save parser. The source reader must be
  // independently anchored before this domain can contribute to completeness.
  bool traits_read = false;
  std::uint32_t trait_count = 0;
  std::array<std::int32_t, kCombatScopedChainMaxTraitsV1> trait_ids{};
  bool trait_tracks_read = false;
  std::uint32_t trait_track_raw_count = 0;
  std::array<std::int64_t, kCombatScopedChainMaxTraitTracksV1> trait_track_raw_values{};
  bool kills_read = false;
  std::uint32_t kill_count = 0;
  std::array<std::int32_t, 512> kill_character_ids{};
};

struct CombatScopedEntryV1 {
  std::int32_t regiment_id = -1;
  std::int32_t army_id = -1;
  std::int32_t character_id = -1;
  std::uint32_t bucket = 0;
  std::int64_t starting_raw = 0;
  std::int64_t current_raw = 0;
  std::int64_t soft_raw = 0;
  std::int64_t effective_damage_raw = 0;
  std::int64_t effective_toughness_raw = 0;
};

struct CombatScopedSelectorCandidateV1 {
  std::uint64_t scope_word0 = 0;
  std::uint64_t scope_word1 = 0;
  std::int32_t character_id = -1;
  bool character_full_identity_matches = false;
};

struct CombatScopedEntrySnapshotV1 {
  std::array<std::uint32_t, 2> entry_count{};
  std::array<std::array<CombatScopedEntryV1, kCombatScopedChainMaxEntriesV1>, 2> entries{};
  std::array<std::uint32_t, 2> owner_hard_count{};
  std::array<std::array<CombatPhaseEventTraceHardOwnerRowV1,
                       kCombatPhaseEventTraceRingV1MaximumHardOwnersPerSide>, 2> owner_hard{};
};
struct CombatScopedBattleEventSnapshotV1 {
  std::uint32_t count=0;
  std::array<CombatPhaseEventTraceBattleEventRecordV1,256> rows{};
};

struct CombatScopedEffectIdentityV1 {
  std::uintptr_t node = 0;
  std::uint32_t vtable_rva = 0, hash = 0, original_execute_rva = 0;
  bool read = false;
  friend bool operator==(const CombatScopedEffectIdentityV1 &,
                         const CombatScopedEffectIdentityV1 &) = default;
};

struct CombatScopedScriptedDefinitionV1 {
  bool read = false;
  std::uintptr_t object = 0;
  std::uint32_t vtable_rva = 0;
  CombatScopedStableKeyV1 key{};
  std::int32_t parameter_count_raw = -1, invocation_argument_count_raw = -1;
  CombatScopedEffectIdentityV1 default_root{};
  // 3381DFF uses template+120 only when the actual wrapper+94 count is zero.
  // A parameterized instance's active cache root is deliberately not inferred.
  bool default_root_selected_by_empty_arguments = false;
  friend bool operator==(const CombatScopedScriptedDefinitionV1 &,
                         const CombatScopedScriptedDefinitionV1 &) = default;
};

struct CombatScopedChainRecordV1 {
  std::uint32_t sequence = 0;
  std::uint32_t invocation = 0;
  std::uint32_t parent_invocation = 0;
  CombatScopedChainBoundaryV1 boundary = CombatScopedChainBoundaryV1::arm_paused;
  std::uint32_t failure_flags = 0;
  std::uint32_t thread_id = 0;
  std::int32_t native_date_raw = 0;
  std::int32_t combat_id = -1;
  std::int32_t phase_day = -1;
  std::int32_t side_index = -1;
  std::int32_t native_event_load_index = -1;
  std::uintptr_t node_identity = 0;
  std::uint32_t node_vtable_rva = 0;
  std::uint32_t node_hash = 0;
  // Only exact whitelisted original layouts are read. Unknown types do not
  // become empty groups or a null false branch by default.
  std::uint32_t node_original_execute_rva = 0;
  bool effect_children_read = false;
  std::uintptr_t effect_children_data = 0;
  std::int32_t effect_child_count_raw = -1;
  std::uint32_t effect_child_identity_count = 0;
  std::array<CombatScopedEffectIdentityV1,kCombatScopedChainMaxEffectChildrenV1> effect_children{};
  bool effect_if_optional_read = false;
  std::uintptr_t effect_if_optional_node = 0;
  CombatScopedEffectIdentityV1 effect_if_optional_identity{};
  CombatScopedScriptedDefinitionV1 scripted_effect_definition{};
  std::uint32_t depth = 0;
  std::uintptr_t caller_return_address = 0;
  std::int64_t casualty_damage_raw = 0;
  std::int32_t selected_candidate_index = -1;
  std::uint32_t selector_candidate_count = 0;
  std::array<CombatScopedSelectorCandidateV1, 256> selector_candidates{};
  std::uintptr_t execution_context = 0, native_root_scope = 0;
  std::array<std::uint64_t,2> native_scope_words{};
  std::uintptr_t selector_vector = 0, selector_data = 0, selector_list_context = 0;
  std::int32_t selector_prefix_count = -1, selector_current_index = -1;
  std::int32_t selector_source_side_index = -1;
  bool selector_source_combat_identity_matches = false;
  std::int32_t source_predicate_count = -1, shared_predicate_count = -1;
  std::uintptr_t source_predicate = 0, shared_predicate = 0, predicate = 0;
  std::uint32_t predicate_role = 0;
  bool original_predicate_boolean_read = false, original_predicate_boolean = false;
  std::uint64_t original_return_bits = 0;
  std::uintptr_t variable_owner = 0;
  bool variable_owner_from_original_getter=false;
  std::uintptr_t variable_owner_scope=0;
  std::array<std::uint64_t,2> variable_owner_scope_words{};
  bool requested_character_full_identity_matches=false;
  std::int32_t variable_key_id = -1, requested_expiry = -1, list_elapsed_offset = 0;
  CombatScopedStableKeyV1 variable_key{};
  std::array<std::uint64_t,2> requested_scope_words{};
  bool variable_list_read = false, variable_list_present = false;
  std::uint32_t variable_list_count = 0;
  std::array<std::array<std::uint64_t,2>,128> variable_list_values{};
  std::array<std::int32_t,128> variable_list_expirations{};
  std::array<CombatScopedCharacterV1, 2> characters{};
  std::array<std::int64_t, 2> side_cache_raw{};
  std::array<std::int64_t, 2> side_first_bucket_cache_raw{};
  std::array<bool, 2> scoped_regiment_in_side{};
  // Entries / owner ledger are copied at arm, phase, casualty and final
  // boundaries. Effect nodes carry character state only, keeping hook cost
  // bounded independently of the entire battle's number of participants.
  bool combat_entries_read = false;
  std::int32_t entry_snapshot_index = -1;
  std::int32_t death_victim_id = -1;
  std::int32_t death_killer_id = -1;
  std::int32_t requested_death_artifact_id = -1;
  std::uintptr_t requested_death_artifact = 0;
  bool requested_artifact_id_read = false;
  std::int64_t requested_death_date_raw = 0;
  std::uintptr_t requested_death_reason = 0;
  std::int32_t death_queue_count = -1;
  std::uintptr_t death_queue = 0;
  bool battle_events_read=false;
  std::int32_t battle_event_snapshot_index=-1;
};

struct CombatScopedChainV1 {
  std::atomic<std::uint32_t> armed{0};
  std::atomic<std::uint32_t> active_readers{0};
  std::atomic<std::uint32_t> count{0};
  std::atomic<std::uint32_t> next_invocation{0};
  std::atomic<std::uint32_t> entry_snapshot_count{0};
  std::atomic<std::uint32_t> battle_event_snapshot_count{0};
  std::atomic<std::uint32_t> failure_flags{0};
  const CombatPhaseEventTraceCapturePlanV1 *plan = nullptr;
  std::array<std::int32_t, 2> character_ids{-1, -1};
  std::array<std::uintptr_t, 2> character_objects{};
  std::array<std::int32_t, 2> prearmed_regiment_ids{-1, -1};
  std::int32_t event_load_index = -1;
  std::int32_t before_date_raw = 0;
  std::uintptr_t identifier_table = 0;
  std::atomic<std::uint32_t> simulation_thread_id{0};
  std::uint32_t trait_definition_count = 0;
  std::array<CombatScopedTraitDefinitionV1, kCombatScopedChainMaxTraitDefinitionsV1>
      trait_definitions{};
  std::array<CombatScopedChainRecordV1, kCombatScopedChainMaxRecordsV1> records{};
  std::array<CombatScopedEntrySnapshotV1, 16> entry_snapshots{};
  std::array<CombatScopedBattleEventSnapshotV1,8> battle_event_snapshots{};
};

// The observer records the declared two-character combat/death write set. It
// makes no claim about other characters, arbitrary script variables or the
// game's global mutable state. Live postcondition acceptance is separate.
bool ArmCombatScopedChainV1(CombatScopedChainV1 &chain,
                           const CombatPhaseEventTraceCapturePlanV1 &plan,
                           std::int32_t character_id,
                            std::int32_t related_character_id,
                            std::int32_t event_load_index,
                            std::uintptr_t offline_trait_database_override = 0,
                            std::uintptr_t offline_identifier_table_override = 0) noexcept;
void FinishCombatScopedChainV1(CombatScopedChainV1 &chain) noexcept;
void CancelCombatScopedChainV1(CombatScopedChainV1 &chain) noexcept;
std::uint32_t EnterCombatScopedEffectV1(void *node, std::int32_t side,
                                      std::int32_t event, std::uint32_t depth,
                                      void *execution_context = nullptr) noexcept;
void ReturnCombatScopedEffectV1(std::uint32_t invocation, void *node,
                              std::int32_t side, std::int32_t event,
                              std::uint32_t depth) noexcept;
void ObserveCombatScopedPhaseV1(CombatPhaseEventTraceBoundaryV1 boundary,
                              std::int32_t side) noexcept;
void ObserveCombatScopedSelectorV1(bool before, std::int32_t side,
                                 std::int32_t event, void *candidates,
                                 std::int32_t selected_index = -1) noexcept;
// Optional serialization-only attribution. It never changes capture validity.
struct CombatScopedWireDiagnosticV1 {
  const char *failure_gate = "none";
  const char *field = "none";
  std::int32_t record_index = -1, character_index = -1, side_index = -1;
  std::int32_t element_index = -1, byte_index = -1;
  std::uint32_t sequence = 0, invocation = 0, boundary = 0;
  std::uint64_t observed = 0, limit = 0, output_bytes = 0;
};
std::string SerializeCombatScopedChainV1(
    const CombatScopedChainV1 &chain,
    CombatScopedWireDiagnosticV1 *diagnostic = nullptr);

struct CombatScopedDetourV1 {
  std::uintptr_t target = 0;
  void *trampoline = nullptr;
  std::uint32_t patch_size = 0;
  std::array<std::uint8_t, 20> original{};
  bool installed = false;
};
struct CombatScopedDetoursV1 {
  std::array<CombatScopedDetourV1, 8> hooks{};
  std::uint32_t failure_flags = 0;
};
// Exact-anchor utility shared by the independent passive variable observer.
// The caller must prove exact build and paused quiescence before installation.
bool InstallCombatScopedExactDetourV1(CombatScopedDetourV1 &state,
                                    std::uintptr_t target, std::uintptr_t hook,
                                    const std::uint8_t *anchor, std::size_t length) noexcept;
bool UninstallCombatScopedExactDetourV1(CombatScopedDetourV1 &state,
                                      std::uintptr_t hook) noexcept;
bool InstallCombatScopedDetoursV1(CombatScopedDetoursV1 &state,
                                std::uintptr_t module_base,
                                bool exact_build_admitted,
                                bool paused_quiescence_proven) noexcept;
bool UninstallCombatScopedDetoursV1(CombatScopedDetoursV1 &state) noexcept;

// Same ABI as the four frozen original entry points. This fixture binding is
// unavailable while armed and is not exposed through the native command wire.
using CombatScopedDeathOriginalV1 = void (*)(void *, void *, void *, void *, void *, void *);
using CombatScopedQueueOriginalV1 = std::uintptr_t (*)(void *, const void *);
using CombatScopedCasualtyOriginalV1 = std::uintptr_t (*)(void *, std::int64_t, void *);
bool BindCombatScopedOriginalsForOfflineFixtureV1(
    CombatScopedDeathOriginalV1 request, CombatScopedDeathOriginalV1 commit,
    CombatScopedQueueOriginalV1 enqueue, CombatScopedCasualtyOriginalV1 casualty) noexcept;
extern "C" void __fastcall ScopedDeathRequest(
    void *, void *, void *, void *, void *, void *) noexcept;
extern "C" void __fastcall ScopedDeathCommit(
    void *, void *, void *, void *, void *, void *) noexcept;
extern "C" std::uintptr_t __fastcall ScopedDeathEnqueue(void *, const void *) noexcept;
extern "C" std::uintptr_t __fastcall ScopedCasualty(void *, std::int64_t, void *) noexcept;
using CombatScopedMaterializerOriginalV1 = std::uintptr_t (*)(void *,void *,void *);
using CombatScopedFilterOriginalV1 = std::uintptr_t (*)(void *,void *,void *,void *,void *);
using CombatScopedPredicateOriginalV1 = std::uintptr_t (*)(void *,void *,std::uint8_t);
using CombatScopedListWriterOriginalV1 = std::uintptr_t (*)(void *,std::int32_t,const void *,std::int32_t);
struct CombatScopedEffectContextV1 {
  bool read=false;
  std::uint64_t managed_daily_sequence_token=0;
  std::uint32_t invocation=0,depth=0,node_hash=0,node_vtable_rva=0;
  std::int32_t combat_id=-1,side_index=-1,event_load_index=-1;
  std::uintptr_t node=0,execution_context=0;
  friend bool operator==(const CombatScopedEffectContextV1 &,
                         const CombatScopedEffectContextV1 &)=default;
};
// Only the currently executing original 264BCB0 invocation on this thread.
// No last-death cache, endpoint-derived victim, or asynchronous attribution.
struct CombatScopedDeathCommitContextV1 {
  bool read=false, victim_full_identity_matches=false, killer_full_identity_matches=false;
  std::uint64_t managed_daily_sequence_token=0;
  std::uint32_t invocation=0, parent_invocation=0, thread_id=0;
  std::int32_t native_date_raw=0, combat_id=-1, victim_id=-1, killer_id=-1;
  std::uintptr_t manager=0, victim=0, killer=0, reason=0, date_argument=0, artifact=0;
  std::int64_t requested_death_date_raw=0;
  bool reason_key_read=false, artifact_actual_null=false, artifact_id_read=false;
  std::int32_t artifact_id=-1;
  CombatScopedStableKeyV1 reason_key{};
  friend bool operator==(const CombatScopedDeathCommitContextV1 &,
                         const CombatScopedDeathCommitContextV1 &)=default;
};
bool ReadCurrentCombatScopedEffectContextV1(CombatScopedEffectContextV1 &) noexcept;
bool ReadCurrentCombatScopedDeathCommitContextV1(CombatScopedDeathCommitContextV1 &) noexcept;
void ObserveCombatScopedOriginalVariableOwnerV1(const void *,void *) noexcept;
bool BindCombatScopedSelectorOriginalsForOfflineFixtureV1(CombatScopedMaterializerOriginalV1,
    CombatScopedFilterOriginalV1,CombatScopedPredicateOriginalV1,CombatScopedListWriterOriginalV1) noexcept;
extern "C" std::uintptr_t __fastcall ScopedSelectorMaterializer(void *,void *,void *) noexcept;
extern "C" std::uintptr_t __fastcall ScopedSelectorFilter(void *,void *,void *,void *,void *) noexcept;
extern "C" std::uintptr_t __fastcall ScopedSelectorPredicate(void *,void *,std::uint8_t) noexcept;
extern "C" std::uintptr_t __fastcall ScopedCombatListWriter(void *,std::int32_t,const void *,std::int32_t) noexcept;

// Optional passive publication; the original six-parameter callee is still forwarded once.
using CombatScopedOriginalDeathCommitObserverV1 = void (*)(bool,void *,void *,void *,void *,void *,void *) noexcept;
bool BindCombatScopedOriginalDeathCommitObserverV1(CombatScopedOriginalDeathCommitObserverV1) noexcept;

} // namespace xar::ck3_11906
