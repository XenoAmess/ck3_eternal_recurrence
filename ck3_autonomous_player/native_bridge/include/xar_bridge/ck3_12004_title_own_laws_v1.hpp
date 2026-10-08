#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12003_title_properties_leaf.hpp"
#include "xar_bridge/title_own_laws_v1.hpp"

namespace xar::ck3_12004 {
struct TitleOwnLawsBindingsV1 {
  bool enabled = false;
  CoreBindings core;
  ck3_12003::title_properties::Bindings titles;
};

// Exact .4 address binding; no process discovery or native call.
TitleOwnLawsBindingsV1 BindTitleOwnLawsImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const CoreBindings &actual_core) noexcept;

// Owning-main-thread read only. The caller's mailbox owns revision/provenance.
// Every uint32 full TitleID except UINT32_MAX is a valid selector, including
// IDs whose generation sets the high bit. An unresolved ID remains unavailable.
game::ReadTitleOwnLawsV1Result ReadTitleOwnLawsV1(
    const TitleOwnLawsBindingsV1 &bindings, std::uint32_t title_id,
    game::TitleOwnLawsV1 &output) noexcept;
} // namespace xar::ck3_12004
