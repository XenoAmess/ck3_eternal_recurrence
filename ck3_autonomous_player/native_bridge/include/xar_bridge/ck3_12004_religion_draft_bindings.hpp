#pragma once

#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include "xar_bridge/religion_reform12002_fullchoices.hpp"
#include "xar_bridge/religion_reform12002_group_model.hpp"
#include "xar_bridge/religion_reform12002_tenet_sources.hpp"
#include "xar_bridge/religion_reform12003_creation_terms.hpp"

namespace xar::ck3_12004::religion {

using DraftChoiceBindings = ck3_12002::religion_reform::DraftChoiceBindings;
using TenetSourcesBindings = ck3_12002::religion_reform::TenetSourcesBindings;
using DraftCreationTermsBindings =
    ck3_12002::religion_reform::creation_terms12003::Bindings;

// Existing adopted software readers; pointers belong exclusively to the
// finite mapped .4 image. No window or game registry is initialized here.
DraftChoiceBindings BindCurrentDraftChoices12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
TenetSourcesBindings BindCurrentDraftTenetSources12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
DraftCreationTermsBindings BindDraftCreationTermsImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

bool ReadCurrentDraftFullDoctrineChoices12004(const DraftChoiceBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion_reform::DraftFullDoctrineChoices &) noexcept;
bool ReadCurrentDraftGroupModel12004(const DraftChoiceBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion_reform::DraftGroupModel &) noexcept;
bool ReadCurrentDraftTenetSources12004(const TenetSourcesBindings &,
    std::uint64_t capture_epoch,
    ck3_12002::religion_reform::DraftTenetSources &) noexcept;

} // namespace xar::ck3_12004::religion
