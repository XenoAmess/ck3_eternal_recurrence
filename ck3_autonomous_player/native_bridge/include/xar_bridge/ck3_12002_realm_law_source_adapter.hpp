#pragma once

#include "xar_bridge/ck3_12002_realm_law.hpp"
#include "xar_bridge/ck3_12002_realm_law_enact_command_v1.hpp"
#include "xar_bridge/realm_law_native_binder_v1.hpp"
#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/ck3_12002_realm_law_components.hpp"

namespace xar::ck3_12002 {

// This context is private, durable application-main storage. Native addresses
// are reacquired for every source transaction and never enter its value DTO.
struct RealmLawCrownSource12002 {
  std::uintptr_t module_base = 0;
  std::string_view admitted_executable_sha256{};
  void *callback_context = nullptr;
  bridge::ReadRealmLawNativeRuntimeProofV1 read_runtime_proof = nullptr;
  bridge::CaptureRealmLawGovernanceSourceFrameV1 capture_frame = nullptr;
  private_law::ReadRealmLawActiveMemory read_memory = nullptr;
  private_law::RealmLawFinalTerms12002Operations final_operations{};
  private_law::RealmLawComponentBindings12002 component_operations{};
  NativeCampaignRootCharacterResolverV1 primary_title = nullptr;
  private_law::AddLawCommandAccessV1 command_access{};
  RealmLawReadback12002 readback{};
  std::array<std::uintptr_t,
      ck3_11906::private_law::kRealmLawMaximumRelevantCandidates11906>
      crown_law_addresses{};
  std::uintptr_t crown_group_address = 0;
  std::array<private_law::RealmLawComponents12002,
      ck3_11906::private_law::kRealmLawMaximumRelevantCandidates11906>
      crown_components{};
  std::array<bridge::RealmLawGovernanceSuccessionShapeV1,
      ck3_11906::private_law::kRealmLawMaximumRelevantCandidates11906>
      crown_succession_shapes{};
  std::uint64_t connection_generation = 0;
  std::string failure{};
};

// Actual native source operations for the existing LAW2/LAW4/LAW5 contract.
// Only crown_authority is projected into LAW2. The raw two-group final-terms
// catalog remains available through CaptureRealmLawReadback12002.
bridge::RealmLawNativeBinderOperationsV1
MakeRealmLawCrownSourceOperations12002() noexcept;

bool ResolveRealmLawCrownTarget12002(
    void *context, const bridge::RealmLawEnactSubmissionV1 &submission,
    bridge::RealmLawNativeEnactTargetLeaseV1 &output) noexcept;

// Admission is explicit 1.20. The old binder default remains 1.19, and no
// source callback substitutes an executable digest to pass that old default.
bool BindRealmLawCrownSource12002(
    RealmLawCrownSource12002 &source,
    std::string_view source_signature_manifest_sha256,
    bridge::RealmLawNativeBinderStateV1 &state,
    bool offline_fixture = false) noexcept;

} // namespace xar::ck3_12002
