#include "xar_bridge/ck3_12004_pending_context.hpp"
#include "xar_bridge/ck3_12004_interaction_context.hpp"
#include "xar_bridge/ck3_12004_prisoner_named.hpp"

#include <windows.h>

namespace xar::ck3_12004 {
namespace {

struct NativeStringView {
  const char *data;
  std::int32_t size;
  std::int32_t padding;
};
static_assert(sizeof(NativeStringView) == 0x10);

bool ReadReceivedRansomFlag12004(void *, std::uintptr_t module,
                               std::string_view key,
                               std::int32_t &identifier) noexcept {
  if (module == 0) return false;
  const auto bindings = BindInteractionContext12004(module, kExecutableSha256);
  const NativeStringView view{
      key.data(), static_cast<std::int32_t>(key.size()), 0};
  if (!bindings.enabled || bindings.get_script_identifier_table == nullptr ||
      bindings.lookup_script_identifier_id == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    void *table = bindings.get_script_identifier_table();
    return table != nullptr &&
           bindings.lookup_script_identifier_id(table, &identifier, &view) !=
               nullptr && identifier >= 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool ReadReceivedNamedGold12004(std::uintptr_t module, const void *scope,
                               std::int32_t actor, std::int32_t jailer,
                               std::int32_t prisoner, std::string_view key,
                               std::int64_t &raw) noexcept {
  if (module == 0) return false;
  const auto interaction = BindInteractionContext12004(module, kExecutableSha256);
  const auto named = BindPrisonerNamedImage12004(module, kExecutableSha256);
  if (!interaction.enabled || interaction.stable_hash == nullptr ||
      !named.enabled) return false;
#if defined(_MSC_VER)
  __try {
#endif
    const auto hash = interaction.stable_hash(
        nullptr, key.data(), static_cast<std::uint32_t>(key.size()));
    // Existing received semantics: prisoner root, payer actor, recipient
    // jailer; borrow the pending interaction's native scope.
    return ReadNamedInteractionFixed12004(
        named, scope, static_cast<std::uint32_t>(prisoner),
        static_cast<std::uint32_t>(actor), static_cast<std::uint32_t>(jailer),
        key, static_cast<std::uint32_t>(hash), raw);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool ReadReceivedRansomGold12004(void *, std::uintptr_t module,
    const void *scope, std::int32_t actor, std::int32_t jailer,
    std::int32_t prisoner, std::int64_t &raw) noexcept {
  return ReadReceivedNamedGold12004(module, scope, actor, jailer, prisoner,
                                  "normal_ransom_cost_value", raw);
}

bool ReadReceivedRansomCurrentGold12004(void *, std::uintptr_t module,
    const void *scope, std::int32_t actor, std::int32_t jailer,
    std::int32_t prisoner, std::int64_t &raw) noexcept {
  return ReadReceivedNamedGold12004(module, scope, actor, jailer, prisoner,
                                  "current_gold_value", raw);
}

constexpr std::string_view kOldBuild =
    "\"build\":{\"version\":\"1.20.0.2\",\"exe_sha256\":\""
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D\"}";
constexpr std::string_view kNewBuild =
    "\"build\":{\"version\":\"1.20.0.4\",\"exe_sha256\":\""
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\"}";
constexpr std::string_view kProvenance =
    "\"provenance\":{"
    "\"backend_id\":\"ck3-1.20.0.4-native-pending-character-interaction-context-v1\","
    "\"pending_storage_slot_rva\":\"0x5D1EC80\","
    "\"character_storage_slot_rva\":\"0x5C67568\","
    "\"expiration_days_rva\":\"0x5C68CFC\","
    "\"local_routing_predicate_rva\":\"0x136D190\","
    "\"reply_validator_rva\":\"0x2968470\","
    "\"auto_accept_trigger_evaluator_rva\":\"0x372DF10\","
    "\"cost_evaluator_rva\":\"0x310CEC0\","
    "\"common_war_relation_rva\":\"0x28BC250\","
    "\"target_type_registry_getter_rva\":\"0x3795A60\","
    "\"target_type_registry_rva\":\"0x54F2AF0\","
    "\"script_identifier_name_rva\":\"0x3F4F8E0\","
    "\"reply_primary_vtable_rva\":\"0x448BC28\","
    "\"reply_secondary_vtable_rva\":\"0x448BBF8\","
    "\"war_victory_special_vtable_rva\":\"0x46C3AB0\","
    "\"war_white_peace_special_vtable_rva\":\"0x46C3B20\","
    "\"war_defeat_special_vtable_rva\":\"0x46C3B90\"}}";

} // namespace

ck3_12002::PendingCharacterInteractionNativeEnvironmentV1
BindPendingCharacterInteractionNativeEnvironment12004(
    std::uintptr_t module_base,
    std::string_view actual_executable_sha256) noexcept {
  ck3_12002::PendingCharacterInteractionNativeEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = module_base != 0 &&
      actual_executable_sha256 == kExecutableSha256;
  if (!output.exact_build_admitted) return output;
  output.pending_storage_slot = reinterpret_cast<void **>(
      module_base + kPendingStorageRva12004);
  output.character_storage_slot = reinterpret_cast<void **>(
      module_base + kPendingCharacterStorageRva12004);
  output.expiration_days = reinterpret_cast<const std::int32_t *>(
      module_base + kPendingExpirationDaysRva12004);
  output.local_routing = reinterpret_cast<
      ck3_12002::NativePendingInteractionLocalRoutingV1>(
          module_base + kPendingLocalRoutingRva12004);
  output.reply_validator = reinterpret_cast<
      ck3_12002::NativePendingInteractionReplyValidatorV1>(
          module_base + kPendingReplyValidatorRva12004);
  output.trigger_evaluator = reinterpret_cast<
      ck3_12002::NativePendingInteractionTriggerEvaluatorV1>(
          module_base + kPendingTriggerEvaluatorRva12004);
  output.cost_evaluator = reinterpret_cast<
      ck3_12002::NativePendingInteractionCostEvaluatorV1>(
          module_base + kPendingCostEvaluatorRva12004);
  output.common_war_relation = reinterpret_cast<
      ck3_12002::NativePendingInteractionCommonWarRelationV1>(
          module_base + kPendingCommonWarRelationRva12004);
  output.target_type_registry = reinterpret_cast<
      ck3_12002::NativePendingInteractionTargetTypeRegistryGetterV1>(
          module_base + kPendingTargetRegistryGetterRva12004);
  output.script_identifier_name = reinterpret_cast<
      ck3_12002::NativePendingInteractionScriptIdentifierNameV1>(
          module_base + kPendingIdentifierNameRva12004);
  output.reply_primary_vtable = module_base + kPendingReplyPrimaryVtableRva12004;
  output.reply_secondary_vtable = module_base + kPendingReplySecondaryVtableRva12004;
  output.war_victory_special_vtable = module_base + kPendingWarVictoryVtableRva12004;
  output.war_white_peace_special_vtable =
      module_base + kPendingWarWhitePeaceVtableRva12004;
  output.war_defeat_special_vtable = module_base + kPendingWarDefeatVtableRva12004;
  return output;
}

game::ReadPendingCharacterInteractionContextResultV1
ReadPendingCharacterInteractionContext12004(
    const ck3_12002::PendingCharacterInteractionNativeEnvironmentV1 &environment,
    const ck3_12002::PendingCharacterInteractionAccessV1 &access,
    const ck3_12002::PendingCharacterInteractionContextRequestV1 &request,
    game::PendingCharacterInteractionContextV1 &output) noexcept {
  auto selected_access = access;
  selected_access.read_ransom_flag_identifier = ReadReceivedRansomFlag12004;
  selected_access.read_ransom_named_gold = ReadReceivedRansomGold12004;
  selected_access.read_ransom_named_current_gold =
      ReadReceivedRansomCurrentGold12004;
  return ck3_12002::ReadPendingCharacterInteractionContextV1(
      environment, selected_access, request, output);
}

std::string SerializePendingCharacterInteractionContext12004(
    const game::PendingCharacterInteractionContextV1 &context) {
  auto wire = ck3_12002::SerializePendingCharacterInteractionContextV1(context);
  if (wire.empty()) return {};
  // Fixed generated JSON object keys, never user-text values.
  const auto build_at = wire.find(kOldBuild);
  if (build_at == std::string::npos) return {};
  wire.replace(build_at, kOldBuild.size(), kNewBuild);
  const auto provenance_at = wire.rfind("\"provenance\":{");
  if (provenance_at == std::string::npos) return {};
  wire.replace(provenance_at, wire.size() - provenance_at, kProvenance);
  return wire;
}

} // namespace xar::ck3_12004
