#pragma once

#include "xar_bridge/ck3_12002_province.hpp"
#include "xar_bridge/title_holder_v1.hpp"

namespace xar::ck3_12003 {

struct TitleHolderBindingsV1 {
  bool enabled = false;
  ck3_12002::ProvinceBindings provinces;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void *(*immediate_liege)(void *) = nullptr;
  void *(*top_liege)(void *) = nullptr;
  // Exact-profile optional point reader; no engine pointer escapes the DTO.
  bool (*read_title_key)(const void *, std::string &) noexcept = nullptr;
};

TitleHolderBindingsV1 BindTitleHolderImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Application-main caller supplies its current paused frame. This reads one
// requested full title ID at any native tier, without own-partition filtering.
game::ReadTitleHolderV1Result ReadTitleHolderV1(
    const TitleHolderBindingsV1 &bindings, const game::Snapshot &paused_scope,
    std::int32_t title_id, game::TitleHolderV1 &output) noexcept;

} // namespace xar::ck3_12003
