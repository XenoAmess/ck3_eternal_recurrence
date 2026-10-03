#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/religion_reform12002_tenet_sources.hpp"

namespace xar::ck3_12003::religion::confession_permission {

using Bindings = ck3_12002::religion_reform::TenetSourcesBindings;
using CurrentContext = ck3_12002::religion::Context;
inline constexpr const char *kSchema = "ck3_12003_confession_rite_permission_v1";
inline constexpr const char *kTenetKey = "tenet_confession";

struct Terms {
  bool available = false;
  std::string unavailable_reason{"bindings_unavailable"};
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint8_t> current_rite_status;
  std::optional<bool> has_at_least_permitted;
};

// Existing paused application-main owner only. Reuses the current Context and
// actual played actor. Consumes only the existing loaded Tenet DB and status
// getter bindings; no draft window, constructor, lookup interner or action.
bool ReadPlayerConfessionRitePermission12003(const Bindings &,
    const ck3_12002::religion::Bindings &, void *actual_actor,
    const CurrentContext &, Terms &) noexcept;
std::string SerializePlayerConfessionRitePermission12003(const Terms &);

} // namespace xar::ck3_12003::religion::confession_permission
