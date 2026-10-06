#include "xar_bridge/ck3_12004_family_obligations_alliance.hpp"

namespace xar::ck3_12004 {
namespace {
inline constexpr std::uintptr_t kAllianceConstructContextRva = 0x3076C70;
inline constexpr std::uintptr_t kAllianceWarStorageSlotRva = 0x5D1DE58;
inline constexpr std::uintptr_t kAllianceWarFallbackSlotRva = 0x5D1DE40;
inline constexpr std::uintptr_t kAllianceInteractionMissingSlotRva = 0x5D1DD28;
inline constexpr std::uintptr_t kAllianceIsAlliedRva = 0x2911DD0;
inline constexpr std::uintptr_t kAllianceDefinitionKeyHashRva = 0x3F7E220;
inline constexpr std::uintptr_t kAllianceDefinitionLookupRva = 0xA055E0;
inline constexpr std::uintptr_t kAllianceCanPickWarTargetRva = 0x307A670;
inline constexpr std::uintptr_t kAllianceWasCalledRva = 0x2497750;
inline constexpr std::uintptr_t kAllianceFinalAnswerRva = 0x307BC60;
inline constexpr std::uintptr_t kAllianceSetupRva = 0x307A750;
inline constexpr std::uintptr_t kAllianceAvailabilityRva = 0x307A840;
inline constexpr std::uintptr_t kAlliancePrecheckRva = 0x307AB50;
inline constexpr std::uintptr_t kAllianceAlreadyConsideringRva = 0x307A550;
inline constexpr std::uintptr_t kAlliancePairRestrictionRva = 0x2BF5E10;
inline constexpr std::uintptr_t kAllianceDiplomaticRangeRva = 0x307D6C0;
inline constexpr std::uintptr_t kAllianceContainsParticipantRva = 0x2494B40;
} // namespace

ck3_12002::family_obligations_alliance::Bindings
BindFamilyObligationsAllianceImage(
    std::uintptr_t base, std::string_view sha) noexcept {
  namespace alliance = ck3_12002::family_obligations_alliance;
  alliance::Bindings bindings{};
  bindings.core = BindCoreImage(base, sha);
  if (!bindings.core.enabled) return bindings;
  bindings.context = BindFamilyContextImage(base, sha);
  if (!bindings.context.enabled) return bindings;
  bindings.enabled = true;
  bindings.construct_context =
      reinterpret_cast<ck3_12002::ConstructInteractionContext>(
          base + kAllianceConstructContextRva);
  bindings.war_storage_slot =
      reinterpret_cast<void **>(base + kAllianceWarStorageSlotRva);
  bindings.war_fallback_slot =
      reinterpret_cast<void **>(base + kAllianceWarFallbackSlotRva);
  bindings.interaction_missing_slot =
      reinterpret_cast<void **>(base + kAllianceInteractionMissingSlotRva);
  bindings.is_allied =
      reinterpret_cast<alliance::IsAllied>(base + kAllianceIsAlliedRva);
  bindings.key_hash = reinterpret_cast<alliance::DefinitionKeyHash>(
      base + kAllianceDefinitionKeyHashRva);
  bindings.lookup_definition = reinterpret_cast<alliance::DefinitionLookup>(
      base + kAllianceDefinitionLookupRva);
  bindings.can_pick_war_target = reinterpret_cast<alliance::CanPickWarTarget>(
      base + kAllianceCanPickWarTargetRva);
  bindings.was_called =
      reinterpret_cast<alliance::WasCalled>(base + kAllianceWasCalledRva);
  bindings.final_answer =
      reinterpret_cast<alliance::FinalAnswer>(base + kAllianceFinalAnswerRva);
  bindings.setup =
      reinterpret_cast<alliance::ContextPredicate>(base + kAllianceSetupRva);
  bindings.availability = reinterpret_cast<alliance::ContextAvailability>(
      base + kAllianceAvailabilityRva);
  bindings.send_precheck =
      reinterpret_cast<alliance::SendPrecheck>(base + kAlliancePrecheckRva);
  bindings.already_considering = reinterpret_cast<alliance::ContextPredicate>(
      base + kAllianceAlreadyConsideringRva);
  bindings.pair_restriction = reinterpret_cast<alliance::PairRestriction>(
      base + kAlliancePairRestrictionRva);
  bindings.diplomatic_range = reinterpret_cast<alliance::DiplomaticRange>(
      base + kAllianceDiplomaticRangeRva);
  bindings.contains_participant = reinterpret_cast<alliance::ContainsParticipant>(
      base + kAllianceContainsParticipantRva);
  // Optional C88 description callbacks have no actual4 mapping in this packet.
  // The existing reader retains its Boolean result and reports text unavailable.
  return bindings;
}

} // namespace xar::ck3_12004
