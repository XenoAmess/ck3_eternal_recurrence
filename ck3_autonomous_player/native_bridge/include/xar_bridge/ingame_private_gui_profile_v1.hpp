#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

namespace xar::ck3_11906 {

// Strict identity/profile join for the existing private decision and exit paths.
// The actual .4 branch cannot select the retained .3 native coordinates.
constexpr bool IngamePrivateGuiIdentityAdmittedV1(std::string_view version,
    std::string_view executable_sha256,GuiAbiRevisionV1 revision) noexcept {
  if(revision==GuiAbiRevisionV1::crozier12004)
    return version==ck3_12004::kGameVersion && executable_sha256==ck3_12004::kExecutableSha256;
  if(revision==GuiAbiRevisionV1::crozier12003)
    return version=="1.20.0.3" && executable_sha256=="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
  return false;
}

} // namespace xar::ck3_11906
