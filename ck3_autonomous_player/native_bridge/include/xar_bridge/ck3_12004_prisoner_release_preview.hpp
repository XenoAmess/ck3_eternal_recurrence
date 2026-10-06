#pragma once

#include "xar_bridge/ck3_12004_interaction_context.hpp"
#include "xar_bridge/ck3_12003_prisoner_release_preview.hpp"

namespace xar::ck3_12004 {

// Copied software contracts; .4 native admission is performed by this binder.
using PrisonerReleasePreview12004 = ck3_12003::PrisonerReleasePreview12003;
using PrisonerReleasePreviewBindings12004 =
    ck3_12003::PrisonerReleasePreviewBindings12003;
using PrisonerReleasePreviewAccess12004 = ck3_12003::PrisonerReleasePreviewAccess12003;

PrisonerReleasePreviewBindings12004 BindPrisonerReleasePreview12004(
    std::uintptr_t module_base,
    std::string_view actual_executable_sha256) noexcept;
bool ReadPrisonerReleasePreview12004(
    const PrisonerReleasePreviewBindings12004 &bindings,
    const PrisonerReleasePreviewAccess12004 &access,
    std::uint32_t jailer_character_id, std::uint32_t prisoner_character_id,
    PrisonerReleasePreview12004 &output) noexcept;
std::string SerializePrisonerReleasePreview12004(
    const PrisonerReleasePreview12004 &output);

} // namespace xar::ck3_12004
