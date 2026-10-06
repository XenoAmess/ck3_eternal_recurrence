#pragma once

#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/religion_reform12002_ai_inputs_mailbox.hpp"
#include "xar_bridge/religion_rite_governance12002_context.hpp"
#include "xar_bridge/religion_rite_governance12002_organization_members.hpp"

namespace xar::ck3_12004::religion::adopted {

using AIReformInputsBindings =
    ck3_12002::PlayerReligionAIReformInputsBindings12002;
using GovernanceBindings = ck3_12002::religion::governance::Bindings;
using MembersBindings = ck3_12002::religion::organization::members::Bindings;

AIReformInputsBindings BindPlayerReligionAIReformInputsImage12004(
    std::uintptr_t image_base, std::string_view actual_sha) noexcept;
GovernanceBindings BindRiteGovernanceImage12004(
    std::uintptr_t image_base, std::string_view actual_sha) noexcept;
MembersBindings BindOrganizationMembersImage12004(
    std::uintptr_t image_base, std::string_view actual_sha) noexcept;

bool ReadPlayerReligionAIReformInputs12004(const AIReformInputsBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::PlayerReligionAIReformInputsObservation12002 &) noexcept;
bool ReadPlayedRiteGovernance12004(const GovernanceBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion::governance::Context &) noexcept;
bool ReadPlayedOrganizationMembers12004(const MembersBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion::organization::members::Snapshot &) noexcept;

} // namespace xar::ck3_12004::religion::adopted
