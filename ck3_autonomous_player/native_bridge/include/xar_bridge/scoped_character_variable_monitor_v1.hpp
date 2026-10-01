#pragma once
#include "xar_bridge/combat_scoped_transition_chain_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <memory>

namespace xar::ck3_11906 {
inline constexpr std::string_view kScopedCharacterVariableMonitorBeginV1 =
    "experimental-scoped-character-variable-monitor-begin-v1";
inline constexpr std::string_view kScopedCharacterVariableMonitorFinishV1 =
    "experimental-scoped-character-variable-monitor-finish-v1";
enum class ScopedVariableMonitorStageV1 : std::uint32_t { idle, armed, drained, failed };
enum class ScopedVariableMonitorBoundaryV1 : std::uint32_t {
  arm, original_owner_return, variable_write_enter, variable_write_return,
  house_predicate_enter, house_predicate_return, final_paused,
  original_death_commit_enter, original_death_commit_return
};
struct ScopedVariableValueV1 {
  bool read = false;
  bool present = false;
  std::int32_t expiration_raw = -1;
  std::array<std::uint64_t, 2> words{};
  bool flag_name_read = false;
  std::uint32_t flag_index = 0, flag_identifier_count = 0;
  std::uint8_t flag_identifier_epoch = 0;
  CombatScopedStableKeyV1 flag_name{};
  friend bool operator==(const ScopedVariableValueV1 &, const ScopedVariableValueV1 &) = default;
};
enum class ScopedNotificationNamedReadFailureV1 : std::uint32_t {
  none, context_extent, identifier_table_extent, prearmed_key,
  identifier_names_span, identifier_count_shrunk, identifier_epoch,
  identifier_key_index, identifier_key_name, store_extent, primary_rows,
  fallback_store_extent, fallback_parent_extent, fallback_rows,
  resolved_character_extent, identifier_header_changed, identifier_key_changed,
  snapshots_differ, observations_unread, access_fault, not_observed
};
struct ScopedNotificationNamedDeadCharacterV1 {
  bool read = false, stable_two_reads = false, present = false, scope_words_read = false;
  // Actual per-observation header; prearm session fields remain unchanged.
  bool identifier_header_read = false, identifier_key_name_matches = false;
  std::uintptr_t identifier_table = 0, identifier_data = 0;
  std::int32_t identifier_count = 0;
  std::uint32_t prearmed_identifier_count = 0, identifier_key_index = 0;
  std::uint8_t identifier_epoch = 0, prearmed_identifier_epoch = 0;
  ScopedNotificationNamedReadFailureV1 failure_stage = ScopedNotificationNamedReadFailureV1::not_observed;
  std::uintptr_t execution_context = 0, store = 0, primary_data = 0, fallback_parent = 0, fallback_data = 0, found_row = 0;
  std::int32_t key_id = -1, primary_count = 0, fallback_count = 0, found_index = -1;
  bool fallback_pointer_read = false, fallback_header_read = false;
  std::uint32_t source_level = 0; // 0 absent, 1 primary, 2 fallback; only meaningful when read.
  std::array<std::uint64_t,2> scope_words{};
  std::uint16_t kind = 0, subtype = 0;
  std::int64_t payload = 0;
  std::uint64_t payload_raw64 = 0;
  bool character_full_id_low32_read = false;
  std::uint32_t character_full_id_raw32 = 0;
  bool character_identity_read = false, character_full_identity_matches = false, matches_monitored_victim = false;
  std::int32_t character_id = -1, observed_character_id = -1;
  std::uintptr_t resolved_character = 0;
  friend bool operator==(const ScopedNotificationNamedDeadCharacterV1 &, const ScopedNotificationNamedDeadCharacterV1 &)=default;
};
struct ScopedVariableEventProducerV1 {
  bool read = false;
  std::uint32_t matched_root_execution_depth = 0, active_effect_group_depth = 0;
  std::uint32_t invocation = 0, definition_index = 0, definition_id = 0, runtime_stats_ordinal = 0;
  std::uintptr_t definition = 0, immediate_root = 0, context = 0, root_scope = 0;
  std::uintptr_t children_data = 0;
  std::int32_t children_capacity = 0, children_count = 0;
  std::uint32_t definition_vtable_rva = 0, root_vtable_rva = 0, root_hash = 0, original_execute_rva = 0;
  std::array<std::uint64_t,2> root_scope_words{};
  CombatScopedStableKeyV1 definition_key{};
  CombatScopedDeathCommitContextV1 activation_death_commit_context{};
  ScopedNotificationNamedDeadCharacterV1 named_dead_character_at_activation{};
  ScopedNotificationNamedDeadCharacterV1 named_dead_character_at_observation{};
  friend bool operator==(const ScopedVariableEventProducerV1 &,
                         const ScopedVariableEventProducerV1 &)=default;
};
struct ScopedVariableMonitorRecordV1 {
  std::uint32_t sequence = 0, invocation = 0, failure_flags = 0, thread_id = 0;
  ScopedVariableMonitorBoundaryV1 boundary = ScopedVariableMonitorBoundaryV1::arm;
  std::int32_t date_raw = 0, character_id = -1, observed_character_id = -1;
  bool full_identity_matches = false, victim_dead = false;
  std::uintptr_t owner = 0, previous_owner = 0, container = 0;
  bool owner_from_original_getter = false, owner_from_same_setter_invocation = false;
  std::int32_t key_id = -1, duration = 0;
  ScopedVariableValueV1 value{};
  std::array<std::uint64_t, 2> requested_value{};
  ScopedVariableValueV1 requested_value_decoding{};
  std::uintptr_t setter_node = 0, execution_context = 0, native_root_scope = 0;
  std::array<std::uint64_t, 2> native_scope_words{};
  std::uint32_t setter_node_hash = 0, setter_node_vtable_rva = 0;
  std::uintptr_t caller = 0;
  std::uint32_t stack_count = 0;
  std::array<std::uint32_t, 40> stack_rvas{};
  std::array<std::int32_t, 2> house_ids{-1,-1};
  std::uintptr_t relation_type = 0;
  std::int32_t relation_type_id = -1;
  CombatScopedStableKeyV1 relation_type_key{};
  bool original_boolean_read = false, original_boolean = false;
  std::uint64_t original_return_bits = 0;
  CombatScopedEffectContextV1 daily_effect_context{};
  ScopedVariableEventProducerV1 event_producer{};
  CombatScopedDeathCommitContextV1 current_death_commit_context{};
  // Direct original264BCB0 argument observations, independent of writer TLS overlap.
  CombatScopedDeathCommitContextV1 original_death_commit_context{};
  // Aggregate only equal dead/null original getter returns, never writes.
  std::uint64_t owner_observation_first_call_index = 0,
                owner_observation_last_call_index = 0,
                owner_observation_count = 0, owner_state_epoch = 0,
                owner_activity_epoch = 0;
};
struct ScopedCharacterVariableMonitorV1 {
  ScopedVariableMonitorStageV1 stage = ScopedVariableMonitorStageV1::idle;
  Bindings bindings{};
  std::uintptr_t module_base = 0, date_object = 0, date_slot = 0;
  std::int32_t begin_date = 0;
  std::uint64_t token = 0;
  std::array<std::int32_t, 2> character_ids{-1,-1};
  std::array<std::uintptr_t, 2> character_objects{};
  std::array<std::atomic<std::uintptr_t>, 2> owners{};
  std::int32_t signature_key_id = -1;
  std::int32_t dead_character_key_id = -1;
  std::uintptr_t identifier_table = 0;
  std::uint32_t identifier_count = 0;
  std::uint8_t identifier_epoch = 0;
  std::atomic<std::uint32_t> armed{0}, active_callbacks{0}, count{0}, next_invocation{0}, failure_flags{0};
  std::array<CombatScopedDetourV1, 5> detours{};
  std::uintptr_t event_manager_slot = 0, event_manager = 0, event_definitions_data = 0;
  std::int32_t event_definitions_count = 0;
  std::array<ScopedVariableEventProducerV1,7> event_producer_definitions{};
  bool event_producer_definitions_read = false;
  std::array<ScopedVariableMonitorRecordV1, 128> records{};
  std::array<ScopedVariableValueV1, 2> last_owner_values{};
  // Protect owner/value state and published owner-row aggregation across GUI threads.
  // No original native call runs while this lock is held.
  SRWLOCK owner_observation_lock = SRWLOCK_INIT;
  std::array<bool, 2> owner_state_seen{}, last_owner_dead{};
  std::array<std::uint64_t, 2> owner_state_epochs{};
  std::array<std::uint32_t, 128> owner_record_indices{};
  std::uint32_t owner_record_count = 0;
  std::atomic<std::uint64_t> owner_activity_epoch{0}, owner_getter_observed{0},
      owner_getter_retained{0}, owner_getter_coalesced{0},
      owner_nonnull_unchanged_unrecorded{0};
  bool detours_uninstalled = false;
};
struct ScopedVariableMonitorQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  ScopedCharacterVariableMonitorV1 *session = nullptr;
  const game::GameAdapter *game_adapter = nullptr;
  game::Snapshot expected_snapshot{};
  bool begin = false, exact_build = false;
  Bindings bindings{};
  std::uintptr_t module_base = 0;
  std::uint64_t token = 0;
  std::array<std::int32_t, 2> character_ids{-1,-1};
  bool completed = false;
};
bool ExecuteScopedVariableMonitorQueryV1(void *, const MainThreadExecutionStampV1 &) noexcept;
bool StartScopedCharacterVariableMonitorV1(ScopedCharacterVariableMonitorV1 &, const Bindings &,
    std::uintptr_t module_base, std::array<std::int32_t,2> ids,
    std::uint64_t token, bool exact_build, bool paused_quiescence,
    std::uintptr_t offline_identifier_table = 0, std::uintptr_t offline_date_slot = 0,
    std::uintptr_t offline_event_manager_slot = 0) noexcept;
bool FinishScopedCharacterVariableMonitorV1(ScopedCharacterVariableMonitorV1 &, bool paused_quiescence) noexcept;
std::string SerializeScopedCharacterVariableMonitorV1(const ScopedCharacterVariableMonitorV1 &);
bool ScopedVariableMonitorHasInstalledHooksV1(const ScopedCharacterVariableMonitorV1 &) noexcept;

using ScopedVariableOwnerOriginalV1 = void *(*)(const void *);
using ScopedVariableSetterOriginalV1 = std::uintptr_t (*)(void *, std::int32_t, const void *, std::int32_t);
using ScopedVariableEffectOriginalV1 = std::uintptr_t (*)(void *, void *);
using ScopedHousePredicateOriginalV1 = std::uintptr_t (*)(void *, void *, void *);
using ScopedEventImmediateRootOriginalV1 = void (*)(void *, void *);
bool BindScopedVariableMonitorOfflineOriginalsV1(ScopedVariableOwnerOriginalV1,
     ScopedVariableSetterOriginalV1, ScopedVariableEffectOriginalV1, ScopedHousePredicateOriginalV1,
     ScopedEventImmediateRootOriginalV1 = nullptr) noexcept;
extern "C" void *__fastcall ObservedCharacterVariableOwnerV1(const void *) noexcept;
extern "C" std::uintptr_t __fastcall ObservedCharacterVariableSetterV1(void *, std::int32_t, const void *, std::int32_t) noexcept;
extern "C" std::uintptr_t __fastcall ObservedCharacterVariableEffectV1(void *, void *) noexcept;
extern "C" std::uintptr_t __fastcall ObservedScopedHousePredicateV1(void *, void *, void *) noexcept;
extern "C" void __fastcall ObservedScopedEventImmediateRootV1(void *, void *) noexcept;
void ObserveScopedVariableMonitorOriginalDeathCommitV1(bool entering, void *manager,
    void *victim, void *reason, void *date, void *killer, void *artifact) noexcept;
bool ReadScopedNotificationNamedDeadCharacterV1(const ScopedCharacterVariableMonitorV1 &,
     std::uintptr_t execution_context, ScopedNotificationNamedDeadCharacterV1 &) noexcept;
// Pure comparison of two original passive observations; never reads native state.
bool ValidateScopedNotificationNamedDeadCharacterPairV1(const ScopedNotificationNamedDeadCharacterV1 &,
     const ScopedNotificationNamedDeadCharacterV1 &, ScopedNotificationNamedDeadCharacterV1 &) noexcept;
} // namespace xar::ck3_11906
