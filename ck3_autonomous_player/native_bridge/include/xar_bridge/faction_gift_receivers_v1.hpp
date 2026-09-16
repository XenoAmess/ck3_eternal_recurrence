#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/faction_targeting_row_probe_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr std::uintptr_t kFactionGiftFactionStorageSlotRvaV1 =
    0x570C768;
inline constexpr std::uintptr_t kFactionGiftFactionFallbackSlotRvaV1 =
    0x570C6F8;
inline constexpr std::uintptr_t kFactionGiftWarStorageSlotRvaV1 = 0x570C740;
inline constexpr std::uintptr_t kFactionGiftWarFallbackSlotRvaV1 = 0x570C718;
inline constexpr std::uintptr_t kFactionGiftFactionVtableRvaV1 = 0x4305228;
inline constexpr std::uintptr_t kFactionGiftWarVtableRvaV1 = 0x42F77C8;
inline constexpr std::uintptr_t kFactionGiftNullWarVtableRvaV1 = 0x431C298;
inline constexpr std::uintptr_t kFactionGiftWarAliveLeafRvaV1 = 0x10495A0;
inline constexpr std::uintptr_t kFactionGiftNullWarAliveLeafRvaV1 = 0x7E6590;
inline constexpr std::uintptr_t kFactionGiftPowerLeafRvaV1 = 0x138F370;
inline constexpr std::uintptr_t kFactionGiftDiscontentLeafRvaV1 = 0x13902F0;
inline constexpr std::uint32_t kFactionGiftMetricScaleV1 = 100000;

inline constexpr std::uintptr_t kFactionGiftCharacterStorageSlotRvaV1 =
    0x570C130;
inline constexpr std::uintptr_t kFactionGiftCharacterFallbackSlotRvaV1 =
    0x570C138;
inline constexpr std::uintptr_t kFactionGiftReadCharacterOpinionRvaV1 =
    0x2610A50;
inline constexpr std::uintptr_t kFactionGiftOpinionModifierDatabaseSlotRvaV1 =
    0x57C0970;
inline constexpr std::uintptr_t kFactionGiftStableHashRvaV1 = 0x3B8B000;
inline constexpr std::uintptr_t kFactionGiftOpinionModifierLookupRvaV1 =
    0x231D3E0;
inline constexpr std::uintptr_t kFactionGiftFindActiveOpinionGroupRvaV1 =
    0x2696D90;
inline constexpr std::uintptr_t kFactionGiftSumOpinionModifierRvaV1 =
    0x23101A0;
inline constexpr std::uintptr_t kFactionGiftOpinionModifierVtableRvaV1 =
    0x43F67E0;
inline constexpr std::uintptr_t kFactionGiftOpinionModifierSecondaryVtableRvaV1 =
    0x43F6800;
inline constexpr std::size_t kFactionGiftOpinionModifierSecondaryOffsetV1 =
    0x80;
inline constexpr std::uintptr_t kFactionGiftActiveOpinionVtableRvaV1 =
    0x4300DF8;
inline constexpr std::uintptr_t kFactionGiftTemporaryOpinionVtableRvaV1 =
    0x4300DC0;
inline constexpr std::uint32_t kFactionGiftOpinionModifierStableHashV1 =
    0xCA82155BU;
inline constexpr std::string_view kFactionGiftOpinionModifierKeyV1 =
    "gift_opinion";

inline constexpr std::uintptr_t kFactionGiftNamedValueDatabaseGetterRvaV1 =
    0x999AF0;
inline constexpr std::uintptr_t kFactionGiftNamedValueLookupRvaV1 = 0x9999B0;
inline constexpr std::uintptr_t kFactionGiftCloneEventTargetScopeRvaV1 =
    0x3358E00;
inline constexpr std::uintptr_t kFactionGiftSupport118ConstructorRvaV1 =
    0x3354330;
inline constexpr std::uintptr_t kFactionGiftSupport2A8ConstructorRvaV1 =
    0x3354280;
inline constexpr std::uintptr_t kFactionGiftEvaluateNamedIntegerRvaV1 =
    0x3369600;
inline constexpr std::uintptr_t kFactionGiftEvaluateNamedFixedRvaV1 =
    0x3369820;
inline constexpr std::uintptr_t kFactionGiftNamedValueVtableRvaV1 =
    0x44C9EA0;
inline constexpr std::uintptr_t kFactionGiftNamedValueSecondaryVtableRvaV1 =
    0x44C9F10;
inline constexpr std::uintptr_t kFactionGiftNamedValueNullVtableRvaV1 =
    0x44C9DB0;
inline constexpr std::uintptr_t kFactionGiftNamedValueNullSecondaryVtableRvaV1 =
    0x44C9D78;
inline constexpr std::uintptr_t kFactionGiftEvaluationFlagRvaV1 = 0x570C3F4;
inline constexpr std::uint32_t kFactionGiftSendOpinionStableHashV1 =
    0xF8A1F946U;
inline constexpr std::string_view kFactionGiftSendOpinionKeyV1 =
    "send_gift_opinion";

// Testable representation of the exact 1.19.0.6 component stores. Production
// obtains every member directly from the frozen module RVAs above. The view is
// data only: no callback can replace the identity, vtable, or at-war logic.
struct FactionAtWarExactStoresV1 {
  void *faction_storage = nullptr;
  void *faction_fallback = nullptr;
  void *war_storage = nullptr;
  void *war_fallback = nullptr;
  std::uintptr_t expected_faction_vtable = 0;
  std::uintptr_t expected_war_vtable = 0;
  std::uintptr_t expected_null_war_vtable = 0;
  std::uintptr_t expected_war_alive_leaf = 0;
  std::uintptr_t expected_null_war_alive_leaf = 0;
};

// Returns false for a typed read/ABI failure. A true return with at_war=false
// is the stock legal no-war state and is deliberately distinct from failure.
bool ReadFactionAtWarFromExactStoresV1(
    const FactionAtWarExactStoresV1 &stores, std::uint32_t faction_id,
    bool &at_war) noexcept;

// Production entry. It reads the exact module-relative stores twice and
// accepts only stable, full-generation, exact-vtable observations.
bool ReadFactionAtWarExact11906V1(std::uintptr_t module_base,
                                 std::uint32_t faction_id,
                                 bool &at_war) noexcept;

// FactionItem.GetPower and FactionItem.GetDiscontent read only the full
// generation faction identity from FactionItem+0x00 and write a signed
// Q100000 result. The production receiver first resolves the exact CFaction
// identity itself, rejecting the stock getter's null-object fallback, then
// accepts only equal paused samples of both native final getters.
bool ReadFactionMetricsExact11906V1(std::uintptr_t module_base,
                                    std::uint32_t faction_id,
                                    std::int64_t &power_raw,
                                    std::int64_t &discontent_raw) noexcept;

// Data-only fixture for the identical two-sample publication gate. It cannot
// replace either production callback; only the exact native getter is used in
// ReadFactionMetricsExact11906V1.
struct FactionMetricsExactFixtureV1 {
  bool available = false;
  std::uint32_t faction_identity_first = 0;
  std::uint32_t faction_identity_second = 0;
  std::uintptr_t faction_vtable_first = 0;
  std::uintptr_t faction_vtable_second = 0;
  std::uintptr_t expected_faction_vtable = 0;
  std::int64_t power_first = 0;
  std::int64_t power_second = 0;
  std::int64_t discontent_first = 0;
  std::int64_t discontent_second = 0;
};
bool ReadFactionMetricsFromExactFixtureV1(
    const FactionMetricsExactFixtureV1 &fixture, std::uint32_t faction_id,
    std::int64_t &power_raw, std::int64_t &discontent_raw) noexcept;

// Direct source-vector view traced from the stock FactionsWindow refresh:
// player CCharacter+0x1B8 land state, vector data +0x120/count +0x12C.
// This producer does not need the FactionsWindow GUI callback. The data-only
// store view supports a focused fixture; production loads the frozen module
// slots and accepts only full-generation object round trips.
struct FactionGiftDirectSourceStoresV1 {
  void *character_storage = nullptr;
  void *faction_storage = nullptr;
  void *faction_fallback = nullptr;
  std::uintptr_t expected_faction_vtable = 0;
};
bool ReadFactionGiftDirectTargetingRowsFromStoresV1(
    const FactionGiftDirectSourceStoresV1 &stores,
    const bridge::FactionTargetingRowProbeBindingV1 &required,
    bridge::FactionTargetingRowProbeResultV1 &rows) noexcept;
bool ReadFactionGiftDirectTargetingRowsExact11906V1(
    std::uintptr_t module_base, const Bindings &bindings,
    const bridge::FactionTargetingRowProbeBindingV1 &required,
    bridge::FactionTargetingRowProbeResultV1 &rows) noexcept;

// Independent post-action entity lookup. The player targeting vector is only
// a view; absence from that vector does not mean the full-generation faction
// entity was destroyed. This lookup reads the exact faction store, validates
// target and member identities, and reports a known absent slot separately
// from an incomplete/failed read. Metric values are populated only when the
// entity exists and the stock final getters pass their paired sample gate.
struct FactionGiftIndependentEntityV1 {
  bool present = false;
  std::uint32_t target_character_id = 0;
  std::optional<std::uint32_t> leader_character_id;
  std::vector<std::uint32_t> member_character_ids;
  bool metrics_available = false;
  std::int64_t power_raw = 0;
  std::int64_t discontent_raw = 0;
  std::uint32_t metric_scale = 0;

  friend bool operator==(const FactionGiftIndependentEntityV1 &,
                         const FactionGiftIndependentEntityV1 &) = default;
};
bool ReadFactionGiftIndependentEntityFromStoresV1(
    const FactionGiftDirectSourceStoresV1 &stores, std::uint32_t faction_id,
    FactionGiftIndependentEntityV1 &entity) noexcept;
bool ReadFactionGiftIndependentEntityExact11906V1(
    std::uintptr_t module_base, const Bindings &bindings,
    std::uint32_t faction_id,
    FactionGiftIndependentEntityV1 &entity) noexcept;

struct GiftOpinionReceiverResultV1 {
  bool query_complete = false;
  std::int32_t recipient_opinion_of_player = 0;
  bool gift_opinion_present = false;
  std::optional<std::int32_t> gift_opinion_modifier_value;
};

// A data-only deterministic fixture. Repeated identities, vtables,
// definitions and values model the same two-sample gates as production. No
// fixture callback can replace the native receiver or evaluator.
struct GiftOpinionReceiverFixtureV1 {
  bool available = false;
  std::uint32_t recipient_identity_before = 0;
  std::uint32_t recipient_identity_after = 0;
  std::uint32_t player_identity_before = 0;
  std::uint32_t player_identity_after = 0;
  std::uintptr_t modifier_definition = 0;
  std::uintptr_t modifier_definition_after = 0;
  std::uintptr_t modifier_vtable = 0;
  std::uintptr_t expected_modifier_vtable = 0;
  std::uint32_t modifier_hash = 0;
  std::string_view modifier_key{};
  std::int32_t opinion_first = 0;
  std::int32_t opinion_second = 0;
  bool modifier_present_first = false;
  bool modifier_present_second = false;
  std::optional<std::int32_t> modifier_value_first;
  std::optional<std::int32_t> modifier_value_second;
  std::uintptr_t named_definition = 0;
  std::uintptr_t named_definition_after = 0;
  std::uintptr_t named_vtable = 0;
  std::uintptr_t named_secondary_vtable = 0;
  std::uintptr_t expected_named_vtable = 0;
  std::uintptr_t expected_named_secondary_vtable = 0;
  std::uint32_t named_hash = 0;
  std::string_view named_key{};
  std::int32_t opinion_delta_first = 0;
  std::int32_t opinion_delta_second = 0;
};

bool ReadGiftOpinionFromExactFixtureV1(
    const GiftOpinionReceiverFixtureV1 &fixture,
    std::uint32_t recipient_character_id,
    std::uint32_t player_character_id,
    GiftOpinionReceiverResultV1 &output) noexcept;
bool ReadGiftOpinionDeltaFromExactFixtureV1(
    const GiftOpinionReceiverFixtureV1 &fixture,
    std::uint32_t recipient_character_id,
    std::uint32_t player_character_id,
    std::int32_t &opinion_delta) noexcept;

// Production entries. Both resolve full generation-bearing character IDs,
// demand exact definition/vtable/key/hash identity, sample twice and repeat
// fresh DB lookup before publication.
bool ReadGiftOpinionExact11906V1(
    std::uintptr_t module_base, const Bindings &bindings,
    std::uint32_t recipient_character_id,
    std::uint32_t player_character_id,
    GiftOpinionReceiverResultV1 &output) noexcept;
bool ReadGiftOpinionDeltaExact11906V1(
    std::uintptr_t module_base, const void *character_interaction_scope,
    std::uint32_t recipient_character_id,
    std::uint32_t player_character_id,
    std::int32_t &opinion_delta) noexcept;

} // namespace xar::ck3_11906
