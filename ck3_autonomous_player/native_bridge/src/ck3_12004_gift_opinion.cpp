#include "xar_bridge/ck3_12004_gift_opinion.hpp"

#include <windows.h>

namespace xar::ck3_12004 {

ck3_12002::GiftOpinionBindings12002 BindGiftOpinionImage(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  ck3_12002::GiftOpinionBindings12002 result{};
  result.core = BindCoreImage(module_base, executable_sha256);
  if (!result.core.enabled) return result;
  result.enabled = true;
  result.module_base = module_base;
  result.modifier_database_slot = reinterpret_cast<void **>(
      module_base + kOpinionModifierDatabaseSlotRva);
  result.read_opinion = reinterpret_cast<ck3_12002::GiftReadCharacterOpinion12002>(
      module_base + kReadCharacterOpinionRva);
  result.lookup_modifier = reinterpret_cast<ck3_12002::GiftLookupOpinionModifier12002>(
      module_base + kOpinionModifierLookupRva);
  result.find_group = reinterpret_cast<ck3_12002::GiftFindOpinionGroup12002>(
      module_base + kFindActiveOpinionGroupRva);
  result.sum_modifier = reinterpret_cast<ck3_12002::GiftSumOpinionModifier12002>(
      module_base + kSumOpinionModifierRva);
  result.modifier_primary_vtable = module_base + kOpinionModifierVtableRva;
  result.modifier_secondary_vtable = module_base + kOpinionModifierSecondaryVtableRva;
  result.active_opinion_vtable = module_base + kActiveOpinionVtableRva;
  result.temporary_opinion_vtable = module_base + kTemporaryOpinionVtableRva;
  return result;
}

bool ReadCharacterOpinion(
    const ck3_12002::GiftOpinionBindings12002 &bindings,
    std::uint32_t recipient_character_id, std::uint32_t player_character_id,
    std::int32_t &output) noexcept {
  output = 0;
  if (!bindings.enabled || !bindings.core.enabled ||
      bindings.read_opinion == nullptr || recipient_character_id == 0 ||
      recipient_character_id == 0xFFFFFFFFU || player_character_id == 0 ||
      player_character_id == 0xFFFFFFFFU)
    return false;
#if defined(_MSC_VER)
  __try {
#endif
    auto *recipient = ck3_12004::ResolveCoreCharacter(bindings.core,
        static_cast<std::int32_t>(recipient_character_id));
    auto *actor = ck3_12004::ResolveCoreCharacter(bindings.core,
        static_cast<std::int32_t>(player_character_id));
    if (recipient == nullptr || actor == nullptr) return false;
    const auto first = bindings.read_opinion(recipient, actor);
    const auto second = bindings.read_opinion(recipient, actor);
    if (first != second ||
        ck3_12004::ResolveCoreCharacter(bindings.core,
            static_cast<std::int32_t>(recipient_character_id)) != recipient ||
        ck3_12004::ResolveCoreCharacter(bindings.core,
            static_cast<std::int32_t>(player_character_id)) != actor)
      return false;
    output = first;
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

} // namespace xar::ck3_12004
