#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/ck3_12002_faction_gift.hpp"
#include "xar_bridge/ck3_12002_prisoner_abi.hpp"
#include "xar_bridge/player_prisoner_collection_query_v1_private.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12003 {

inline constexpr std::string_view kPrisonerReleaseDefinitionKey12003 =
    "release_from_prison_interaction";
inline constexpr std::array<std::string_view, 13> kPrisonerReleaseOptionKeys12003{
    "demand_conversion", "renounce_claims", "banish", "gain_hook",
    "take_vows", "change_prison", "make_puppet", "become_executioner",
    "recruit", "disfigure", "blind", "castrate", "demand_admin"};
inline constexpr std::array<std::string_view, 10> kPrisonerReleaseCostKeys12003{
    "gold", "prestige", "piety", "renown", "influence", "herd",
    "treasury", "treasury_or_gold", "merit", "barter_goods"};
inline constexpr std::size_t kPrisonerReleaseDefinitionOrdinalOffset12003 = 0x10;
inline constexpr std::size_t kPrisonerReleaseDefinitionOptionRowsOffset12003 = 0x2258;
inline constexpr std::size_t kPrisonerReleaseDefinitionOptionCountOffset12003 = 0x2264;
inline constexpr std::size_t kPrisonerReleaseDefinitionOptionRowStride12003 = 0x730;
inline constexpr std::size_t kPrisonerReleaseDefinitionOptionFlagOffset12003 = 0x368;
inline constexpr std::size_t kPrisonerReleaseContextSecondaryActorOffset12003 = 0x2E0;
inline constexpr std::size_t kPrisonerReleaseContextSecondaryRecipientOffset12003 = 0x2E4;
inline constexpr std::size_t kPrisonerReleaseContextIntermediaryOffset12003 = 0x2E8;
inline constexpr std::size_t kPrisonerReleaseContextOptionDataOffset12003 = 0x300;
inline constexpr std::size_t kPrisonerReleaseContextOptionCapacityOffset12003 = 0x308;
inline constexpr std::size_t kPrisonerReleaseContextOptionCountOffset12003 = 0x30C;

// Copied observation only. Costs are actor resources consumed on send;
// on-accept dread, stress, opinion and other effects are outside this leaf.
struct PrisonerReleasePreview12003 {
  bool available = false;
  std::string unavailable_reason = "not_evaluated";
  bridge::PlayerPrisonerFrameV1 frame{};
  std::string definition_key;
  std::uint64_t definition_stable_hash = 0;
  std::int32_t definition_ordinal = -1;
  std::uint32_t actor_character_id = 0;
  std::uint32_t recipient_character_id = 0;
  std::uint32_t jailer_character_id = 0;
  std::uint32_t prisoner_character_id = 0;
  std::uint32_t puppet_or_actor_character_id = 0;
  bool can_send = false;
  bool auto_accept = false;
  std::array<std::int64_t, 10> send_costs_raw{};
  std::int64_t raw_scale = 100000;
  std::int32_t observed_definition_option_count = 0;
  std::int32_t observed_context_option_count = 0;
  std::uint32_t selected_option_mask_bits = 0;
};

struct PrisonerReleasePreviewBindings12003 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  ck3_12002::FactionGiftBindingsV1 gift{};
  ck3_11906::GetScriptIdentifierTable get_script_identifier_table = nullptr;
  ck3_11906::LookupScriptIdentifierId lookup_script_identifier_id = nullptr;
  void (*clear_local_options)(void *) = nullptr;
};

struct PrisonerReleasePreviewAccess12003 {
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
  void *context = nullptr;
  bridge::CapturePlayerPrisonerCollectionFrameV1 capture_frame = nullptr;
  bridge::ReadPlayerPrisonerCollectionMemoryV1 read_memory = nullptr;
};

// Admit the actual .3 identity before reusing the reviewed .2 context ABI.
PrisonerReleasePreviewBindings12003 BindPrisonerReleasePreview12003(
    std::uintptr_t module_base,
    std::string_view actual_executable_sha256) noexcept;

// Synchronous owning-thread query. A fully observed false CanSend returns true;
// read/binding/selection failures return false with an unavailable reason.
// No send command is constructed or submitted.
bool ReadPrisonerReleasePreview12003(
    const PrisonerReleasePreviewBindings12003 &bindings,
    const PrisonerReleasePreviewAccess12003 &access,
    std::uint32_t jailer_character_id, std::uint32_t prisoner_character_id,
    PrisonerReleasePreview12003 &output) noexcept;

std::string SerializePrisonerReleasePreview12003(
    const PrisonerReleasePreview12003 &output);

} // namespace xar::ck3_12003
