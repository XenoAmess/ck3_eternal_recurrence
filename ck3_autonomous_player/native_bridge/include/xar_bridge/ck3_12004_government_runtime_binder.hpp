#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/government_runtime_adapter_source_adapter_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

namespace xar::ck3_12004 {

// Exact .4 operands and targets are recorded in native-government's finite
// family maps. These are independent native bindings, not old-build aliases.
inline constexpr std::uintptr_t kGovernmentRuntimeResolverRva = 0x28C2DF0;
inline constexpr std::uintptr_t kGovernmentRuntimeFallbackSlotRva = 0x5D1E2A8;
inline constexpr std::uintptr_t kGovernmentRuntimeIdentifierNameRva = 0x3F4F8E0;
inline constexpr std::uintptr_t kGovernmentRuntimeFeatureRootSlotRva = 0x5CB87F8;
inline constexpr std::uintptr_t kGovernmentRuntimeFeatureRegistryRva = 0x47334D0;
inline constexpr std::uintptr_t kGovernmentRuntimeFeatureRegistryEndRva = 0x4733580;
inline constexpr std::uintptr_t kGovernmentRuntimeScriptDlcSetRva = 0x5CC15E0;
inline constexpr std::size_t kGovernmentRuntimeNativeFeatureCount = 44;

struct GovernmentRuntimeBindingsV1 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  CoreBindings core{};
  ck3_11906::NativeCampaignRootCharacterResolverV1 government = nullptr;
  ck3_11906::NativeLoadedFeatureScriptIdentifierNameV1 identifier_name = nullptr;
  void **government_fallback_slot = nullptr;
  void **feature_root_slot = nullptr;
  const std::uint32_t *feature_registry = nullptr;
  void *script_dlc_set = nullptr;
};

GovernmentRuntimeBindingsV1 BindGovernmentRuntimeImageV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Captures only the campaign fields actually consumed by the existing GOV
// source adapter, with current feature/DLC identities in the same paused frame.
// It does not publish a complete CampaignRootContext or complete Snapshot.
bool ReadGovernmentRuntimeCollectorSampleV1(
    const GovernmentRuntimeBindingsV1 &bindings,
    const ck3_11906::CampaignRootAccessV1 &campaign_access,
    const ck3_11906::LoadedFeatureManifestAccessV1 &feature_access,
    std::uint64_t expected_revision,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    bridge::private_observer::GovernmentRuntimeAdapterCollectorSampleV1 &output)
    noexcept;

} // namespace xar::ck3_12004
