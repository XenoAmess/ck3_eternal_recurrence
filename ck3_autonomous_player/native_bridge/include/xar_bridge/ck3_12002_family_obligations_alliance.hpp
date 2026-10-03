#pragma once

#include "xar_bridge/ck3_12002_context.hpp"
#include "xar_bridge/ck3_12002_diplomacy.hpp"
#include "xar_bridge/ck3_12002_family_query_abi.hpp"

#include <array>
#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::ck3_12002::family_obligations_alliance {

inline constexpr std::uintptr_t kIsAlliedRva = 0x2911DF0;
inline constexpr std::uintptr_t kWarStorageSlotRva = 0x5D1DE58;
inline constexpr std::uintptr_t kWarFallbackSlotRva = 0x5D1DE40;
inline constexpr std::uintptr_t kInteractionMissingSlotRva = 0x5D1DD28;
inline constexpr std::uintptr_t kDefinitionKeyHashRva = 0x3F7E240;
inline constexpr std::uintptr_t kDefinitionLookupRva = 0xA055E0;
inline constexpr std::uintptr_t kCanPickWarTargetRva = 0x307A690;
inline constexpr std::uintptr_t kSendSetupRva = 0x307A770;
inline constexpr std::uintptr_t kSendAvailabilityRva = 0x307A860;
inline constexpr std::uintptr_t kSendPrecheckRva = 0x307AB70;
inline constexpr std::uintptr_t kAlreadyConsideringRva = 0x307A570;
inline constexpr std::uintptr_t kPairRestrictionRva = 0x2BF5E30;
inline constexpr std::uintptr_t kDiplomaticRangeRva = 0x307D6E0;
inline constexpr std::array<std::size_t, 7> kSendDefinitionGateOffsets{
    0xAE8, 0xC88, 0xE28, 0x1168, 0xFC8, 0xD58, 0xEF8};
inline constexpr std::uintptr_t kWasCalledRva = 0x2497770;
inline constexpr std::uintptr_t kContainsParticipantRva = 0x2494B60;
inline constexpr std::size_t kCharacterFamilyOffset = 0x1A8;
inline constexpr std::size_t kCharacterRelationsOffset = 0x1B0;
inline constexpr std::size_t kCharacterRealmOffset = 0x1C0;
inline constexpr std::size_t kFamilyBetrothedOffset = 0x10;
inline constexpr std::size_t kFamilySpousesOffset = 0x20;
inline constexpr std::size_t kRelationsRowsOffset = 0x20;
inline constexpr std::size_t kRealmWarIdsOffset = 0x318;
inline constexpr std::size_t kContextActorOffset = 0x2D8;
inline constexpr std::size_t kContextRecipientOffset = 0x2DC;
inline constexpr std::size_t kContextTargetOffset = 0x2F0;
inline constexpr std::size_t kContextTargetTokenOffset = 0x2F8;
inline constexpr std::size_t kContextSpecialInstanceOffset = 0x330;
inline constexpr std::uint16_t kWarTargetType = 16;
inline constexpr std::string_view kInteractionKey = "call_ally_interaction";

using IsAllied = bool (*)(const void *, const void *);
using DefinitionKeyHash = std::uint32_t (*)(const void *, const char *, std::uint32_t);
using DefinitionLookup = void *(*)(void *, std::int32_t);
using CanPickWarTarget = bool (*)(void *, const void *, void *);
using FinalAnswer = std::uint8_t (*)(void *, std::uint8_t, std::uint8_t, void *, void *);
using ContextPredicate = bool (*)(void *);
using ContextAvailability = bool (*)(void *, void *);
using SendPrecheck = bool (*)(void *, std::uint8_t, std::uint8_t, void *);
using PairRestriction = bool (*)(void *, void *, void *, void *);
using DiplomaticRange = bool (*)(void *, const void *);
using WasCalled = bool (*)(const void *, std::int32_t);
using ContainsParticipant = bool (*)(const void *, std::int32_t);

struct alignas(8) WarTarget {
  std::uint16_t type_index = kWarTargetType;
  std::array<std::byte, 6> reserved{};
  std::uint64_t full_war_id = 0;
};
static_assert(sizeof(WarTarget) == 16);
static_assert(offsetof(WarTarget, full_war_id) == 8);

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  ContextBindings context{};
  ConstructInteractionContext construct_context = nullptr;
  void **war_storage_slot = nullptr;
  void **war_fallback_slot = nullptr;
  void **interaction_missing_slot = nullptr;
  IsAllied is_allied = nullptr;
  DefinitionKeyHash key_hash = nullptr;
  DefinitionLookup lookup_definition = nullptr;
  CanPickWarTarget can_pick_war_target = nullptr;
  WasCalled was_called = nullptr;
  FinalAnswer final_answer = nullptr;
  ContextPredicate setup = nullptr;
  ContextAvailability availability = nullptr;
  SendPrecheck send_precheck = nullptr;
  ContextPredicate already_considering = nullptr;
  PairRestriction pair_restriction = nullptr;
  DiplomaticRange diplomatic_range = nullptr;
  ContainsParticipant contains_participant = nullptr;
};

enum class Side : std::uint8_t { attacker, defender, absent };

struct WarExposure {
  std::int32_t war_id = -1;
  std::int32_t caller_character_id = -1;
  std::int32_t recipient_character_id = -1;
  Side caller_side = Side::absent;
  Side recipient_side = Side::absent;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::vector<std::int32_t> attacker_character_ids;
  std::vector<std::int32_t> defender_character_ids;
  bool caller_is_primary_war_leader = false;
  bool recipient_was_called = false;
  bool native_target_can_be_picked = false;
  // False is an observed picker rejection; selected-context terms stay unavailable.
  bool native_selected_target_context_available = false;
  bool native_complete_can_send = false;
  // This is the exact native CallAlly UI row gate, which is separate from
  // full CanSend. Neither is a prediction that the recipient will join.
  bool native_target_row_selectable = false;
  std::array<std::int64_t, 10> send_cost_raw{};
  std::int64_t recipient_acceptance_raw = 0;
  bool native_auto_accept = false;
  std::uint8_t recipient_answer_status_raw = 0;
  // Complete CanSend uses answer flags 0,0, independently of preview flags 1,1.
  std::uint8_t native_send_answer_status_raw = 0;
  bool native_send_precheck_passed = false;
  bool native_send_setup_passed = false;
  bool native_send_availability_passed = false;
  bool native_send_pair_restriction_blocked = false;
  bool native_send_diplomatic_range_passed = false;
  bool native_send_already_considering_blocked = false;
  // Observed definition trigger results: AE8,C88,E28,1168,FC8,D58,EF8.
  std::array<bool, 7> native_send_definition_gate_results{};
  std::string_view native_first_failed_send_stage = "none";
};

struct Snapshot {
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::int32_t first_character_id = -1;
  std::int32_t second_character_id = -1;
  bool first_has_second = false;
  bool second_has_first = false;
  std::vector<WarExposure> first_wars;
  std::vector<WarExposure> second_wars;
};

struct CurrentAlly {
  std::int32_t character_id = -1;
  bool player_has_ally = false;
  bool ally_has_player = false;
  bool has_realm_data = false;
};

struct CurrentAlliesSnapshot {
  std::int32_t played_character_id = -1;
  std::vector<std::int32_t> source_character_ids;
  std::vector<std::int32_t> unresolved_source_character_ids;
  std::vector<std::int32_t> dead_source_character_ids;
  std::vector<CurrentAlly> allies;
};

// Actual stored source IDs, then full-generation resolution and native
// IsAllied in both directions. Membership is separate from war-call legality.
bool ReadCurrentAllies(const Bindings &, const CoreSnapshotPrefix &,
                       CurrentAlliesSnapshot &, std::string_view *reason = nullptr) noexcept;

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;

// Owning paused application thread only. The caller supplies its same-frame
// prefix and two concrete IDs, including prospective native marriage pair
// identities. The observer never submits a command or creates an alliance.
bool Read(const Bindings &, const CoreSnapshotPrefix &,
          std::int32_t first_character_id, std::int32_t second_character_id,
          Snapshot &, std::string_view *reason = nullptr) noexcept;


// Caller is the current paused player. This is only a native owning-thread
// submitter; the external transport must bind expected snapshot revision.
struct CallAllySubmitRequest {
  std::int32_t recipient_character_id = -1;
  std::int32_t war_id = -1;
  std::array<std::int64_t, 10> expected_send_cost_raw{};
};
struct CallAllySubmitReceipt {
  bool selected_target_native_legal = false;
  bool copied_context_identity_verified = false;
  bool send_cost_sampled = false;
  std::array<std::int64_t, 10> actual_send_cost_raw{};
};
CommandSubmitResult SubmitCallAlly(const Bindings &, const CoreSnapshotPrefix &,
    const CallAllySubmitRequest &, CallAllySubmitReceipt &,
    std::string_view *reason = nullptr) noexcept;

} // namespace xar::ck3_12002::family_obligations_alliance
